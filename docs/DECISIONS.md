# Decision Log

(See PRD for initial deviations D1-D8).

| # | Decision | Reason | Alternatives Rejected |
|---|---|---|---|
| D9 | Use FastAPI for ML service and Express for proxy | PRD specification. ML tools (scikit-learn, pgvector, LLM SDK) are Python-native. Express handles auth securely before hitting ML backend. | A monolithic Node.js backend (rejected due to ML ecosystem mismatch) or monolithic Python backend (rejected due to PRD specifying Node/Express proxy). |
| D10 | Implement FHLSNN and MFHLSNN with issue flags | The papers contained ambiguities and possible typos (e.g., `x * gamma` instead of `(x - l) * gamma`). These are kept as printed behind boolean flags like `issue_1_f_uses_x_gamma`, so they can be toggled. | Fixing the typos without permission, which violates the PRD rule not to invent/guess. |
| D11 | Collinearity tolerance introduced | Exact collinearity checks as printed lead to floating point issues. Introduced `collinearity_tol=1e-5`. | No tolerance, which causes numerical instability. |
| D12 | Issue 6: Intersection Restore Logic | The paper's Eq 15 text suggests restoring endpoints of previous segment of other class if step 4 creates intersection. It is implemented by discarding the newly created point segment to avoid intersection. | Implementing Eq 15 literally, which would corrupt the other class's segment without geometric sense. |
| D13 | Rename `ml-service` to `ml_service` | Python module names cannot contain hyphens. The folder was renamed to `ml_service` to allow standard importing. | Keeping the hyphen and hacking `sys.path` or `importlib`, which is fragile. |
| D14 | Unified FHLSNN Class with Pluggable Membership | Rather than keeping FHLSNN and MFHLSNN as separate classes, a single `FHLSNN` class with a `membership_type` parameter handles all 4 variants. | Separate inheritance classes for each paper, which duplicates learning logic unnecessarily. |
| D15 | Tie-break / all-zero fallback uses projection distance to segment | When all memberships are zero or tied, we compute the exact geometric (projection-based) distance from R to each segment (clipping t to [0,1]). This matches the EFHLSNN 2017 segment-projection geometry. | Midpoint-based fallback (rejected: a long segment's midpoint can be far from a nearby point on the segment). |
| D16 | Collinearity test uses cross-product height | Replaced the perimeter formula `(l1+l2+l) - 2*max(l1,l2,l)` with the cross-product formula `height = ||(W-V) x (R-V)|| / l`, which is numerically stable for nearly-collinear points. | Perimeter formula (rejected: catastrophic floating-point cancellation for small offsets). |
