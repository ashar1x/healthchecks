# 09 — API and integration testing

The FR-tagged API tests are in `tests/team/api/test_crud.py`, with role and
boundary tests in `tests/team/unit/test_decorators_auth.py` and
`test_validation_bva.py`. Generated data comes from `tools/testgen/generator.py`
and `spec/test_data.json`. Endpoint weaknesses are filed as GitHub Issues
(#6–#9) and linked in `docs/13-security.md` and `docs/19-completion-report.md`.
Requirements coverage: 12/12 FR = 100%, computed by
`tools/traceability/coverage.py` into `evidence/raw/requirements-coverage.json`.
