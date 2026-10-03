"""
Gate-A evidence scripts.
Produces all printed output required for the Session 3 gate report:
  A3: Iris θ-curve (20 seeds, 7 θ values)
  A4: 12-pattern example segment listing at θ=0.5
  A8: OpenML cache demonstration

Run from project root:  python scratch/gate_evidence.py
"""

import sys
import os
import numpy as np
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sklearn.datasets import load_iris
from sklearn.preprocessing import MinMaxScaler
from ml_service.fhlsnn.fhlsnn import FHLSNN

# ── A3: Iris theta-curve ──────────────────────────────────────────────────────
print("=" * 70)
print("A3: Iris theta-curve  (fhlsnn2001, all 150 patterns, gamma=1, 20 seeds)")
print("=" * 70)

iris = load_iris()
X_iris_raw, y_iris = iris.data, iris.target
scaler = MinMaxScaler()
X_iris = scaler.fit_transform(X_iris_raw)

# Count distinct rows (handle duplicates)
distinct = len(np.unique(X_iris, axis=0))
print(f"Distinct rows in scaled Iris: {distinct}")

theta_vals = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
n_seeds    = 20

# Reference values from 2014 paper Table III (FHLSNN, all 150 patterns)
ref = {0.0: 147, 0.1: 98, 0.2: 79, 0.3: 76, 0.4: 74, 0.5: 74, 1.0: 74}

print(f"\n{'theta':>6} {'mean±std segs':>18} {'2014 ref':>10} {'diff':>8}")
print("-" * 50)
for theta in theta_vals:
    counts = []
    for seed in range(n_seeds):
        m = FHLSNN(zeta=theta, gamma=1.0, membership_type='fhlsnn2001',
                   shuffle=True, random_state=seed)
        m.fit(X_iris, y_iris)
        counts.append(m.n_segments_)
    mean_c = np.mean(counts)
    std_c  = np.std(counts)
    paper  = ref.get(theta, '?')
    diff   = f"{mean_c - paper:+.1f}" if isinstance(paper, int) else "?"
    print(f"{theta:6.1f} {mean_c:8.1f}±{std_c:5.1f}          {paper:>6}    {diff:>6}")

print()
print("Note: 'diff' = our mean - paper's value.")

# ── A4: 12-pattern example at θ=0.5 ──────────────────────────────────────
print()
print("=" * 70)
print("A4: 12-pattern example  (2001 paper Fig. 4/5, theta=0.5, shuffle=False)")
print("=" * 70)

patterns_12 = np.array([
    [0.0,  0.00],  # class 2
    [0.15, 0.05],  # class 1
    [0.2,  0.15],  # class 2
    [0.3,  0.15],  # class 1
    [0.5,  0.20],  # class 2
    [0.3,  0.25],  # class 2
    [0.15, 0.30],  # class 1
    [0.4,  0.30],  # class 1
    [0.4,  0.40],  # class 2
    [0.4,  0.50],  # class 1
    [0.6,  0.50],  # class 1
    [0.6,  0.60],  # class 2
])
classes_12 = np.array([2, 1, 2, 1, 2, 2, 1, 1, 2, 1, 1, 2])

m12 = FHLSNN(zeta=0.5, gamma=1.0, membership_type='fhlsnn2001',
             shuffle=False, use_intersection_test=True, step4_intersection='skip')
m12.fit(patterns_12, classes_12)

print(f"\ntheta=0.5: {m12.n_segments_} segments (paper says 7)")
print(f"\n{'#':>3} {'V':>20} {'W':>20} {'cls':>5} {'len':>8}")
print("-" * 62)
for i, seg in enumerate(m12.segments_):
    V   = seg['V']
    W   = seg['W']
    cls = seg['class']
    length = float(np.linalg.norm(W - V))
    print(f"{i+1:>3} ({V[0]:5.3f},{V[1]:5.3f})    ({W[0]:5.3f},{W[1]:5.3f})   {cls:>3}   {length:8.4f}")

# Also show which theta values give exactly 7 segments
print("\n\nTheta sweep (no-shuffle) giving exactly 7 segments:")
print(f"{'theta':>6} {'segs':>6}")
for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    mc = FHLSNN(zeta=t, gamma=1.0, membership_type='fhlsnn2001',
                shuffle=False, use_intersection_test=True, step4_intersection='skip')
    mc.fit(patterns_12, classes_12)
    marker = " <- 7 segs" if mc.n_segments_ == 7 else ""
    print(f"{t:6.1f} {mc.n_segments_:>6}{marker}")

# ── A8: OpenML cache ─────────────────────────────────────────────────────
print()
print("=" * 70)
print("A8: OpenML download cache location + offline second load")
print("=" * 70)
try:
    from sklearn.datasets import fetch_openml
    import sklearn
    data_home = sklearn.datasets._base.get_data_home()
    print(f"scikit-learn data_home: {data_home}")

    print("First load (Pendigits)...")
    t0 = time.perf_counter()
    pend = fetch_openml(name='pendigits', version=1, as_frame=False, parser='auto')
    t1 = time.perf_counter()
    print(f"  Done in {t1-t0:.2f}s.  Shape: {pend.data.shape}")

    print("Second load (from cache)...")
    t0 = time.perf_counter()
    pend2 = fetch_openml(name='pendigits', version=1, as_frame=False, parser='auto')
    t1 = time.perf_counter()
    print(f"  Done in {t1-t0:.2f}s. (should be much faster)")
    print(f"  Cached files in: {data_home}")
    import os
    for root, dirs, files in os.walk(data_home):
        for f in files:
            if 'pendigit' in f.lower() or 'openml' in root.lower():
                print(f"    {os.path.join(root, f)}")
                break
        else:
            continue
        break
except Exception as e:
    print(f"  Error: {e}")

print("\nDone.")
