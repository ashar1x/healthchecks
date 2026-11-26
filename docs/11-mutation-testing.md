# 11 — Mutation Testing and CI Quality Gate (Phase 8)

## 1. Tool and Configuration

**Tool:** `mutmut` 3.8.1 (Python 3.12.3, pytest 9.2.0, pytest-django 4.14.0, Linux).
mutmut modifies the source, runs the team tests against each mutant, and
classifies a mutant as **killed** (a test failed) or **survived** (all selected
tests passed). It was chosen because it works with pytest/Django and exposes
per-mutant evidence and CI-friendly statistics.

**Measurement scope.** The source paths in `setup.cfg` are the two files named
as the Phase 5 measurement target in `docs/08-unit-testing.md §1` and
`.coveragerc`:

| File | Functions |
|------|-----------|
| `hc/api/models.py` | `get_status`, `get_grace_start`, `going_down_after`, `ping`, pause/resume data rules, `prune`, `create_flip` |
| `hc/api/decorators.py` | `authorize`, `authorize_read`, `cors` (API key / role checks) |

**Configuration (`setup.cfg`, mutmut 3.x keys — one list item per line):**

```ini
[mutmut]
source_paths = hc/
only_mutate =
    hc/api/models.py
    hc/api/decorators.py
mutate_only_covered_lines = true
pytest_add_cli_args_test_selection = tests/team/
also_copy =
    pytest.ini
    manage.py
    CHANGELOG.md
    templates/
    evidence/raw
```

- `source_paths = hc/` copies the whole package so the mutants can be imported
  (Django settings, URLconf). `only_mutate` restricts mutation to the two
  measured files; 653 other files are copied but ignored.
- `mutate_only_covered_lines = true` mutates only lines exercised by
  `tests/team/`. The rest of `models.py` is outside the Phase 5 scope and is
  defended line by line in `docs/08-unit-testing.md §5`.
- `pytest.ini`, `manage.py` and `CHANGELOG.md` must be copied into `mutants/`:
  without `manage.py`, pytest-django walks up to the original repo root and
  inserts it at `sys.path[0]`, so tests import **unmutated** code and no mutant
  is ever associated with a test.

## 2. Running Mutation Testing Locally (Linux)

```bash
cd /path/to/healthchecks
python3 -m venv mutmut_venv
source mutmut_venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install mutmut pytest pytest-django
mutmut run                       # ~30 min with --max-children 2
mutmut results                   # lists every mutant verdict
mutmut export-cicd-stats         # mutants/mutmut-cicd-stats.json
python tools/mutation/score_gate.py --no-gate
python tools/mutation/custom_operators.py
```

The earlier `BadTestExecutionCommandsException` from `pytest-randomly` is a
mutmut 2.x issue. With mutmut 3.x and no `pytest-randomly` in this venv the
suite runs unchanged; the CI workflow still uninstalls it as a safeguard.

### 2.1 CI Workflow (`.github/workflows/mutation.yml`)

Runs on every PR and push affecting the measured paths to `master` or
`area1/ashar`:

1. Checkout, Python 3.12, install `requirements.txt`, `requirements-dev.txt`,
   `mutmut`, `pytest`, `pytest-django`; remove `pytest-randomly`.
2. `mutmut run`, then `mutmut results` and `mutmut export-cicd-stats`.
3. `python tools/mutation/score_gate.py` enforces the **80% threshold** on the
   business-rule score and fails the job below it. No `continue-on-error` or
   `|| true` escape hatches.

**Why 80%:** Phase 5 reached 100% statement/branch coverage of the measured
logic, the `get_status` MCC table has 128 rows and 7 MC/DC pairs, BR-03 covers
every allowed/disallowed transition and BR-04 covers all six principals.
Below 80% therefore indicates weak assertions rather than untested code.

## 3. Results (run on 2026-11-26)

Command: `mutmut run --max-children 2` (resumed once after an interruption;
mutmut caches verdicts). Evidence: `evidence/mutation/mutmut-summary.json`.

| Metric | Result |
|--------|--------|
| Mutants generated | **365** (357 in `models.py`, 8 in `decorators.py`) |
| Killed | **310** |
| Survived | **52** |
| No tests / not checked | **3** |
| **Full-file mutation score** | **84.9%** (310 / 365) |
| **Business-rule score (gate)** | **88.3%** (203 / 230 measured mutants) |
| Team tests | **221 passed** |
| Gate threshold | 80% — **PASSED** on both scores |

The business-rule score is computed by `tools/mutation/score_gate.py`, which
selects only the mutants in the functions listed in §1. The full-file score
also includes serialisation helpers (`to_dict`, `channels_str`, `isostring`)
that are executed but intentionally not asserted by the unit suite.

## 4. Surviving Mutant Analysis

52 mutants survived. Full diffs for all of them are saved in
`evidence/mutation/survivor-diffs.txt` (generated with `mutmut show`). The
table below analyses 24 of them across every surviving function. Categories:
**E** equivalent in the exercised context, **M** missing test, **W** weak
assertion, **T** tool artifact (in-process module cache).

| Mutant | Mutation | Class | Justification / action |
|--------|----------|-------|------------------------|
| `x_cors__mutmut_1` | `set(methods)` → `None` | T | `cors(...)` runs at import time; mutmut's worker inherits the already-imported module, so the change is never executed. Not a test weakness. |
| `x_cors__mutmut_2` | `set(methods)` → `set(None)` | T | Same import-time module-cache artifact. |
| `x_cors__mutmut_3` | `.add("OPTIONS")` → `.add(None)` | T | Same artifact; no test can observe it in this process model. |
| `x_cors__mutmut_4` | `"OPTIONS"` → `"XXOPTIONSXX"` | T | Same artifact. A direct header assertion would kill it outside mutmut. |
| `x_cors__mutmut_5` | `"OPTIONS"` → `"options"` | T | Same artifact. |
| `x_cors__mutmut_6` | `methods_str` → `None` | T | Same artifact. |
| `x_cors__mutmut_7` | `", ".join(methods_set)` → `join(None)` | T | Same artifact. |
| `x_cors__mutmut_8` | separator `", "` → `"XX, XX"` | T | Same artifact. |
| `x_isostring__mutmut_1` | `if dt` → `if dt and False` | M | Tests only assert `last_ping is None`; no non-None timestamp is formatted. Add a ping round-trip assertion. |
| `x_isostring__mutmut_3` | `microsecond=0` → `microsecond=None` | M | Same missing non-None datetime witness. |
| `x_isostring__mutmut_4` | `microsecond=0` → `microsecond=1` | W | Needs an exact ISO string assertion for a datetime with microseconds. |
| `get_grace_start__mutmut_1` | `with_started=True` → `False` | M | All tests pass `with_started` explicitly; the default is never exercised. |
| `get_grace_start__mutmut_22` | `ZoneInfo(self.tz)` → `None` | E | Container local timezone is UTC, so the instant is unchanged (DST-sensitive in production). |
| `get_grace_start__mutmut_31` | `astimezone(utc)` → `astimezone(None)` | E | Same UTC-equivalence in this environment. |
| `get_grace_start__mutmut_32` | `kind == ... and status == "up"` → `or` | M | No test uses a cron/oncalendar check with a non-`up` stored status. |
| `get_grace_start__mutmut_41` | `ZoneInfo(self.tz)` → `None` (oncalendar) | E | UTC-equivalence. |
| `get_grace_start__mutmut_50` | `astimezone(utc)` → `astimezone(None)` | E | UTC-equivalence. |
| `get_grace_start__mutmut_51` | `result = NEVER` → `None` | E | Both values become `None` at the final `result != NEVER` guard. |
| `get_status__mutmut_1` | `with_started=False` → `True` | M | MCC tests always pass `with_started` explicitly. |
| `get_status__mutmut_17` | `with_started=False` → `None` | E | `None` is falsy; behaviour is identical. |
| `channels_str__mutmut_3` | `str(channel.code)` → `str(None)` | M | No test assigns a channel and asserts its code in the API payload. |
| `to_dict__mutmut_1` | `readonly=False` → `True` (default) | M | API always passes `readonly` explicitly; add a direct default-argument test. |
| `to_dict__mutmut_2` | `v=3` → `v=4` (default) | M | Same default not exercised by the API caller. |
| `ping__mutmut_79` | `"start"` → `"XXstartXX"` in kind list | W | State tests assert status/flip but not `Ping.kind`; add `assert ping.kind == "start"`. |
| `ping__mutmut_93` | `len(body) > 100 and S3_BUCKET` → `or` | M | No S3 bucket in the test environment; branch needs a test double. |

**Killable survivors already fixed.** The first full run had 120 survivors,
dominated by `to_dict` (57) and `clamped_last_duration`. The new
`tests/team/unit/test_api_payload.py` (exact API read-back of every field) and
three exact `>=` boundary tests in `test_get_status_edges.py` killed 68 of
them. The remaining survivors are predominantly equivalent or tool artifacts;
the genuinely missing tests need S3/channel fixtures and are recorded as
residual risk rather than silently ignored.

## 5. Manual Fallback Checklist

Not used — mutmut ran successfully. The five BR checks in the original
fallback checklist remain satisfied by `test_validation_bva.py`,
`test_get_status_mcc.py`, `test_ping_state_machine.py`,
`test_decorators_auth.py` and the absence of `pragma: no cover` in the
measured files.

## 6. Custom Mutation Operators

Two operators derived from the business rules are implemented in
`tools/mutation/custom_operators.py` (each mutant is applied, the relevant
tests run, and the source restored):

1. **BoundaryValueOperator (BR-01)** — `AddCheckForm.timeout`/`grace`
   `min_value=60` → 59/61 and `max_value=31536000` → 31535999/31536001
   (8 mutants).
2. **BooleanNegationOperator (BR-02/BR-03)** — in `get_status`,
   `get_grace_start` and `ping`: negate conditions, flip `>=`/`==`, swap
   `and`/`or`, change `min()` → `max()` (12 mutants).

**Result: 20/20 killed (100%).** Evidence:
`evidence/mutation/custom-operators.json`. The three comparison mutants
(`>=` → `>`) were initially survived; they are now killed by the exact
boundary tests added in §4.

## 7. Phase 8 Status Tracking

| Component | Done | By | Notes |
|-----------|------|----|-------|
| `docs/11-mutation-testing.md` | ✅ | Ashar / Ali | Documentation + executed results |
| `.github/workflows/mutation.yml` | ✅ | Ashar / Ali | 80% gate, corrected for mutmut 3.x |
| `setup.cfg` | ✅ | Ashar / Ali | mutmut 3.x config, measured scope |
| Manual fallback checklist | ✅ | Ashar | Not needed |
| Mutation score | ✅ | Ali | 84.9% full / 88.3% business-rule |
| Custom operators | ✅ | Ali | 20/20 killed |
| Surviving-mutant analysis (≥15) | ✅ | Ali | 24 analysed in §4 |
| CI quality gate auto-validate | ✅ | Ali | PR to `area1/ashar` |

## 8. Next Steps

1. Merge PR `ali-phase8-mutation` → `area1/ashar`; CI revalidates the gate.
2. Phase 9: Node.js/Playwright Lighthouse and axe-core tests (Ali).

## 9. Revision History

| Date | Change |
|------|--------|
| 2026-11-26 | Initial Phase 8 documentation created (Ashar) |
| 2026-11-26 | Executed mutmut 3.8.1 on Linux; recorded 84.9%/88.3% scores, 24 survivor analyses, custom operators 20/20; fixed CI workflow and added API payload / boundary tests (Ali) |
