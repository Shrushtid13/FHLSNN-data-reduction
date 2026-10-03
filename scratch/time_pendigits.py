import time
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_service.fhlsnn.fhlsnn import FHLSNN
from sklearn.datasets import fetch_openml
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
from sklearn.preprocessing import MinMaxScaler

print("Loading Pendigits...")
pendigits = fetch_openml('pendigits', version=1, parser='auto')
X = pendigits.data.to_numpy(dtype=np.float32)
y = pendigits.target.to_numpy()

skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
train_idx, test_idx = next(skf.split(X, y))

sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
fit_rel, val_rel = next(sss.split(X[train_idx], y[train_idx]))
fit_idx = train_idx[fit_rel]

X_fit = X[fit_idx]
y_fit = y[fit_idx]

scaler = MinMaxScaler()
X_fit_scaled = scaler.fit_transform(X_fit)

print(f"Fitting on {len(X_fit_scaled)} patterns (theta=0.8, gamma=0.25)...")

model = FHLSNN(zeta=0.8, gamma=0.25)
t0 = time.time()
model.fit(X_fit_scaled, y_fit)
t1 = time.time()

print(f"Total time (seconds): {t1 - t0:.2f}")
print(f"Intersection time (seconds): {getattr(model, 'inter_time_', 0.0):.2f}")
print(f"Segment count: {model.n_segments_}")
