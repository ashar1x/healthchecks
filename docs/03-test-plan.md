# 03 — Test Plan

Status: **DRAFT for Taimoor Khaliq (area 2) to complete, confirm and defend.** Items marked `[CONFIRM]` need a team decision (schedule dates, thresholds) or instructor/TA confirmation (API coverage criteria). Requirement and rule IDs refer to `docs/01-scope-and-test-basis.md`; risk IDs refer to `docs/05-risk-register.md`; exit-criteria detail to `docs/06-exit-criteria.md`.

Owner: Taimoor Khaliq (24i-3052). Contributors: Ashar Ahmed (area 1), Ali Haider (area 3). Last updated: 2026-11-22.

## 1. Scope

### 1.1 In scope

- **WF1 — Check management** (dashboard UI + HTTP API): create, edit, pause, resume, delete, list/fetch (docs/01 §3).
- **WF2 — Ping and status lifecycle**: success/fail/start pings, derived status (`new`/`up`/`grace`/`down`/`paused`), paused + manual-resume rule (docs/01 §3).
- Functional requirements **FR-01 … FR-12** and business rules **BR-01 … BR-04** (docs/01 §5–§6).
- API endpoints listed in §8.2 of this plan; dashboard screens used by UC-01 … UC-06 (docs/01 §8).
- Quality attributes: functional correctness, security (access decisions), performance (p95 of one operation), usability/accessibility (key screens).

### 1.2 Out of scope

- Notification channel integrations (email, Slack, Telegram, …) beyond their effect on check configuration — they are configured but not exercised end to end.
- Payments/billing (`USE_PAYMENTS=False` in the test environment).
- Upstream's own test suite (`hc/**/tests/`) — it earns no marks and is never copied; our tests live in `tests/team/`.
- Non-functional load beyond the single k6 operation chosen in Phase 12 (performance scope fixed then).
- Browser support matrix (Chromium only, via Playwright).

## 2. Approach by risk level

Risk level comes from `docs/05-risk-register.md` (score = likelihood × impact, 5×5). Level decides technique and depth:

| Risk level | Techniques and depth applied |
|---|---|
| **High** (score ≥ 15 [CONFIRM threshold in risk register]) | Complete MCC then MC/DC pairs on the critical module (`Check.get_status`); equivalence partitioning with 3-point boundary value analysis; decision tables for every rule with ≥2 conditions; state-transition tests for every allowed transition + one disallowed per state; mutation analysis with ≥2 custom operators; CI gate blocking merge |
| **Medium** (score 8–14 [CONFIRM]) | Equivalence partitioning and 3-point BVA on all inputs; decision-table or state-transition tests where the rule applies; no MC/DC requirement |
| **Low** (score ≤ 7 [CONFIRM]) | Smoke checks only (one happy-path assertion per requirement) |

Test levels and which techniques apply where:

| Level | Owner | Techniques |
|---|---|---|
| White-box unit (Phase 5) | Ashar | 100% statement + branch coverage of server-side business logic; MCC + MC/DC on `Check.get_status`; all four BRs covered |
| API and integration (Phase 7) | Taimoor | EP and 3-point BVA on every input of every in-scope endpoint from generated data; rule rejections; invalid transitions; repeated requests; read-back of shared records; cross-workflow checks |
| Browser end-to-end / use cases (Phase 9) | Ali (+ all: UC automation) | Every flow of UC-01 … UC-06 automated in Playwright with postcondition assertions |
| Usability and accessibility (Phase 9) | Ali | Lighthouse + axe-core on key screens; keyboard-navigation test |
| Defensive security (Phase 10) | Ali | Access-matrix verification (≥4 decisions), ZAP passive scan, dependency audit (pip-audit) |
| Performance and recovery (Phase 12) | Ali | k6 p95 runs (1 and ≥5 users, 2 runs each, ≥60 s), one failure-and-recovery test |
| Mutation and CI gate (Phase 8/10) | Ashar | mutmut/Cosmic Ray on the business-rule module, ≥15 surviving mutants analysed, thresholds as CI gates |

## 3. Roles and area ownership

| Member | Area | Plan responsibilities |
|---|---|---|
| Ashar Ahmed (24i-3072) | 1 — static analysis, unit tests, mutation, CI | `docs/01` scope, SonarQube, unit tests, mutation, pipeline; owns entry into Phases 3, 5, 8 |
| Taimoor Khaliq (24i-3052) | 2 — API testing, test data generation | This plan, estimation, risk register, exit criteria, traceability, weekly/completion reports; OpenAPI spec, generator, API tests |
| Ali Haider (24i-3102) | 3 — use cases, usability, a11y, security, performance | Use-case specs, Playwright automation, Lighthouse/axe, ZAP + dependency audit, k6, defect triage |

Review rule: each finished piece is reviewed by a different member before merge (master prompt).

## 4. Environment

| Item | Value |
|---|---|
| OS / runtime | Windows 11 host, Python 3.12.10 in `.venv` (no WSL — see docs/01 §12) |
| Server | `.\scripts\start.ps1` → `http://localhost:8000` (Host must be `localhost`, never `127.0.0.1`; use `curl --noproxy '*'`) |
| Database | SQLite `hc.sqlite`, wiped and re-seeded by `.\scripts\reset.ps1` between test runs |
| API tests | pytest + requests against a freshly reset database; every test sets up its own data through the API |
| Static analysis | SonarQube Community (Docker) + scanner; metrics into `evidence/raw/` |
| Browser | Playwright + Chromium (requires Node.js — pending install) |
| CI | GitHub Actions (`.github/workflows/ci.yml`), one job per gate, **no escape hatches** |

## 5. Test data

Seeded by `scripts/seed.py` (deterministic, idempotent; ping UUIDs stable via uuid5):

| Data | Value |
|---|---|
| Password (all accounts) | `sqe-test-pass-2026` |
| Accounts | `admin@example.com` (superuser), `owner@example.com`, `member-rw@example.com`, `member-ro@example.com`, `other-owner@example.com` |
| Main project rw / ro key | `hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4` / `hcr_Z9y8X7w6V5u4T3s2R1q0P9o8N7m6` |
| Other project rw key | `hcw_B2c3D4e5F6g7H8i9J0k1L2m3N4o5` (cross-project tests) |
| Checks | `seed-new`, `seed-up`, `seed-grace`, `seed-down`, `seed-paused`, `seed-paused-manual`, `other-up` (display statuses documented in docs/01 §10) |
| Generated data (Phase 6+) | `tools/testgen/` output — EP classes and 3-point BVA per spec constraint, deterministic (fixed seed, sorted, header with spec hash). API tests consume **only** generated values; no hand-copied numbers |

Boundary values under test (BR-01): timeout/grace 59 / 60 / 61 and 31535999 / 31536000 / 31536001 seconds; check limit boundary by setting `profile.check_limit` explicitly (local effective limit is 10000 — docs/01 A-05).

## 6. Schedule

`[CONFIRM — team to fill actual dates at the Phase 4 call; submission 29 Nov 2026 is fixed.]`

| Milestone | Planned dates | Owner | Depends on |
|---|---|---|---|
| Phases 1–2: baseline, scope, test basis | done (2026-11-22) | Ashar | — |
| Phase 3: SonarQube + complexity | `[CONFIRM]` | Ashar | Docker |
| Phase 4: this plan, estimation, risk register, exit criteria, traceability | `[CONFIRM]` | Taimoor (drafts by agent) | docs/01 (done) |
| Phase 5: unit tests + coverage | `[CONFIRM]` | Ashar | docs/01, this plan |
| Phases 6–7: spec, generator, API tests | `[CONFIRM]` | Taimoor | this plan, Phase 5 |
| Phase 8: mutation + custom operators | `[CONFIRM]` | Ashar | tool decision (WSL/Docker/CI) |
| Phase 9: use cases, Playwright, Lighthouse/axe | `[CONFIRM]` | Ali (+ members' UCs) | Node.js install |
| Phase 10: ZAP passive, dependency audit, CI gate | `[CONFIRM]` | Ali / Ashar | Phase 9 |
| Phases 11–14: defects, performance, weekly reports, completion report, submission | `[CONFIRM]` | all | — |

## 7. Entry, exit, suspension and resumption criteria

### 7.1 Entry criteria (per level)

- **Unit testing (Phase 5):** docs/01 merged; environment reproducible by `setup.ps1` + `reset.ps1` from a clean clone; `manage.py check` passes with no errors.
- **API testing (Phase 7):** this plan approved; `spec/openapi.yaml` curated and verified against the running app; generator output available; database resettable to a known state; at least one passing smoke test per in-scope endpoint.
- **E2E / use cases (Phase 9):** Node.js + Playwright installed; seed data stable across resets; each UC specification has preconditions and postconditions written.
- **Performance (Phase 12):** response-time limit and failure-rate limit set **before** running (docs/06, `[CONFIRM]` with justification for the chosen operation).

### 7.2 Exit criteria (summary — full measurable criteria in `docs/06-exit-criteria.md`)

Draft, measurable, tied to risks (≥3, ≥2 linked to the highest risks [CONFIRM final thresholds in docs/06]):

1. **Functional:** 100% of FR-01 … FR-12 have at least one passing automated test, and requirements coverage computed by script from test IDs ≥ 100% of in-scope FRs; zero open defects of severity high/critical.
2. **API:** every API coverage criterion in §8.2 measured at ≥ [CONFIRM]% with raw output saved under `evidence/raw/`; all rule-rejection and invalid-transition tests pass twice in a row on a reset database.
3. **Reliability of the suite:** unit + API suites pass twice consecutively with no flaky tests (a flaky test counts as a failure, links RISK-xx for SQLite concurrency).
4. **Performance:** p95 of the chosen operation ≤ [CONFIRM] ms and unexpected failures < [CONFIRM]% (limits justified in docs/06 before measurement).

### 7.3 Suspension criteria

Suspend testing when: the server cannot start from a clean reset; the database cannot be re-seeded deterministically; a severity-1 defect blocks the workflow under test; or the environment diverges from §4 (e.g. Node.js/Playwright missing for E2E).

### 7.4 Resumption criteria

Resume when: the blocking defect is fixed or a workaround is agreed and recorded in the risk register; `reset.ps1` produces the documented seed output again; and the responsible member confirms the environment matches §4. All suspended test cases are re-run from the start of the affected level.

## 8. API coverage criteria

### 8.1 Why

The brief requires API coverage criteria defined in the test plan and reported as percentages (Phase 7). `[CONFIRM with instructor/TA]` — Taimoor asks for confirmation once the list below is agreed.

### 8.2 Endpoints in scope (our two workflows)

| # | Operation | Endpoint | Documented status codes (source: `templates/docs/api.md`) |
|---|---|---|---|
| 1 | GET | `/api/v3/checks/` | 200, 401 (`api.md:120-123`) |
| 2 | POST | `/api/v3/checks/` | 201, 200, 400, 401, 403 (`api.md:642-655`) |
| 3 | GET | `/api/v3/checks/<uuid>` | 200, 401, 403, 404 (`api.md:277-286`) |
| 4 | POST | `/api/v3/checks/<uuid>` | 200, 400, 401, 403, 404 (`api.md:955-968`) |
| 5 | DELETE | `/api/v3/checks/<uuid>` | 200, 401, 403, 404 (`api.md:1180-1189`) |
| 6 | POST | `/api/v3/checks/<uuid>/pause` | 200, 401, 403, 404 (`api.md:1035-1044`) |
| 7 | POST | `/api/v3/checks/<uuid>/resume` | 200, 401, 403, 404, 409 (`api.md:1106-1119`) |
| 8 | GET | `/ping/<uuid>`, `/ping/<uuid>/fail`, `/ping/<uuid>/start`, `/ping/<uuid>/<exitstatus>` | 200 `OK`, 400, 404 (code: `hc/api/views.py:196-261`; ping endpoints are unauthenticated by design — A-06) |
| 9 | GET | `/ping/<ping_key>/<slug>` (+ `?create=1`) | 200/201 `Created`, 400, 404, 409 (code: `hc/api/views.py:264-304`) |

### 8.3 Coverage criteria (seven dimensions) and how each is measured

Each criterion is a tuple that a request must cover; a criterion counts as covered when at least one executed request matches it **and** asserts the documented outcome:

| Criterion | Definition | Measurement |
|---|---|---|
| C1 Endpoint | each endpoint in §8.2 appears in the request log | script counts distinct `path` patterns vs §8.2 |
| C2 Operation | each HTTP method each endpoint documents | distinct `(path, method)` pairs |
| C3 Documented status code | each documented code for that operation is produced by at least one test and asserted | distinct `(path, method, status)` triples vs §8.2 column |
| C4 Parameter | each path/query parameter the endpoint accepts (e.g. `tag`, `slug`, `uuid`, `exitstatus`, `rid`) exercised with valid and invalid values | request-log fields `params` vs spec parameters |
| C5 Request-body field | each request-body field (`name`, `timeout`, `grace`, `schedule`, `tz`, `slug`, `tags`, `desc`, `methods`, `manual_resume`, …) exercised valid + invalid | parsed JSON body keys vs spec `requestBody` properties |
| C6 Role | each principal that the spec/BR-04 says can call the operation: rw key, ro key, rw member, ro member, owner, unauthenticated, other-project key | `X-Api-Key` / session identity recorded per request |
| C7 Auth state | authenticated vs unauthenticated vs wrong-key vs missing-key for each secured endpoint | distinct auth headers per endpoint |

**How measured:** a pytest fixture appends one JSON line per request (`evidence/raw/api-requests.jsonl`: timestamp, method, path, status, params, body keys, auth identity class). `tests/team/api/coverage.py` reads it plus `spec/openapi.yaml`, computes per-criterion covered/total and a percentage, and writes `evidence/raw/api-coverage.json`. Raw output is saved untouched; the script output is the reported number (never hand-counted). `[CONFIRM thresholds with instructor/TA]`

## 9. Risks (summary — full register in `docs/05-risk-register.md`)

Highest-scoring risks driving this plan's depth. IDs and meanings are final in `docs/05-risk-register.md` (scores there are proposed planning judgements pending the Phase 4 call):

| Draft ID | Risk | Level (draft) | Technique triggered |
|---|---|---|---|
| RISK-01 | Check shown as `up` after its grace period has passed (BR-02 time edge) | High | MC/DC on `get_status`, BVA at grace boundary, mutation |
| RISK-02 | Ping to a paused check changing status contrary to `manual_resume` (BR-03) | High | state transitions + decision table, mutation |
| RISK-03 | Read-only key or member changing a check (BR-04) | High | access-matrix tests (API + Playwright), ZAP passive |
| RISK-04 | One project's key reaching another project's checks (BR-04) | High | cross-project tests at every endpoint |
| RISK-05 | timeout/grace outside 60..31536000 accepted (BR-01) | High | 3-point BVA, generator-driven negatives |
| RISK-06 | Concurrent pings and SQLite locking (`select_for_update` is a no-op on SQLite) | Medium | recovery/failure test, repeated-request tests |
| RISK-07 | Check limit bypassed (BR-01) | Medium | boundary tests with `check_limit` set explicitly |
| RISK-08 | Clock/timezone edges at the grace boundary | Medium | time-machine frozen-time tests |
| RISK-09 | API keys exposed in pages or URLs | Medium | source/config review, ZAP passive |
| RISK-10 | Inaccessible forms (keyboard, contrast, ARIA) | Medium | axe-core + Lighthouse + keyboard test |
| RISK-11 | Project: flaky local environment (Host/proxy quirks, no WSL) | Medium | documented quirks in docs/01 §12, scripts pin commands |
| RISK-12 | Project: time left before 29 Nov submission | High | weekly report control actions, early handoffs |

The full register (`docs/05-risk-register.md`, 11 product + 4 project risks) keeps the IDs and meanings above and adds RISK-13 (Docker/SonarQube resource limits), RISK-14 (teammate availability) and RISK-15 (ping log/count drift after a failed write). Scores and levels there are the authoritative ones.

## 10. Traceability and reporting

- Requirements → rules → risks → tests → defects: `docs/07-traceability.csv` + `.md`; coverage computed by script from test names/markers (every test name carries FR and BR IDs).
- Defects: GitHub Issues with severity, priority, status, triage (Ali leads triage); endpoint weaknesses from Phase 7 linked to risk IDs.
- Weekly report (GQM: defect density, requirements coverage, reopen rate) in `docs/18-weekly-reports/`; completion report `docs/19-completion-report.md`.
- Effort: `docs/effort-log.csv` — every member appends their own rows as work happens; **no back-filling**; compared against `docs/04-estimation.md` at the end.

## 11. Assumptions and open questions

- A-01 … A-07 from docs/01 §9.2 apply to this plan (esp. A-03: resume status-code inconsistency API 409 vs dashboard 400 — candidate defect to be filed).
- `[CONFIRM]` API coverage thresholds (C1–C7 percentages) with instructor/TA.
- `[CONFIRM]` risk-level score cutoffs with the team (proposal: High ≥15, Medium 8–14, Low ≤7).
- `[CONFIRM]` schedule dates at the Phase 4 call.
- Open: Node.js install (Phase 9 gate), mutation tool choice (WSL/Docker/CI), `gh` CLI for issue/PR automation.

## 12. References

- `docs/01-scope-and-test-basis.md` — workflows, FR-01…FR-12, BR-01…BR-04, roles, assumptions, verified behavior matrix.
- `README-team.md` — quick start, credentials, quirks.
- Brief §2 (test plan contents), master prompt Phase 4 (this document's required sections).
- `templates/docs/api.md` — documented API status codes (citations in §8.2).
