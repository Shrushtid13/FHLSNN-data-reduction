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
  θ (zeta) AND γ (gamma) are tuned once per dataset on the validation split
  using a small grid over the unreduced model.  The best (θ, γ) pair is then
  frozen for all reduction methods on that dataset.
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
    The model is re-trained from scratch for each candidate.
    """
    theta_grid = theta_grid or DEFAULT_THETA_GRID
    gamma_grid = gamma_grid or DEFAULT_GAMMA_GRID

    best_acc   = -1.0
    best_theta = theta_grid[0]
    best_gamma = gamma_grid[0]

    for theta, gamma in product(theta_grid, gamma_grid):
        params = {**base_params, 'zeta': theta, 'gamma': gamma}
        mdl = model_cls(**params)
        mdl.fit(X_fit, y_fit)
        y_pred_val = mdl.predict(X_val)
        acc = float(np.mean(y_pred_val == y_val))
        if acc > best_acc:
            best_acc   = acc
            best_theta = theta
            best_gamma = gamma

    return best_theta, best_gamma


def run_experiment(
    X: np.ndarray,
    y: np.ndarray,
    model_cls: Callable,
    model_params: Dict[str, Any],
    pre_reducer_fn: Optional[Callable] = None,
    pre_reducer_params: Optional[Dict[str, Any]] = None,
    post_reducer_fn: Optional[Callable] = None,
    post_reducer_params: Optional[Dict[str, Any]] = None,
    tune_theta_gamma: bool = False,
    theta_grid: Optional[list] = None,
    gamma_grid: Optional[list] = None,
    n_splits: int = 5,
    val_size: float = 0.20,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Stratified k-fold cross-validation with a common fit/val/test split.

    Args:
        pre_reducer_fn:  instance-level reducer called AFTER scaling, BEFORE training.
                         Signature: (X_fit, y_fit, **params) -> (X_red, y_red, n_kept)
        post_reducer_fn: segment-level reducer called AFTER training.
                         Signature: (model, X_val, y_val, **params) -> pruned_model
        tune_theta_gamma: if True, tune zeta and gamma on val before training;
                         model_params must NOT contain zeta/gamma (they are overwritten).
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    metrics_list = []

    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y)):

        # ── carve validation from training fold (ALWAYS, for every method) ─
        # PRD 4.5: the validation split is carved first for every method.
        sss = StratifiedShuffleSplit(
            n_splits=1, test_size=val_size, random_state=random_state
        )
        fit_local, val_local = next(sss.split(X[train_idx], y[train_idx]))
        fit_idx = train_idx[fit_local]   # absolute indices into X
        val_idx = train_idx[val_local]

        # Assertion: no test index leaks into fit or val
        assert len(np.intersect1d(fit_idx, test_idx)) == 0, "LEAKAGE: fit∩test"
        assert len(np.intersect1d(val_idx, test_idx)) == 0, "LEAKAGE: val∩test"

        X_fit_raw = X[fit_idx]
        y_fit     = y[fit_idx]
        X_val_raw = X[val_idx]
        y_val     = y[val_idx]
        X_test_raw = X[test_idx]
        y_test     = y[test_idx]
        n_train    = len(fit_idx)        # PRD 4.4: n_train = fit-set size

        # ── scale on fit set only ───────────────────────────────────────
        scaler     = MinMaxScaler()
        X_fit      = scaler.fit_transform(X_fit_raw)   # fit() called once, here
        X_val      = scaler.transform(X_val_raw)
        X_test     = scaler.transform(X_test_raw)

        # ── optional (θ, γ) tuning ──────────────────────────────────────
        if tune_theta_gamma:
            best_theta, best_gamma = tune_hyperparams(
                X_fit, y_fit, X_val, y_val,
                model_cls, model_params, theta_grid, gamma_grid,
            )
            params = {**model_params, 'zeta': best_theta, 'gamma': best_gamma}
        else:
            params = model_params
            best_theta = model_params.get('zeta', None)
            best_gamma = model_params.get('gamma', None)

        # ── instance-level pre-reducer (M1, CNN, ENN, k-means, random) ─
        if pre_reducer_fn is not None:
            pre_ret = pre_reducer_fn(
                X_fit, y_fit, **(pre_reducer_params or {})
            )
            # Depending on reducer, it might return 3 items (X, y, result)
            X_fit_red, y_fit_red = pre_ret[0], pre_ret[1]
            if hasattr(pre_ret[2], 'kept_idx'):
                # It's a ReductionResult
                stored_vecs = len(pre_ret[0])
            else:
                stored_vecs = pre_ret[2]
        else:
            X_fit_red, y_fit_red = X_fit, y_fit
            stored_vecs = None   # determined from model after fit

        # ── train ────────────────────────────────────────────────────────
        model = model_cls(**params)
        t0 = time.perf_counter()
        model.fit(X_fit_red, y_fit_red)

        # ── segment-level post-reducer (M3) ──────────────────────────────
        if post_reducer_fn is not None:
            post_ret = post_reducer_fn(model, X_val, y_val, **(post_reducer_params or {}))
            if isinstance(post_ret, tuple):
                model, facts = post_ret
            else:
                model = post_ret

        train_time_s = time.perf_counter() - t0

        # ── predict ──────────────────────────────────────────────────────
        t0      = time.perf_counter()
        y_pred  = model.predict(X_test)
        recall_s = time.perf_counter() - t0
        recall_ms_per_pattern = recall_s / len(X_test) * 1000.0

        zero_mem_frac = getattr(model, '_last_zero_mem_frac', None)

        # ── stored vectors ────────────────────────────────────────────────
        if stored_vecs is None:
            if hasattr(model, 'get_stored_vectors_count'):
                stored_vecs = model.get_stored_vectors_count()
            else:
                stored_vecs = len(X_fit_red)

        n_segments = getattr(model, 'n_segments_', None)

        class_met = compute_classification_metrics(y_test, y_pred)
        red_met   = compute_reduction_metrics(
            n_train=n_train,
            stored_vectors=stored_vecs,
        )

        fold_row = {
            'fold':                  fold,
            'n_train':               n_train,
            'best_theta':            best_theta,
            'best_gamma':            best_gamma,
            'n_segments':            n_segments,
            'stored_vectors':        stored_vecs,
            'zero_mem_frac':         zero_mem_frac,
            'train_time_s':          train_time_s,
            'recall_ms_per_pattern': recall_ms_per_pattern,
            **class_met,
            **red_met,
        }
        metrics_list.append(fold_row)

    # ── aggregate ────────────────────────────────────────────────────────
    agg = {}
    skip = {'fold'}
    for key in metrics_list[0]:
        if key in skip:
            continue
        vals = [m[key] for m in metrics_list if m[key] is not None]
        if vals:
            agg[f'{key}_mean'] = float(np.mean(vals))
            agg[f'{key}_std']  = float(np.std(vals))

    return {'folds': metrics_list, 'aggregate': agg}
