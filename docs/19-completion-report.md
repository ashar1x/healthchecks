# Test completion report

**Date:** 2026-11-27. **Build:** `area1/ashar` plus the uncommitted final-package branch; baseline tag remains on the imported upstream commit.

## 1. Tested

- White-box: 225 pytest tests in `tests/team/unit/`, `api/` and `test_recovery.py`; MCC 128 rows and 7 MC/DC pairs for `Check.get_status`; BR-01..BR-04 exercised.
- API/data: generated EP/BVA data from `spec/openapi.yaml`; CRUD and role/BVA tests read back shared records. Requirements coverage 12/12 FR (100%, 67 test functions).
- Mutation: 365 mutants, 310 killed, 52 survived, 3 undetected; 84.9% full-file and 88.3% business-rule; 2 custom operators, 20/20 killed; 24 survivors analysed.
- Browser/a11y: 13 Playwright tests; Lighthouse checks 72→100, axe violations 8→2 on the fixed screen.
- Security: 5/5 access decisions, ZAP passive (498 alerts), pip-audit 0/54.
- Performance: 4 k6 runs (worst p95 143.1 ms, 0 failures); failure-and-recovery test passes.

## 2. Not tested or only partly tested

- Production deployment, real SMTP/S3, Postgres/MySQL concurrency (`select_for_update` is a no-op on the SQLite used locally).
- Active security scanning, fuzzing or any traffic outside localhost (forbidden by the brief).
- Vendored JavaScript upgrade and S3/network failure injection (open items).
- A unified CI gate with Sonar, E2E and deploy jobs is not yet in place.

## 3. Deviations from the plan

- ZAP ran as a local daemon because the Docker image pull failed; the scan was still passive and proxied through Playwright.
- Lighthouse used a storageState cookie header instead of a remote-debugging port.
- The recovery test doubles `create_flip` on pause rather than a DB write inside `Check.ping`.
- Our docs use numbering 11/12/13/15/16 where the master prompt asks for 12/13/14/15/16; alias documents will map them.

## 4. Open defects and residual risk

| Issue | Severity | Status | Residual risk |
|---|---|---|---|
| #6 DOMPurify | High | New | Release blocker until vendored asset is upgraded |
| #7 bare HTTP 400 | Medium | New | Usability; client-side BR-01 message covers the flow |
| #8 traceability 0% | High | Fix applied in this branch | Must be verified after CI refresh |
| #9 missing CSP | Low | New | Deployment configuration item |

RISK-01/02 (status logic) are mitigated by unit and mutation evidence; RISK-03/04 (access) by the access matrix; RISK-10 (accessibility) by the checks-screen fix; RISK-15 (traceability) by the regenerated 100% coverage.

## 5. Estimates versus actual effort

No member has logged hours in `docs/effort-log.csv`, so the variance against the 172.82 h estimate cannot be computed. This is an open item for Taimoor and the team before the viva; no hours have been invented here.

## 6. Recommendation

**HOLD** the release decision. The functional and quality evidence is strong, but issue #6 (High security finding) and the incomplete unified CI gate are release blockers. Should Ashar upgrade the vendored asset and the team complete the CI gate and effort log, the evidence supports changing this to RELEASE.
