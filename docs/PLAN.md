# Plan: FHLSNN-Based Data Reduction Platform
Based on PRD: FHLSNN-Based Data Reduction Platform (1-month build).

## Week 1: P0 Research Core
### Goal: FHLSNN, MFHLSNN, Unit Tests, Baselines, Harness Skeleton
* Files to create:
  * `ml-service/fhlsnn/fhlsnn.py`: FHLSNN algorithm implementation.
  * `ml-service/fhlsnn/mfhlsnn.py`: MFHLSNN algorithm implementation.
  * `tests/test_fhlsnn.py`: Unit tests for FHLSNN algorithms with hand-computed 2-D examples.
  * `tests/literature_targets.yaml`: Target accuracy numbers from papers.
  * `ml-service/benchmark/baselines.py`: Baselines using imbalanced-learn and scikit-learn.
  * `ml-service/benchmark/harness.py`: Benchmark harness skeleton for running experiments and tracking metrics.
* Order of work:
  1. Set up python environment and dependencies (`requirements.txt`, `Makefile`).
  2. Implement FHLSNN, verify with unit tests (Gate A).
  3. Implement MFHLSNN, verify with unit tests.
  4. Write the classical baseline implementations.
  5. Develop the benchmarking harness and run on Iris/Wine/Breast Cancer.
* Verification: `make test` passes. `make benchmark` outputs results comparable to the literature targets.

## Week 2: P0 Reduction Core
### Goal: M1, M3, Hybrid, Full Sweep on small+medium datasets
* Files to create:
  * `ml-service/reducers/m1_prefilter.py`: Boundary-Proximity Pre-Filtering.
  * `ml-service/reducers/m3_prune.py`: Membership-Contribution Pruning.
  * `ml-service/reducers/hybrid.py`: Hybrid method (M1 -> train -> M3).
  * `ml-service/benchmark/runner.py`: Logic to run the full sweep on datasets.
* Order of work:
  1. Implement M1 and write tests.
  2. Implement M3 and write tests.
  3. Implement Hybrid and write tests.
  4. Integrate reducers into benchmark harness.
  5. Run full sweep on small (Iris, Wine, BC) and medium (Digits) datasets.
* Verification: Gate B (Reduction results on >= 3 datasets with baselines). Data is plotted and logged.

## Week 3: P1 Platform / AI
### Goal: Results page, Recommender, Explainability agent, Agent-tool integration
* Files to create:
  * `db/schema.sql`: Supabase schema and RLS.
  * `api/server.js`: Express server for proxying.
  * `ml-service/main.py`: FastAPI ML service endpoints.
  * `ml-service/worker.py`: RQ worker setup.
  * `web/`: React frontend scaffolding.
  * `ml-service/agents/profiler.py`: Dataset profiler.
  * `ml-service/agents/recommender.py`: Recommendation agent.
  * `ml-service/agents/explainability.py`: Explainability agent.
* Order of work:
  1. Setup Supabase database.
  2. Create FastAPI ML service endpoints.
  3. Create RQ worker for background jobs.
  4. Implement AI agents (Profiler, Recommender, Explainability).
  5. Setup frontend.
* Verification: Gate C (End-to-end demo works). Upload CSV -> profile -> recommend -> run -> explain.

## Week 4: P2 Reduction Agent / Finalization
### Goal: Reduction Agent, README, Demo script
* Files to create:
  * `ml-service/agents/reduction_agent.py`: Reduction agent.
  * `README.md`: Final documentation.
* Order of work:
  1. Implement Reduction Agent and evaluate.
  2. Clean up code, finalize README and docs.
  3. Prepare final report metrics and figures.
* Verification: Gate D (reproducible `make benchmark`, rehearsed demo).
