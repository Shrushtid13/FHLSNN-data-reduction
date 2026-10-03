import pytest
import numpy as np
from ml_service.reducers.m1_prefilter import run_m1_prefilter
from ml_service.reducers.m3_prune import run_m3_prune
from ml_service.fhlsnn.fhlsnn import FHLSNN

def test_m1_per_class():
    """M1 must select PER CLASS (keep_fraction applied within each class)
    and keep at least 2 samples per class (or all if fewer)."""
    # Class 0 near x=0
    # Classes 1 and 2 overlapping near x=5
    X = np.array([
        [0.0, 0.0], [0.1, 0.0], [0.2, 0.0],  # class 0 (far)
        [5.0, 5.0], [5.1, 5.0], [5.2, 5.0],  # class 1 (overlapping)
        [5.05, 5.05], [5.15, 5.05], [5.25, 5.0] # class 2 (overlapping)
    ])
    y = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])
    
    # Very small keep fraction to force pruning
    X_res, y_res, result = run_m1_prefilter(X, y, keep_fraction=0.1, interior_keep_rate=0.0)
    
    classes, counts = np.unique(y_res, return_counts=True)
    assert len(classes) == 3
    # Must keep at least 2 samples per class
    for c in counts:
        assert c >= 2
        
    assert len(result.kept_idx) == len(X_res)

def test_m3_prune_constraints():
    """
    (a) Count wins only for CORRECTLY classified validation patterns.
    (b) Never prune the last segment of a class.
    (c) Never mutate the input model.
    """
    model = FHLSNN()
    model.segments_ = [
        {'V': np.array([0.0]), 'W': np.array([0.1]), 'class': 0}, # seg 0
        {'V': np.array([0.5]), 'W': np.array([0.6]), 'class': 0}, # seg 1
        {'V': np.array([1.0]), 'W': np.array([1.1]), 'class': 1}  # seg 2
    ]
    model.n_segments_ = 3
    model._rebuild_matrices()
    
    # Validation data
    X_val = np.array([
        [0.05],  # Near seg 0, true class 0 -> CORRECT -> seg 0 gets 1 win
        [0.55],  # Near seg 1, true class 1 -> MISCLASSIFIED (model predicts 0) -> seg 1 gets 0 wins
                 # Note: model predicts class 0, but true is 1. Seg 1 wins, but is incorrect.
    ])
    y_val = np.array([0, 1])
    
    # Since seg 2 gets 0 wins, and seg 1 gets 0 wins
    # Prune with threshold=1
    pruned_model, facts = run_m3_prune(model, X_val, y_val, threshold=1)
    
    # (a) M3 must count wins only for CORRECT classification. Seg 1 got a win structurally, but it's incorrect.
    # Therefore seg 1 has 0 valid wins and gets pruned.
    # Seg 0 has 1 valid win.
    
    # (b) Seg 2 is the ONLY segment for class 1. It has 0 wins.
    # But we NEVER prune the last segment of a class.
    # So seg 2 must be kept!
    assert pruned_model.n_segments_ == 2
    classes_kept = [s['class'] for s in pruned_model.segments_]
    assert classes_kept.count(0) == 1
    assert classes_kept.count(1) == 1
    
    # (c) The original model must be unchanged
    assert model.n_segments_ == 3

def test_hybrid_reduction():
    """Hybrid: M1 -> Train -> M3."""
    X_train = np.array([[0.0], [0.1], [1.0], [1.1], [0.2], [1.2]])
    y_train = np.array([0, 0, 1, 1, 0, 1])
    
    X_red, y_red, m1_res = run_m1_prefilter(X_train, y_train, keep_fraction=0.1, interior_keep_rate=0.0)
    
    # 1. M1 output has fewer rows than its input
    assert len(X_red) < len(X_train)
    
    # 2 & 3. Model trained ONLY on M1 output, validation rows never reach fit()
    class TrackingFHLSNN(FHLSNN):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fit_input_X = None
    
        def fit(self, X, y):
            self.fit_input_X = X.copy()
            return super().fit(X, y)
            
    model = TrackingFHLSNN(zeta=2.0)
    model.fit(X_red, y_red)
    
    assert model.n_segments_ <= len(X_red)
    assert np.array_equal(model.fit_input_X, X_red)
    
    # Validation rows
    X_val = np.array([[5.0], [6.0]])
    y_val = np.array([0, 1])
    
    # Assert val rows are not in fit input
    for row in X_val:
        assert not any(np.array_equal(row, fit_row) for fit_row in model.fit_input_X)
    
    # 4. A segment known to have zero wins is removed
    model.segments_.append({'V': np.array([5.0]), 'W': np.array([5.1]), 'class': 0})
    model.n_segments_ += 1
    model._rebuild_matrices()
    
    old_segments = model.n_segments_
    
    pruned, facts = run_m3_prune(model, X_val, y_val, threshold=1)
    
    assert pruned.n_segments_ < old_segments
