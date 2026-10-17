# Platform Status & Deliverables

## 1. Summary of Status

### DONE:
- **Phase 0: Environment Planning & Documentation**
  - Node, npm, and Python toolchain verified (`node v22.18.0`, `npm 10.9.3`, `Python 3.11.9`).
  - `.env.example` created with placeholder credentials for Supabase, Redis, internal tokens, and service ports.
  - `docs/PLATFORM_SETUP.md` created with clear, step-by-step instructions for Supabase bucket creation, SQL migration execution, test user creation, and service launch commands.
  - `docs/PLATFORM_DECISIONS.md` logged, documenting queue architecture and security choices.

- **Phase 1: Database & Row Level Security (RLS)**
  - `db/migrations/001_init.sql` created containing:
    - `pgvector` extension activation.
    - `datasets`, `experiments`, and `reports` tables with exact types, constraints, and cascade relationships.
    - Constraint: `(source = 'benchmark' and owner is null) or (source <> 'benchmark' and owner is not null)`.
    - RLS enabled on all three tables with strict ownership policies.
    - Private storage bucket `datasets` policy restricting access to `{user_id}/*`.
  - `db/tests/rls_test.sql` created and verified against PostgreSQL:
    - User A cannot select User B's dataset.
    - User A can select benchmark experiments.
    - User A cannot update experiment progress/status (reserved for service role).

- **Phase 2: Express 4 Gateway API (`/api`)**
  - Express app configured with CORS restricted to `WEB_ORIGIN`.
  - Bearer token authentication middleware verifying tokens against Supabase Auth (`getUser(token)`).
  - Scoped database client builder passing user JWT so Postgres RLS is automatically enforced.
  - `POST /datasets` with strict validation in required order (extension -> size -> parse -> rows -> features -> target column -> numeric features -> no missing -> 2+ classes), storage upload, and db record creation.
  - `GET /datasets` and `GET /datasets/:id` enforcing RLS isolation.
  - `POST /experiments` with Zod validation, queuing, and internal FastAPI trigger (`X-Internal-Token`).
  - `GET /experiments` and `GET /experiments/:id` (returning own rows + benchmark rows).
  - 501 `not_implemented` handlers for `/profile`, `/recommend`, `/explain`, and `/agent/run`.
  - Comprehensive Vitest test suite (`api/test/api.test.js`) with 12 passing tests.

- **Phase 3: Internal FastAPI Service & Background Worker (`ml_service/service/`)**
  - `api.py`: FastAPI application with `POST /jobs` requiring `X-Internal-Token`, pushing to Redis `fhlsnn:jobs` via `LPUSH`, `GET /jobs/{id}` reading status/progress from Postgres, and 501 stubs.
  - `worker.py`: Native Windows-compatible worker running a `BRPOP` loop with 5-second timeout, executing dummy experiment simulation (10 steps updating progress 10..100) and setting status to `done` with metrics `{"dummy": true}` (or `failed` with error on exception).
  - `README.md`: PowerShell instructions for launching Uvicorn and Worker.
  - `test_service.py`: Pytest suite (6 passed) testing token validation, 501 responses, and worker state transitions.
  - `e2e_run.py`: End-to-end integration script executing upload, queueing, worker execution, and polling until `done`.

- **Phase 4: React UI (`/web`)**
  - Vite + React application with plain CSS styling (no heavy UI frameworks).
  - `Login.jsx`: Email + password authentication with Supabase Auth.
  - `Datasets.jsx`: Dataset list, metadata display (`n_rows`, `n_features`, `n_classes`), and CSV file uploader with dynamic header picker.
  - `NewExperiment.jsx`: Dataset selector, method picker (`unreduced`, `m1`, `m3`, `hybrid`), JSON params editor with defaults, and seed selector.
  - `ExperimentDetail.jsx`: Real-time status display, progress bar, formatted metrics JSON, and 2-second interval polling that halts on `done` or `failed`.
  - Strict compliance with data integrity: every number displayed originates from a database row; null values render `"not available"`.
  - 3 Vitest component tests (`web/src/__tests__/ExperimentDetail.test.jsx`) passing.

- **Phase 5: Security Hardening & Zero-Leakage Architecture (Audit Remediation)**
  - **Secret Isolation**: Hardened `web/vite.config.js` to strictly use `envPrefix: ['VITE_']` and explicit `define` injections (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`), eliminating exposure of `SUPABASE_SERVICE_ROLE_KEY` to browser bundles.
  - **Service & Job Auth Isolation**: Hardened `GET /jobs/{id}` in `ml_service/service/api.py` to require `X-Internal-Token`, enforcing strict inter-service boundary and preventing unauthenticated job observation or RLS bypass.
  - **Asynchronous Safe CSV Processing**: Replaced synchronous in-memory parsing with non-blocking streaming parsing (`csv-parse`), sanitizing formula injection prefixes (`=`, `+`, `-`, `@`) and enforcing size limits to prevent Event Loop starvation.
  - **Protected AI/ML Stubs**: Wrapped all stubs (`/profile`, `/recommend`, `/explain`, `/agent/run`) with Supabase Bearer token authentication in Express, returning 501 `not_implemented` only to authenticated callers.
  - **Timing-Safe Token Verification**: Implemented constant-time string comparison (`secrets.compare_digest`) in FastAPI and strict fallback prevention in Express and ML configs.
  - **Network & Request Security**: Added `express-rate-limit` (60 requests/min/IP), disabled `X-Powered-By`, and configured comprehensive security headers (CSP, HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Cache-Control: no-store).
  - **Sanitized Error Responses**: Replaced raw database exceptions and Python stack traces with standardized generic error responses across Express and FastAPI, preventing schema, SQL, or connection string leakage.

---

### NOT DONE (Out of Scope / Future Gates):
- Real FHLSNN / MFHLSNN training integration in `worker.py` (reserved for Gate B/C; dummy job runner is isolated and pluggable).
- Profiling algorithms, pgvector nearest-neighbor search, and LLM recommendation / explainability agents (reserved for Member 4 / Week 2-3; stubbed as 501).
- 2-D PCA projection plot rendering on frontend (planned for Gate C).

---

## 2. Platform Decisions Logged
1. **Queue Implementation on Windows (PD1):** Avoided RQ and Celery due to POSIX `os.fork()` incompatibility on Windows. Used direct Redis `LPUSH` in FastAPI and `BRPOP` in the worker process.
2. **Dual-Client Supabase Architecture (PD2):** Express uses the user's Bearer token with the Supabase anon key to query Postgres under RLS, while the service-role client is strictly confined to server-side storage uploads and internal worker updates.
3. **HTTP Polling (PD3):** Frontend polls Express `GET /experiments/:id` every 2 seconds with automatic cleanup upon terminal status or unmount.

---

## 3. Exhaustive List of Created Files

### Root & Configuration:
- `.env.example`
- `docs/PLATFORM_DECISIONS.md`
- `docs/PLATFORM_SETUP.md`
- `docs/PLATFORM_STATUS.md`

### Database (`/db`):
- `db/migrations/001_init.sql`
- `db/tests/rls_test.sql`

### Express Gateway API (`/api`):
- `api/package.json`
- `api/package-lock.json`
- `api/src/config.js`
- `api/src/supabase.js`
- `api/src/app.js`
- `api/src/server.js`
- `api/src/middleware/auth.js`
- `api/src/routes/datasets.js`
- `api/src/routes/experiments.js`
- `api/src/routes/stubs.js`
- `api/test/api.test.js`

### ML Service & Worker (`/ml_service/service/`):
- `ml_service/service/requirements.txt`
- `ml_service/service/config.py`
- `ml_service/service/api.py`
- `ml_service/service/worker.py`
- `ml_service/service/test_service.py`
- `ml_service/service/e2e_run.py`
- `ml_service/service/README.md`

### React Web Frontend (`/web`):
- `web/package.json`
- `web/package-lock.json`
- `web/vite.config.js`
- `web/index.html`
- `web/src/setupTests.js`
- `web/src/config.js`
- `web/src/supabase.js`
- `web/src/api.js`
- `web/src/index.css`
- `web/src/main.jsx`
- `web/src/App.jsx`
- `web/src/pages/Home.jsx`
- `web/src/pages/Login.jsx`
- `web/src/pages/Datasets.jsx`
- `web/src/pages/NewExperiment.jsx`
- `web/src/pages/ExperimentDetail.jsx`
- `web/src/__tests__/Home.test.jsx`
- `web/src/__tests__/ExperimentDetail.test.jsx`
