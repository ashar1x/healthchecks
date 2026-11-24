# 04 — Estimation

Owner: Taimoor Khaliq (24i-3052). Contributors: Ashar Ahmed (area 1), Ali Haider (area 3). Status: **DRAFT for the Phase 4 team call** (2026-11-23).
Every number below is a **proposed planning estimate from the agent, not measured data**. `[CONFIRM]` marks values the three members must agree or replace before these estimates are used for the weekly report or completion report. Actual hours go into `docs/effort-log.csv` as work happens — **never back-fill**.

## 1. Method

Three-point estimate per area and activity: optimistic **O**, most likely **M**, pessimistic **P**; expected effort **E = (O + 4M + P) / 6** (PERT). Pessimistic values include rework after review, environment problems and the documented Windows/proxy quirks (`docs/01` §12). All values are hours of member effort, rounded to 2 decimal places at the end; agent assistance does not count as member effort.

## 2. Estimates by area and activity

### Area 1 — Ashar Ahmed (static analysis, white box, mutation, CI)

| ID | Activity | O | M | P | E = (O+4M+P)/6 |
|---|---|---:|---:|---:|---:|
| A1-1 | Phase 1 setup, seed, lifecycle verification, scope document | 6 | 8 | 12 | 8.33 |
| A1-2 | Phase 3 SonarQube, CFG and hand-calculated complexity | 5 | 7 | 11 | 7.33 |
| A1-3 | Phase 5 unit tests, 100% statement/branch, MCC + MC/DC, coverage | 10 | 14 | 22 | 14.67 |
| A1-4 | Phase 8 mutation testing and custom operators | 6 | 9 | 14 | 9.33 |
| A1-5 | Phase 10 CI gate and the two documented pull requests | 5 | 7 | 12 | 7.50 |
| A1-6 | UC-01 and UC-02 specifications and Playwright automation (with area 3 setup) | 6 | 9 | 15 | 9.50 |
| | **Area 1 subtotal** | | | | **56.66** |

### Area 2 — Taimoor Khaliq (API testing, test data, test management)

| ID | Activity | O | M | P | E = (O+4M+P)/6 |
|---|---|---:|---:|---:|---:|
| A2-1 | Phase 4 documents (plan, this estimate, risk register, exit criteria, traceability) | 8 | 11 | 16 | 11.33 |
| A2-2 | Phase 6 OpenAPI spec curation and deterministic test-data generator | 10 | 14 | 22 | 14.67 |
| A2-3 | Phase 7 API/integration tests, coverage script, endpoint weakness issues | 14 | 19 | 30 | 20.00 |
| A2-4 | Weekly reports and completion report (GQM metrics, effort vs estimate) | 4 | 6 | 10 | 6.33 |
| A2-5 | UC-03 and UC-04 specifications and Playwright automation | 6 | 9 | 15 | 9.50 |
| | **Area 2 subtotal** | | | | **61.83** |

### Area 3 — Ali Haider (use cases, usability, accessibility, security, performance)

| ID | Activity | O | M | P | E = (O+4M+P)/6 |
|---|---|---:|---:|---:|---:|
| A3-1 | UC-05/06 specifications and Playwright setup for all six UCs | 12 | 17 | 26 | 17.67 |
| A3-2 | Lighthouse and axe-core runs, keyboard-navigation test | 5 | 7 | 12 | 7.50 |
| A3-3 | ZAP passive scan, dependency audit, access-matrix verification | 6 | 9 | 14 | 9.33 |
| A3-4 | k6 performance runs (1 and ≥5 users, 2×60 s) and failure/recovery test | 8 | 12 | 18 | 12.33 |
| A3-5 | Defect triage, root-cause analysis, Pareto | 5 | 7 | 12 | 7.50 |
| | **Area 3 subtotal** | | | | **54.33** |

**Team total: 172.82 h** (56.66 + 61.83 + 54.33). Average per member ≈ 57.61 h. `[CONFIRM — available hours per member per day; submission 29 Nov 2026 is fixed. If the team has less time, cut scope using the risk levels in docs/05, not test depth on high risks.]`

## 3. Basis for the estimates

- The three O/M/P values are **judgements**, each linked to scope in `docs/01` §3 and the work orders in the three member prompt files. No timing tool was run; these are not measured durations.
- P values assume one review-and-rework cycle per piece, the documented proxy/Host quirks, and a re-run of SonarQube after Phase 5.
- A2-3 is the largest single item because it covers 9 endpoints × 7 API coverage criteria (C1–C7 in `docs/03` §8), read-back after every request, and cross-workflow checks.
- A1-3 and A1-4 assume mutmut/Cosmic Ray can be run through Docker (WSL is absent — `docs/01` A-07); a tool change would move hours from A1-4 to A1-3.
- A3-1 assumes Node.js is installed before Phase 9 — **currently blocked**; if it is not installed, the estimate does not shrink, the start date moves.

## 4. Actuals versus estimate (fill at the end — no back-filling)

`docs/effort-log.csv` columns: `date,member,activity,hours`. Each member appends **their own** rows on the day the work is done. To compare at completion:

| Area | Estimated E | Actual (sum of own logged rows) | Variance | Note |
|---|---:|---:|---:|---|
| Area 1 | 56.66 | `[fill from effort-log.csv]` | — | — |
| Area 2 | 61.83 | `[fill from effort-log.csv]` | — | — |
| Area 3 | 54.33 | `[fill from effort-log.csv]` | — | — |
| Team | 172.82 | `[fill from effort-log.csv]` | — | — |

The weekly report (`docs/18-weekly-reports/`) and completion report (`docs/19-completion-report.md`) use these numbers; a variance beyond ±25% is explained in words, not hidden.

## 5. Open decisions for the Phase 4 call

- Confirm or replace every O/M/P value above (they are proposals from the agent).
- Confirm the available hours per member until 29 Nov 2026 and the weekly report day.
- Confirm the API coverage thresholds marked `[CONFIRM]` in `docs/03` §8 with the instructor/TA.
- Confirm the performance thresholds proposed in `docs/06` before any k6 run.
