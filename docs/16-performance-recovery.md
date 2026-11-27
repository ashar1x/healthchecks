# 16 — Performance and recovery

Canonical report: `docs/15-performance.md`; k6 script `tests/k6/load.js` with
raw runs in `evidence/performance/`; recovery test `tests/team/test_recovery.py`.
Worst p95 across four runs: 143.1 ms against a 500 ms limit; 0 unexpected failures.
