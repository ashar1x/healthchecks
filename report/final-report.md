# SE3002 Software Quality Engineering — Final Project Report

**Project:** automated testing of Healthchecks (open-source MIS, BSD 3-clause).
**Team:** Ashar Ahmed (24i-3072), Taimoor Khaliq (24i-3052), Ali Haider (24i-3102), Section C.
**Repository:** https://github.com/ashar1x/healthchecks
**Upstream:** https://github.com/healthchecks/healthchecks (commit tagged `baseline`).
**Submission:** 29 November 2026.

## 1. Scope and test basis

Two related workflows in the Checks module: check management (create, edit,
pause, resume) and ping handling (status new/up/grace/down/paused/started). The
shared record is the Check (timeout, grace, status, last ping, last start, ping
count). Twelve functional requirements, four business rules and six use cases
are fixed in `docs/01-scope-and-test-basis.md`. Business rules: BR-01 boundary
(60..31536000 s), BR-02 compound status decision, BR-03 state transitions,
BR-04 role and key permissions. Roles: owner, rw member, ro member, rw key,
ro key, unauthenticated. Full scope and assumptions are in `docs/01` and
`docs/00-brief-notes.md`.

## 2. Area ownership and commits

| Area | Owner | Evidence |
|---|---|---|
| 1 — static analysis, white-box, mutation, CI | Ashar Ahmed | `docs/02`, `docs/08`, `docs/11`, `docs/12-ci-gate.md` |
| 2 — API testing, data generation | Taimoor Khaliq | `docs/09-api-testing.md`, `docs/10`, `tests/team/api/` |
| 3 — use cases, usability, security, performance | Ali Haider | `docs/16`, `docs/14`, `docs/15`, `docs/16-performance-recovery.md` |
| Shared test management | Taimoor leads; all contribute | `docs/03`–`docs/07`, `docs/18-weekly-reports/`, `docs/19-completion-report.md` |
| Defect management and RCA | Ali leads | GitHub Issues #6–#9, `docs/17-defects/` |

Each member commits under their own identity; PRs #1, #3, #4 and #5 are merged
into `area1/ashar`.

## 3. Risk register and traceability

The 5 × 5 register in `docs/05-risk-register.md` holds 15 product and 4 project
risks. Technique and depth follow the risk level: high risks get MCC/MC-DC,
EP/3-point BVA, decision-table and state-transition tests plus mutation and a
CI gate. Exit criteria RC-1/RC-2/RC-3 are in `docs/06-exit-criteria.md`. The
traceability matrix `docs/07-traceability.csv` links FR → BR → RISK → test →
defect; `tools/traceability/coverage.py` computes 12/12 FR = 100% executed
coverage from 67 test functions (`evidence/raw/requirements-coverage.json`,
manifest IDs EV-004/EV-005).

## 4. Results by activity

| Activity | Result | Evidence |
|---|---|---|
| SonarQube and hand V(G) | metrics and complexity comparison recorded | `docs/02`, `evidence/raw/sonar-*.json` |
| White-box | 225 pytest tests; MCC 128 rows, 7 MC/DC pairs | `docs/08`, `evidence/raw/pytest-report.json` |
| API and BVA | CRUD FR-01/02/04 with read-back; 3-point BVA on timeout/grace | `tests/team/api/`, `docs/09-api-testing.md` |
| Test data generation | OpenAPI spec, deterministic generator, change-two demo | `spec/`, `tools/testgen/`, `docs/10` |
| Use cases and browser | 13 Playwright tests covering main, alternative and exception flows | `docs/16`, `tests/e2e/` |
| Mutation | 365 mutants, 310 killed, 52 survived, 3 undetected; 84.9% full / 88.3% business-rule; custom operators 20/20 killed; 24 survivors analysed | `docs/11`, `evidence/mutation/` |
| Usability/accessibility | Lighthouse checks 72→100; axe violations 8→2 on fixed checks screen; keyboard submit verified | `docs/14`, `evidence/phase9/` |
| Security | 5/5 access decisions; ZAP passive 498 alerts; pip-audit 0/54; npm audit 0 | `docs/15`, `evidence/security/` |
| Performance/recovery | 4 k6 runs, worst p95 143.1 ms vs 500 ms, 0 failures; recovery test passes | `docs/16-performance-recovery.md`, `evidence/performance/` |
| Defects | Issues #6–#9; RCAs and Pareto | `docs/17-defects/`, `evidence/raw/pareto.svg` |

## 5. Findings with root cause, severity, risk and fix

| Finding | Root cause | Severity / priority | Risk | Fix |
|---|---|---|---|---|
| #6 vendored DOMPurify vulnerable | upstream asset inherited at baseline and never version-checked | High / P1 | RISK-03/04 | upgrade vendored file via documented PR (`docs/17-defects/rca-01-def01.md`) |
| #7 bare 400 on invalid timeout | view returns `HttpResponseBadRequest()` with no field error | Medium / P2 | RISK-02, FR-06/BR-01 | render field error naming the 60 s / 365-day bounds |
| #8 traceability 0% | Phase 4 JSON never regenerated after tests were added | High / P1 | RISK-15 | regenerate from pytest JSON report; fixed to 100% (`rca-02-def03.md`) |
| #9 missing CSP | local dev server has no deployment proxy header policy | Low / P2 | RISK-03 | set CSP in deployment configuration |
| axe button-name/landmark/label | icon buttons and layout lacked accessible names/landmarks | Critical→fixed | RISK-10 | added aria-labels, main landmark, h1, header scopes |
| Lighthouse colour contrast | primary button and footer link colours too light | Serious→fixed | RISK-10 | darker button, underlined darker links |
| k6 no threshold breach | operation is a cheap read on local SQLite | n/a | RISK-06/15 | keep 500 ms / 1% limits; no fix needed |

## 6. Test management, AI use and viva

Test plan, estimation, risk register, exit criteria and weekly reports are in
`docs/03`–`docs/07` and `docs/18-weekly-reports/`. Actuals remain unlogged in
`docs/effort-log.csv` — a known gap for Taimoor. AI use is disclosed per row in
`docs/ai-use-record.md`, with prompts and both source documents in
`docs/prompts/`. Viva notes and the live-task change map are in `docs/viva/`.

## 7. Release decision

| Criterion | Target | Actual | Met |
|---|---|---|---|
| RC-1 functional status correctness | 100% MCC/MC-DC cases pass; BVA at all bounds | 225 tests pass; boundary tests at 59/60/61 and 31535999/31536000/31536001 | Yes |
| RC-2 access control | 100% decisions, zero High auth defects | 5/5 automated decisions pass, but issue #6 is High and unresolved | No |
| RC-3 performance/reliability | p95 ≤ 500 ms, <1% failures, 4 runs | worst p95 143.1 ms, 0 failures, 4 runs; recovery test passes | Yes |

**Decision: HOLD.** The single release blocker is issue #6 (High vulnerability
in a vendored asset), plus the uncompleted branch-protection step. Full detail
and residual risk are in `docs/19-completion-report.md`. Evidence links and
hashes are indexed in `evidence/manifest.csv` (71 artefacts).
