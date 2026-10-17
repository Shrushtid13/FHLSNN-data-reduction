"""
Sweep script – thin caller of ml_service.benchmark.harness primitives.

All fold splitting, scaling, and baseline routing is done by the harness
functions get_cv_folds, tune_hyperparams, and run_one_method. This script
only adds sweep-level orchestration: theta_sweep expansion, order noise,
M3 anomaly diagnostics, paired design, plots, and CSV output.
"""
import os
import sys
import yaml
import time
import hashlib
import platform
import importlib.metadata
import pandas as pd
import numpy as np
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_service.benchmark.harness import get_cv_folds, tune_hyperparams, run_one_method
from ml_service.fhlsnn.fhlsnn import FHLSNN
from sklearn.datasets import load_iris, load_wine, load_breast_cancer
from sklearn.metrics import accuracy_score, f1_score
from ml_service.benchmark.baselines import run_cnn, run_enn, run_kmeans_prototypes, run_random_subsampling
from ml_service.reducers.m1_prefilter import run_m1_prefilter
from ml_service.reducers.m3_prune import run_m3_prune
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def get_metadata(config_bytes):
    sha256 = hashlib.sha256(config_bytes).hexdigest()
    packages = ['scikit-learn', 'numpy', 'imbalanced-learn']
    versions = {}
    for pkg in packages:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = 'unknown'
    return {
        'config_sha256': sha256,
        'python_version': platform.python_version(),
        'packages': versions,
    }


def get_dataset(name):
    if name == 'iris': return load_iris(return_X_y=True)
    if name == 'wine': return load_wine(return_X_y=True)
    if name == 'breast_cancer': return load_breast_cancer(return_X_y=True)
    raise ValueError(f"Unknown dataset {name}")


def build_sweep_jobs(config):
    """Build the list of method descriptors from the YAML config."""
    jobs = []
    b = config['sweep']['baselines']

    jobs.append({'method': 'unreduced', 'pre': None, 'pre_params': None, 'post': None, 'post_params': None})
    jobs.append({'method': 'theta_sweep', 'pre': None, 'pre_params': None, 'post': None, 'post_params': None})

    if b.get('cnn'):
        jobs.append({'method': 'cnn', 'pre': run_cnn, 'pre_params': {}, 'post': None, 'post_params': None})
    if b.get('enn'):
        jobs.append({'method': 'enn', 'pre': run_enn, 'pre_params': {}, 'post': None, 'post_params': None})

    for kf in b.get('kmeans', {}).get('k_fractions', []):
        jobs.append({'method': f'kmeans_{kf}', 'pre': run_kmeans_prototypes,
                     'pre_params': {'k_per_class': kf}, 'post': None, 'post_params': None})

    for r in b.get('random', {}).get('ratios', []):
        jobs.append({'method': f'random_{r}', 'pre': run_random_subsampling,
                     'pre_params': {'ratio': r}, 'post': None, 'post_params': None})

    m1 = b.get('m1', {})
    for kf in m1.get('keep_fractions', []):
        for ikr in m1.get('interior_keep_rates', []):
            for ef in m1.get('edit_first', []):
                jobs.append({
                    'method': f'm1_{kf}_{ikr}_{ef}',
                    'pre': run_m1_prefilter,
                    'pre_params': {'keep_fraction': kf, 'interior_keep_rate': ikr, 'edit_first': ef},
                    'post': None, 'post_params': None,
                })

    m3 = b.get('m3', {})
    for mw in m3.get('min_wins', []):
        jobs.append({
            'method': f'm3_{mw}', 'pre': None, 'pre_params': None,
            'post': run_m3_prune, 'post_params': {'threshold': mw},
        })

    for kf in m1.get('keep_fractions', []):
        for ikr in m1.get('interior_keep_rates', []):
            for ef in m1.get('edit_first', []):
                for mw in b.get('hybrid', {}).get('m3_min_wins', []):
                    jobs.append({
                        'method': f'hybrid_{kf}_{ikr}_{ef}_{mw}',
                        'pre': run_m1_prefilter,
                        'pre_params': {'keep_fraction': kf, 'interior_keep_rate': ikr, 'edit_first': ef},
                        'post': run_m3_prune, 'post_params': {'threshold': mw},
                    })
    return jobs


def run_sweep(config=None, datasets_override=None, out_dir=None, tag='sweep1'):
    if config is None:
        with open('configs/sweep1.yaml', 'r') as f:
            config_bytes = f.read().encode('utf-8')
        config = yaml.safe_load(config_bytes)
    else:
        config_bytes = yaml.dump(config).encode('utf-8')

    if out_dir is None:
        timestamp = time.strftime('%Y%m%d_%H%M')
        out_dir = f'results/run_{timestamp}_{tag}'
    # Write-once guard (PRD §4.5)
    if out_dir is not None and os.path.exists(out_dir) and os.listdir(out_dir):
        raise FileExistsError(
            f"Output folder '{out_dir}' already exists and is non-empty. "
            "Refusing to overwrite (PRD §4.5 write-once). "
            "Choose a different --out-dir or use the auto-generated timestamped folder."
        )
    os.makedirs(out_dir, exist_ok=True)

    meta = get_metadata(config_bytes)
    with open(f'{out_dir}/metadata.yaml', 'w') as f:
        yaml.dump(meta, f)

    datasets = config['sweep']['datasets']
    if datasets_override:
        allowed = [x.strip() for x in datasets_override.split(',')]
        datasets = [d for d in datasets if d['name'] in allowed]

    jobs = build_sweep_jobs(config)
    n_splits = config['sweep']['protocol']['n_splits']
    val_size = config['sweep']['protocol']['val_size']
    seeds = config['sweep']['protocol']['seeds']
    theta_c = config['sweep']['hyperparams']['theta_c_grid']
    gamma_grid = config['sweep']['hyperparams']['gamma_grid']

    for d in datasets:
        all_runs = []
        dset_name = d['name']
        print(f"Dataset: {dset_name}", flush=True)
        sweep_t0 = time.perf_counter()

        X, y = get_dataset(dset_name)
        d_feats = X.shape[1]
        theta_grid = [c * np.sqrt(d_feats) for c in theta_c]

        m3_val_sizes = []
        m3_zero_win_fracs = []
        m3_max_keep = []

        for seed in seeds:
            # Reset numpy global RNG deterministically per (dataset, seed).
            # This ensures reproducibility when run_sweep is called multiple times
            # in the same Python process (PRD §4.5 seeding requirement).
            global_seed = int(
                int.from_bytes(
                    hashlib.sha256(f"{dset_name}_{seed}_global".encode()).digest()[:4], 'big'
                ) & 0x7FFFFFFF
            )
            np.random.seed(global_seed)
            print(f"  Seed {seed}", flush=True)


            for fd in get_cv_folds(X, y, n_splits=n_splits, val_size=val_size, random_state=seed):
                fold_idx = fd['fold_idx']
                print(f"    Fold {fold_idx}", flush=True)

                _, class_counts = np.unique(fd['y_fit'], return_counts=True)
                min_class_size = int(class_counts.min())

                # ── tune theta/gamma using harness tune_hyperparams ─
                best_theta, best_gamma = tune_hyperparams(
                    fd['X_fit'], fd['y_fit'], fd['X_val'], fd['y_val'],
                    model_cls=FHLSNN,
                    base_params={'use_intersection_test': True, 'random_state': seed},
                    theta_grid=theta_grid,
                    gamma_grid=gamma_grid,
                )

                base_params = {
                    'zeta': best_theta, 'gamma': best_gamma,
                    'use_intersection_test': True, 'random_state': seed,
                }

                for job in jobs:
                    method_name = job['method']
                    # ── (seed, fold, method) derived seed (PRD §4.5) ─
                    method_seed = int(
                        int.from_bytes(
                            hashlib.sha256(
                                f"{seed}_{fold_idx}_{method_name}".encode()
                            ).digest()[:4],
                            'big'
                        ) & 0x7FFFFFFF
                    )

                    # ── theta_sweep: separate rows per theta ─
                    if method_name == 'theta_sweep':
                        for th in theta_grid:
                            th_params = {**base_params, 'zeta': th}
                            res = run_one_method(
                                fd, model_cls=FHLSNN, model_params=th_params)
                            all_runs.append({
                                'dataset': dset_name,
                                'method': f'theta_sweep_{th:.3f}',
                                'seed': seed, 'fold': fold_idx,
                                'best_theta': best_theta, 'best_gamma': best_gamma,
                                'n_segments': res['n_segments'],
                                'stored_vectors': res['stored_vectors'],
                                'reduction_vs_raw': res['reduction_vs_raw'],
                                'accuracy': res['accuracy'],
                                'macro_f1': res['macro_f1'],
                                'zero_mem_frac': res['zero_mem_frac'],
                                'train_time_s': res['train_time_s'],
                                'order_noise_std': np.nan,
                            })
                        continue

                    # ── resolve k_per_class fraction → integer ─
                    pre_p = dict(job['pre_params']) if job['pre_params'] else None
                    if pre_p and 'k_per_class' in pre_p and isinstance(pre_p['k_per_class'], float):
                        pre_p['k_per_class'] = max(1, int(min_class_size * pre_p['k_per_class']))

                    # ── inject method_seed into stochastic pre-reducers ─
                    if pre_p is not None:
                        # CNN, k-means, random subsampling, M1 all accept random_state
                        if job['pre'] in (run_cnn, run_kmeans_prototypes,
                                          run_random_subsampling, run_m1_prefilter):
                            pre_p['random_state'] = method_seed
                            # Also seed numpy global RNG: imblearn CNN uses it internally
                            np.random.seed(method_seed)

                    # ── M3 anomaly + order noise (unreduced only) ─
                    order_noise_std = np.nan
                    if method_name == 'unreduced':
                        m_unred = FHLSNN(**base_params)
                        m_unred.fit(fd['X_fit'], fd['y_fit'])
                        y_val_pred = m_unred.predict(fd['X_val'])
                        y_val_winners = np.array(m_unred.winning_segment(fd['X_val']))

                        correct_mask = (y_val_pred == fd['y_val'])
                        m3_max_keep.append(int(correct_mask.sum()))
                        m3_val_sizes.append(len(fd['y_val']))

                        correct_winners = y_val_winners[correct_mask]
                        win_counts = np.bincount(correct_winners,
                                                 minlength=m_unred.n_segments_)
                        zw_frac = ((win_counts == 0).sum() / m_unred.n_segments_
                                   if m_unred.n_segments_ > 0 else 0.0)
                        m3_zero_win_fracs.append(zw_frac)

                        noise_accs = []
                        for ns in range(5):
                            mn = FHLSNN(zeta=best_theta, gamma=best_gamma,
                                        use_intersection_test=True,
                                        random_state=seed + fold_idx * 100 + ns)
                            mn.fit(fd['X_fit'], fd['y_fit'])
                            noise_accs.append(accuracy_score(
                                fd['y_test'], mn.predict(fd['X_test'])))
                        order_noise_std = float(np.std(noise_accs))

                    # ── run_one_method from the harness ─
                    res = run_one_method(
                        fd, model_cls=FHLSNN, model_params=base_params,
                        pre_reducer_fn=job['pre'], pre_reducer_params=pre_p,
                        post_reducer_fn=job['post'], post_reducer_params=job['post_params'],
                    )

                    all_runs.append({
                        'dataset': dset_name, 'method': method_name,
                        'seed': seed, 'fold': fold_idx,
                        'best_theta': best_theta, 'best_gamma': best_gamma,
                        'n_segments': res['n_segments'],
                        'stored_vectors': res['stored_vectors'],
                        'reduction_vs_raw': res['reduction_vs_raw'],
                        'accuracy': res['accuracy'],
                        'macro_f1': res['macro_f1'],
                        'zero_mem_frac': res['zero_mem_frac'],
                        'train_time_s': res['train_time_s'],
                        'order_noise_std': order_noise_std,
                    })

        # ── save runs ─
        df = pd.DataFrame(all_runs)
        df.to_csv(f'{out_dir}/{dset_name}_runs.csv', index=False)

        # ── paired differences vs unreduced ─
        unred_df = df[df['method'] == 'unreduced'][
            ['seed', 'fold', 'accuracy', 'macro_f1', 'stored_vectors']
        ].rename(columns={'accuracy': 'u_acc', 'macro_f1': 'u_f1',
                          'stored_vectors': 'u_sv'})
        df = df.merge(unred_df, on=['seed', 'fold'])
        df['acc_diff'] = df['accuracy'] - df['u_acc']
        df['f1_diff'] = df['macro_f1'] - df['u_f1']
        df['sv_diff'] = df['stored_vectors'] - df['u_sv']

        # ── summary ─
        agg = df.groupby('method').agg(
            n_segments_mean=('n_segments', 'mean'),
            n_segments_std=('n_segments', 'std'),
            stored_vectors_mean=('stored_vectors', 'mean'),
            stored_vectors_std=('stored_vectors', 'std'),
            reduction_vs_raw_mean=('reduction_vs_raw', 'mean'),
            reduction_vs_raw_std=('reduction_vs_raw', 'std'),
            accuracy_mean=('accuracy', 'mean'),
            accuracy_std=('accuracy', 'std'),
            macro_f1_mean=('macro_f1', 'mean'),
            macro_f1_std=('macro_f1', 'std'),
            zero_mem_frac_mean=('zero_mem_frac', 'mean'),
            zero_mem_frac_std=('zero_mem_frac', 'std'),
            acc_diff_mean=('acc_diff', 'mean'),
            acc_diff_std=('acc_diff', 'std'),
            f1_diff_mean=('f1_diff', 'mean'),
            f1_diff_std=('f1_diff', 'std'),
            sv_diff_mean=('sv_diff', 'mean'),
            sv_diff_std=('sv_diff', 'std'),
            order_noise_std_mean=('order_noise_std', 'mean'),
            train_time_s_mean=('train_time_s', 'mean'),
            fold_count=('method', 'count'),
        ).reset_index()

        def family_order(m):
            fams = ['unreduced', 'theta_sweep', 'cnn', 'enn',
                    'kmeans_', 'random_', 'm1_', 'm3_', 'hybrid_']
            for i, f in enumerate(fams):
                if m.startswith(f):
                    return i
            return 99
        agg['fidx'] = agg['method'].apply(family_order)
        agg = agg.sort_values(['fidx', 'method']).drop(columns=['fidx'])
        agg.to_csv(f'{out_dir}/{dset_name}_summary.csv', index=False)

        # ── anomalies ─
        with open(f'{out_dir}/{dset_name}_anomalies.txt', 'w') as f:
            if m3_val_sizes:
                f.write(f"M3 validation-set size: {m3_val_sizes[0]}\n")
            if m3_zero_win_fracs:
                f.write(f"M3 zero-win fraction mean on UNPRUNED model: "
                        f"{np.mean(m3_zero_win_fracs):.4f}\n")
            if m3_max_keep:
                f.write(f"M3 max segments it can keep (correct val patterns) "
                        f"mean: {np.mean(m3_max_keep):.1f}\n")
            f.write("\nzero_mem_frac per method:\n")
            for _, r in agg.iterrows():
                f.write(f"  {r['method']}: {r['zero_mem_frac_mean']:.4f}\n")

            acc_counts = agg['accuracy_mean'].round(6).value_counts()
            dups = acc_counts[acc_counts > 1].index
            if len(dups) > 0:
                f.write("\nMethods with exactly equal mean accuracy:\n")
                for dup in dups:
                    methods = agg[agg['accuracy_mean'].round(6) == dup]['method'].tolist()
                    f.write(f"  {dup}: {', '.join(methods)}\n")

            neg_red = agg[agg['reduction_vs_raw_mean'] < 0]
            if not neg_red.empty:
                f.write("\nNegative mean reduction_vs_raw configurations:\n")
                for _, r in neg_red.iterrows():
                    f.write(f"  {r['method']}: {r['reduction_vs_raw_mean']:.4f}\n")

        # ── headline table (5 bins, all families) ─
        bins = [float('-inf'), 0.2, 0.4, 0.6, 0.8, 1.0]
        bin_labels = ['(-inf,0.2)', '[0.2,0.4)', '[0.4,0.6)', '[0.6,0.8)', '[0.8,1.0]']
        agg['bin'] = pd.cut(agg['reduction_vs_raw_mean'], bins=bins,
                            labels=bin_labels, right=False)

        def family_name(m):
            if m == 'unreduced': return 'unreduced'
            for f in ['theta_sweep', 'cnn', 'enn', 'kmeans', 'random',
                       'm1', 'm3', 'hybrid']:
                if m.startswith(f): return f
            return 'other'
        agg['family'] = agg['method'].apply(family_name)

        hl = agg.groupby(['family', 'bin'], observed=False).agg(
            mean_acc=('accuracy_mean', 'mean'),
            count=('method', 'count'),
        ).reset_index()
        hl = hl[hl['count'] > 0]
        hl.to_csv(f'{out_dir}/{dset_name}_headline_table.csv', index=False)

        # ── plots ─
        families = ['theta_sweep', 'cnn', 'enn', 'kmeans', 'random',
                     'm1', 'm3', 'hybrid', 'unreduced']
        colors = ['blue', 'red', 'orange', 'green', 'purple',
                  'brown', 'pink', 'gray', 'black']

        plt.figure(figsize=(10, 6))
        for fam, c in zip(families, colors):
            f_df = agg[agg['method'].str.startswith(fam)]
            if len(f_df) == 0:
                continue
            f_df = f_df.sort_values('reduction_vs_raw_mean')
            plt.errorbar(f_df['reduction_vs_raw_mean'], f_df['accuracy_mean'],
                         yerr=f_df['accuracy_std'], label=fam, marker='o',
                         color=c, linestyle='-' if len(f_df) > 1 else '')
        plt.xlabel('Reduction vs Raw')
        plt.ylabel('Accuracy')
        plt.title(f'{dset_name} - Accuracy vs Reduction')
        plt.legend()
        plt.savefig(f'{out_dir}/{dset_name}_acc_vs_red.png')
        plt.close()

        plt.figure(figsize=(10, 6))
        for fam, c in zip(families, colors):
            f_df = agg[agg['method'].str.startswith(fam)]
            if len(f_df) == 0:
                continue
            f_df = f_df.sort_values('n_segments_mean')
            plt.errorbar(f_df['n_segments_mean'], f_df['accuracy_mean'],
                         yerr=f_df['accuracy_std'], label=fam, marker='o',
                         color=c, linestyle='-' if len(f_df) > 1 else '')
        plt.xlabel('Number of Segments')
        plt.ylabel('Accuracy')
        plt.title(f'{dset_name} - Accuracy vs Segments')
        plt.legend()
        plt.savefig(f'{out_dir}/{dset_name}_acc_vs_segments.png')
        plt.close()

        print(f"  Runtime: {time.perf_counter() - sweep_t0:.1f}s", flush=True)

    return out_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datasets', type=str, help='Comma separated dataset names')
    parser.add_argument('--tag', type=str, default='sweep1', help='Tag for the output directory')
    parser.add_argument('--out-dir', type=str, default=None, help='Explicit output directory override')
    args = parser.parse_args()

    run_sweep(datasets_override=args.datasets, out_dir=args.out_dir, tag=args.tag)


if __name__ == '__main__':
    main()
