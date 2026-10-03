import sys
import os
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_service.fhlsnn.fhlsnn import FHLSNN

X = np.array([[0.0, 0.0], [0.5, 0.0], [0.25, 0.0]])
y = np.array([0, 0, 1])

for policy in ['skip', 'drop_new']:
    m = FHLSNN(zeta=2.0, shuffle=False, use_intersection_test=True, step4_intersection=policy)
    m.fit(X, y)
    print(f"\nPolicy '{policy}': {m.n_segments_} segments")
    for i, seg in enumerate(m.segments_):
        print(f"  {i+1}: class {seg['class']}, V={seg['V']}, W={seg['W']}")
