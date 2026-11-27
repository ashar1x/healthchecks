# Viva notes

Each member must rerun one test and explain its assertions. The notes below
name the command and what a pass looks like.

| Test file | Command | What it checks | Pass looks like |
|---|---|---|---|
| `tests/team/unit/test_get_status_mcc.py` | `pytest tests/team/unit/test_get_status_mcc.py -q` | 128-row MCC truth table and 7 MC/DC pairs for `Check.get_status` | all rows pass; changing a `>=` to `>` fails a boundary row |
| `tests/team/unit/test_validation_bva.py` | `pytest tests/team/unit/test_validation_bva.py -q` | 3-point BVA at 59/60/61 and 31535999/31536000/31536001 | exact accept/reject at every point |
| `tests/team/api/test_crud.py` | `pytest tests/team/api/test_crud.py -q` | FR-01/02/04 create, update, delete with API read-back | 201/200/200 and the changed field visible in the list |
| `tests/team/test_recovery.py` | `pytest tests/team/test_recovery.py -q` | failure before a state-changing write, then retry | no flip after failure, exactly one after retry |
| `tools/mutation/custom_operators.py` | `python tools/mutation/custom_operators.py --dry-run` | 2 business-rule operators, 20 mutants | 20 named mutants listed; full run killed 20/20 |
| `tests/e2e/create-check.spec.js` | `npx playwright test tests/e2e/create-check.spec.js` | create check, BR-01 rejection/correction, keyboard submit | 3 pass, confirmation row visible |
| `tests/e2e/access-control.spec.js` | `npx playwright test tests/e2e/access-control.spec.js` | 5 access decisions across rw/ro roles | 5/5 PASS in `evidence/security/access-matrix.md` |
| `tests/e2e/lighthouse.js` | `node tests/e2e/lighthouse.js after` | Lighthouse on authenticated screens | JSON reports written; checks accessibility 100 |

The detailed prediction exercise is in `docs/viva/change-map.md`.
