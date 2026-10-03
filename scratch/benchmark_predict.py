import sys
import os
import numpy as np
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_service.fhlsnn.fhlsnn import FHLSNN

n_patterns = 5000
n_segments = 2000
n_features = 4

print(f"Benchmarking predict: {n_patterns} patterns x {n_segments} segments...")

# Create dummy model with random segments
model = FHLSNN()
rng = np.random.RandomState(42)
segs = []
for i in range(n_segments):
    segs.append({
        'V': rng.rand(n_features),
        'W': rng.rand(n_features),
        'class': rng.randint(0, 3)
    })
model.segments_ = segs
model.n_segments_ = n_segments
model._rebuild_matrices()

X_test = rng.rand(n_patterns, n_features)

# Warmup
_ = model.predict(X_test[:10])

t0 = time.perf_counter()
_ = model.predict(X_test)
t1 = time.perf_counter()

print(f"Time taken: {t1 - t0:.4f} seconds")
print(f"Time per pattern: {(t1 - t0) / n_patterns * 1000:.4f} ms")
