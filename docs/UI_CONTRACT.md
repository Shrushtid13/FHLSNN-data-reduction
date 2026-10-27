# UI Contract: FHLSNN Platform Frontend & Worker Interface

This document specifies the exact JSON contract between the React frontend (`/web`) and the backend data sources (Supabase Postgres, Express API `/api`, and the ML worker `/ml_service`). 

The worker writes `metrics` and `facts` into the `experiments` database row upon execution progress and completion. The frontend reads these objects from `GET /experiments/:id` and formats them deterministically. Every number displayed in the UI must strictly originate from these fields; any missing, null, or undefined values must render `"not available"`.

---

## 1. Top-Level Experiment Row Shape

A single experiment record retrieved from `GET /experiments/:id` has the following structure:

```typescript
interface ExperimentRow {
  id: string;                                 // UUID
  dataset_id: string;                         // UUID referencing datasets(id)
  method: 'unreduced' | 'm1' | 'm3' | 'hybrid';
  params: ExperimentParams;                   // JSON object (see Section 4)
  seed: number;                               // Integer (default: 42)
  status: 'queued' | 'running' | 'done' | 'failed';
  progress: number;                           // Integer between 0 and 100
  metrics: ExperimentMetrics | null;          // JSON object populated on completion
  facts: ExperimentFacts | null;              // JSON object populated during/after execution
  error: string | null;                       // Failure message if status === 'failed'
  created_at: string;                         // ISO 8601 timestamp
}
```

---

## 2. `metrics` Object Specification

The `metrics` column contains summary statistical and operational evaluation metrics computed against the held-out test split and the training fold.

```typescript
interface ExperimentMetrics {
  // --- Accuracy & Performance Fractions (0.0 to 1.0) ---
  accuracy: number;                           // Test accuracy fraction [0, 1]
  macro_f1: number;                           // Macro-averaged F1 score [0, 1]
  reduction_vs_raw: number;                   // 1 - (stored_vectors / n_fit). Note: Can be negative if stored_vectors > n_fit
  zero_mem_frac: number;                      // Fraction of test patterns with zero membership across all segments [0, 1]

  // --- Integer Pattern & Segment Counts ---
  stored_vectors: number;                     // Count of distinct endpoint vectors stored in the model
  n_fit: number;                              // Count of patterns in the training fit split (80% of train fold)
  n_val: number;                              // Count of patterns in the validation split (20% of train fold)
  n_test: number;                             // Count of patterns in the test split
  n_segments: number;                         // Count of hyperline segments in the trained model

  // --- Tuned Hyperparameters ---
  best_theta: number;                         // Maximum hyperline segment length threshold (e.g. 0.4)
  best_gamma: number;                         // Sensitivity / slope parameter (e.g. 0.25)

  // --- Baseline Reference (Unreduced Run on the exact same split) ---
  reference: {
    accuracy: number;                         // Unreduced test accuracy fraction [0, 1]
    macro_f1: number;                         // Unreduced macro-F1 fraction [0, 1]
    stored_vectors: number;                   // Unreduced stored vector count
    n_segments: number;                       // Unreduced hyperline segment count
  };
}
```

---

## 3. `facts` Object Specification

The `facts` column contains runtime execution telemetry, intermediate logs, reduction curves, PCA projections, class breakdowns, and natural language explanations.

```typescript
interface ExperimentFacts {
  // --- Execution Stage Telemetry ---
  // One of five sequential pipeline stages:
  stage?: 'profile' | 'split_scale' | 'tune' | 'train' | 'evaluate';

  // --- Live Execution Log Lines ---
  // Chronological array of log strings emitted by the worker (rendered last 50 lines in UI)
  log?: string[];

  // --- Accuracy vs. Reduction Curves ---
  curve?: {
    series: Array<{
      name: string;                           // e.g. "Hybrid (this run)", "Random subsampling", "Unreduced baseline"
      style: 'solid' | 'dashed' | 'dotted';   // Line dash style for chart rendering
      points: Array<{
        x: number;                            // reduction_vs_raw fraction [0, 1]
        y: number;                            // accuracy fraction [0, 1]
      }>;
    }>;
  };

  // --- Per-Class Sample Breakdown ---
  per_class?: Array<{
    label: string;                            // Class label / name (e.g. "Setosa", "Versicolor")
    before: number;                           // Count of patterns before reduction
    kept: number;                             // Count of patterns retained after reduction
  }>;

  // --- 2D PCA Projections (Before vs. After) ---
  pca?: {
    points: Array<{
      x: number;                              // 1st Principal Component coordinate
      y: number;                              // 2nd Principal Component coordinate
      label: string;                          // Class label for coloring
      kept: boolean;                          // true = retained, false = removed (rendered faded)
    }>;
  };

  // --- Natural Language Explanation ---
  explanation?: {
    text: string;                             // Plain English explanation of the reduction outcome and variance
  };
}
```

---

## 4. `params` Object Specification (Configure Screen Payload)

The `params` JSON object is submitted by the frontend via `POST /experiments` and read by the worker to configure model reduction and training:

```typescript
interface ExperimentParams {
  // Selected model variant
  variant: 'fhlsnn2001' | 'mfhlsnn2014_midpoint';

  // M1 Boundary-Proximity Pre-Filtering parameters (applicable for 'm1' and 'hybrid')
  keep_fraction?: number;                     // Float in range [0.2, 0.9] (default: 0.5)
  interior_keep_rate?: number;                // Float in range [0.0, 1.0] (default: 0.1)

  // M3 Membership-Contribution Pruning parameters (applicable for 'm3' and 'hybrid')
  min_wins?: number;                          // Integer >= 1 (default: 1)

  // Hyperparameter tuning
  tune_hyperparams: boolean;                  // Boolean (default: true)
}
```

### Parameter Validation Rules:
1. `variant`: Must be either `'fhlsnn2001'` or `'mfhlsnn2014_midpoint'`.
2. `keep_fraction`: Enabled only when `method === 'm1' || method === 'hybrid'`. Range: `0.2` to `0.9` (step `0.1`).
3. `interior_keep_rate`: Enabled only when `method === 'm1' || method === 'hybrid'`. Range: `0.0` to `1.0` (step `0.1`).
4. `min_wins`: Enabled only when `method === 'm3' || method === 'hybrid'`. Integer: `>= 1`.
5. `seed`: Integer in range `0` to `2147483647` (default: `42`).
6. `tune_hyperparams`: Checkbox boolean (default: `true`).

---

## 5. UI Formatting & Display Rules

| Metric / Field | Raw Type / Unit | Formatted Display Rule | Example |
| :--- | :--- | :--- | :--- |
| `accuracy` | Float fraction `[0, 1]` | `(val * 100).toFixed(1) + "%"` | `0.957` &rarr; `95.7%` |
| `macro_f1` | Float fraction `[0, 1]` | `(val * 100).toFixed(1) + "%"` | `0.956` &rarr; `95.6%` |
| `reduction_vs_raw` | Float fraction | `(val * 100).toFixed(1) + "%"` | `0.500` &rarr; `50.0%` |
| `zero_mem_frac` | Float fraction `[0, 1]` | `(val * 100).toFixed(1) + "%"` | `0.0` &rarr; `0.0%` |
| Delta vs. Reference | Float delta `(curr - ref)` | `((curr - ref) * 100).toFixed(1) + " pp"` (with explicit `+` or `-`) | `+0.1 pp` vs unreduced |
| `stored_vectors` | Integer count | Main: `{stored_vectors}`<br>Subtext: `"of {n_fit} fit patterns"` | Main: `48`<br>Subtext: `of 96 fit patterns` |
| `n_segments` | Integer count | Main: `{n_segments}`<br>Subtext: `"unreduced: {reference.n_segments}"` | Main: `24`<br>Subtext: `unreduced: 48` |
| Share Kept (Class) | Ratio `(kept / before)` | `((kept / before) * 100).toFixed(0) + "%"` | `16 / 32` &rarr; `50%` |
| Explanation Footer | Integer metadata | `"Seed {seed}. Fit {n_fit}, validation {n_val}, test {n_test}."` | `Seed 42. Fit 96, validation 24, test 30.` |
| Missing / Null Values | `null` or `undefined` | Must render `"not available"`. Never invent or guess values. | `not available` |

---

## 6. Development & Test Fixtures

- Test fixture file: [`web/src/fixtures/sampleExperiment.json`](file:///d:/Final%20Year%20project/web/src/fixtures/sampleExperiment.json).
- The fixture strictly complies with `ExperimentRow` above and represents a completed, verified benchmark run.
- Used exclusively by unit/integration tests and the DEV-only route `/dev/sample-result`.
- The `/dev/sample-result` route is gated behind `import.meta.env.DEV` and displays a persistent red warning banner:
  > **SAMPLE DATA, NOT A REAL RUN**
- In production builds (`npm run build`), the `/dev/sample-result` route and the string `"SAMPLE DATA"` are completely stripped from the output bundle.
