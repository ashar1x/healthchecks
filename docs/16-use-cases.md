# 16 — Use Case Specification and Automation (Area 3)

The use case numbers below are fixed by `docs/01-scope-and-test-basis.md §8`.
Ali owns **UC-05** and **UC-06**; UC-01/UC-02 (Ashar) are automated in
`tests/e2e/create-check.spec.js` and `pause-resume.spec.js`, and UC-03/UC-04
(Taimoor) by the API/data-generation suite. This document completes the area-3
use case specification and maps every flow to an automated test.

## UC-05 — A read-only member manages checks and is denied writes

**Preconditions:** seeded project `SQE Test Project`; accounts
`owner@example.com` (rw) and `member-ro@example.com` (read-only); rw and ro API
keys from `scripts/seed.py`. **Postcondition:** the read-only principal can read
checks but cannot create, pause or resume any check.

| Flow | Steps | Expected outcome | Automated by |
|------|-------|------------------|--------------|
| Main | log in as read-only member, open the project checks list | checks are visible; write controls absent | `tests/e2e/access-control.spec.js` |
| Alt 1 | open a check's details screen | status and schedule are visible, no Pause button | `access-control.spec.js` |
| Alt 2 | call `GET /api/v3/checks/` with the ro API key | 200, check list returned | `tests/team/unit/test_decorators_auth.py` |
| Exc 1 | ro API key POSTs `/api/v3/checks/<code>/pause` | 401, no state change | `access-control.spec.js` |
| Exc 2 | attempt Add Check / Pause in the dashboard | button absent; no write route reachable | `access-control.spec.js` |

Evidence: `evidence/security/access-matrix.md` — 5/5 decisions PASS.

## UC-06 — Recover a failed check: fail ping, alert window, success ping

**Preconditions:** a seeded check with a known grace/timeout; controlled clock
(`time_machine`) for unit tests. **Postcondition:** after a failed dependency
or failed ping the state can be recovered with no duplicate flip or check.

| Flow | Steps | Expected outcome | Automated by |
|------|-------|------------------|--------------|
| Main | ping fail → display status `down` → ping success → `up` | status sequence new → down → up, exactly one flip per change | `tests/team/unit/test_ping_state_machine.py` |
| Alt 1 | fail while a `start` signal is active | running state ends, `last_start` cleared | `test_ping_state_machine.py` |
| Alt 2 | repeated pause of an already paused check | still paused, no second flip | `tests/team/unit/test_pause_resume.py`, `tests/e2e/use-cases.spec.js` |
| Exc 1 | `Check.create_flip` fails before writing (test double) | HTTP error, check unchanged, zero flips | `tests/team/test_recovery.py` |
| Exc 2 | resume a check that is not paused | 409 "check is not paused" | `tests/e2e/use-cases.spec.js`, `test_pause_resume.py` |

Evidence: `tests/team/test_recovery.py` (1 passed), Phase 5 unit suite
(221 passed before this phase, 222 with the recovery test).

## Phase 9/10 browser automation inventory

| Spec file | Tests | Purpose |
|---|---|---|
| `create-check.spec.js` | 3 | create + read-back, BR-01 rejection/correction, keyboard navigation |
| `pause-resume.spec.js` | 1 | resume → pause with API postcondition |
| `accessibility.spec.js` | 3 | axe scans of checks, modal, details (UC-05 surfaces) |
| `access-control.spec.js` | 1 | five access decisions for UC-05 |
| `use-cases.spec.js` | 5 | cron create, suggested slug, invalid timeout, idempotent pause, disallowed resume |

All browser tests use the seeded local app and the shared Playwright login
setup (`tests/e2e/auth.setup.js`). Every flow listed above has at least one
executable assertion, so the use case specification is traceable to evidence
rather than prose only.

## Revision history

| Date | Change |
|------|--------|
| 2026-11-27 | Area-3 use case specification and flow-to-test mapping added |
