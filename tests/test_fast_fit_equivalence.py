"""
Equivalence tests for FHLSNN fast vectorized fit vs _partial_fit_reference.

PRD Step 1a requirement:
Assert the fast and reference fits give identical segments (V, W, class, in order)
within 1e-12 and identical predictions across 5 datasets, 3 seeds, and 3 theta values.
"""

import pytest
import numpy as np
from sklearn.datasets import load_iris, load_wine, load_breast_cancer
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils import resample

from ml_service.benchmark.datasets import load_dataset
from ml_service.fhlsnn.fhlsnn import FHLSNN


def _make_synthetic_2d(n_points=100, seed=42):
    """Synthetic 2-D dataset with frequent cross-class alternating points."""
    rng = np.random.RandomState(seed)
    grid = np.linspace(0.1, 0.9, int(np.sqrt(n_points)))
    X = []
    y = []
    for i, x1 in enumerate(grid):
        for j, x2 in enumerate(grid):
            X.append([x1, x2])
            y.append((i + j) % 2)
    X = np.array(X, dtype=np.float64)
    y = np.array(y, dtype=int)
    X += rng.normal(0, 0.005, X.shape)
    return MinMaxScaler().fit_transform(X), y


# Pre-load static data fixtures for speed
@pytest.fixture(scope="module")
def dataset_cache():
    cache = {}
    
    # 1. Iris
    i_X, i_y = load_iris(return_X_y=True)
    cache['iris'] = (MinMaxScaler().fit_transform(i_X), i_y.astype(int))
    
    # 2. Wine
    w_X, w_y = load_wine(return_X_y=True)
    cache['wine'] = (MinMaxScaler().fit_transform(w_X), w_y.astype(int))
    
    # 3. Breast Cancer raw (subsampling will be done per seed)
    b_X, b_y = load_breast_cancer(return_X_y=True)
    cache['bc_raw'] = (b_X, b_y.astype(int))
    
    # 4. Pendigits 1000
    p_X, p_y = load_dataset('pendigits')
    p_X_sc = MinMaxScaler().fit_transform(p_X)
    cache['pen_1k'] = (p_X_sc[:1000], p_y[:1000].astype(int))
    
    return cache


@pytest.mark.parametrize("dname", ['iris', 'wine', 'bc_1k', 'pen_1k', 'synth_2d'])
@pytest.mark.parametrize("seed", [42, 100, 2026])
@pytest.mark.parametrize("theta", [0.05, 0.2, 0.8])
def test_fast_reference_equivalence(dataset_cache, dname, seed, theta):
    """Assert fast and reference fits give identical segments (within 1e-12) and predictions."""
    if dname == 'iris':
        X, y = dataset_cache['iris']
    elif dname == 'wine':
        X, y = dataset_cache['wine']
    elif dname == 'bc_1k':
        b_X, b_y = dataset_cache['bc_raw']
        X_sub, y = resample(b_X, b_y, n_samples=1000, replace=True, random_state=seed)
        X = MinMaxScaler().fit_transform(X_sub)
    elif dname == 'pen_1k':
        X, y = dataset_cache['pen_1k']
    elif dname == 'synth_2d':
        X, y = _make_synthetic_2d(n_points=100, seed=seed)
    else:
        raise ValueError(f"Unknown dataset: {dname}")

    gamma = 0.5
    
    # Reference fit
    m_ref = FHLSNN(zeta=theta, gamma=gamma, random_state=seed, use_intersection_test=True)
    m_ref._fit_reference(X, y)

    # Fast fit
    m_fast = FHLSNN(zeta=theta, gamma=gamma, random_state=seed, use_intersection_test=True)
    m_fast.fit(X, y)

    # Exact assertions required by PRD Step 1a
    assert m_ref.n_segments_ == m_fast.n_segments_, (
        f"Segment count mismatch on {dname} (seed={seed}, theta={theta}): "
        f"{m_ref.n_segments_} (ref) vs {m_fast.n_segments_} (fast)"
    )
    assert np.allclose(m_ref._V, m_fast._V, atol=1e-12), (
        f"V matrix mismatch on {dname} (seed={seed}, theta={theta})"
    )
    assert np.allclose(m_ref._W, m_fast._W, atol=1e-12), (
        f"W matrix mismatch on {dname} (seed={seed}, theta={theta})"
    )
    assert np.array_equal(m_ref._cls, m_fast._cls), (
        f"Class array mismatch on {dname} (seed={seed}, theta={theta})"
    )

    # Identical predictions assertion
    p_ref = m_ref.predict(X)
    p_fast = m_fast.predict(X)
    assert np.array_equal(p_ref, p_fast), (
        f"Predictions mismatch on {dname} (seed={seed}, theta={theta})"
    )
