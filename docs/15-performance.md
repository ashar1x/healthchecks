# 15 — Performance and Recovery (Area 3)

## 1. Operation, targets and justification

**Operation:** `GET /api/v3/checks/` with the project's rw API key — the
read-back used by the create-check workflow.

**Targets fixed before testing:** p95 ≤ **500 ms**, unexpected failures
< **1 %** of requests. The endpoint is a small read-only JSON query over a
local SQLite database, so half a second is generous but still catches a
regression (the measured p95 is well below it); the 1 % failure ceiling allows
no unexpected errors for such a deterministic request.

## 2. Environment

- Local Django `runserver` (`DEBUG=True`), SQLite `hc.sqlite`, seeded with
  `scripts/seed.py`, 127.0.0.1:8000
- k6 v2.3.0, 4 vCPU / 3.7 GB RAM machine
- Same build, same machine, same starting data for all four runs
- Each run: 10 s ramp-up, **60 s at target VUs**, 5 s ramp-down

## 3. Workloads and results

| Setup | Run | VUs | Requests | Throughput | p95 | Failures | Target |
|---|---|---:|---:|---:|---:|---:|---|
| 1 user | 1 | 1 | 184 | 2.44 /s | 88.2 ms | 0 (0 %) | PASS |
| 1 user | 2 | 1 | 196 | 2.61 /s | 63.7 ms | 0 (0 %) | PASS |
| 5 users | 1 | 5 | 949 | 12.65 /s | 107.4 ms | 0 (0 %) | PASS |
| 5 users | 2 | 5 | 905 | 12.04 /s | 143.1 ms | 0 (0 %) | PASS |

Raw evidence: `evidence/performance/k6-{1v,5v}-run{1,2}.json` (summary) and
`.log` (full k6 output). Script: `tests/k6/load.js`. The worst p95 across all
runs is 143 ms — about 3.5× faster than the 500 ms limit — and no request
failed unexpectedly. Throughput scales from ~2.5 req/s to ~12 req/s when the
user count goes from 1 to 5, with a modest p95 increase, so the endpoint meets
both targets under the chosen workloads. These are local development-server
numbers and are not claimed as production capacity.

## 4. Controlled failure and recovery

**Operation:** pause a check (state-changing). The dependency test double
replaces `Check.create_flip` with a function that raises
`DependencyUnavailableError` *before* any write.

1. **Failure:** POST pause with the dependency unavailable → exception raised,
   no flip created, check still `new` (verified by refreshing from the DB).
2. **Restore:** remove the test double (monkeypatch context exits).
3. **Retry:** POST pause again → HTTP 200, status `paused`, exactly **one**
   flip recorded. No duplicate state change.

Test: `tests/team/test_recovery.py::test_FR03_BR03_pause_recovers_without_duplicate_flip`
— **1 passed**. This maps to RISK-06/RISK-15 (reliability of state-changing
operations) and complements the Phase 5 state-transition tests.

## 5. Residual risk

The local dev server and SQLite are single-node; the k6 results do not cover
concurrent writers, replication lag or a production web server. The recovery
test uses a narrow test double at the flip-creation seam, not a real S3 or
network outage; a production failure-injection run remains future work.

## 6. Revision history

| Date | Change |
|------|--------|
| 2026-11-27 | Initial performance and recovery evaluation: 4 k6 runs, controlled failure test |
