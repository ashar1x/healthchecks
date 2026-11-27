# Live-task change map

The viva gives a business-rule change or an updated API spec. Predict which
tests and gate fail, make the change, show the result.

| Change | Code location | Unit tests | API tests | E2E tests | CI gate that fails |
|---|---|---|---|---|---|
| Flip `>=` to `>` in `Check.get_status` grace end | `hc/api/models.py:get_status` | `test_get_status_mcc.py`, `test_get_status_edges.py` (exact-boundary tests) | BVA read-back in `test_validation_bva.py` | keyboard/BR-01 flow | mutation gate: custom `BooleanNegationOperator` targets this exact comparison |
| Change timeout minimum 60 → 59 | `hc/front/forms.py:AddCheckForm` | `test_validation_bva.py` 3-point cases | `tests/team/api/test_crud.py`, generated data from `spec/openapi.yaml` | BR-01 rejection/correction test | mutation gate (BR-01 boundary operator), API tests |
| Change role check so read-only keys may pause | `hc/api/decorators.py:authorize` | `test_decorators_auth.py` | `tests/team/api/` role tests | `access-control.spec.js` | mutation gate and workflow-lint do not catch this; API/E2E jobs fail |
| Change spec constraint (e.g. max timeout) | `spec/openapi.yaml` | `test_validation_bva.py` after regeneration | generator output changes (`tools/testgen/generator.py`) | BR-01 upper-bound flow | API job fails on regenerated data |

Rehearsal 1 (comparison flip): run the MCC test before and after the edit; the
exact-boundary test must fail with `down` expected and `grace` observed.
Rehearsal 2 (spec change): run the generator, diff `spec/test_data.json`, then
run the API tests and report which new boundary case fails.
