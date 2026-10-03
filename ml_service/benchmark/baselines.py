import numpy as np
from imblearn.under_sampling import CondensedNearestNeighbour, EditedNearestNeighbours
from sklearn.cluster import KMeans
from typing import Tuple

def run_cnn(X: np.ndarray, y: np.ndarray, random_state: int = None) -> Tuple[np.ndarray, np.ndarray, int]:
    """Condensed Nearest Neighbour."""
    cnn = CondensedNearestNeighbour(random_state=random_state)
    X_res, y_res = cnn.fit_resample(X, y)
    return X_res, y_res, len(X_res)

def run_enn(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, int]:
    """Edited Nearest Neighbours."""
    enn = EditedNearestNeighbours()
    X_res, y_res = enn.fit_resample(X, y)
    return X_res, y_res, len(X_res)

def run_kmeans_prototypes(X: np.ndarray, y: np.ndarray, k_per_class: int, random_state: int = None) -> Tuple[np.ndarray, np.ndarray, int]:
    """Per-class K-Means prototype selection."""
    classes = np.unique(y)
    X_res = []
    y_res = []
    for c in classes:
        X_c = X[y == c]
        if len(X_c) < k_per_class:
            k = len(X_c)
        else:
            k = k_per_class
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init="auto")
        kmeans.fit(X_c)
        X_res.append(kmeans.cluster_centers_)
        y_res.extend([c] * k)
    
    if len(X_res) == 0:
        return np.array([]), np.array([]), 0
        
    X_res = np.vstack(X_res)
    y_res = np.array(y_res)
    return X_res, y_res, len(X_res)

def run_random_subsampling(X: np.ndarray, y: np.ndarray, ratio: float, random_state: int = None) -> Tuple[np.ndarray, np.ndarray, int]:
    """Stratified random subsampling."""
    rng = np.random.RandomState(random_state)
    classes = np.unique(y)
    X_res = []
    y_res = []
    for c in classes:
        X_c = X[y == c]
        n_keep = max(1, int(len(X_c) * ratio))
        idx = rng.choice(len(X_c), n_keep, replace=False)
        X_res.append(X_c[idx])
        y_res.extend([c] * n_keep)
        
    X_res = np.vstack(X_res)
    y_res = np.array(y_res)
    return X_res, y_res, len(X_res)
