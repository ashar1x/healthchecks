# RCA-02 — DEF-03: traceability coverage reported 0%

**Defect:** `evidence/raw/requirements-coverage.json` reported
`test_functions_found: 0` and `planned_coverage_pct: 0.0` because the JSON was
generated in Phase 4 before any tests existed and was never regenerated.

**Severity:** High. **Priority:** P1. **Status:** New (fix applied in this
branch). **Risk:** RISK-15; traceability rubric line (7 marks).
**Corrective action:** regenerate the JSON from the real test suite with
`pytest --json-report`; the fixed result is 12/12 FR = 100% executed coverage
from 67 test functions.
**Preventive action:** add the traceability computation to the CI gate so the
number is refreshed on every PR.

## 5 Whys

1. Why was coverage shown as 0%? The committed JSON was captured before Phase 5.
2. Why was it not refreshed? No step in the workflow re-ran
   `tools/traceability/coverage.py`.
3. Why did the script still work? Its discovery logic was correct; only its
   input evidence was stale.
4. Why was stale evidence accepted? The team treated the Phase 4 JSON as final
   rather than as a snapshot.
5. Why did this matter? The final report needs a real requirements-coverage
   number, and a 0% figure would be wrong and indefensible in the viva.

## Fishbone source

`docs/17-defects/rca-02-fishbone.dot`; regenerate with
`dot -Tsvg docs/17-defects/rca-02-fishbone.dot -o docs/17-defects/rca-02-fishbone.svg`.
