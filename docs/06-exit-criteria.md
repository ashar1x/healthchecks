# 06 — Exit criteria (release criteria)

Owner: Taimoor Khaliq (24i-3052). Status: **DRAFT for the Phase 4 team call** (2026-11-23). These three measurable criteria become the three release criteria in `docs/19-completion-report.md` and the final PDF. Thresholds marked `[CONFIRM]` are proposals from the agent and must be agreed **before** the relevant test run — a limit chosen after measuring would be fabricated evidence.

## 1. RC-1 — Functional correctness of the derived status

**Risk link:** RISK-01 (`up` after grace, score 20) and RISK-02 (paused + `manual_resume`, score 20) — the two highest product risks; also RISK-08 (clock edges).

| Measure | Target | How measured / raw evidence |
|---|---|---|
| MCC and MC/DC on `Check.get_status` | 100% of test cases from the complete MC/DC set pass | `evidence/raw/pytest-unit.xml` + test names carrying `FR-10` / `BR-02` |
| BR-02 and BR-03 state transitions | Every allowed transition plus one disallowed per state passes **twice in a row** on a reset database | Two consecutive pytest runs; `evidence/raw/unit-runs/` |
| Grace boundary BVA | 59/60/61 and 31535999/31536000/31536001 with frozen time all produce the documented status | Unit + API test IDs in `docs/07-traceability.csv` |
| Open defects against FR-10 / FR-11 | Zero with severity High or Critical | GitHub Issues exported to `evidence/raw/defects.json` |

**Pass/fail:** all four rows must pass. A failure is a **hold** decision, regardless of the other criteria.

## 2. RC-2 — Security and access control

**Risk link:** RISK-03 (read-only write, score 15) and RISK-04 (cross-project key, score 15); also RISK-09 (key exposure, score 10).

| Measure | Target | How measured / raw evidence |
|---|---|---|
| BR-04 access matrix | 100% of decisions for all 7 principals pass on the API **and** in Playwright | `tests/team/api/` + `tests/team/e2e/`; raw results under `evidence/raw/` |
| Cross-project isolation | Every in-scope endpoint denies the other project's key (403/404) | API test IDs in `docs/07-traceability.csv` |
| Open auth defects | Zero with severity High or Critical | GitHub Issues + `docs/17-defects/` |
| Key exposure | No `hcw_`/`hcr_` key in rendered HTML, response bodies or URLs on the key screens | ZAP passive report + source grep in `evidence/raw/` |

**Pass/fail:** all four rows must pass; a failing auth test is a hold.

## 3. RC-3 — Performance and reliability under concurrent pings

**Risk link:** RISK-06 (SQLite concurrency, score 12) and RISK-15 (ping log/count drift, score 12).

| Measure | Target (set BEFORE running) | How measured / raw evidence |
|---|---|---|
| Operation | `GET /api/v3/checks/` on the freshly reset, seeded database — one operation only | Fixed in test plan §1.2; no scope growth at measurement time |
| p95 response time | ≤ **500 ms** `[CONFIRM — justify from one warm-up run; do not change after measuring]` | k6 summary JSON in `evidence/raw/performance/` |
| Runs | 2 runs of ≥60 s each at 1 user and 2 runs at ≥5 users | k6 summary JSON per run |
| Unexpected failures | < **1%** of requests `[CONFIRM]` | k6 `http_req_failed` |
| Ping count/log consistency | Zero drift in `n_pings` and Flip rows after 100 repeated pings | API read-back in `evidence/raw/` |

**Pass/fail:** all rows must pass. If SQLite locking is observed, record it as a residual risk against RISK-06 even if the run passes.

## 4. Supporting checks (measured and reported, not release-blocking)

These still earn marks and are reported; they do not change the release decision above.

| Check | Target | Risk |
|---|---|---|
| Requirements coverage (script, not hand-counted) | 100% of FR-01…FR-12 with ≥1 passing test | All |
| API coverage criteria C1–C7 | Each ≥ `[CONFIRM with instructor/TA]`% from `evidence/raw/api-coverage.json` | RISK-05, RISK-03 |
| axe-core / Lighthouse on key screens | Zero critical violations; keyboard navigation works | RISK-10 |
| Mutation score on the business-rule module | ≥ `[CONFIRM]`% with ≥15 surviving mutants analysed | RISK-01, RISK-02 |
| SonarQube after Phase 5 | Coverage > 0%; no new blocker/critical issues vs the Phase 3 baseline in `docs/02` | RISK-01, RISK-12 |

## 5. Entry and suspension link

Entry/exit/suspension/resumption criteria for each test level are in `docs/03-test-plan.md` §7. A suspended level cannot be counted toward RC-1…RC-3 until its resumption criteria are met and all affected tests are re-run from the start of that level.
