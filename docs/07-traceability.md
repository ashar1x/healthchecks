# 07 — Traceability

Owner: Taimoor Khaliq (24i-3052). Status: **DRAFT for the Phase 4 team call** (2026-11-23).
Machine-readable matrix: `docs/07-traceability.csv`. Coverage script: `tools/traceability/coverage.py` (writes `evidence/raw/requirements-coverage.json`).

## 1. Direction of traceability

`FR (docs/01 §5)` → `BR (docs/01 §6)` → `RISK (docs/05)` → `test IDs (tests/team/)` → `defect IDs (GitHub Issues / docs/17-defects/)`.
Forward (requirement → test) proves every requirement is tested; backward (defect → risk → requirement) shows which risk a failure threatens. Test **names** carry FR and BR IDs (e.g. `test_FR10_BR02_grace_boundary_up`), so coverage is computed by a script from source, never counted by hand.

## 2. Matrix (summary — full CSV is authoritative)

| FR | Rule(s) | Risk(s) | Planned test IDs | Owner |
|---|---|---|---|---|
| FR-01 Create check | BR-01, BR-04 | RISK-05, RISK-07 | T-API-FR01-01, T-UC01-01 | Taimoor |
| FR-02 Edit check | BR-01 | RISK-05 | T-API-FR02-01, T-UC03-01 | Taimoor |
| FR-03 Pause/resume | BR-04, BR-03 | RISK-03, RISK-02 | T-API-FR03-01, T-UC02-01 | Taimoor |
| FR-04 Delete check | BR-04 | RISK-03 | T-API-FR04-01 | Taimoor |
| FR-05 List/fetch scoped to project | BR-04 | RISK-03, RISK-04, RISK-09 | T-API-FR05-01, T-UC05-01 | Taimoor |
| FR-06 Reject invalid timeout/grace | BR-01 | RISK-05 | T-API-FR06-01, T-UNIT-BR01-01 | Taimoor |
| FR-07 Success ping sets up | BR-03 | RISK-06, RISK-15 | T-API-FR07-01, T-UC04-01 | Taimoor |
| FR-08 Start + success records duration | BR-03 | RISK-15 | T-API-FR08-01 | Taimoor |
| FR-09 Fail ping sets down | BR-03 | RISK-06, RISK-15 | T-API-FR09-01, T-UC06-01 | Taimoor |
| FR-10 Derived status at grace boundary | BR-02 | RISK-01, RISK-08 | T-UNIT-BR02-01, T-API-FR10-01 | Ashar |
| FR-11 Paused + manual_resume rule | BR-03 | RISK-02 | T-UNIT-BR03-01, T-API-FR11-01, T-UC02-01 | Ashar |
| FR-12 Unknown UUID / bad key | BR-04 | RISK-09, RISK-04 | T-API-FR12-01 | Taimoor |

The `defect_ids` column is empty now; Ali (defect triage) fills it as GitHub Issues are opened, and the weekly report uses it for defect density and reopen rate.

## 3. Requirements coverage computation

```powershell
.venv\Scripts\python.exe tools\traceability\coverage.py
# with executed (passing) test results:
.venv\Scripts\python.exe tools\traceability\coverage.py --pytest-report evidence\raw\pytest-report.json
```

The script:
1. reads FR and BR IDs from `docs/01-scope-and-test-basis.md`;
2. reads every row of `docs/07-traceability.csv` and validates that all referenced FR/BR/RISK IDs resolve (RISKs against `docs/05-risk-register.md`);
3. scans `tests/team/**/test_*.py`, extracts each `def test_…` with its immediate decorators, and records the FR/BR IDs in that name;
4. if a pytest JSON report is supplied, counts only **passed** tests for executed coverage;
5. writes the untouched raw result to `evidence/raw/requirements-coverage.json`.

Planned coverage = FRs with ≥1 test definition / 12. Executed coverage = FRs with ≥1 passing test / 12 (reported as "not available" until a pytest report exists — no number is invented).

**Current state:** no tests under `tests/team/` yet (Phase 5/7 pending), so planned and executed coverage are 0/12. The command exits 0 when the matrix is internally valid and prints `OK: ... IDs resolve`; it exits non-zero on a dangling ID. This is an intentional pre-test baseline, not a passed exit criterion.

## 4. Maintenance rule

When a test is written, its name must contain the FR and BR IDs from its matrix row, and the row's `test_ids` and `status` are updated (planned → implemented → passing). When a defect is filed, its row links the Issue ID. No row is deleted: a dropped requirement becomes status `deferred` with a reason recorded in `docs/19-completion-report.md`.
