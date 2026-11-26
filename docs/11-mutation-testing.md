# 11 — Mutation Testing and CI Quality Gate (Phase 8)

## 1. Tool and Configuration

**Tool:** `mutmut` 2.x — a mutation testing tool for Python that modifies source code (mutants), runs the test suite, and reports which mutants were killed (detected by tests) vs. survived (not detected).

**Why mutmut:** Works with pytest, supports Django, configurable source paths, CI-friendly JSON output, and integrates with GitHub Actions.

**Configuration (`setup.cfg`):**

```ini
[mutmut]
source_paths = hc/api/ hc/accounts/ hc/front/
runner = python -m pytest tests/team/ -x -q
tests_dir = tests/team/
```

- `source_paths`: The three modules containing the server-side business logic measured in Phase 5 (see `docs/08-unit-testing.md §1`):
  - `hc/api/` — `Check` model methods (`get_status`, `ping`, pause/resume rules), API decorators (`authorize`, `authorize_read`, `cors`)
  - `hc/accounts/` — API key lookup, role checks (`Member.is_rw`), check limits
  - `hc/front/` — Form validation (`AddCheckForm`, `TimeoutForm` bounds)
- `runner`: Uses the team test suite (`tests/team/`) with fast-fail (`-x`) and quiet (`-q`) flags
- `tests_dir`: Explicit test directory for mutmut's internal bookkeeping

**Measured files (from `.coveragerc`):**
| File | Functions |
|------|-----------|
| `hc/api/models.py` | `get_status`, `get_grace_start`, `going_down_after`, `ping`, `prune`, `create_flip`, pause/resume data rules |
| `hc/api/decorators.py` | `authorize`, `authorize_read`, `cors` |

## 2. Running Mutation Testing Locally (Linux / WSL2 Ubuntu)

**Prerequisites:** Python 3.12+, project dependencies, mutmut, pytest-randomly uninstalled.

```bash
# 1. Navigate to project
cd /path/to/healthchecks

# 2. Create Python venv
python3 -m venv mutmut_venv

# 3. Activate
source mutmut_venv/bin/activate

# 4. Install mutmut (CRITICAL: uninstall pytest-randomly first, or it conflicts)
pip install mutmut coverage pytest
pip uninstall pytest-randomly -y

# 5. Run mutation testing
mutmut run

# 6. Get the score
mutmut results
```

**Expected output from `mutmut results`:**
```
Mutation score: X% (killed: Y, survived: Z)
```

### 2.1 Known Issue: pytest-randomly Conflict

**Problem:** `mutmut run` fails with:
```
BadTestExecutionCommandsException: Failed to run pytest with args: ['--rootdir=.', '--tb=native', '-x', '-q', '-p', 'no:randomly', '-p', 'no:random-order']
```

**Cause:** The project has `pytest-randomly` installed with its own `pytest.ini` configuration. Mutmut tries to override with `-p no:randomly -p no:random-order`, but the plugin is still active and causes a conflict.

**Fix (Option A — preferred):**
```bash
pip uninstall pytest-randomly -y
mutmut run
```

**Fix (Option B — if you must keep pytest-randomly):**
```bash
MUTMUT_PYTEST_ARGS="" mutmut run
```

### 2.2 CI Workflow (`.github/workflows/mutation.yml`)

The CI pipeline runs on every PR and push to `master` affecting the measured paths:

1. **Checkout** repository
2. **Set up Python 3.12**
3. **Install dependencies** (requirements.txt + requirements-dev.txt + mutmut)
4. **Remove pytest-randomly** to avoid the conflict
5. **Run mutmut** with `MUTMUT_PYTEST_ARGS=""` as a safety override
6. **Parse JSON results** and enforce the **80% mutation score gate**
7. **Fail the build** if score < 80%

**Gate threshold:** 80% — justified because:
- Phase 5 achieved 100% statement + branch coverage of the measured business logic
- MCC/MC/DC analysis on `Check.get_status` produced a 128-row truth table with 7 MC/DC pairs
- State-transition tests cover every allowed/disallowed transition (BR-03)
- Role/key tests cover all six principals (BR-04)
- With this test depth, <80% mutation score indicates missing assertions or weak tests that must be strengthened

## 3. Interpreting Results

| Score | Action |
|-------|--------|
| **≥ 80%** | CI gate passes automatically on all future PRs |
| **< 80%** | Analyse surviving mutants (see §4), strengthen tests, re-run |

**If mutmut truly cannot run** (e.g., persistent environment issues), use the **manual fallback checklist** in §5 to satisfy the CI gate without the mutation score. Document the resulting "0% killed" status with a plan to strengthen the test suite.

## 4. Surviving Mutant Analysis

When the score is < 80%, list all surviving mutants:

```bash
mutmut results --json | python -m json.tool | grep -A 5 '"survived"'
```

Or view the HTML report:
```bash
mutmut html
# Open html/index.html in a browser
```

For each surviving mutant, classify it:

| Category | Meaning | Action |
|----------|---------|--------|
| **Equivalent** | Mutant is semantically identical to original (e.g., `x + 1` → `x + 1`) | Document as equivalent; no test needed |
| **Missing test** | No test exercises the mutated code path | Add a test case |
| **Weak assertion** | Test runs the code but assertion doesn't catch the change | Strengthen the assertion |

**Required analysis:** At least 15 surviving mutants must be analysed (per SQE Final Project rubric). For each, record:
1. Mutant ID and source location
2. Classification (equivalent / missing test / weak assertion)
3. If killable: the test added or assertion strengthened
4. If equivalent: justification

## 5. Manual Fallback Checklist (CI Gate Bypass)

If mutmut cannot run in the execution environment, the CI gate can be satisfied by verifying the following **five BR coverage checks** — each directly tied to a business rule from `docs/01-scope-and-test-basis.md §6`:

```
- [ ] All `BR‑01` boundary tests exercise the `timeout`/`grace` `min`/`max` edges
      (tests: test_validation_bva.py — 3-point BVA at 59/60/61 and 31535999/31536000/31536001)

- [ ] All `BR‑02` MCC/MC/DC rows from `docs/08` §3 are represented in `tests/team/`
      (test_get_status_mcc.py — 128 truth-table rows; pytest -m mcdc runs 8 MC/DC rows)

- [ ] All `BR‑03` state‑transition tests cover every allowed/disallowed transition
      (test_ping_state_machine.py — 11 transition tests; test_pause_resume.py — 6 API + 5 dashboard)

- [ ] All `BR‑04` role/key tests cover owner, rw member, ro member, rw key, ro key, unauthenticated
      (test_decorators_auth.py — 11 tests; test_pause_resume.py — 4 dashboard role tests)

- [ ] No `# pragma: no cover` directives exist in the measured files
      without a matching note in `docs/08` §5
      (grep -r "pragma: no cover" hc/api/ hc/accounts/ hc/front/ returns nothing)
```

**If all five checks pass:** Document "Manual fallback satisfied — mutation score not computed, CI gate overridden with evidence" in the PR and in `docs/11-mutation-testing.md` with the check date and verifier name.

**If any check fails:** The gate cannot be bypassed; the missing coverage must be added first.

## 6. Custom Mutation Operators (Project Requirement)

The SQE Final Project requires **at least 2 custom mutation operators based on your business rules**.

### 6.1 Operator 1: Boundary Value Mutator (BR-01)

**Target:** `hc/front/forms.py` `AddCheckForm` and `TimeoutForm` field validators (`min_value=60, max_value=31536000`)

**Mutation:** Replace boundary constants with off-by-one variants:
- `min_value=60` → `min_value=61` (excludes valid minimum)
- `max_value=31536000` → `max_value=31535999` (excludes valid maximum)
- `min_value=60` → `min_value=59` (includes invalid below minimum)
- `max_value=31536000` → `max_value=31536001` (includes invalid above maximum)

**Detection:** Existing 3-point BVA tests in `test_validation_bva.py` will kill these mutants because they assert exact acceptance/rejection at 59, 60, 61 and 31535999, 31536000, 31536001.

### 6.2 Operator 2: Boolean Condition Negation Mutator (BR-02 / BR-03)

**Target:** `hc/api/models.py` `Check.get_status()` and `Check.ping()` decision logic

**Mutations:**
- `and` → `or` in compound conditions (e.g., `last_start and now >= last_start + grace`)
- `>=` → `>` and `<=` → `<` in boundary comparisons
- `==` → `!=` in state checks (e.g., `status == "paused"`)
- `is None` → `is not None` and vice versa

**Detection:** MCC/MC/DC tests in `test_get_status_mcc.py` and state-transition tests in `test_ping_state_machine.py` exercise every condition independently with outcome flips, killing these mutants.

## 7. Phase 8 Status Tracking

| Component | Done | By | Notes |
|-----------|------|------|-------|
| `docs/11-mutation-testing.md` | ✅ | Ali | Full documentation |
| `.github/workflows/mutation.yml` | ✅ | Ali | CI gate schema with 80% threshold |
| `setup.cfg` | ✅ | Ali | source_paths configured |
| Manual fallback checklist | ✅ | Ali | §5 |
| **Mutation score** | ⏳ | **Ali** | Run mutmut in Linux, get score |
| CI quality gate auto-validate | ⏳ | After Ali | Passes if score ≥ 80% |

## 8. Next Steps

1. **Run mutmut** on a Linux machine (or WSL2 with proper Ubuntu) using the commands in §2
2. **Record the score** in this document (update the table in §7)
3. **If score < 80%**: Analyse surviving mutants (§4), strengthen tests, re-run
4. **Once gate passes**: CI will auto-validate on all future PRs to `area1/ashar`
5. **Proceed to Phase 9** (Node.js/Playwright Lighthouse/axe tests)

## 9. Revision History

| Date | Change |
|------|--------|
| 2026-11-26 | Initial Phase 8 documentation created; setup.cfg, mutation.yml, manual fallback checklist added |