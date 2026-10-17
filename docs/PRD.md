# PRD: FHLSNN-Based Data Reduction Platform (1-month build)

Final-year BE project, Group 43, Dept. of AI & Data Science, ADYPSOE Pune. Team of 4.
Build window: ~4 weeks. The written report is due ~2 months from now, so Month 2 is for report writing and extra experiments, not new features.

---

## 0. Instructions to the coding agent (read first)

You are the coding agent building this project. Read this whole document before writing any code. Source documents are in `/docs`: `FHLSNN_Project_Proposal.pdf`, the Stage-I presentation (`.pptx`), and `/docs/papers/*` (the FHLSNN / MFHLSNN papers). Where this PRD and the proposal differ, **this PRD wins**; every difference is listed with its reason in Section 3.

**Working agreements**

1. **Plan before code.** At the start of each milestone, write the plan to `docs/PLAN.md`: files to create, order of work, how you will verify it.
2. **Small, verified steps.** Every module ships with tests. Run them before saying something is done. Never say "done" for code you have not run.
3. **Never fabricate results.** No hardcoded metrics, no placeholder numbers in the UI, README, or reports. Every number shown to a user must come from a database row produced by a real run. If a result is bad, report it as bad.
4. **Do not invent algorithm details.** FHLSNN/MFHLSNN equations and procedures come from the papers in `/docs/papers`. If a paper is ambiguous or missing, stop, record the ambiguity in `docs/DECISIONS.md`, pick the simplest reasonable reading, and flag it to the human. Do not silently guess formulas.
5. **Keep two living docs** (they become report material): `docs/DECISIONS.md` (decision, reason, alternatives rejected) and `docs/STATUS.md` (done / in progress / blocked, updated at the end of every session).
6. **Ask the human only for real blockers** (missing paper, credentials, a correctness-affecting ambiguity). Otherwise choose the simplest option, log it, and continue.
7. **Respect the priority tiers (Section 2).** Do not start P1 work until the P0 gate passes. Do not start P2 work until the P1 gate passes. If time runs short, P2 is cut first, then P1 items in reverse order.
8. **Simplicity.** Build the smallest thing that meets the acceptance criteria. No extra frameworks, no speculative abstractions.
9. **Reproducibility.** Seed all randomness, pin dependencies, provide `make setup`, `make test`, `make dev`, `make benchmark`.
10. **Readable by students.** Four students must explain this code in a viva. Use clear names and comments that explain *why* at each algorithm step. Avoid clever one-liners in the core algorithm.

---

## 1. Product summary

**One sentence:** a web platform that shrinks a classification training set using Fuzzy Hyperline Segment Neural Network (FHLSNN) based methods while keeping accuracy close to the unreduced model, plus an AI layer that recommends a reduction strategy, explains what was removed and why, and (stretch) searches for the best configuration under a user's accuracy budget.

**The problem (from the proposal):** FHLSNN / MFHLSNN create many hyperline segments on large training sets, which raises training time and per-pattern recall time. Prior work (UFHLSNN + CUDA) scaled compute; this project reduces the data/segment count instead.

**What is genuinely the research contribution:** the reduction methods and their benchmark against classical instance-selection baselines. Everything else (web app, agents) is the delivery vehicle. If forced to choose, protect the research core.

---

## 2. Scope and priority tiers

### P0: Research core (must work; gate at end of Week 2)
- FHLSNN and MFHLSNN classifiers (NumPy), scikit-learn-style API (`fit`, `predict`).
- Two proposed reduction methods:
  - **M1: Boundary-Proximity Pre-Filtering** (proposal 5.1), instance-level.
  - **M3: Membership-Contribution Pruning** (proposal 5.3), segment-level.
  - **Hybrid** = M1 → train → M3 (a chain of the two; no new algorithm).
- Four classical baselines: Condensed NN, Edited NN, per-class k-means prototypes, random stratified subsampling.
- Benchmark harness that logs every run to the database.
- Datasets: Iris, Wine, Breast Cancer (small), sklearn `digits` (medium), Pendigits (~11k × 16, large; OpenML/UCI). Letter Recognition (20k × 16, 26 classes) is a stretch dataset.

### P1: Platform (gate at end of Week 3)
- Auth, CSV upload, dataset profiling, experiment creation, background job execution, results page with metrics and charts, benchmark page.
- **Recommendation agent** (retrieval over past experiments + one LLM call) and **explainability agent** (structured facts in, plain English out).

### P2: Stretch (only if P0 and P1 gates passed)
- **Reduction Agent**: tool-using LLM loop that searches for a configuration meeting a user goal ("maximize reduction with ≤ X pp accuracy loss"), evaluated against random search and Optuna.
- M4 Clustering-Guided Initialization (proposal 5.4).
- Redis pub/sub live progress (polling is the P1 default).

### Explicitly out of scope
GPU/CUDA, feature selection/reduction, streaming/incremental data, mixed continuous/discrete attributes (EFHLSNN), MongoDB, gRPC, Supabase Realtime, multi-tenant production hardening, M2 Segment Merging (documented as future work).

---

## 3. Decision log: deviations from the proposal and why

| # | Proposal says | This PRD does | Reason |
|---|---|---|---|
| D1 | "Implement ≥ 2 of the 4 methods" | Implement M1 + M3 (+ hybrid); M4 stretch; M2 future work | Matches the proposal's own "at least two" rule. M1 reduces samples (the headline claim) and M3 reduces segments (the documented bottleneck). They are independent, cheap, and composable. M2 needs a pairwise similarity design and tuning that is risky for a one-month build. |
| D2 | MERN (MongoDB) | Supabase Postgres only, no MongoDB | The proposal itself allows this. The data is relational (datasets, experiments, results) and needs RLS and pgvector. A second database adds work for no benefit. **Human must confirm with the project guide.** |
| D3 | REST/gRPC service | REST only (FastAPI) | gRPC adds tooling cost and nothing the project needs. |
| D4 | Redis queue + pub/sub + cache | Redis queue (RQ) + progress written to Postgres/Redis key, frontend polls every 2 s. Distance-matrix cache optional. | Polling delivers the same user-visible behavior with far less code. Pub/sub is a P2 swap. |
| D5 | Supabase Realtime | Polling | Same reasoning as D4. |
| D6 | "SLM-based dataset profiling" | Deterministic profiler (type inference, class balance, dimensionality, class-overlap indicators) producing a numeric profile vector. Optionally a small scikit-learn model that predicts the best method from profile + history. | A rule-based profiler is not a language model, and the report must not call it one. Call it "dataset profiler" (or "lightweight learned profiler" if the sklearn model is built). **Human must tell the guide about the wording change.** |
| D7 | pgvector RAG over experiment history | Keep pgvector, but the embedded object is the numeric **profile vector**, not text | Retrieval over a few hundred structured experiments works better on numeric similarity than on text embeddings, and it is still a genuine pgvector retrieval. |
| D8 | 8-month timeline (slides) / 5-month (PDF) | ~4-week build + 1 month for report | Student constraint. The report must describe the *actual* timeline. |
| D9 | Proposal and slides: "MFHLSNN uses the midpoint as well as the endpoints" and "creates too many segments on large sets" | Membership made pluggable; FHLSNN-2001 is the baseline; which MFHLSNN is primary is the guide's call (default: 2003 triangle height) | The midpoint description matches Shinde and Kulkarni 2014, not Patil et al. 2003. The "too many segments" statement is in the UFHLSNN paper's abstract and refers to the 2003 height-based MFHLSNN. The proposal blends two different papers; correct this in the proposal, slides and report. |

Add any further deviation to `docs/DECISIONS.md` as it happens.

---

## 4. Research core specification (P0)

### 4.1 FHLSNN / MFHLSNN
- Implement from the papers in `/docs/papers`. **Do not write formulas from memory.** The human supplies the PDFs; if they are missing, ask.
- **Source papers (in `/docs/papers`):** [FHLSNN] Kulkarni, Sontakke, Randale, IJCNN 2001, pp. 2918-2923. [MFHLSNN] Patil, Dhabe, Kulkarni, Sontakke, IEEE Int. Conf. on Fuzzy Systems 2003, pp. 1418-1422. Both PDFs are scans and their equations are garbled in extracted text, so **read the page images, not the extracted text.**
- **FHLSNN as published:** segment j has endpoints V_j and W_j (n-dim). For input R: l1 = ||W_j − R||, l2 = ||V_j − R||, l = ||W_j − V_j||, x = l1 + l2. Membership e_j = 1 − f(x, γ, l), where f = 0 if x = l, otherwise x·γ clipped to [0, 1]. Class score d_k = max membership over that class's segments; prediction = class with the highest score (ties unspecified). Features are scaled to [0, 1] per dimension. Learning is a single ordered pass; for each pattern, look only at same-class segments: (1) if the pattern already lies on a segment, skip; (2) if it lies on the *line* through a segment's endpoints, extend the segment to include it (replace the nearer-side endpoint) provided the new length ≤ ζ; (3) if the segment is a single point (V = W), extend it to include the pattern if length ≤ ζ; (4) otherwise create a new point-segment (V = W = pattern). After any extension or creation, test for intersection with other-class segments and, if one is found, undo the extension (restore the old endpoint) and open a new segment for the pattern.
- **MFHLSNN as published:** only the membership function changes. It builds the triangle (V, W, pattern), computes its height h by Heron's formula with base l, and uses h (the perpendicular distance) in place of x. If h > 0, m = 1 − f(h, γ); if h = 0, m = 1 − f(zz, γ) with zz = min(l1, l2). The 2003 paper does not use a segment midpoint. The midpoint version is a different paper (Shinde and Kulkarni 2014); see the variant map below.
- **Variant map. The literature uses "MFHLSNN" for two different papers, and there are five membership functions in total (read each paper's page images before implementing):**
  - FHLSNN (Kulkarni et al., 2001): x = l1 + l2, the sum of distances to both endpoints.
  - MFHLSNN-2003 (Patil et al.): triangle height, i.e. distance to the infinite line through V and W.
  - MFHLSNN-2014 (Shinde and Kulkarni): y = min(l1 + l2, l3), where l3 is the distance to the midpoint; also handles discrete attributes. This is the version the proposal describes. Printed issues: the midpoint is printed as |(w − v)/2|, which is not the midpoint (it should be (v + w)/2); and since l3 ≤ (l1 + l2)/2 by the triangle inequality, the min() always returns l3, so it is redundant (verify numerically).
  - UFHLSNN-2016 (Dhabe et al.): the 2003 height-based membership computed by vector projection (one square root instead of four), plus a CUDA implementation. It is not a new membership shape.
  - EFHLSNN-2017 (Shinde and Kulkarni): membership uses the shortest distance from the pattern to the *segment* (projection parameter t; closest endpoint if t < 0 or t > 1, perpendicular distance otherwise). It is continuous and equals 1 on the segment. The printed t = Σ(x − v)(w − v)/l probably should divide by l², since t must lie in [0, 1]. Also handles discrete attributes and extracts rules (Section 6.3). Its intersection test runs only after an extension (a newly created point-segment is not tested), which resolves issue 6 below.
  - **Implementation rule:** make the membership function pluggable (`fhlsnn2001`, `mfhlsnn2003_height`, `mfhlsnn2014_midpoint`, `efhlsnn2017_segment`) over one shared learning routine. FHLSNN-2001 is the baseline; which MFHLSNN variant is primary is the guide's decision (default until told otherwise: 2003 height). Variants beyond the first two are P1.
- **Parameter names:** the segment-length bound is ζ in the FHLSNN paper and θ in the MFHLSNN paper (same thing); γ is the sensitivity; the MFHLSNN paper also mentions a membership threshold ξ for inclusion. Use one name in code and note the other.
- **Known issues in the printed text. Implement as printed behind a flag, add a test that exposes each one, log it in `DECISIONS.md`, and ask the human before "fixing" anything:**
  1. FHLSNN's f() as printed uses x·γ, not (x − l)·γ. Membership therefore drops discontinuously from 1 to about 1 − l·γ just off a segment of length l. This may be intended (the MFHLSNN paper criticizes this function's "two slopes") or a typo.
  2. MFHLSNN's f(y, γ) is printed as y·γ if 0 < y·γ < 1, "otherwise 0". Read literally, far-away patterns would get membership 1. It almost certainly should be 1 when y·γ ≥ 1.
  3. h is the distance to the infinite line through V and W, not to the segment. Example: V = (0,0), W = (0.1,0), P = (0.9,0.01) gives h = 0.01 and membership 0.99 at γ = 1, although P is about 0.8 from the segment (FHLSNN gives 0 here). Points exactly on the segment (h = 0) get 1 − min(l1, l2)·γ rather than 1. Verify numerically before trusting the paper's convexity claim.
  4. The MFHLSNN paper describes training in one sentence (include if membership ≥ ξ, else new segment) and does not restate FHLSNN's steps. Simplest reading: same learning algorithm as FHLSNN with the membership function swapped. Log this assumption.
  5. Exact-collinearity checks (step 2 and the intersection test) need a numerical tolerance the papers do not give. Parallel, collinear and degenerate line pairs and the choice of equations for solving r1, r2 are unspecified. Use a least-squares solve with a residual tolerance, exposed as a parameter.
  6. Equation (15) (what to restore when step 4 creates an intersection) is garbled and appears to assign the new segment's endpoints to the old V_n. The accompanying sentence ("restore the end points of the previous segment of the other class") is garbled too. **Default: follow the 2017 paper, which does not intersection-test newly created point-segments** (flag `step4_intersection = "skip"`; alternatives `"swap_2014"` for the 2014 paper's reading and `"drop_new"`, which deletes the training pattern and must never be the default). Flag the choice to the human.
  7. "Contraction" in the paper means undoing the extension, not geometric shrinking.
  8. The paper says intersections are rare in moderate and high dimensions and reports identical recognition without the intersection test (2001 paper, Table 2). Implement the test but make it switchable (`use_intersection_test`).
- **Stored size is not small for the baseline.** The papers report 45 segments for 75 Iris training patterns at θ = 0.05 and 866-950 segments for 1000 ring-feature patterns. Many segments are point-segments, but the baseline barely compresses at small θ. Larger θ gives far fewer segments at an accuracy cost (FHLSNN: 3-4 segments, 8-14 errors out of 75 at θ = 0.8). Section 4.3 explains why this forces an extra baseline.
- Training is order-dependent, so pattern order must be shuffled by a seeded RNG and the seed stored with every experiment.
- Input normalization (typically min-max to the unit hypercube) is **fit on the training fold only**. Fitting on all data is leakage.
- Vectorize distance/membership computations with NumPy. Store all segment endpoints as matrices V and W (m × n) plus a class array, and compute memberships for all segments at once; per-segment Python loops in `predict` or `winning_segment` are not acceptable. Use Numba only if profiling shows it is needed.
- **Never discard a training pattern.** Every pattern must end up covered by a same-class segment. Ties between segments and the case where all memberships are 0 (common when γ is large relative to the feature-space size, because x·γ ≥ 1 gives membership 0) need an explicit, documented tie-break (for example nearest segment by distance), and the fraction of test patterns with all-zero membership must be logged as a metric.
- API: `fit(X, y)` (must reset all learned state, as scikit-learn estimators do; incremental learning goes through a separate `partial_fit`), `predict(X)`, `segments_` (endpoints + class), `n_segments_`, `winning_segment(X)` (needed by M3 and explainability), `extract_rules()` (human-readable per-segment description from endpoints and class).

**Acceptance (Gate A):**
- Unit tests with tiny hand-computed 2-D examples for: membership value, expansion, overlap detection, contraction, prediction.
- **Literature targets are limited.** The two papers report only Iris (4 features, 3 classes, a random 75/75 split whose seed is not published) and a private Devanagari ring-feature set (not reproducible). They give **no** numbers for Wine or Breast Cancer; leave those entries empty in `tests/literature_targets.yaml` and never invent them. Iris numbers from the MFHLSNN paper (75 test patterns, so 1 error = 1.33 pp): at θ = 0.05, γ = 1, FHLSNN made 45 segments / 4 errors and 37 segments / 6 errors for the two split directions; MFHLSNN made 45 / 2 and 37 / 2. At θ = 0.8, γ = 1: FHLSNN 4 segments / 14 errors and 3 / 8; MFHLSNN 40 / 6 and 32 / 2. Use these only as a loose sanity check across several random splits; differences of 2-4 errors are within noise. Do not use the papers' timing tables as targets: the 2001 paper's FHLSNN row (866 segments, 231.1 s) is identical to the 2003 paper's MFHLSNN row, while the 2003 paper lists FHLSNN as 950 segments, 328.23 s. The text and tables of the 2003 paper also disagree in places (its conclusion says "no misclassification at all"; its Table 1 shows 2-6). The 2014 and 2017 papers add datasets (credit approval, Iris, liver, heart, Wine, thyroid, ionosphere, glass) but mostly use "50% train, 100% test", which tests on data that includes the training half, so their accuracies are optimistic. Some rows are impossible (the 2014 Table VI lists MFHLSNN on ionosphere with min 97.43 > max 96.86, and on Wine an average equal to the minimum although the maximum is higher). For Iris with 75 training patterns at θ = 0.8, FHLSNN makes 3-4 segments in the 2003 paper but 39 in the 2014 paper, and the credit result (282 segments, 90.14%) is identical in the 2014 "MFHLSNN" table and the 2017 "EFHLSNN" text although the two papers define different membership functions. Published numbers therefore cannot serve as exact targets. The 2017 paper's Table 8 (3-fold cross-validation against other classifiers) is the cleanest comparison, but its numbers could not be extracted reliably; read it from the PDF.
- **Sanity example from the 2001 paper (Fig. 4/5):** 12 two-dimensional patterns (x, y, class), presented in this order: (0,0,2), (.15,.05,1), (.2,.15,2), (.3,.15,1), (.5,.2,2), (.3,.25,2), (.15,.3,1), (.4,.3,1), (.4,.4,2), (.4,.5,1), (.6,.5,1), (.6,.6,2). The paper says FHLSNN creates 7 segments for them (FMN needs 12 hyperboxes). θ is not stated, so sweep θ and record which values give 7. Verify the coordinates against the page image. Also log how the segment count on this example and on Iris changes as the collinearity tolerance is loosened. With exact collinearity most segments come from pairing two points (roughly n/2 segments), which matches the 2014 and 2017 papers (Iris: 150 patterns → 74 segments; credit: 345 → 282) but not the 3-4 segments in the 2003 paper. This also suggests that M1 (fewer training patterns) should reduce segment count roughly in proportion; treat that as a hypothesis to test.
- **Iris θ-curve (2014 paper, Table III, FHLSNN, all 150 patterns, random order; γ is presumably 1, as the 2017 paper states for its experiments):** segments at θ = 0 / 0.1 / 0.2 / 0.3 / 0.4 and above were 147 / 98 / 79 / 76 / 74. The 147 at θ = 0 should equal the number of distinct rows in the Iris copy used (the UCI file has exact duplicate rows; scikit-learn's copy corrects two rows of the UCI file, so its distinct count may differ slightly; report the count you get). Run many seeded shuffles and report mean ± std segment count at each θ next to these numbers. A clear mismatch means the learning routine differs from the papers and must be investigated before any benchmark sweep. Do not tune parameters to force a match.
- **Training-accuracy check:** the 2014 and 2017 papers report 100% training accuracy for FHLSNN on Iris at every θ. Reproduce this (assuming no identical patterns carry different labels). A model that drops or mislearns training patterns will fail it.
- **Hand-computed membership vectors (γ = 1; recompute by hand before trusting them):** (a) `fhlsnn2001`, V=(0,0), W=(0.2,0), R=(0.3,0): 0.6 as printed, 0.8 with (x − l)·γ. (b) `efhlsnn2017_segment`, same V and W: R=(0.3,0) → 0.9; R=(−0.1,0) → 0.9; R=(0.1,0.05) → 0.95; R=(0.1,0) → 1.0. (c) `mfhlsnn2014_midpoint`, V=(0.2,0.2), W=(0.4,0.2), R=(0.3,0.3): 0.9 with the true midpoint (0.3,0.2); about 0.7172 with the midpoint as printed, |(w − v)/2| = (0.1,0). (d) `mfhlsnn2003_height`, V=(0,0), W=(0.1,0), R=(0.9,0.01): 0.99 as printed.
- **Step-4 scenario test:** after a class-0 segment (0,0)-(0.5,0), learning a class-1 point exactly on it, (0.25,0), must keep the pattern (2 segments in total: the unchanged class-0 segment plus the new class-1 point) under the default `step4_intersection="skip"` and drop it (1 segment) under `"drop_new"`. Step 1 of learning considers only same-class segments, so a class-1 pattern lying on a class-0 segment is **not** covered and must create its own segment. A separate test: class-1 patterns (0.25,−0.5) then (0.25,0.5) must end with two class-1 point segments at exactly those coordinates and the class-0 segment unchanged (extension undone).
- **Tolerance wiring test:** a synthetic test with three nearly collinear points must extend the segment under a loose `collinearity_tol` and must not under a tight one. Design the offsets for the criterion actually implemented. With the paper's sum-of-distances criterion the deviation grows with the square of the sideways offset h: for V=(0,0), W=(0.1,0), R=(0.2,h) it is about 2.5·h², so h = 1e-3 gives about 2.5e-6, which is collinear under tol 1e-5 (one segment) and not under tol 1e-9 (two segments). With a perpendicular-distance criterion use h = 1e-6 instead. Use the patterns in the order (0,0), (0.1,0), (0.2,h), same class, zeta ≥ 0.25 and no shuffling, so that neither the length bound nor the ordering decides the outcome. A sweep in which the segment count never changes does not prove the tolerance works; it may not be wired in.

### 4.2 Reduction methods

Common interface:
```python
@dataclass
class ReductionResult:
    kept_idx: np.ndarray        # indices into the original training set
    removed_idx: np.ndarray
    facts: dict                 # per-item reason data, used by the explainability agent

# instance-level reducers: reduce(X, y, **params) -> ReductionResult
# segment-level reducers:  prune(model, X_val, y_val, **params) -> (new_model, facts)
```

**M1: Boundary-Proximity Pre-Filtering (instance-level, before training)**
- For each sample compute the distance to its nearest other-class sample (k-NN pass; use a KD-tree / `sklearn.neighbors` for speed). Samples far from any other class are "interior"; remove the most interior fraction.
- Parameters: `keep_fraction` or a distance quantile threshold, plus `interior_keep_rate` (keep a small random share of interior points so multi-modal classes are not left uncovered).
- Optional flag `edit_first` (run ENN-style noise removal before filtering). Reason: boundary-based selection tends to *keep* mislabeled/noisy points because they sit near other classes.
- `facts` per removed sample: nearest-other-class distance, its percentile within the class, number of same-class neighbors within that radius.
- **Hypothesis to test, not assume:** segments built from boundary points still cover class interiors well enough. It may fail for multi-modal classes; report it if so.

**M3: Membership-Contribution Pruning (segment-level, after training)**
- Run the trained model over the **validation set**; count, for each segment, how often it is the winning segment for a *correctly classified* sample. Prune segments whose count is below a threshold (a parameter swept in experiments). Re-evaluate.
- The validation set is carved from the training fold (stratified, 20%). It is **never** the test fold. Pruning on test data would be leakage.
- `facts` per pruned segment: class, win count, endpoints, length.

**Hybrid:** M1 → train → M3. Same code, chained.

### 4.3 Classical baselines
Use libraries; do not reimplement. `imbalanced-learn` (`CondensedNearestNeighbour`, `EditedNearestNeighbours`; verify the API of the installed version), `sklearn.cluster.KMeans` per class (centroids as prototypes, sweep k), stratified random subsampling (sweep ratio).

**Fair comparison design (this matters):** every instance-selection method (M1 and all baselines) produces a reduced training set, and **the same FHLSNN classifier is then trained on it**. This isolates the quality of the selection. For the kNN-native baselines also report 1-NN accuracy on the reduced set as reference only. CNN and ENN are parameter-free (a single point, not a curve); M1, k-means and random are swept. Compare on accuracy-vs-reduction **curves**, not by forcing exact matched ratios, which CNN/ENN cannot hit.

**Mandatory extra baseline: the θ-sweep.** In FHLSNN/MFHLSNN, raising θ (maximum segment length) already reduces the segment count, usually at an accuracy cost (the papers show 45 → 4 segments on Iris when θ goes from 0.05 to 0.8). A reduction method is only interesting if it beats this free knob. So the unreduced FHLSNN/MFHLSNN is also run at a sweep of θ values (γ fixed), and its accuracy-vs-segment-count curve is plotted on the same axes as M1, M3 and the Hybrid (which are run at the *frozen* θ from Section 4.5 and at other θ values as a secondary comparison). Without this baseline the claim "our method reduces segments" cannot be falsified.

### 4.4 Metrics (define precisely, compute identically everywhere)
- `n_train`: size of original training fold.
- `stored_vectors`: for instance-selection + kNN = kept samples; for FHLSNN = number of **distinct endpoint vectors** (a point-segment with V = W counts once; a two-endpoint segment counts twice).
- `reduction_vs_raw = 1 − stored_vectors / n_train` (comparable across *all* methods; the headline metric). **It can be negative**: at small θ the papers report 45 segments for 75 Iris patterns, which can mean more stored vectors than training patterns. Report negative values as they are; do not clip them to 0.
- `segment_reduction = 1 − n_segments / n_segments_unreduced_fhlsnn` (FHLSNN-specific; the project's unique metric).
  **Caution:** raising θ alone roughly halves the segment count (segments ≈ n/2 at large θ on Iris, Wine and Breast Cancer in Sweep 1) while `stored_vectors` stays at about n, because every training pattern remains an endpoint. Never report `segment_reduction` without `stored_vectors` next to it, and never present a θ-only segment reduction as compression.
- `accuracy` and `macro_f1` on the held-out test fold. `accuracy_drop_pp = acc_unreduced − acc_reduced`.
- `train_time_s` and `recall_ms_per_pattern` (wall-clock, same machine, median of repeats).

### 4.5 Evaluation protocol
- Small/medium datasets: stratified 5-fold CV × 3 seeds. Large dataset: stratified 3-fold × 2 seeds (runtime). Report mean ± std.
- FHLSNN hyperparameters (θ **and γ**, because γ = 1 can drive almost every unseen pattern to membership 0 in higher dimensions) are tuned **once per outer fold**, on that fold's validation split only (never the test fold and never data from other folds), for the unreduced model by a small grid, then **frozen** for all reduction methods in that fold, so differences come from the reduction, not from re-tuning.
- **Tie-break in tuning:** when several (θ, γ) pairs reach the same validation accuracy, take the one with fewer segments (larger θ). Log any change to this rule in `DECISIONS.md`; on tiny validation sets ties are common and the rule changes the baseline by tens of segments.
- **Seeding and reproducibility:** every stochastic component (pattern shuffle, CNN, k-means, random subsampling, M1 interior sampling) takes an explicit seed derived from (run seed, fold, method). Running the sweep twice on the same config must give identical `runs.csv` files; keep this as a regression test.
- **Result folders are write-once:** each run writes to a fresh `results/run_<date>_<tag>/` folder containing all datasets of that run. Never write a dataset into an older run folder, because a folder mixing files from different code versions cannot be traced to one version.
- **Common fit set (all methods):** the validation split (20% of the training fold, stratified) is carved out first for *every* method, including the unreduced reference and the classical baselines. All methods then train on the same remaining 80% (the "fit set"), and `n_train` in every reduction ratio means the size of the fit set. Otherwise methods that need a validation set (M3, the Hybrid, θ tuning) would train on less data than the others and the comparison would be confounded. Min-max scaling is fit on the fit set only.
- Outputs: a table per dataset and an accuracy-vs-reduction plot (all methods on one axes) per dataset.
- **Success is a hypothesis, not a promise.** Target to test: on at least one dataset, a proposed method achieves ≥ 50% `segment_reduction` or `reduction_vs_raw` with ≤ 2 pp accuracy loss. If it does not, the finding is still valid and is reported honestly.
- Large dataset must be able to show the "too many segments" problem the project claims (record `n_segments` vs `n_train` for the unreduced model). If it does not appear, say so.

---

## 5. Platform specification (P1)

### 5.1 Architecture and repo layout
```
/web          React (Vite) frontend
/api          Node.js + Express: auth verification, CRUD, proxy to ML service
/ml_service   Python FastAPI + RQ worker: FHLSNN, reducers, baselines, harness, profiler, agents
/db           Supabase SQL migrations
/docs         PRD, PLAN, DECISIONS, STATUS, papers
/tests        literature_targets.yaml, integration tests
```
**Why the agents live in `/ml_service` (Python):** the profiler (scikit-learn), the tools (the harness) and the LLM SDK are all Python, so the agent calls its tools in-process instead of through extra network hops. Express only proxies.

Flow: React → Express (verifies Supabase JWT) → FastAPI `POST /jobs` → FastAPI enqueues an RQ job in Redis → worker runs the experiment, writes progress and results to Postgres → React polls Express for status.
Reason Express does not enqueue directly: RQ is a Python library, so enqueueing from Python avoids a cross-language queue format.

### 5.2 Database (Supabase Postgres)
- `datasets(id, owner, name, storage_path, target_column, n_rows, n_features, n_classes, profile jsonb, profile_vec vector(8), created_at)`
- `experiments(id, owner, dataset_id, method, params jsonb, seed, fold, status, progress, metrics jsonb, facts jsonb, source text check in ('benchmark','user','agent'), parent_id, created_at)`
- `reports(id, experiment_id, explanation text, facts_snapshot jsonb, created_at)`
- `agent_runs(id, owner, dataset_id, goal jsonb, transcript jsonb, final_experiment_id, created_at)` (P2)
- RLS: users read/write only their own rows. Benchmark-seed experiments (`source='benchmark'`, owned by a system user) are readable by all authenticated users (needed for retrieval).
- Uploads: CSV only, size and row limits enforced, target column chosen by the user, parsed with pandas, never executed.

### 5.3 ML service API (contract; implement exactly)
- `POST /profile {dataset_id}` → profile JSON + `profile_vec`
- `POST /jobs {dataset_id, method, params, seed}` → `{job_id}`
- `GET /jobs/{job_id}` → `{status, progress, experiment_id?}`
- `POST /recommend {dataset_id}` → `{method, params, rationale, evidence_experiment_ids}`
- `POST /explain {experiment_id}` → `{explanation}`
- `POST /agent/run {dataset_id, goal}` → `{agent_run_id}` (P2)

### 5.4 Frontend pages
1. Login. 2. Datasets: upload, target-column pick, profile card. 3. New experiment: method + parameters, "Recommend" button. 4. Experiment detail: progress bar, metrics, **2-D PCA scatter of original vs reduced data** (removed points faded), segment overlay, explanation text. 5. Benchmark: accuracy-vs-reduction curves from stored benchmark experiments.
Notes: compute PCA server-side and return 2-D coordinates. Because PCA is a linear projection, a hyperline segment projects to a straight segment between its projected endpoints, so overlays are valid. State in the UI that the plot is a 2-D projection of higher-dimensional data.

**Acceptance (Gate B/C):** a new user can sign up, upload a CSV, see its profile, launch a job, watch progress, and see metrics + plots + explanation, end to end, with every displayed number traceable to a DB row.

---

## 6. AI layer specification

General rules for every LLM use: provider-agnostic wrapper (`llm_client.py`, model name and key from environment variables, never hardcoded or committed); temperature 0; structured JSON output validated against a schema; deterministic fallback when the call fails; **the LLM never produces numbers**, it only selects from options and writes prose around numbers supplied by code.

### 6.1 Dataset profiler (P1)
Deterministic. Output: column types, `n`, `d`, `n_classes`, class imbalance ratio, fraction of samples with a different-class neighbor among their k nearest (class-overlap indicator), PCA components needed for 95% variance divided by `d` (redundancy proxy). `profile_vec` = normalized 8-vector of these. Optional: small sklearn model predicting the best method from `profile_vec`, trained on benchmark history.

### 6.2 Recommendation agent (P1)
1. Retrieve the top-k nearest past experiments by `profile_vec` (pgvector), ranked by (reduction achieved, accuracy drop).
2. Pass method/params/outcome summaries to one LLM call; get `{method, params, rationale}`; validate; clamp params to legal ranges.
3. Fallback: a fixed sensible default (e.g. Hybrid with moderate threshold).
- **Cold start:** the knowledge base is only the benchmark sweep (a handful of datasets). So `make benchmark` must seed the DB before the agent can be meaningful.
- **Evaluation (leave-one-dataset-out):** when evaluating on dataset D, exclude D's experiments from retrieval. Compare recommended config vs the fixed default. State plainly in the report that the knowledge base is small and results are indicative only.

### 6.3 Explainability agent (P1)
Input: structured `facts` (counts, distances, win counts, class-wise removal rates, extracted rules). The LLM writes prose; **all numbers are inserted by code from `facts`** (templated placeholders), and a validator rejects any output containing a number not present in `facts`. Include a per-class removal summary and flag any class that lost a disproportionate share of its samples.
**Evaluation:** manually check ≥ 20 explanations against `facts` and report the accuracy.
**Rule extraction (method from the EFHLSNN paper):** the paper does not read rules directly off segments. It quantizes each endpoint coordinate into Q linguistic levels, decodes the discrete attributes, feeds the resulting table to the PART rule learner (Weka), and prunes. PART is not in scikit-learn: either call Weka through a Java bridge or substitute a Python rule/tree learner and log the deviation. The paper reports a compact pruned rule set for credit approval with 11.07% error, but no measure of how faithfully the rules reproduce the network. This project must measure rule fidelity (agreement between the rule set's predictions and the FHLSNN's own predictions) and report it.

### 6.4 Reduction Agent (P2, only after P1 gate)
- **Goal input:** e.g. "maximize `reduction_vs_raw` subject to `accuracy_drop_pp ≤ ε`".
- **Tools:** `profile_dataset`, `query_past_experiments`, `run_reduction(method, params)`, `evaluate`, `compare_baseline(ratio)`. Tool results are real runs from the harness.
- **Loop:** profile → retrieve → propose config → run → read result → adjust → stop when the goal is met or the budget of ≤ 10 `run_reduction` calls is spent. Constraints are checked on the **validation** split; the chosen config is evaluated on the test fold **once** at the end.
- **Guardrails:** parameter ranges validated by code; full transcript stored in `agent_runs`; final report numbers inserted by code and cite experiment ids.
- **Research question:** does the agent reach a feasible, high-reduction config in fewer runs than random search and Optuna (TPE) given the *same* run budget? Metrics: best reduction found, runs to first feasible config; ≥ 5 repeats per dataset; leave-one-dataset-out memory. Report results even if the agent only ties or loses; the fair comparison and the transcripts are the contribution.

---

## 7. Four-week plan with gates

| Week | P0 research core | P1 platform / AI | Gate at end of week |
|---|---|---|---|
| 1 | FHLSNN, then MFHLSNN, unit tests, run on Iris/Wine/BC. Baselines + harness skeleton. | Repo scaffold, Supabase schema + auth, CSV upload, FastAPI stub, RQ "hello-world" job. Profiler. | **Gate A:** FHLSNN tests pass and baseline accuracies are compared to the papers; a dummy job runs through the queue. |
| 2 | M1, M3, Hybrid. Full sweep on small + medium datasets, stored in DB, plots. | Real job flow: upload → queue → run → result row → UI polling. Agent scaffolding against stubbed tools. | **Gate B (P0 complete):** reduction results on ≥ 3 datasets with baselines. |
| 3 | Large-dataset sweep, final tables/figures. (M4 if time.) | Results page (PCA, segment overlay, curves), recommender, explainability agent, agent-tool integration. | **Gate C (P1 complete):** end-to-end demo works. |
| 4 | Freeze new features by day 25. Re-run any figure that changed. | Reduction Agent evaluation (only if A–C passed). Bug fixes, README, demo script, backup screen recording. | **Gate D:** reproducible `make benchmark`, rehearsed demo, `DECISIONS.md` and `STATUS.md` complete. |

**Fallbacks (decide early, do not drift):**
- If FHLSNN does not reach Gate A by day 7: simplify the training procedure exactly where the papers are ambiguous, log it, and continue; never leave the baseline classifier broken while building the platform.
- If Gate B slips: Member 4 (AI layer) helps with the core; P2 is dropped.
- If the large dataset is too slow: subsample it, log the subsampling and runtime, and say so in the report.
- If the LLM API is unavailable or costly: deterministic fallbacks keep the platform working; the demo must never depend on a live LLM call without a fallback.

---

## 8. Team ownership (so every student can defend their part)
- **Member 1:** FHLSNN/MFHLSNN, M1, M3, Hybrid (`/ml_service/fhlsnn`, `/reducers`).
- **Member 2:** baselines, harness, benchmark sweeps, plots, metrics (`/ml_service/benchmark`).
- **Member 3:** `/web`, `/api`, `/db`, Redis job flow.
- **Member 4:** profiler, recommender, explainability, Reduction Agent (`/ml_service/agents`).
Each member must be able to explain every function in their area without the AI's help.

---

## 9. Risks
| Risk | Mitigation |
|---|---|
| FHLSNN implemented subtly wrong (AI-written code often looks right and is not) | Hand-computed unit tests; compare to papers; the human reads the core algorithm line by line. |
| Boundary pre-filtering hurts accuracy (noisy points kept, multi-modal classes uncovered) | `interior_keep_rate`, `edit_first`; report honestly. |
| Data leakage (normalizing or pruning with test data) | Fit on train fold only; separate validation split; tests that assert no test indices appear in any fit call. |
| Order-dependent training produces noisy results | Multiple seeds, mean ± std. |
| Small RAG knowledge base | Leave-one-dataset-out evaluation; state the limitation. |
| LLM nondeterminism and cost | Temperature 0, schema validation, fallbacks, store transcripts, hard run budgets. |
| Scope creep | Tiers and gates in Section 2 and 7. |

---

## 10. Open questions the human must settle (agent: ask at kickoff if still open)
1. Guide approval for D2 (no MongoDB), D4/D5 (polling), D6 (profiler is not an SLM).
2. Paper PDFs are in `/docs/papers` (FHLSNN 2001 and MFHLSNN 2003, both received). Fill `tests/literature_targets.yaml` for Iris only (see Section 4.1). The UFHLSNN/CUDA (2016), Shinde and Kulkarni (2014) and EFHLSNN (2017) papers must also be placed in `/docs/papers`; the explainability module (6.3) follows the EFHLSNN rule-extraction method. Ask the guide which of the printed-formula issues in Section 4.1 (items 1-3, 6) should be implemented as printed and which treated as typos, and which "MFHLSNN" the project means: the 2003 triangle-height version (assumed here), the 2014 midpoint version (which matches the proposal's wording), or the MFHLSNN1/MFHLSNN2 centroid-based variants cited in the proposal (not yet identified).
3. LLM provider, API key, spend limit.
4. Deployment target: local demo only, or hosted (Vercel + Render/Railway)?
5. Which large dataset: Pendigits (default) or Letter Recognition.

---

## 11. Definition of done
- `make setup && make test` passes on a clean machine.
- `make benchmark` regenerates every table and figure used in the report from the database.
- The demo works end to end with a recorded backup.
- `DECISIONS.md` lists every deviation with its reason; `STATUS.md` is current.
- No hardcoded results anywhere; every UI number traces to an experiment row.
