import copy
import numpy as np
from typing import Tuple

def run_m3_prune(model, X_val: np.ndarray, y_val: np.ndarray, threshold: int = 1) -> Tuple[object, dict]:
    """Prune FHLSNN segments by validation win count.

    Args:
        model:      a fitted FHLSNN instance.
        X_val:      validation patterns (already scaled). MUST NOT be test data.
        y_val:      true labels for X_val.
        threshold:  minimum win count to keep a segment.

    Returns:
        pruned_model: deep-copied model with low-contribution segments removed
                      and matrices rebuilt.
        facts:        dict of facts about pruned segments.
    """
    pruned_model = copy.deepcopy(model)

    n_segments = len(pruned_model.segments_)
    if n_segments == 0:
        return pruned_model, {}

    win_counts = np.zeros(n_segments, dtype=int)

    winning_idxs = pruned_model.winning_segment(X_val)
    y_pred_val   = pruned_model.predict(X_val)

    for i, (w_idx, pred, true) in enumerate(zip(winning_idxs, y_pred_val, y_val)):
        if pred == true:
            win_counts[w_idx] += 1

    # Keep track of segments per class
    class_segments = {}
    for j, seg in enumerate(pruned_model.segments_):
        c = seg['class']
        if c not in class_segments:
            class_segments[c] = []
        class_segments[c].append(j)

    kept = []
    facts = {}
    
    # Process each class separately to ensure we never prune the last segment
    for c, seg_idxs in class_segments.items():
        class_kept = [j for j in seg_idxs if win_counts[j] >= threshold]
        
        # If pruning would remove all segments for this class, keep the one with the most wins
        # (or the first one if all have 0 wins)
        if len(class_kept) == 0:
            best_j = seg_idxs[np.argmax(win_counts[seg_idxs])]
            class_kept.append(best_j)
            
        kept.extend(class_kept)
        
        # Record facts for pruned segments
        for j in seg_idxs:
            if j not in class_kept:
                seg = pruned_model.segments_[j]
                facts[j] = {
                    'class': int(seg['class']),
                    'win_count': int(win_counts[j]),
                    'endpoints': [seg['V'].tolist(), seg['W'].tolist()],
                    'length': float(np.linalg.norm(seg['W'] - seg['V']))
                }

    kept.sort()
    pruned_model.segments_ = [pruned_model.segments_[j] for j in kept]
    pruned_model.n_segments_ = len(pruned_model.segments_)
    pruned_model._rebuild_matrices()

    return pruned_model, facts
