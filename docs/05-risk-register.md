# 05 — Risk register

Owner: Taimoor Khaliq (24i-3052). Inputs requested from Ashar (area 1) and Ali (area 3) and merged here. Status: **DRAFT for the Phase 4 team call** (2026-11-23). Machine-readable copy: `docs/05-risk-register.csv`.
Linked requirements resolve to `docs/01` §5–§6. Draft IDs RISK-01…RISK-12 in `docs/03-test-plan.md` §9 keep the same meanings here; RISK-13…RISK-15 are added from the brief's seed list. Scores and likelihoods are **proposed planning judgements** `[CONFIRM]` — they are not measured frequencies.

## 1. Scoring and 5 × 5 matrix

Likelihood **L** (1 rare … 5 almost certain) × Impact **I** (1 negligible … 5 severe) = **score** (1…25).
Levels: **High ≥ 15**, **Medium 8–14**, **Low ≤ 7** `[CONFIRM cutoffs with the team]`.
The level fixes technique and depth (§3): high → full MCC + MC/DC, EP with 3-point BVA, decision tables, state transitions, mutation and a CI gate; medium → EP + BVA (decision tables where the rule has ≥2 conditions); low → smoke checks only.

| L ↓ / I → | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | 5 L | 10 M | 15 H | 20 H | 25 H |
| **4** | 4 L | 8 M | 12 M | 16 H | 20 H |
| **3** | 3 L | 6 L | 9 M | 12 M | 15 H |
| **2** | 2 L | 4 L | 6 L | 8 M | 10 M |
| **1** | 1 L | 2 L | 3 L | 4 L | 5 L |

## 2. Register — 11 product risks + 4 project risks

| ID | Type | Description | L | I | Score | Level | Technique and depth | Owner | Mitigation | Linked requirements |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| RISK-01 | Product | Check displayed `up` after its grace period has passed (time edge in BR-02) | 4 | 5 | 20 | High | MCC + full MC/DC on `get_status`; EP + 3-point BVA at grace boundaries; mutation; CI gate | Ashar + Taimoor | Frozen-time unit tests, 3-point BVA on grace, mutation of comparisons | FR-10; BR-02 |
| RISK-02 | Product | Ping to a paused check changes status contrary to `manual_resume` (BR-03) | 4 | 5 | 20 | High | State-transition set for all allowed + one disallowed per state; decision table; mutation; CI gate | Ashar + Taimoor | Enumerate 11-row transition table from `docs/01` §6; test both rule conditions independently | FR-11; BR-03 |
| RISK-12 | Project | Time left before the 29 Nov 2026 submission; phases 9–14 still pending | 5 | 4 | 20 | High | Weekly GQM report; early handoffs; scope cut by risk level (never cut high-risk depth) | All | Fixed schedule check at each status block; escalate slippage at the weekly call | All |
| RISK-05 | Product | timeout/grace outside 60…31536000 accepted (BR-01) | 4 | 4 | 16 | High | EP + 3-point BVA (59/60/61 and 31535999/31536000/31536001); generator-driven negatives; CI gate | Taimoor | Generator produces boundary values from spec constraints; assert API 400 and dashboard 400 | FR-01; FR-02; FR-06; BR-01 |
| RISK-03 | Product | Read-only key or member changes a check (BR-04) | 3 | 5 | 15 | High | Access matrix for all 7 principals; API + Playwright tests; ZAP passive; CI gate | Taimoor + Ali | Test every write with rw/ro key and rw/ro member; assert 401/403 | FR-03; FR-05; BR-04 |
| RISK-04 | Product | One project's key reaches another project's checks (BR-04) | 3 | 5 | 15 | High | Cross-project tests at every endpoint; access matrix; CI gate | Taimoor | Use `other-up` and the second project key from seed data; assert 403/404 | FR-05; BR-04 |
| RISK-06 | Product | Concurrent pings and SQLite locking (`select_for_update` is a no-op on SQLite) | 3 | 4 | 12 | Medium | EP + BVA on repeated requests; failure-and-recovery test; ping-count read-back | Ashar + Taimoor | Reset DB between runs; repeated-request tests; record residual risk in completion report | FR-07; FR-09; BR-03 |
| RISK-07 | Product | Account check limit bypassed (BR-01) | 3 | 4 | 12 | Medium | EP + 3-point BVA on the limit with `profile.check_limit` set explicitly | Taimoor | Set the profile limit in test setup (local effective limit is 10000 — `docs/01` A-05) | FR-01; BR-01 |
| RISK-15 | Product | Ping log or ping count drifts after a failed write | 3 | 4 | 12 | Medium | EP + repeated-request tests; read-back of `n_pings` and Flip rows after success and rejection | Taimoor | Assert log/count consistency after every ping test; file a defect on drift | FR-07; FR-09; BR-03 |
| RISK-11 | Project | Flaky local environment (Host/proxy quirks, no WSL) | 4 | 3 | 12 | Medium | Documented pinned commands in `README-team.md`; twice-repeated suite runs | Ashar | `curl --noproxy '*'`, `localhost` only, reset script before each run | All |
| RISK-14 | Project | Teammate availability; members busy with other courses | 3 | 4 | 12 | Medium | Early handoffs with one command and viva questions; 10-min review calls | All | Package each piece with HANDOFF.md; verify each member's own commit | All |
| RISK-09 | Product | API keys exposed in pages or URLs | 2 | 5 | 10 | Medium | Source/config review; ZAP passive scan; check every response body and URL | Ali | Grep rendered HTML for `hcw_`/`hcr_`; no keys in query strings | FR-05; FR-12; BR-04 |
| RISK-08 | Product | Clock/time-zone edges at the grace boundary | 3 | 3 | 9 | Medium | EP + BVA with frozen time; time-zone variations in unit tests | Ashar | Freeze `now()` in unit tests; test grace_start and grace_end exactly | FR-10; BR-02 |
| RISK-10 | Product | Inaccessible forms (keyboard, contrast, ARIA) | 3 | 3 | 9 | Medium | axe-core + Lighthouse on key screens; keyboard-navigation test | Ali | Fix critical/high axe findings; re-run after fix | UC-01…UC-06 |
| RISK-13 | Project | Docker or SonarQube resource limits (CE OOM, long scans) | 3 | 3 | 9 | Medium | Monitor CE task status; keep scan scope documented; re-run on failure | Ashar | Scope exclusions in `sonar-project.properties`; check `/api/ce/task` after each scan | All |

Highest-scoring risks: **RISK-01, RISK-02, RISK-12** (score 20). The first two are product risks and are tied directly to release criteria RC-1 in `docs/06`; risk 12 is the project-level schedule risk controlled by the weekly report.

## 3. Technique and depth by level (applies to every risk)

| Level | Required technique and depth |
|---|---|
| High (≥15) | Full MCC then MC/DC pairs on the critical module; EP with 3-point BVA on every in-scope input; decision tables for ≥2-condition rules; state-transition tests (every allowed transition + one disallowed per state); ≥2 custom mutation operators; blocking CI gate |
| Medium (8–14) | EP + 3-point BVA on the inputs; decision-table or state-transition tests where the rule applies; no mutation requirement |
| Low (≤7) | One happy-path smoke assertion per requirement |

## 4. Review and maintenance

- Ashar and Ali were asked for their risks and estimates; their seed risks (SQLite locking, Docker limits, key exposure, accessibility, teammate availability, schedule) are merged above. They must confirm their own rows at the Phase 4 call.
- Re-score a risk when evidence changes (a defect, a failed run, a scope cut). Record the date, old score, new score and reason here; never silently edit a score after testing starts.
- Every defect filed in Phase 11 links to one of these IDs; RC-1 links to the two highest product risks (RISK-01, RISK-02), RC-2 to the high-level access risks (RISK-03, RISK-04), and RC-3 to the medium-level reliability risks (RISK-06, RISK-15).
