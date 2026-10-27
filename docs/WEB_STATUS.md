# Web Frontend Status (`/web`)

> Last updated: 2026-10-27

---

## Phase Summary

| Phase | Scope | Status |
|-------|-------|--------|
| 0 — Docs | `docs/UI_CONTRACT.md`, `web/src/fixtures/sampleExperiment.json` | ✅ Done |
| 1 — Shell | tokens.css, AppLayout, Sidebar, TopBar, Stepper, StatusPill, ProgressBar, MetricCard, EmptyState, ErrorBanner, 401 handling, Login restyle | ✅ Done |
| 2 — Datasets | Filter card (name, size, source), table with balance/status, upload dialog, Reduce button → `/experiments/new?dataset=<id>` | ✅ Done |
| 3 — Configure | Dataset select (preselected from query), AI recommendation card, method radio cards, conditional parameters, range validation, POST `/experiments`, navigate on success | ✅ Done |
| 4 — Experiment | 2 s polling, Processing view (stages, live log, disabled Cancel), Results view (6 MetricCards with deltas, inline SVG chart, PCA scatter, PerClassTable, ExplanationCard, CSV download, print export), Failed view | ✅ Done |
| 5 — Experiments list & polish | ExperimentsList page (short ID, dataset name, method, status pill, progress, created, click opens), responsive CSS (768 px, 480 px), keyboard focus-visible, labels on inputs, SAMPLE DATA absent from prod, WEB_STATUS.md | ✅ Done |

---

## Test Results

```
Test Files  7 passed (7)
     Tests  44 passed (44)
```

## Production Build

```
✓ 104 modules transformed.
dist/index.html                   0.69 kB
dist/assets/index-B3t3DBYe.css   19.65 kB
dist/assets/index-Zd8c3j0Y.js   460.94 kB
✓ built in 1.24s
```

- `grep "SAMPLE DATA" dist/` → **0 matches** ✅

---

## What's Done

### Components (`web/src/components/`)
- **AppLayout.jsx** — flex-wrap shell with `LayoutContext` (activeStep, breadcrumb).
- **Sidebar.jsx** — 220 px primary-blue sidebar with `NavLink` active pill.
- **TopBar.jsx** — breadcrumb + 4-step Stepper.
- **Stepper.jsx** — numbered step pills; `.on` class on the active step.
- **StatusPill.jsx** — `done`, `running`, `waiting`, `failed`, `queued` pills.
- **ProgressBar.jsx** — `role="progressbar"` with `aria-valuenow`.
- **MetricCard.jsx** — value + optional delta/subtext.
- **EmptyState.jsx** — illustration-less empty state with optional action button.
- **ErrorBanner.jsx** — dismissable red banner.
- **AccuracyReductionChart.jsx** — inline SVG polyline chart (no library), legend, axes with ticks from data, distinct line styles per series.
- **PcaScatter.jsx** — dual-panel SVG scatter (all points / after reduction with removed faded).
- **PerClassTable.jsx** — Class, Before, Kept, Share kept table.
- **ExplanationCard.jsx** — explanation text + seed/fit/val/test metadata line.

### Pages (`web/src/pages/`)
- **Login.jsx** — restyled with design tokens.
- **Datasets.jsx** — name search, size filter (`under_1000`, `over_10000`), source filter, class balance (`max/min` rule), conditional Source column, upload dialog, Reduce → navigate.
- **NewExperiment.jsx** — dataset select preselected via `?dataset=`, AI recommendation card (501 → "not available yet"), method radio cards, conditional params (keep_fraction, interior_keep_rate for m1/hybrid; min_wins for m3/hybrid), variant, seed, tune_hyperparams, range validation, POST `/experiments`, navigate to `/experiments/:id`.
- **ExperimentDetail.jsx** — 2 s `setInterval` polling (stops on done/failed, cleans up on unmount). Processing view: overall ProgressBar, 5 fixed stages (Done/Running/Waiting), live log (last 50 lines, monospace, `aria-live="polite"`), disabled Cancel with tooltip, disabled View Results. Results view: 6 MetricCards with deltas vs reference, AccuracyReductionChart, PcaScatter, PerClassTable, ExplanationCard with metadata footer, Download CSV, Export Report (`window.print()`). Failed view: error text + Back to Configure link.
- **ExperimentsList.jsx** — table with short ID, dataset name, method, status pill, progress, created date; client-side search + status filter; click navigates to `/experiments/:id`; empty state.
- **PlaceholderPage.jsx** — Benchmarks, AI Recommendations, Settings (with Sign Out button).
- **SampleResult.jsx** — DEV-only, guarded by `import.meta.env.DEV`, permanent red "SAMPLE DATA, NOT A REAL RUN" banner; full results layout from fixture.

### Styles
- **tokens.css** — CSS variables, layout utilities, sidebar, card, button, form, table, stepper, modal, keyboard focus-visible, responsive breakpoints (768 px, 480 px), print stylesheet.

### API / Auth
- **api.js** — 401 interceptor → `supabase.auth.signOut()` → redirect to `/login`.

### Tests (`web/src/__tests__/`)
- `Home.test.jsx` — 3 tests
- `Phase1Shell.test.jsx` — 9 tests (Stepper, StatusPill, ProgressBar)
- `Phase2Datasets.test.jsx` — 9 tests (balance rules, name/size/source filters, Source column, Reduce button)
- `Phase3Configure.test.jsx` — 6 tests (dataset preselect, recommendation card, conditional fields, range validation, submit payload)
- `Phase4ExperimentDetail.test.jsx` — 10 tests (polling stops on done/failed, processing stages/logs, missing data hiding, full results rendering, delta formatting, CSV content)
- `ExperimentDetail.test.jsx` — 3 tests (legacy compat: progress bar, polling, null metrics)
- `Phase5ExperimentsList.test.jsx` — 4 tests (table rendering, search filter, status filter, empty state)

---

## What's NOT Done (Planned / Deferred)

| Feature | Notes |
|---------|-------|
| Cancel button on processing view | Disabled with tooltip "Cancel is not available yet". Needs a backend `DELETE /experiments/:id` or status-update endpoint. |
| AI Recommendations page | Placeholder. Backend `POST /recommend` returns 501; UI shows "not available yet" gracefully. |
| Benchmarks page | Placeholder ("not available yet"). |
| Settings page | Only Sign Out implemented; no user settings. |
| Dataset deletion | Not in scope; no DELETE endpoint exists. |
| Real-time WebSocket updates | Uses 2 s polling via `setInterval`. Could migrate to WebSocket or SSE. |
| Dark mode | Not in scope. |
| i18n / localization | All text is English only. |
| E2E tests | Only unit/integration tests with Vitest + @testing-library. |

---

## Design Decisions

1. **No chart library** — `AccuracyReductionChart` and `PcaScatter` use inline `<svg>` per spec.
2. **Router-safe components** — `ExperimentDetail` detects `useInRouterContext()` so it works both inside `<BrowserRouter>` (production) and bare `<MemoryRouter>` (tests).
3. **CSS-only responsive** — sidebar stacks at 768 px; cards and buttons go full-width at 480 px.
4. **No fabricated data** — every displayed number comes from API response or renders `"not available"`.
5. **Print stylesheet** — hides sidebar, buttons, and stepper; white background; cards get borders.

---

## Manual Walkthrough Checklist

Use this checklist to verify the full flow manually in the browser:

- [ ] **Login** — Open `/login`. Enter credentials. Redirects to `/datasets` on success.
- [ ] **Datasets (empty)** — First load with no datasets shows EmptyState.
- [ ] **Upload dataset** — Click "Upload dataset". Select a CSV file. Pick a name and target column from the parsed headers. Submit. Dataset appears in the table.
- [ ] **Datasets table** — Verify columns: checkbox, Name, Rows, Features, Classes, Class balance, Status (Profiled / Not profiled). Verify balance tooltip shows the ratio.
- [ ] **Filters** — Type in name search, change size filter, change source filter if Source column appears. Rows filter client-side.
- [ ] **Reduce** — Click the "Reduce" button on a dataset row. Navigates to `/experiments/new?dataset=<id>`.
- [ ] **Configure** — Dataset is pre-selected. AI recommendation card shows "Recommendation not available yet" (501). Select a method (e.g. Hybrid). Adjust parameters. Click "Run experiment".
- [ ] **Processing** — Navigates to `/experiments/:id`. Shows progress bar (polling every 2 s). Stages show Done/Running/Waiting based on `facts.stage`. Live log shows last 50 lines. Cancel button is disabled with tooltip.
- [ ] **Results** — When status reaches `done`: 6 MetricCards appear with deltas. SVG chart renders series. PCA scatter shows two panels. Per-class table shows share kept. Explanation card shows text + metadata.
- [ ] **Results — missing data** — If any section data is `null` or missing, it shows "not available" instead.
- [ ] **Download CSV** — Click "Download CSV". Browser downloads `experiment_<id>.csv`. Open and verify metrics, reference, and per-class rows.
- [ ] **Export report** — Click "Export report". Browser print dialog opens. Sidebar and buttons are hidden.
- [ ] **Failed experiment** — Trigger or view a failed experiment. Error text appears. "Back to Configure" link works.
- [ ] **Experiments list** — Navigate to `/experiments`. Table shows short ID, dataset name, method, status pill, progress, created date. Click a row → opens `/experiments/:id`.
- [ ] **Experiments list filters** — Search by ID/dataset/method. Filter by status dropdown.
- [ ] **Placeholder pages** — `/benchmarks`, `/recommendations` show "not available yet". `/settings` shows "not available yet" + Sign Out button.
- [ ] **Sign Out** — Click Sign Out on Settings. Redirects to `/login`.
- [ ] **DEV-only route** — In dev mode, open `/dev/sample-result`. Red "SAMPLE DATA, NOT A REAL RUN" banner appears. Full results view renders from fixture.
- [ ] **Responsive — 768 px** — Sidebar stacks horizontally above main. Cards wrap.
- [ ] **Responsive — 390 px** — Buttons go full-width. Cards compress. Table scrolls horizontally.
- [ ] **Keyboard focus** — Tab through all interactive elements. Focus ring (3 px primary outline) is visible on buttons, inputs, selects, links.
- [ ] **401 handling** — Simulate an expired token. API returns 401 → user is signed out → redirected to `/login`.
