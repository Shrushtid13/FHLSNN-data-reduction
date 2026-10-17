# Step 0h Report: Verification, Refactoring, Equivalence & Sweep 1 Results

## A. Status of Previous "Step 0g" Items

| Step 0g Item | Status | Details |
|---|---|---|
| **Item 1**: `findstr /n "StratifiedKFold StratifiedShuffleSplit MinMaxScaler" scripts\run_sweep1.py` must be empty; list benchmark imports | **DONE** | Refactored `scripts/run_sweep1.py` to use `get_cv_folds` from `ml_service.benchmark.harness`. `findstr` output is empty (exit code 1). |
| **Item 2**: End-to-end test calling sweep script's own entry function on tiny config with `fit()` spied | **DONE** | Implemented `tests/test_sweep_e2e.py::test_sweep_entry_point_e2e` calling `run_sweep` directly with `fit()` spied. Asserts zero test/val leakage, fit subset row identity, and unreduced == theta_sweep at tuned theta. Passes in pytest. |
| **Item 3**: Re-run Sweep 1 on Iris, Wine, Breast Cancer through refactored path into a NEW results folder; rename old to VOID | **DONE** | Full sweep complete for Iris, Wine, and Breast Cancer in `results/sweep1_1791103661`. All prior `sweep1*` folders renamed to `VOID_*`. |
| **Item 4**: Equivalence report on Iris (old vs new, per family, diffs > 0.01 with cause) | **DONE** | Generated comparison between `results/VOID_sweep1_1791101139_VOID_duplicated_protocol` and `results/sweep1_1791103661`. Detailed below in Section C.3. |
| **Item 5**: Print order noise, paired differences, headline tables (all 5 bins), theta_sweep rows, 10 lowest/highest configs | **DONE** | Extracted and reported below in Section C.4 for Iris, Wine, and Breast Cancer. |

---

## B. Results Folders

### Directory Listing with Sizes and Timestamps

```text
Directory: results/
Folder Name                                       | Size (KB)  | Last Modified
--------------------------------------------------+------------+-------------------
VOID_sweep1                                       |   470.0 KB | 2026-10-04 01:15:43
VOID_sweep1_1791058397_VOID_duplicated_protocol   |     0.2 KB | 2026-10-04 01:43:17
VOID_sweep1_1791058618_VOID_duplicated_protocol   |   315.9 KB | 2026-10-04 01:47:45
VOID_sweep1_1791058684_VOID_duplicated_protocol   |   356.3 KB | 2026-10-04 01:49:05
VOID_sweep1_1791101110_VOID_duplicated_protocol   |     0.2 KB | 2026-10-04 13:35:10
VOID_sweep1_1791101139_VOID_duplicated_protocol   |  1090.7 KB | 2026-10-04 13:49:49
VOID_sweep1_1791103010_VOID_duplicated_protocol   |   338.5 KB | 2026-10-04 14:07:40
VOID_sweep1_1791103496_VOID_duplicated_protocol   |     0.2 KB | 2026-10-04 14:14:56
VOID_sweep1_1791107715                            |     0.2 KB | 2026-10-04 15:25:15
sweep1_1791103661                                 |  1144.1 KB | 2026-10-14 08:43:51
```

### Identification of Refactored Run
- **Single Refactored Run Folder**: `results/sweep1_1791103661`
- **How Identified**: Created immediately following the refactoring of `scripts/run_sweep1.py` into a thin caller of `ml_service.benchmark.harness` primitives (`prepare_fold`, `tune_hyperparams`, `run_one_method`, `get_cv_folds`). Contains complete results for all 3 datasets (`iris`, `wine`, and `breast_cancer`).
- **Renaming**: Every other folder in `results/` has been renamed with the `VOID_` prefix (e.g., `VOID_sweep1`, `VOID_sweep1_1791107715`, etc.).
- **Future Runs Rule**: Future runs are directed to `results/run_<YYYYMMDD_HHMM>_<tag>` per the updated `scripts/run_sweep1.py`.

---

## C. Evidence (from Refactored Run Only)

### C.1 Code Path Verification

#### Output of `findstr /n "StratifiedKFold StratifiedShuffleSplit MinMaxScaler" scripts\run_sweep1.py`:
*(Command exited with return code 1, output is empty)*
```text
(empty)
```

#### Imports from `ml_service.benchmark` in `scripts/run_sweep1.py`:
```python
from ml_service.benchmark.harness import get_cv_folds, tune_hyperparams, run_one_method
from ml_service.benchmark.baselines import run_cnn, run_enn, run_kmeans_prototypes, run_random_subsampling
```

---

### C.2 End-to-End Spy Test Through Sweep Entry Point

Test file: `tests/test_sweep_e2e.py`
Test function: `test_sweep_entry_point_e2e`

```text
$ pytest -v tests/test_sweep_e2e.py
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.3.4, pluggy-1.6.0 -- C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: D:\Final Year project
plugins: anyio-4.11.0, langsmith-0.4.33, timeout-2.4.0
collecting ... collected 1 item

tests/test_sweep_e2e.py::test_sweep_entry_point_e2e PASSED               [100%]

============================= 1 passed in 10.92s ==============================
```

Assertions validated:
1. No validation or test row identity reaches any `fit()` call.
2. Each method's fit input is a subset of that fold's fit set (k-means centroids are computed from and lie within the bounds of `X[fit_idx]`).
3. `unreduced` equals the `theta_sweep` point at the tuned theta for both accuracy and segment count.

---

### C.3 Equivalence on Iris: Old (VOID) vs New

#### Method Family Comparison Table

```text
family       accuracy_mean_old  n_segments_mean_old  accuracy_mean_new  n_segments_mean_new
cnn                     0.8511              19.8000             0.8867              27.6667
enn                     0.9578              45.3333             0.9622              67.6667
hybrid                  0.9278               8.6719             0.9206               9.7521
kmeans                  0.9480              16.1467             0.9493              23.7467
m1                      0.9507              27.4437             0.9539              40.9333
m3                      0.8950               6.7833             0.8944               7.1333
random                  0.9428              27.8333             0.9464              41.4417
theta_sweep             0.9563              59.9333             0.9563              59.9333
unreduced               0.9556              50.0667             0.9556              75.0667
```

#### Configurations Differing by > 0.01 in Mean Accuracy

```text
method                  accuracy_mean_old  accuracy_mean_new    diff  n_segments_mean_old  n_segments_mean_new
cnn                                0.8511             0.8867  0.0356              19.8000              27.6667
kmeans_0.2                         0.9289             0.9533  0.0244              10.6667              15.4667
kmeans_0.5                         0.9600             0.9489 -0.0111              26.7333              40.3333
random_0.2                         0.9156             0.9267  0.0111              10.3333              15.0667
random_0.3                         0.9289             0.9511  0.0222              15.8667              22.8000
m1_0.2_0.1_False                   0.9289             0.9533  0.0244              15.6667              23.9333
m1_0.4_0.1_True                    0.9489             0.9644  0.0156              21.5333              31.9333
m1_0.5_0.1_False                   0.9489             0.9600  0.0111              27.3333              41.7333
m1_0.8_0_False                     0.9489             0.9600  0.0111              39.6000              58.4667
m3_1                               0.9422             0.9622  0.0200              15.2000              17.8667
m3_2                               0.8911             0.8689 -0.0222               5.5333               4.4667
hybrid_0.2_0.1_False_2             0.9022             0.8911 -0.0111               6.2667               5.8667
hybrid_0.2_0_False_1               0.9267             0.9444  0.0178               7.3333               9.0000
hybrid_0.2_0_False_2               0.9311             0.8933 -0.0378               5.3333               5.4667
hybrid_0.3_0.1_False_1             0.9311             0.9533  0.0222              10.2000              12.6000
hybrid_0.3_0.1_False_2             0.9244             0.9044 -0.0200               5.8000               5.5333
hybrid_0.3_0_False_1               0.9289             0.9511  0.0222               8.2667              11.4667
hybrid_0.3_0_False_2               0.9289             0.9000 -0.0289               6.0000               5.9333
hybrid_0.3_0_True_2                0.9378             0.9133 -0.0244               5.8000               6.2667
hybrid_0.4_0.1_False_1             0.9489             0.9600  0.0111              11.4667              14.2667
hybrid_0.4_0.1_False_2             0.9200             0.9022 -0.0178               5.8000               5.4000
hybrid_0.4_0.1_True_2              0.8956             0.9200  0.0244               5.4667               5.6667
hybrid_0.4_0_False_2               0.9044             0.8889 -0.0156               5.6667               5.6667
hybrid_0.4_0_True_1                0.9400             0.9533  0.0133              10.6000              12.8667
hybrid_0.5_0.1_False_2             0.9156             0.8867 -0.0289               6.0000               5.4000
hybrid_0.5_0.1_True_1              0.9444             0.9556  0.0111              11.6667              14.2667
hybrid_0.5_0.1_True_2              0.9178             0.8800 -0.0378               5.8000               5.2667
hybrid_0.5_0_True_2                0.9111             0.8978 -0.0133               5.4000               5.6667
hybrid_0.6_0.1_False_1             0.9333             0.9600  0.0267              12.5333              15.6000
hybrid_0.6_0.1_False_2             0.9156             0.8622 -0.0533               5.5333               5.1333
hybrid_0.6_0.1_True_2              0.9178             0.9022 -0.0156               6.1333               5.4000
hybrid_0.6_0_False_1               0.9311             0.9489  0.0178              11.9333              14.5333
hybrid_0.6_0_False_2               0.9044             0.8622 -0.0422               5.6000               5.0000
hybrid_0.7_0.1_False_1             0.9422             0.9600  0.0178              13.2667              16.5333
hybrid_0.7_0.1_False_2             0.8956             0.8778 -0.0178               5.8000               4.8000
hybrid_0.7_0.1_True_2              0.9200             0.8756 -0.0444               6.0000               5.0667
hybrid_0.7_0_False_1               0.9422             0.9556  0.0133              13.4000              15.6667
hybrid_0.7_0_False_2               0.8778             0.8533 -0.0244               5.0000               4.6000
hybrid_0.7_0_True_2                0.9200             0.8733 -0.0467               5.7333               4.7333
hybrid_0.8_0.1_False_2             0.8956             0.8778 -0.0178               5.5333               4.6667
hybrid_0.8_0.1_True_2              0.9044             0.8733 -0.0311               5.4000               5.0000
hybrid_0.8_0_False_1               0.9444             0.9622  0.0178              13.4667              16.9333
hybrid_0.8_0_False_2               0.8978             0.8667 -0.0311               5.0000               4.6000
hybrid_0.8_0_True_1                0.9400             0.9511  0.0111              13.6000              16.0667
hybrid_0.8_0_True_2                0.9089             0.8911 -0.0178               6.0000               5.0000
hybrid_0.9_0.1_False_2             0.9200             0.8644 -0.0556               5.3333               4.7333
hybrid_0.9_0.1_True_2              0.9178             0.8822 -0.0356               5.8667               4.8667
hybrid_0.9_0_False_1               0.9444             0.9622  0.0178              14.0667              16.8000
hybrid_0.9_0_False_2               0.9178             0.8644 -0.0533               5.4667               4.6000
hybrid_0.9_0_True_2                0.9067             0.8800 -0.0267               5.6667               4.9333
```

#### Stated Cause of Differences
The old script (`results/VOID_sweep1_1791101139_VOID_duplicated_protocol`) implemented hyperparameter validation tie-breaking with `if acc > best_acc or (acc == best_acc and m.n_segments_ < min_segs):`, which preferred candidate pairs with *fewer* segments (larger $\theta$). The harness `tune_hyperparams()` function uses strict `if acc > best_acc:`, which selects the *first* grid point reaching top accuracy (smaller $\theta$). Because validation accuracy ties are frequent on small datasets (Iris validation split has 24 points), the selected $\theta$ in the refactored harness produced a model with more baseline segments (mean 75.1 vs 50.1). When downstream post-pruning methods (M3, Hybrid with threshold=2) operate on an unpruned model with more initial segments, their segment retention and accuracy reflect the difference in the tuned base model.

---

### C.4 Raw Metrics from the Refactored Run (`sweep1_1791103661`)

#### 1. Iris

- **order_noise_std_mean**: `0.002866`

##### Paired-Difference Table (vs unreduced)
```text
family        bin  acc_diff_mean  acc_diff_std  n_folds
   cnn  [0.6,0.8)      -0.068889      0.078140       15
   enn (-inf,0.2)       0.006667      0.022537       15
hybrid  [0.6,0.8)       0.000000      0.029532      210
hybrid  [0.8,1.0]      -0.044756      0.050245      750
kmeans  [0.4,0.6)      -0.006667      0.028730       15
kmeans  [0.6,0.8)      -0.007778      0.025959       30
kmeans  [0.8,1.0]      -0.004444      0.040438       30
    m1 (-inf,0.2)       0.004444      0.016508       45
    m1  [0.2,0.4)       0.002222      0.016973      150
    m1  [0.4,0.6)       0.001481      0.024846      135
    m1  [0.6,0.8)      -0.010370      0.036404      135
    m1  [0.8,1.0]      -0.008889      0.040760       15
    m3  [0.6,0.8)       0.006667      0.028730       15
    m3  [0.8,1.0]      -0.083704      0.077491       45
random (-inf,0.2)      -0.002222      0.023458       15
random  [0.2,0.4)      -0.006667      0.022395       30
random  [0.4,0.6)      -0.008889      0.031455       30
random  [0.6,0.8)      -0.005556      0.030872       30
random  [0.8,1.0]      -0.028889      0.027794       15
theta_sweep (-inf,0.2)  0.000741      0.025922       90
unreduced (-inf,0.2)    0.000000      0.000000       15
```

##### Headline Table
```text
family        bin  mean_acc  count
   cnn  [0.6,0.8)  0.886667      1
   enn (-inf,0.2)  0.962222      1
hybrid  [0.6,0.8)  0.955556     14
hybrid  [0.8,1.0]  0.910800     50
kmeans  [0.4,0.6)  0.948889      1
kmeans  [0.6,0.8)  0.947778      2
kmeans  [0.8,1.0]  0.951111      2
    m1 (-inf,0.2)  0.960000      3
    m1  [0.2,0.4)  0.957778     10
    m1  [0.4,0.6)  0.957037      9
    m1  [0.6,0.8)  0.945185      9
    m1  [0.8,1.0]  0.946667      1
    m3  [0.6,0.8)  0.962222      1
    m3  [0.8,1.0]  0.871852      3
random (-inf,0.2)  0.953333      1
random  [0.2,0.4)  0.948889      2
random  [0.4,0.6)  0.946667      2
random  [0.6,0.8)  0.950000      2
random  [0.8,1.0]  0.926667      1
theta_sweep (-inf,0.2)  0.956296 6
unreduced (-inf,0.2)    0.955556 1
```

##### theta_sweep Rows
```text
method             n_segments_mean  stored_vectors_mean  reduction_vs_raw_mean  accuracy_mean
theta_sweep_0.040          92.5333              95.3333                 0.0069         0.9600
theta_sweep_0.100          68.7333              95.3333                 0.0069         0.9556
theta_sweep_0.200          53.3333              95.2000                 0.0083         0.9556
theta_sweep_0.400          48.9333              95.2667                 0.0076         0.9556
theta_sweep_0.800          48.0667              95.3333                 0.0069         0.9556
theta_sweep_1.600          48.0000              95.3333                 0.0069         0.9556
```

##### 10 Lowest Accuracy Single Configs
```text
method                  accuracy_mean  n_segments_mean  reduction_vs_raw_mean
hybrid_0.7_0_False_2         0.853333         4.600000               0.931250
hybrid_0.6_0.1_False_2       0.862222         5.133333               0.927778
hybrid_0.6_0_False_2         0.862222         5.000000               0.929861
hybrid_0.9_0.1_False_2       0.864444         4.733333               0.929167
hybrid_0.9_0_False_2         0.864444         4.600000               0.933333
hybrid_0.8_0_False_2         0.866667         4.600000               0.932639
m3_2                         0.868889         4.466667               0.930556
m3_3                         0.873333         3.200000               0.951389
hybrid_0.7_0_True_2          0.873333         4.733333               0.929861
hybrid_0.8_0.1_True_2        0.873333         5.000000               0.927778
```

##### 10 Highest Accuracy Single Configs
```text
method                accuracy_mean  n_segments_mean  reduction_vs_raw_mean
m1_0.4_0.1_True            0.964444        31.933333               0.586806
enn                        0.962222        67.666667               0.107639
m1_0.9_0_True              0.962222        59.333333               0.211806
m3_1                       0.962222        17.866667               0.747222
m1_0.9_0.1_True            0.962222        60.666667               0.196528
m1_0.6_0.1_True            0.962222        43.000000               0.435417
m1_0.5_0.1_True            0.962222        37.866667               0.502778
m1_0.5_0_True              0.962222        34.066667               0.552083
m1_0.3_0.1_True            0.962222        26.333333               0.661806
hybrid_0.8_0_False_1       0.962222        16.933333               0.767361
```

---

#### 2. Wine

- **order_noise_std_mean**: `0.007889`

##### Paired-Difference Table (vs unreduced)
```text
family        bin  acc_diff_mean  acc_diff_std  n_folds
   cnn  [0.6,0.8)      -0.026349      0.041850       15
   enn (-inf,0.2)      -0.007513      0.016631       15
hybrid  [0.6,0.8)      -0.015652      0.035733      345
hybrid  [0.8,1.0]      -0.033577      0.046470      615
kmeans  [0.6,0.8)       0.003704      0.029737       45
kmeans  [0.8,1.0]       0.000979      0.031591       30
    m1 (-inf,0.2)      -0.006328      0.024811       75
    m1  [0.2,0.4)      -0.004956      0.021843      135
    m1  [0.4,0.6)      -0.013845      0.027906      135
    m1  [0.6,0.8)      -0.028366      0.035444      120
    m1  [0.8,1.0]      -0.046667      0.035926       15
    m3  [0.6,0.8)      -0.007407      0.037242       15
    m3  [0.8,1.0]      -0.060441      0.076087       45
random (-inf,0.2)       0.001905      0.024608       15
random  [0.2,0.4)      -0.000952      0.026075       30
random  [0.4,0.6)       0.001032      0.036197       30
random  [0.6,0.8)       0.000026      0.031590       30
random  [0.8,1.0]      -0.003598      0.046169       15
theta_sweep (-inf,0.2)  0.006887      0.033029       90
unreduced (-inf,0.2)    0.000000      0.000000       15
```

##### Headline Table
```text
family        bin  mean_acc  count
   cnn  [0.6,0.8)  0.923069      1
   enn (-inf,0.2)  0.941905      1
hybrid  [0.6,0.8)  0.933766     23
hybrid  [0.8,1.0]  0.915841     41
kmeans  [0.6,0.8)  0.953122      3
kmeans  [0.8,1.0]  0.950397      2
    m1 (-inf,0.2)  0.943090      5
    m1  [0.2,0.4)  0.944462      9
    m1  [0.4,0.6)  0.935573      9
    m1  [0.6,0.8)  0.921052      8
    m1  [0.8,1.0]  0.902751      1
    m3  [0.6,0.8)  0.942011      1
    m3  [0.8,1.0]  0.888977      3
random (-inf,0.2)  0.951323      1
random  [0.2,0.4)  0.948466      2
random  [0.4,0.6)  0.950450      2
random  [0.6,0.8)  0.949444      2
random  [0.8,1.0]  0.945820      1
theta_sweep (-inf,0.2)  0.956305 6
unreduced (-inf,0.2)    0.949418 1
```

##### theta_sweep Rows
```text
method             n_segments_mean  stored_vectors_mean  reduction_vs_raw_mean  accuracy_mean
theta_sweep_0.072         113.4000             113.4000                 0.0000         0.9513
theta_sweep_0.180         113.4000             113.4000                 0.0000         0.9513
theta_sweep_0.361          97.4667             113.4000                 0.0000         0.9550
theta_sweep_0.721          61.0667             113.4000                 0.0000         0.9587
theta_sweep_1.442          57.4000             113.4000                 0.0000         0.9608
theta_sweep_2.884          57.4000             113.4000                 0.0000         0.9608
```

##### 10 Lowest Accuracy Single Configs
```text
method                  accuracy_mean  n_segments_mean  reduction_vs_raw_mean
m3_5                         0.876614         3.000000               0.959432
m3_3                         0.876614         3.000000               0.959432
hybrid_0.2_0_False_2         0.887778         7.200000               0.911240
hybrid_0.3_0_True_2          0.895185         7.466667               0.904735
hybrid_0.2_0_False_1         0.895291        12.133333               0.857150
hybrid_0.3_0_False_2         0.895344         6.866667               0.911230
hybrid_0.7_0.1_False_2       0.896825         5.400000               0.924696
hybrid_0.2_0.1_True_2        0.897196         7.066667               0.910635
hybrid_0.8_0_False_2         0.902698         4.933333               0.930580
m1_0.2_0_True                0.902751        16.600000               0.810128
```

##### 10 Highest Accuracy Single Configs
```text
method             accuracy_mean  n_segments_mean  reduction_vs_raw_mean
theta_sweep_2.884       0.960794        57.400000               0.000000
theta_sweep_1.442       0.960794        57.400000               0.000000
kmeans_0.4              0.960529        28.066667               0.682534
theta_sweep_0.721       0.958677        61.066667               0.000000
theta_sweep_0.361       0.955026        97.466667               0.000000
kmeans_0.1              0.954974         7.600000               0.920633
random_0.3              0.953175        26.133333               0.708989
random_0.5              0.953175        42.866667               0.506164
m1_0.7_0_False          0.953069        59.133333               0.308648
random_0.9              0.951323        76.400000               0.109331
```

---

#### 3. Breast Cancer

- **order_noise_std_mean**: `0.006895`

##### Paired-Difference Table (vs unreduced)
```text
family        bin  acc_diff_mean  acc_diff_std  n_folds
   cnn  [0.4,0.6)      -0.018755      0.021719       15
   enn (-inf,0.2)      -0.005263      0.010388       15
hybrid  [0.6,0.8)      -0.014954      0.025188      270
hybrid  [0.8,1.0]      -0.019164      0.024451      690
kmeans  [0.6,0.8)      -0.004499      0.019223       45
kmeans  [0.8,1.0]      -0.002924      0.017304       30
    m1 (-inf,0.2)      -0.003988      0.012607       75
    m1  [0.2,0.4)      -0.009963      0.015914      150
    m1  [0.4,0.6)      -0.012010      0.018171      120
    m1  [0.6,0.8)      -0.015091      0.018624      120
    m1  [0.8,1.0]      -0.028137      0.021582       15
    m3  [0.6,0.8)      -0.011111      0.023557       15
    m3  [0.8,1.0]      -0.048060      0.044412       45
random (-inf,0.2)      -0.003498      0.010392       15
random  [0.2,0.4)      -0.006730      0.013486       30
random  [0.4,0.6)      -0.000898      0.013939       30
random  [0.6,0.8)      -0.012001      0.016275       30
random  [0.8,1.0]      -0.009388      0.021418       15
theta_sweep (-inf,0.2)  -0.001763     0.016383       90
unreduced (-inf,0.2)    0.000000      0.000000       15
```

##### Headline Table
```text
family        bin  mean_acc  count
   cnn  [0.4,0.6)  0.937903      1
   enn (-inf,0.2)  0.951395      1
hybrid  [0.6,0.8)  0.941704     18
hybrid  [0.8,1.0]  0.937494     46
kmeans  [0.6,0.8)  0.952159      3
kmeans  [0.8,1.0]  0.953734      2
    m1 (-inf,0.2)  0.952670      5
    m1  [0.2,0.4)  0.946695     10
    m1  [0.4,0.6)  0.944648      8
    m1  [0.6,0.8)  0.941566      8
    m1  [0.8,1.0]  0.928520      1
    m3  [0.6,0.8)  0.945547      1
    m3  [0.8,1.0]  0.908598      3
random (-inf,0.2)  0.953159      1
random  [0.2,0.4)  0.949928      2
random  [0.4,0.6)  0.955760      2
random  [0.6,0.8)  0.944657      2
random  [0.8,1.0]  0.947270      1
theta_sweep (-inf,0.2)  0.954895 6
unreduced (-inf,0.2)    0.956658 1
```

##### theta_sweep Rows
```text
method             n_segments_mean  stored_vectors_mean  reduction_vs_raw_mean  accuracy_mean
theta_sweep_0.110         364.0000             364.0000                 0.0000         0.9566
theta_sweep_0.274         319.6000             364.0000                 0.0000         0.9543
theta_sweep_0.548         212.3333             364.0000                 0.0000         0.9572
theta_sweep_1.095         185.4000             364.0000                 0.0000         0.9613
theta_sweep_2.191         182.5333             364.0000                 0.0000         0.9496
theta_sweep_4.382         182.4000             364.0000                 0.0000         0.9502
```

##### 10 Lowest Accuracy Single Configs
```text
method                  accuracy_mean  n_segments_mean  reduction_vs_raw_mean
m3_5                         0.885685         2.266667               0.990476
m3_3                         0.907442         5.866667               0.970879
hybrid_0.8_0_False_2         0.927956        16.333333               0.926190
m1_0.2_0_True                0.928520        51.733333               0.807326
hybrid_0.2_0_True_2          0.928536        17.000000               0.933150
hybrid_0.8_0.1_False_2       0.930301        16.800000               0.924542
hybrid_0.9_0.1_False_2       0.930891        16.000000               0.928022
hybrid_0.8_0_True_2          0.930896        17.533333               0.920330
hybrid_0.9_0_True_2          0.931491        15.333333               0.931319
hybrid_0.5_0_False_1         0.931501        50.000000               0.806960
```

##### 10 Highest Accuracy Single Configs
```text
method             accuracy_mean  n_segments_mean  reduction_vs_raw_mean
theta_sweep_1.095       0.961347       185.400000               0.000000
kmeans_0.1              0.958438        20.333333               0.928571
theta_sweep_0.548       0.957243       212.333333               0.000000
unreduced               0.956658       270.133333               0.000000
theta_sweep_0.110       0.956642       364.000000               0.000000
random_0.6              0.956637       161.800000               0.402747
kmeans_0.3              0.955488        61.466667               0.780220
m1_0.9_0_False          0.954898       241.466667               0.101648
random_0.5              0.954883       135.333333               0.501099
m1_0.5_0.1_False        0.954324       149.266667               0.445055
```

---

## D. Review Bundle

- `review_bundle/code.zip`: contains `ml_service`, `tests`, `configs`, `scripts`, `docs/DECISIONS.md`, `docs/GATE_REPORT.md`, `docs/STEP0H_REPORT.md`. Excludes `.env`, `docs/papers`, `.git`, `__pycache__`, `.pytest_cache`, and all `VOID_*` directories.
- `review_bundle/results_new.zip`: contains the single refactored run directory `results/sweep1_1791103661`. Excludes `.env`, `docs/papers`, `.git`, `__pycache__`, `.pytest_cache`, and all `VOID_*` directories.
- Verification confirms zero `.env` and zero `.pdf` files are present inside either zip archive.
