from dataclasses import dataclass
import numpy as np

@dataclass
class ReductionResult:
    kept_idx: np.ndarray        # indices into the original training set
    removed_idx: np.ndarray
    facts: dict                 # per-item reason data, used by the explainability agent
