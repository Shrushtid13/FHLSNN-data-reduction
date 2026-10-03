import numpy as np
from ml_service.benchmark.datasets import load_dataset
from ml_service.benchmark.harness import run_experiment
from ml_service.fhlsnn.fhlsnn import FHLSNN
from ml_service.reducers.m1_prefilter import run_m1_prefilter
from ml_service.reducers.m3_prune import run_m3_prune
from ml_service.benchmark.baselines import run_cnn, run_enn, run_kmeans_prototypes, run_random_subsampling
import matplotlib.pyplot as plt
import os
import json

def run_theta_sweep(X, y, dataset_name, random_state=42):
    thetas = [0.05, 0.1, 0.2, 0.4, 0.6, 0.8]
    results = []
    
    print(f"\n--- Theta Sweep (Baseline) for {dataset_name} ---")
    for theta in thetas:
        res = run_experiment(
            X, y, 
            model_cls=FHLSNN, 
            model_params={'zeta': theta, 'gamma': 1.0, 'membership_type': 'mfhlsnn2003_height'},
            n_splits=3,
            random_state=random_state
        )
        agg = res['aggregate']
        print(f"Theta: {theta:.2f} | Acc: {agg['accuracy_mean']:.3f} | SegRed: {agg.get('segment_reduction_mean', 0.0):.3f} | RawRed: {agg['reduction_vs_raw_mean']:.3f}")
        results.append((theta, agg))
    return results

def run_m1_sweep(X, y, dataset_name, base_theta=0.1, random_state=42):
    keep_fractions = [0.2, 0.4, 0.6, 0.8]
    results = []
    print(f"\n--- M1 Pre-Filtering Sweep for {dataset_name} ---")
    
    for kf in keep_fractions:
        res = run_experiment(
            X, y,
            model_cls=FHLSNN,
            model_params={'zeta': base_theta, 'gamma': 1.0, 'membership_type': 'mfhlsnn2003_height'},
            pre_reducer_fn=run_m1_prefilter,
            pre_reducer_params={'keep_fraction': kf, 'interior_keep_rate': 0.1, 'random_state': random_state},
            n_splits=3,
            random_state=random_state
        )
        agg = res['aggregate']
        print(f"Keep Frac: {kf:.2f} | Acc: {agg['accuracy_mean']:.3f} | RawRed: {agg['reduction_vs_raw_mean']:.3f}")
        results.append((kf, agg))
    return results

def run_m3_sweep(X, y, dataset_name, base_theta=0.1, random_state=42):
    thresholds = [1, 2, 3, 5]
    results = []
    print(f"\n--- M3 Pruning Sweep for {dataset_name} ---")
    
    for t in thresholds:
        res = run_experiment(
            X, y,
            model_cls=FHLSNN,
            model_params={'zeta': base_theta, 'gamma': 1.0, 'membership_type': 'mfhlsnn2003_height'},
            post_reducer_fn=run_m3_prune,
            post_reducer_params={'threshold': t},
            n_splits=3,
            random_state=random_state
        )
        agg = res['aggregate']
        print(f"Threshold: {t} | Acc: {agg['accuracy_mean']:.3f} | RawRed: {agg['reduction_vs_raw_mean']:.3f}")
        results.append((t, agg))
    return results

def run_hybrid_sweep(X, y, dataset_name, base_theta=0.1, random_state=42):
    # Fix M1, sweep M3
    kf = 0.6
    thresholds = [1, 2, 3]
    results = []
    print(f"\n--- Hybrid (M1+M3) Sweep for {dataset_name} (M1 keep={kf}) ---")
    
    for t in thresholds:
        res = run_experiment(
            X, y,
            model_cls=FHLSNN,
            model_params={'zeta': base_theta, 'gamma': 1.0, 'membership_type': 'mfhlsnn2003_height'},
            pre_reducer_fn=run_m1_prefilter,
            pre_reducer_params={'keep_fraction': kf, 'interior_keep_rate': 0.1, 'random_state': random_state},
            post_reducer_fn=run_m3_prune,
            post_reducer_params={'threshold': t},
            n_splits=3,
            random_state=random_state
        )
        agg = res['aggregate']
        print(f"Threshold: {t} | Acc: {agg['accuracy_mean']:.3f} | RawRed: {agg['reduction_vs_raw_mean']:.3f}")
        results.append((t, agg))
    return results

def main():
    datasets = ['iris', 'wine', 'breast_cancer']
    
    all_results = {}
    for ds in datasets:
        X, y = load_dataset(ds)
        # Using 3 splits for quick runs, theta=0.1 as base
        res_theta = run_theta_sweep(X, y, ds)
        res_m1 = run_m1_sweep(X, y, ds, base_theta=0.1)
        res_m3 = run_m3_sweep(X, y, ds, base_theta=0.1)
        res_hybrid = run_hybrid_sweep(X, y, ds, base_theta=0.1)
        
        all_results[ds] = {
            'theta': res_theta,
            'm1': res_m1,
            'm3': res_m3,
            'hybrid': res_hybrid
        }

if __name__ == "__main__":
    main()
