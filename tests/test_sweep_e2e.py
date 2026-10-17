"""
End-to-end test for the sweep script's own entry function run_sweep.

Uses a tiny config (Iris, 1 seed, 2 folds; unreduced, theta_sweep x2, cnn, enn, kmeans, random, m1, m3, hybrid)
with fit() spied to assert:
  - no validation or test row reaches any fit()
  - each method's fit input is a subset of the fold's fit set (k-means: computed from X[fit_idx])
  - unreduced equals the theta_sweep point at the tuned theta
"""
import os
import sys
import tempfile
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch
from sklearn.datasets import load_iris

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import scripts.run_sweep1 as sweep_mod
from ml_service.fhlsnn.fhlsnn import FHLSNN


def test_sweep_entry_point_e2e():
    # 1. Prepare data with unique integer IDs in the last column
    X_raw, y = load_iris(return_X_y=True)
    ids = np.arange(len(X_raw), dtype=np.float64).reshape(-1, 1)
    X_with_id = np.hstack([X_raw, ids])

    tiny_config = {
        'sweep': {
            'datasets': [{'name': 'iris', 'loader': 'sklearn.datasets.load_iris'}],
            'protocol': {
                'n_splits': 2,
                'val_size': 0.20,
                'seeds': [42],
            },
            'hyperparams': {
                'theta_c_grid': [0.05, 0.2],
                'gamma_grid': [0.5],
            },
            'baselines': {
                'cnn': True,
                'enn': True,
                'kmeans': {'k_fractions': [0.2]},
                'random': {'ratios': [0.5]},
                'm1': {
                    'keep_fractions': [0.5],
                    'interior_keep_rates': [0],
                    'edit_first': [False],
                },
                'm3': {'min_wins': [1]},
                'hybrid': {'m3_min_wins': [1]},
            }
        }
    }

    # Tracking state
    active_fold = {}
    fit_invocations = []

    orig_get_cv_folds = sweep_mod.get_cv_folds
    def tracking_get_cv_folds(X, y, n_splits, val_size, random_state):
        for fd in orig_get_cv_folds(X, y, n_splits=n_splits, val_size=val_size, random_state=random_state):
            active_fold['fit_idx'] = set(fd['fit_idx'])
            active_fold['val_idx'] = set(fd['val_idx'])
            active_fold['test_idx'] = set(fd['test_idx'])
            active_fold['scaler'] = fd['scaler']
            active_fold['fold_idx'] = fd['fold_idx']
            active_fold['X_fit_raw'] = X[fd['fit_idx']]
            yield fd

    orig_fit = FHLSNN.fit
    def tracking_fit(self, X_fit, y_fit):
        # Record a snapshot of what was passed to fit()
        scaler = active_fold.get('scaler')
        fit_invocations.append({
            'X_fit': X_fit.copy(),
            'y_fit': y_fit.copy(),
            'fold_idx': active_fold.get('fold_idx'),
            'fit_idx': set(active_fold.get('fit_idx', set())),
            'val_idx': set(active_fold.get('val_idx', set())),
            'test_idx': set(active_fold.get('test_idx', set())),
            'scaler': scaler,
            'X_fit_raw': active_fold.get('X_fit_raw'),
        })
        return orig_fit(self, X_fit, y_fit)

    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch.object(sweep_mod, 'get_dataset', return_value=(X_with_id, y)), \
             patch.object(sweep_mod, 'get_cv_folds', side_effect=tracking_get_cv_folds), \
             patch.object(FHLSNN, 'fit', side_effect=tracking_fit, autospec=True):

            out_dir = sweep_mod.run_sweep(
                config=tiny_config,
                datasets_override='iris',
                out_dir=tmp_dir,
                tag='test'
            )

        # Assertions on captured fit invocations
        assert len(fit_invocations) > 0, "No fit() calls were captured"

        for inv in fit_invocations:
            X_passed = inv['X_fit']
            fit_idx = inv['fit_idx']
            val_idx = inv['val_idx']
            test_idx = inv['test_idx']
            scaler = inv['scaler']

            # Check if this invocation is k-means prototypes:
            # k-means generates synthetic prototypes (centroids), not original rows
            # K-means rows = k_per_class * n_classes = 0.2 * min_class_size * 3
            is_kmeans = False
            # If centroids, they won't have integer IDs in the last column
            X_unscaled = scaler.inverse_transform(X_passed)
            recovered_ids = X_unscaled[:, -1]
            rounded_ids = np.round(recovered_ids)

            if not np.allclose(recovered_ids, rounded_ids, atol=1e-3):
                is_kmeans = True

            if is_kmeans:
                # k-means: assert centroids are computed from X[fit_idx]
                # Coordinates must lie within the bounds of X[fit_idx]
                X_fit_raw = inv['X_fit_raw']
                min_b = X_fit_raw.min(axis=0) - 1e-5
                max_b = X_fit_raw.max(axis=0) + 1e-5
                assert np.all(X_unscaled >= min_b), "k-means prototype below fit set min"
                assert np.all(X_unscaled <= max_b), "k-means prototype above fit set max"
            else:
                passed_ids = set(rounded_ids.astype(int))
                # 1. Each method's fit input is a subset of that fold's fit set
                assert passed_ids.issubset(fit_idx), f"Passed IDs not subset of fit_idx: {passed_ids - fit_idx}"
                # 2. No validation row identity reaches any fit()
                assert len(passed_ids.intersection(val_idx)) == 0, f"Leaked val rows into fit(): {passed_ids.intersection(val_idx)}"
                # 3. No test row identity reaches any fit()
                assert len(passed_ids.intersection(test_idx)) == 0, f"Leaked test rows into fit(): {passed_ids.intersection(test_idx)}"

        # Verify unreduced equals the theta_sweep point at the tuned theta (PRD §4.5 Step 0i item 5)
        runs_df = pd.read_csv(f'{out_dir}/iris_runs.csv')
        assert 'best_theta' in runs_df.columns, "runs.csv must contain best_theta column"
        assert 'best_gamma' in runs_df.columns, "runs.csv must contain best_gamma column"

        for (seed_val, fold), fold_df in runs_df.groupby(['seed', 'fold']):
            unred_rows = fold_df[fold_df['method'] == 'unreduced']
            assert len(unred_rows) == 1, f"Expected 1 unreduced row per (seed,fold), got {len(unred_rows)}"
            unred_row = unred_rows.iloc[0]

            tuned_theta = unred_row['best_theta']
            # Find the theta_sweep row whose theta equals the tuned theta
            th_label = f'theta_sweep_{tuned_theta:.3f}'
            th_rows = fold_df[fold_df['method'] == th_label]
            assert len(th_rows) == 1, (
                f"Seed {seed_val} Fold {fold}: no theta_sweep row for best_theta={tuned_theta:.3f} "
                f"(label={th_label}). Available: {fold_df['method'].tolist()}"
            )
            th_row = th_rows.iloc[0]
            assert unred_row['n_segments'] == th_row['n_segments'], (
                f"Seed {seed_val} Fold {fold}: unreduced n_segments={unred_row['n_segments']} "
                f"!= theta_sweep@best_theta n_segments={th_row['n_segments']}"
            )
            assert np.isclose(unred_row['accuracy'], th_row['accuracy']), (
                f"Seed {seed_val} Fold {fold}: unreduced accuracy={unred_row['accuracy']} "
                f"!= theta_sweep@best_theta accuracy={th_row['accuracy']}"
            )


def test_identical_runs_regression():
    """Running run_sweep twice on the same config must yield identical runs.csv (PRD §4.5 seeding)."""
    tiny_config = {
        'sweep': {
            'datasets': [{'name': 'iris', 'loader': 'sklearn.datasets.load_iris'}],
            'protocol': {
                'n_splits': 3,
                'val_size': 0.20,
                'seeds': [42],
            },
            'hyperparams': {
                'theta_c_grid': [0.05, 0.2],
                'gamma_grid': [0.5],
            },
            'baselines': {
                'cnn': True,
                'enn': True,
                'kmeans': {'k_fractions': [0.2]},
                'random': {'ratios': [0.5]},
                'm1': {
                    'keep_fractions': [0.5],
                    'interior_keep_rates': [0.1],
                    'edit_first': [False],
                },
                'm3': {'min_wins': [1]},
                'hybrid': {'m3_min_wins': [1]},
            }
        }
    }

    with tempfile.TemporaryDirectory() as tmp1, \
         tempfile.TemporaryDirectory() as tmp2:

        sweep_mod.run_sweep(config=tiny_config, datasets_override='iris',
                            out_dir=tmp1, tag='test')
        sweep_mod.run_sweep(config=tiny_config, datasets_override='iris',
                            out_dir=tmp2, tag='test')

        df1 = pd.read_csv(f'{tmp1}/iris_runs.csv')
        df2 = pd.read_csv(f'{tmp2}/iris_runs.csv')

        # Compare numerically (allow float tolerance)
        assert list(df1.columns) == list(df2.columns), "Column mismatch between runs"
        assert len(df1) == len(df2), f"Row count mismatch: {len(df1)} vs {len(df2)}"

        numeric_cols = df1.select_dtypes(include=[np.number]).columns.tolist()
        str_cols = [c for c in df1.columns if c not in numeric_cols]

        for col in str_cols:
            assert (df1[col] == df2[col]).all(), f"String column '{col}' differs between runs"

        for col in numeric_cols:
            if col in ('order_noise_std', 'train_time_s'):
                continue  # timing and order_noise are inherently non-deterministic
            assert np.allclose(df1[col].fillna(-999), df2[col].fillna(-999), equal_nan=False), \
                f"Numeric column '{col}' differs between runs:\nRun1: {df1[col].values}\nRun2: {df2[col].values}"

