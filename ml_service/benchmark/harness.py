"""
Benchmark harness – PRD 4.5 (evaluation protocol).

Protocol (PRD 4.5 "Common fit set"):
  For EVERY method (including the unreduced reference and classical baselines)
  the validation split is carved out FIRST.  All methods then train on the
  same fit set (80 % of the training fold).  n_train means the fit-set size.
  Min-max scaling is fit on the fit set only (no leakage).

  Fold structure:
    outer fold  → train_idx / test_idx   (StratifiedKFold)
    inner split → fit_idx   / val_idx    (stratified 20 % of train_idx)

  The scaler's fit() is called only on X[fit_idx].
  The scaler's transform() is called on val and test.
  No row from test_idx ever reaches fit().

Hyperparameter tuning (PRD 4.5):
  θ (zeta) AND γ (gamma) are tuned once per outer fold on that fold's validation
  split only using a small grid over the unreduced model. The best (θ, γ) pair is
  then frozen for all reduction methods in that fold.
"""

import numpy as np
import time
from itertools import product
from typing import Callable, Dict, Any, Optional, Tuple
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
from sklearn.preprocessing import MinMaxScaler

from ml_service.benchmark.metrics import (
    compute_classification_metrics,
    compute_reduction_metrics,
)


# ── fold-level primitives (shared by harness and sweep script) ─────────────
def prepare_fold(X, y, train_idx, test_idx, val_size=0.20, random_state=42):
    """Carve validation from training fold, scale on fit set only.

    Returns dict with keys:
        fit_idx, val_idx, test_idx (absolute indices into X),
        X_fit, y_fit, X_val, y_val, X_test, y_test (scaled arrays),
        scaler (fitted MinMaxScaler), n_train (fit-set size).
    """
    sss = StratifiedShuffleSplit(
        n_splits=1, test_size=val_size, random_state=random_state
    )
    fit_local, val_local = next(sss.split(X[train_idx], y[train_idx]))
    fit_idx = train_idx[fit_local]
    val_idx = train_idx[val_local]

    assert len(np.intersect1d(fit_idx, test_idx)) == 0, "LEAKAGE: fit∩test"
    assert len(np.intersect1d(val_idx, test_idx)) == 0, "LEAKAGE: val∩test"

    scaler = MinMaxScaler()
    X_fit  = scaler.fit_transform(X[fit_idx])
    X_val  = scaler.transform(X[val_idx])
    X_test = scaler.transform(X[test_idx])

    return {
        'fit_idx': fit_idx, 'val_idx': val_idx, 'test_idx': test_idx,
        'X_fit': X_fit, 'y_fit': y[fit_idx],
        'X_val': X_val, 'y_val': y[val_idx],
        'X_test': X_test, 'y_test': y[test_idx],
        'scaler': scaler, 'n_train': len(fit_idx),
    }


def get_cv_folds(X, y, n_splits=5, val_size=0.20, random_state=42):
    """Generator yielding prepared fold dictionaries for outer CV.

    Yields dicts with:
        fold_idx, fit_idx, val_idx, test_idx,
        X_fit, y_fit, X_val, y_val, X_test, y_test,
        scaler, n_train
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        fd = prepare_fold(X, y, train_idx, test_idx, val_size=val_size, random_state=random_state)
        fd['fold_idx'] = fold_idx
        yield fd


def run_one_method(fold_data, model_cls, model_params,
                   pre_reducer_fn=None, pre_reducer_params=None,
                   post_reducer_fn=None, post_reducer_params=None):
    """Train and evaluate a single method on a prepared fold.

    Returns dict with accuracy, macro_f1, n_segments, stored_vectors,
    reduction_vs_raw, zero_mem_frac, train_time_s, and the fitted model.
    """
    X_fit = fold_data['X_fit']
    y_fit = fold_data['y_fit']
    X_test = fold_data['X_test']
    y_test = fold_data['y_test']
    X_val = fold_data['X_val']
    y_val = fold_data['y_val']
    n_train = fold_data['n_train']

    # pre-reducer
    if pre_reducer_fn is not None:
        pre_ret = pre_reducer_fn(X_fit, y_fit, **(pre_reducer_params or {}))
        X_fit_red, y_fit_red = pre_ret[0], pre_ret[1]
    else:
        X_fit_red, y_fit_red = X_fit, y_fit

    # train
    model = model_cls(**model_params)
    t0 = time.perf_counter()
    if len(y_fit_red) > 0:
        model.fit(X_fit_red, y_fit_red)

    # post-reducer
    if post_reducer_fn is not None:
        post_ret = post_reducer_fn(model, X_val, y_val, **(post_reducer_params or {}))
        if isinstance(post_ret, tuple):
            model = post_ret[0]
        else:
            model = post_ret

    train_time_s = time.perf_counter() - t0

    # predict
    y_pred = model.predict(X_test)
    class_met = compute_classification_metrics(y_test, y_pred)
    zero_mem_frac = getattr(model, '_last_zero_mem_frac', 0.0)
    n_segments = getattr(model, 'n_segments_', 0)

    # stored vectors
    stored_vecs = 0
    for seg in model.segments_:
        if np.array_equal(seg['V'], seg['W']):
            stored_vecs += 1
        else:
            stored_vecs += 2

    red_met = compute_reduction_metrics(n_train=n_train, stored_vectors=stored_vecs)

    return {
        **class_met,
        'n_segments': n_segments,
        'stored_vectors': stored_vecs,
        'zero_mem_frac': zero_mem_frac,
        'train_time_s': train_time_s,
        **red_met,
        'model': model,
    }



# ── hyperparameter grids (PRD 4.5) ────────────────────────────────────────
DEFAULT_THETA_GRID = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
DEFAULT_GAMMA_GRID = [0.5, 1.0, 2.0, 5.0]


def tune_hyperparams(
    X_fit: np.ndarray,
    y_fit: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    model_cls: Callable,
    base_params: Dict[str, Any],
    theta_grid: list = None,
    gamma_grid: list = None,
) -> Tuple[float, float]:
    """Grid-search (θ, γ) on the validation split.

    Returns the best (theta, gamma) pair by validation accuracy.
    Tie-break (PRD 4.5): when several (θ, γ) pairs reach the same validation
    accuracy, choose the one with fewer segments (larger θ).
    """
    theta_grid = theta_grid or DEFAULT_THETA_GRID
    gamma_grid = gamma_grid or DEFAULT_GAMMA_GRID

    best_acc   = -1.0
    best_theta = theta_grid[0]
    best_gamma = gamma_grid[0]
    min_segs   = float('inf')

    for theta, gamma in product(theta_grid, gamma_grid):
        params = {**base_params, 'zeta': theta, 'gamma': gamma}
        mdl = model_cls(**params)
        mdl.fit(X_fit, y_fit)
        y_pred_val = mdl.predict(X_val)
        acc = float(np.mean(y_pred_val == y_val))
        n_segs = getattr(mdl, 'n_segments_', float('inf'))
        if acc > best_acc or (acc == best_acc and (n_segs < min_segs or (n_segs == min_segs and theta > best_theta))):
            best_acc   = acc
            min_segs   = n_segs
            best_theta = theta
            best_gamma = gamma

    return best_theta, best_gamma

