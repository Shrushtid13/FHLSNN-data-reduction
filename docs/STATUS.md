# Status

* **In Progress**: 
  * Running full evaluation sweeps (Gate B).
* **Done**: 
  * Project setup, Makefile, requirements.
  * Dataset loaders, metrics, classical baselines, benchmark harness.
  * FHLSNN and MFHLSNN core implementation behind issue flags.
  * Pluggable membership functions (fhlsnn2001, mfhlsnn2003_height, mfhlsnn2014_midpoint, efhlsnn2017_segment).
  * Implementation of Reducers: M1 (Pre-filtering), M3 (Pruning), Hybrid.
  * Scripts for theta-sweep baseline and 12-pattern sanity checks.
* **Blocked / Pending Human Actions**: 
  * Waiting for human to provide the UFHLSNN/CUDA, Shinde and Kulkarni 2014, and EFHLSNN papers in `docs/papers/`.
  * Waiting for human to clarify guide approval on D2, D4/D5, D6 architecture decisions.
  * Waiting for human to provide LLM provider, API key, and spend limit.
  * Waiting for human to clarify deployment target (local vs hosted).
  * Waiting for human to decide large dataset (Pendigits vs Letter Recognition).
