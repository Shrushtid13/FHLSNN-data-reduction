import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from typing import Dict, Optional

def compute_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Accuracy and macro-F1 on the test fold."""
    return {
        "accuracy":  float(accuracy_score(y_true, y_pred)),
        "macro_f1":  float(f1_score(y_true, y_pred, average='macro', zero_division=0)),
    }

def compute_reduction_metrics(
    n_train: int,
    stored_vectors: int,
    n_segments: Optional[int] = None,
    n_segments_unreduced: Optional[int] = None,
) -> Dict[str, Optional[float]]:
    """
    PRD 4.4 reduction metrics.

    reduction_vs_raw = 1 − stored_vectors / n_train.
    This CAN be negative (e.g. 45 segments on 75 patterns → 75 stored_vectors
    vs 75 training patterns → negative reduction).  Do NOT clip to 0.

    segment_reduction requires n_segments_unreduced to be non-None.
    """
    reduction_vs_raw = 1.0 - stored_vectors / n_train if n_train > 0 else None

    seg_reduction = None
    if n_segments is not None and n_segments_unreduced is not None and n_segments_unreduced > 0:
        seg_reduction = 1.0 - n_segments / n_segments_unreduced

    return {
        "reduction_vs_raw": reduction_vs_raw,
        "segment_reduction": seg_reduction,
    }

