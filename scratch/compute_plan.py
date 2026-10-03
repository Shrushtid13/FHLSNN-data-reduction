import time
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_service.fhlsnn.fhlsnn import FHLSNN
from sklearn.datasets import fetch_openml
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score

print("Loading Pendigits...")
pendigits = fetch_openml('pendigits', version=1, parser='auto')
X = pendigits.data.to_numpy(dtype=np.float32)
y = pendigits.target.to_numpy()

# Stratified subsample of 2000 patterns
sss = StratifiedShuffleSplit(n_splits=1, train_size=2000, random_state=42)
idx_2k, _ = next(sss.split(X, y))
X_sub = X[idx_2k]
y_sub = y[idx_2k]

# Split into 1600 fit, 400 test
sss2 = StratifiedShuffleSplit(n_splits=1, train_size=1600, random_state=42)
fit_idx, test_idx = next(sss2.split(X_sub, y_sub))

X_fit = X_sub[fit_idx]
y_fit = y_sub[fit_idx]
X_test = X_sub[test_idx]
y_test = y_sub[test_idx]

scaler = MinMaxScaler()
X_fit_scaled = scaler.fit_transform(X_fit)
X_test_scaled = scaler.transform(X_test)

def run_test(use_intersection):
    print(f"\n--- use_intersection_test={use_intersection} ---")
    model = FHLSNN(zeta=0.8, gamma=0.25, use_intersection_test=use_intersection)
    t0 = time.perf_counter()
    model.fit(X_fit_scaled, y_fit)
    t1 = time.perf_counter()
    
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"Time (s): {t1 - t0:.2f}")
    print(f"Segments: {model.n_segments_}")
    print(f"Accuracy: {acc:.4f}")
    return t1 - t0

t_true = run_test(True)
t_false = run_test(False)

print("\n--- ESTIMATE ---")
# The full sweep configuration is:
# 3 datasets, 5 folds, 3 seeds = 45 folds.
# Wait, for the large dataset sweep (Pendigits/Letter)...
# Let's say: 1 dataset (Pendigits), 5 folds, 3 seeds = 15 outer loops
# tune_hyperparams: 6 thetas x 5 gammas = 30 fits on the val split
# methods: unreduced, sweep, M1(8), M3(4), Hybrid(8), CNN, ENN, KMeans(5), Random(8) = ~38 configs trained using the frozen theta/gamma
# Total fits per fold = 30 (tuning) + 38 (baselines) = 68 fits
# Total fits for 15 outer loops = 15 * 68 = 1020 fits per large dataset.

# For tuning, n_train is 80% of 80% = 64%.
# For the main train, it's 80%.
# Let's conservatively use the time for 1600 patterns as a baseline, but Pendigits is ~11k patterns.
# Time scales O(N * S) where S is segments. S scales with N. Time is roughly O(N^2).
# Pendigits 1600 patterns -> t_true
# Pendigits 5800 patterns -> ~72 seconds (from earlier)

# If full training takes 72s.
print(f"Estimated fits per dataset: 1020")
print(f"Time per fit on large dataset (~5800 patterns) with intersection=True: ~72 seconds")
print(f"Total time per dataset = 1020 * 72s = 73,440 seconds (~20.4 hours)!!")

print("\nPROPOSED PLAN:")
print("1. Subsample validation split for tuning (e.g. max 2000 patterns) to speed up 30-fit grid search.")
print("2. Disable intersection tests during theta/gamma tuning, ONLY enable for final training.")
print("3. Downsample M1 grid (from 8 to 4 keeping fractions) and Random grid (from 8 to 4).")
