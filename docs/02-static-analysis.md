# 02 — Static analysis and hand-calculated complexity

Owner: Ashar Ahmed (24i-3072), area 1. Status: **Phase 3 complete** (2026-11-23).
Raw evidence: `evidence/raw/`; control-flow graph: `evidence/cfg-get-status.dot` / `.png` / `.svg`.
Risk IDs link to the draft register in `docs/03-test-plan.md` §9 until Taimoor's `docs/05-risk-register.md` exists.

## 1. Toolchain and what was scanned

| Item | Value |
|---|---|
| Server | SonarQube Community **26.11.0.134175**, Docker container `sonarqube`, `http://localhost:9000` |
| Scanner | SonarScanner CLI **8.4.0.16527** (`sonarsource/sonar-scanner-cli` image) |
| Analysed languages | Python 15,980 ncloc; JavaScript 1,592 ncloc; web/HTML 3,836 ncloc (HTML templates under `hc/`); **total 21,408 ncloc** |
| Python runtime | 3.12.10 (test environment, `docs/01` §12) |
| Cross-check tools | radon **6.0.1** (independent McCabe implementation); Graphviz **16.1.2** (CFG rendering) |

Configuration: `sonar-project.properties` (project key `sqe-healthchecks`), `sonar.sources=hc,static/js`.

**Documented exclusions** (in `sonar.exclusions`): `hc/**/tests/**` — upstream's own tests earn no marks and are never copied; including them would inflate duplication/coverage counts. `static/js/*.min.js`, `static/js/webauthn-json.browser-global.js`, `static/js/zxcvbn.min.js` — third-party minified/vendored libraries, not our code. Analysis covered 469 source files.

```powershell
docker run --rm -v "D:\University Assignments\SQE Project\healthchecks:/usr/src" -w /usr/src `
  -e SONAR_HOST_URL=http://host.docker.internal:9000 `
  -e SONAR_TOKEN=<analysis-token> sonarsource/sonar-scanner-cli
```

The analysis returned `ANALYSIS SUCCESSFUL`; compute-engine task `eebfd363-6e49-4189-b173-338ec43174e4` finished `SUCCESS` (`evidence/raw/sonar-ce-task.json`). A SonarQube dashboard screenshot is supporting evidence only and is taken manually by a team member (full window, URL and clock visible); the authoritative numbers are the API JSON files under `evidence/raw/`, pulled from `/api/measures/component`.

## 2. Metrics — number, meaning, risk linkage

All values from `evidence/raw/sonar-measures-component.json` (2026-11-22 baseline, before our tests).

| Metric | Value | What it shows | Risk it feeds / follow-up |
|---|---|---|---|
| ncloc | 21,408 (py 15,980; js 1,592; web 3,836) | Size of the analysed surface; we test only our two workflows, not all 21k lines | RISK-12 (time): scope control; `docs/01` §3 defines the tested subset |
| Cyclomatic complexity (`complexity`) | 2,540 | Total decision density; high-count modules are where branch testing and mutation matter most | RISK-01 (grace edge), RISK-02 (paused/manual resume) → MCC + MC/DC on `get_status` in Phase 5, mutation in Phase 8 |
| Cognitive complexity | 2,355 | How hard the nesting is to understand (nested `if`s cost more than flat ones) | RISK-01/02; identifies refactor candidates among the business rules |
| Duplicated lines | 1,284 (4.5%) | Copy-paste blocks; a fix in one copy can miss another | RISK-11 (inconsistent local edits) → code review in every PR |
| Code smells | 25 | Maintainability issues, not necessarily defects | RISK-12 (time) → cleanup only where it touches tested code |
| Bugs | 23 | Patterns SonarQube is confident are wrong | RISK-01, RISK-02, RISK-07 (check limit) → Phase 11 defect triage and regression tests |
| Vulnerabilities | 87 | Security weaknesses found in source (dependency analysis was skipped by the scanner) | RISK-03 (read-only writes), RISK-04 (cross-project), RISK-09 (key exposure) → Phase 10 ZAP passive scan + `pip-audit` |
| Security hotspots | 0 (`security_review_rating` A) | No security-sensitive code flagged for manual review; does **not** replace Phase 10 security testing | RISK-03/04/09 → still test the BR-04 permission matrix |
| Coverage | **0.0%** (10,733 lines to cover, all uncovered) | Expected before our tests exist — not a quality failure at this stage | Exit criteria in `docs/06`: Phase 5 writes `coverage.xml`, then **re-run SonarQube and update these numbers** |
| Technical debt | `sqale_index` 133 min; debt ratio 0.0% | Small estimated remediation effort relative to codebase size | RISK-12 → keep CI thresholds modest but justified in Phase 10 |
| Ratings | Maintainability **A** (1.0); Reliability **D** (4.0); Security **D** (4.0) | A = best, E = worst. Reliability D follows from 23 bugs; security D from 87 vulnerabilities | Reliability → RISK-01/02; security → RISK-03/04/09; gates set in Phase 10 |
| `alert_status` | OK | No failing quality-gate conditions are configured yet — do **not** read this as "quality approved" | Phase 10 configures the blocking gate |

Focused file measurement from `evidence/raw/sonar-measures-models.json`: `hc/api/models.py` = 1,090 ncloc, 100 functions, complexity 232, cognitive complexity 185, 0 bugs, 0 smells, 6 vulnerabilities, 0.0% duplication. This is the file containing the business rules BR-02/BR-03.

## 3. Hand-calculated cyclomatic complexity — `Check.get_status`

Source: `hc/api/models.py:355-380` (function body is reproduced verbatim in `evidence/calibration/get_status_calibration.py`). The rebuildable CFG source is `evidence/cfg-get-status.dot`; rendered images `evidence/cfg-get-status.png` and `.svg` (Graphviz `dot`). All seven decisions are binary (`in` is a membership test, not a boolean operator); there are no `and`/`or`, loops, or exception handlers in this function, so there is no counting ambiguity in the hand calculation.

| # | Decision (node in CFG) |
|---|---|
| 1 | `if self.last_start` (node 2) |
| 2 | `if frozen_now >= self.last_start + self.grace` (node 3) |
| 3 | `elif with_started` (node 5) |
| 4 | `if self.status in ("new", "paused", "down")` (node 7) |
| 5 | `if grace_start is None` (node 10) |
| 6 | `if frozen_now >= grace_end` (node 13) |
| 7 | `if frozen_now >= grace_start` (node 15) |

The CFG has **N = 18 nodes** (including one common EXIT node that all seven `return` statements reach) and **E = 24 edges**, with **P = 1** connected component:

**V(G) = E − N + 2P = 24 − 18 + 2 = 8.** Cross-check by the second formula: decisions + 1 = 7 + 1 = **8**. The two hand calculations agree.

## 4. Comparison with the tools

| Source | Complexity | Evidence |
|---|---|---|
| Hand calculation (CFG, E−N+2P) | **8** | §3, `evidence/cfg-get-status.*` |
| radon 6.0.1 (independent McCabe) | **8** | `evidence/raw/radon-cc-models.txt`: `M 355:4 Check.get_status - B (8)` |
| SonarQube 26.11 — `complexity` | **7** | Calibration scan of the extracted function: `evidence/raw/sonar-calibration-getstatus.json` (`complexity=7`, `functions=1`, `cognitive_complexity=8`) |
| SonarQube 26.11 — `cognitive_complexity` | **8** | Same JSON |

**Why SonarQube says 7, not 8.** SonarQube's API exposes complexity only at file/folder/project granularity — `qualifiers=FUNC` and `BRC` are rejected (valid: `UTS, FIL, DIR, TRK`; raw probe in `evidence/raw/sonar-qualifier-probe.txt`). To get the tool's own number for this function, the function body was extracted verbatim into a one-function project (source kept in `evidence/calibration/`) and scanned separately. Three micro-calibrations establish the counting rules:

| Calibration input (in `evidence/calibration/`) | SonarQube `complexity` | radon | Meaning |
|---|---|---|---|
| `no_branch.py`: `return x + 1` | 1 | 1 | Baseline is 1 |
| `if_elif.py`: `if x: … elif y: …` | 2 | 3 | **SonarPython counts an `if`/`elif` chain as one decision**; McCabe counts the `elif` as a second binary decision |
| `bool_ops.py`: `if a and b or c:` | 4 | 4 | Both tools count `and` and `or` as decisions |

Raw values: `evidence/raw/sonar-calibration-{trivial,ifelif,bool}.json`, `evidence/raw/sonar-calibration-counting-rules.txt`.

`get_status` has exactly one `elif` (`elif with_started`, node 5). SonarQube therefore reports 8 − 1 = **7**; standard McCabe (hand calc and radon) reports **8**. SonarQube's cognitive complexity of 8 reflects the separate `elif` and the nested `if` (if +1, nested if +2, elif +1, four later ifs +4 = 8). This is a **counting-convention difference, not a disagreement about the control flow**. For Phase 5 MCC/MC-DC we use V(G) = 8, the true graph complexity; for CI trend thresholds we use SonarQube's 7 so the tool's own baseline is consistent. Early `return`s do not add decisions in either convention — each is just an edge to the common EXIT node.

At file level, radon's function-only sum for `models.py` is 282 (100 functions) against SonarQube's 232 (100 functions); part of that gap is the `elif` rule above (12 `elif`s in the file), and the rest is other construct-level counting differences. That file-level gap is recorded here for transparency; the required function-level comparison is the one in the table above.

## 5. Coverage now and the re-run after Phase 5

Coverage is 0.0% because our tests do not exist yet (Phase 5). The scanner's "Zero Coverage Sensor" correctly reports 10,733 uncovered lines. This is the **baseline**, not a target. After Phase 5:

1. Generate `coverage.xml` from pytest-cov (raw HTML + XML kept).
2. Add `sonar.python.coverage.reportPaths=coverage.xml` to `sonar-project.properties`.
3. Re-run the scanner and append a dated update to §2 with the new coverage, bugs, vulnerabilities and ratings. The 0.0% row stays as the baseline.

## 6. Reproduce

```powershell
# Main scan (SonarQube must be running on :9000)
docker run --rm -v "D:\University Assignments\SQE Project\healthchecks:/usr/src" -w /usr/src `
  -e SONAR_HOST_URL=http://host.docker.internal:9000 -e SONAR_TOKEN=<token> `
  sonarsource/sonar-scanner-cli

# Pull the same numbers used in §2
curl.exe -u admin:admin -s "http://localhost:9000/api/measures/component?component=sqe-healthchecks&metricKeys=ncloc,complexity,cognitive_complexity,duplicated_lines,duplicated_lines_density,code_smells,bugs,vulnerabilities,security_hotspots,coverage,lines_to_cover,sqale_index,sqale_debt_ratio,reliability_rating,security_rating,software_quality_maintainability_rating,alert_status"

# Rebuild the CFG image from the text source
& "C:\Program Files\Graphviz\bin\dot.exe" -Tpng evidence\cfg-get-status.dot -o evidence\cfg-get-status.png

# Independent complexity cross-check
.venv\Scripts\python.exe -m radon cc hc/api/models.py -s
```

Calibration projects (`sqe-calib-getstatus`, `sqe-calib-trivial`, `sqe-calib-ifelif`, `sqe-calib-bool`) were each scanned with the same scanner image and a minimal `sonar-project.properties` pointing at the corresponding file in `evidence/calibration/`.

## 7. Limitations

- SonarQube Community 26.11 does not expose per-function metrics through its API; the calibration scan is the documented way we obtained a tool number for `get_status`.
- SonarQube's 87 vulnerabilities are source findings, not a dependency audit — `pip-audit` is still due in Phase 10.
- Excluded upstream tests and vendor JS are out of scope; our own tests live in `tests/team/` and are not scanned as production code.
- The manual dashboard screenshot (member-owned) supports the API evidence; it is never a substitute for the raw JSON.
