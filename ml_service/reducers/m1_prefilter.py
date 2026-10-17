import numpy as np
from sklearn.neighbors import NearestNeighbors
from imblearn.under_sampling import EditedNearestNeighbours
from ml_service.benchmark.baselines import run_enn
from ml_service.reducers.types import ReductionResult
from typing import Tuple

def run_m1_prefilter(
    X: np.ndarray, 
    y: np.ndarray, 
    keep_fraction: float = 0.5, 
    interior_keep_rate: float = 0.1, 
    edit_first: bool = False,
    random_state: int = None
) -> Tuple[np.ndarray, np.ndarray, ReductionResult]:
    """
    M1: Boundary-Proximity Pre-Filtering.
    Selects samples PER CLASS. Ensures at least 2 samples per class are kept.
    Returns: X_reduced, y_reduced, ReductionResult
    """
    rng = np.random.RandomState(random_state)
    
    n_samples = len(X)
    facts = {}
    
    if n_samples == 0:
        return X, y, ReductionResult(np.array([], dtype=int), np.array([], dtype=int), {})
        
    classes, counts = np.unique(y, return_counts=True)
    if len(classes) < 2:
        idx = np.arange(n_samples)
        return X, y, ReductionResult(idx, np.array([], dtype=int), {})
        
    # Apply ENN if edit_first
    valid_mask = np.ones(n_samples, dtype=bool)
    enn_removed_idx = []
    
    if edit_first:
        enn = EditedNearestNeighbours()
        enn.fit_resample(X, y)
        kept_by_enn = enn.sample_indices_
        
        valid_mask.fill(False)
        valid_mask[kept_by_enn] = True
        
        enn_removed_idx = np.where(~valid_mask)[0]
        for i in enn_removed_idx:
            facts[int(i)] = {'reason': 'removed_by_enn'}
            
    min_dist_to_other = np.full(n_samples, np.inf)
    
    for c in classes:
        # Only use valid points to build the KDTree and query
        idx_c = np.where((y == c) & valid_mask)[0]
        idx_other = np.where((y != c) & valid_mask)[0]
        
        if len(idx_other) == 0:
            continue
            
        nn = NearestNeighbors(n_neighbors=1, algorithm='kd_tree')
        nn.fit(X[idx_other])
        
        distances, _ = nn.kneighbors(X[idx_c])
        min_dist_to_other[idx_c] = distances.flatten()
        
    kept_idx_list = []
    removed_idx_list = list(enn_removed_idx)
    
    for c in classes:
        idx_c = np.where((y == c) & valid_mask)[0]
        if len(idx_c) <= 2:
            kept_idx_list.extend(idx_c)
            continue
            
        dists_c = min_dist_to_other[idx_c]
        threshold = np.quantile(dists_c, keep_fraction)
        
        sorted_c = idx_c[np.argsort(dists_c)]
        must_keep = sorted_c[:2]
        rest = sorted_c[2:]
        
        kept_class = list(must_keep)
        for i in rest:
            dist = min_dist_to_other[i]
            if dist <= threshold:
                kept_class.append(i)
            else:
                if rng.rand() < interior_keep_rate:
                    kept_class.append(i)
                else:
                    removed_idx_list.append(i)
                    perc = float((dist > dists_c).mean() * 100.0)
                    same_class_dists = np.linalg.norm(X[idx_c] - X[i], axis=1)
                    n_same = int(np.sum(same_class_dists <= dist)) - 1 # exclude self
                    facts[int(i)] = {
                        'class': int(c),
                        'nearest_other_class_dist': float(dist),
                        'percentile_in_class': perc,
                        'same_class_neighbors_in_radius': n_same
                    }
                    
        kept_idx_list.extend(kept_class)
        
    kept_idx = np.array(kept_idx_list, dtype=int)
    removed_idx = np.array(removed_idx_list, dtype=int)
    
    kept_idx = np.sort(kept_idx)
    X_res = X[kept_idx]
    y_res = y[kept_idx]
    
    result = ReductionResult(kept_idx=kept_idx, removed_idx=removed_idx, facts=facts)
    return X_res, y_res, result
