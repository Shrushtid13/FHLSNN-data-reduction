import numpy as np
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_digits, fetch_openml
from typing import Tuple

def load_dataset(name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Loads standard benchmark datasets.
    Supported: 'iris', 'wine', 'breast_cancer', 'digits', 'pendigits', 'letter'
    Returns X, y (both as numpy arrays, y as integer class labels).
    """
    name = name.lower()
    if name == "iris":
        data = load_iris()
        return data.data, data.target
    elif name == "wine":
        data = load_wine()
        return data.data, data.target
    elif name == "breast_cancer":
        data = load_breast_cancer()
        return data.data, data.target
    elif name == "digits":
        data = load_digits()
        return data.data, data.target
    elif name == "pendigits":
        # Load from OpenML
        data = fetch_openml(name='pendigits', version=1, as_frame=False)
        return data.data, data.target.astype(int)
    elif name == "letter":
        # Load letter recognition from OpenML
        data = fetch_openml(name='letter', version=1, as_frame=False)
        # letter target is 'A'-'Z', convert to int 0-25
        y = np.array([ord(c) - ord('A') for c in data.target])
        return data.data, y
    else:
        raise ValueError(f"Unknown dataset: {name}")

