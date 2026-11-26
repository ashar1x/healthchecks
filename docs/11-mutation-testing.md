# 11 — Mutation Testing and CI Quality Gate (Phase 8, Area 1, 8 marks)

> **Goal:** verify that the test suite detects injected faults (mutants); establish a
> CI quality gate that blocks merges when mutant survival exceeds a threshold.

## 1. Mutation testing tool

The master prompt Phase 5 rule 5 states: *"For every uncovered line or branch write a
justification (dead code, framework glue, unreachable). Prefer fewer exclusions.
No `# pragma: no cover` without a matching note."*

### 1.1 `mutmut` (recommended)

- **Package:** `mutmut` (PyPI)
- **Default executor:** `mutmut run` then `mutmut results`
- **Windows / WSL status:** *Native Windows support is tracked in*
  <https://github.com/boxed/mutmut/issues/397>.  The tool exits with the
  message: *"To run mutmut on Windows, please use the WSL."*
- **Docker workaround:**  Docker can install `mutmut` inside a container
  (`docker run --mount type=bind,src=./,dst=/workdir ...`), but the
  container runtime (`runc`) fails to execute `mutmut` unless WSL 2 is
  available on the host.  The error is:
  ```
  WSL (7) ERROR: UtilBindVsockAnyPort:... socket failed 1
  ```
- **Decision:** *Phase 8 mutation testing is deferred until WSL or an
  alternative mutator is available.*  The CI quality gate (section 2) is
  documented regardless, so the pipeline schema exists for when the mutator
  becomes Windows-compatible.

### 1.2 Alternative: manual fault injection

As a stop-gap, the team can implement a *manual* mutant selector that
inverts a small, curated set of Boolean sub-expressions in the measured
files (`hc/api/models.py`, `hc/api/decorators.py`).  Each mutant is a
single‑bit flip in a condition that feature tests already cover.  The
pipeline can count "survivors" (tests that pass despite the fault) and
report the score as *0% mutation killed* until the test assertions are
strengthened.  This approach satisfies the *CI quality gate* requirement
without requiring `mutmut` Windows support.

## 2. CI quality gate

The CI pipeline (GitHub Actions, Azure Pipelines, or GitLab CI) should
include a job named `mutation-test` that:

| Step | Command (once `mutmut` is Windows‑compatible) | Purpose |
|------|---------------------------------------------|---------|
| **install** | `pip install mutmut coverage` | ensure the mutator and coverage runner are available |
| **mutate** | `mutmut run --paths-to-mutate hc/api/ hc/accounts/ hc/front/` | generate mutants (one at a time, in‑process) |
| **test** | `python -m pytest tests/team/ -q --tb=short` | run the full team test suite |
| **results** | `mutmut results --show-surviving` | display which mutants survived |
| **gate** | `mutmut results --fail-under=80` | fail the job if >20% of mutants survive |

**Gate rationale:** 80% mutation killing is a common minimum for
production‑critical Django projects.  Below that threshold the test suite
is considered *insufficient* to catch regressions, and the PR should be
blocked until the test suite is strengthened.

If `mutmut` cannot run (WSL not available), the gate falls back to a
**manual checklist**:

- [ ] All `BR‑01` boundary tests exercise the `timeout`/`grace` `min`/`max` edges
- [ ] All `BR‑02` MCC/MC/DC rows from `docs/08` §3 are represented in `tests/team/`
- [ ] All `BR‑03` state‑transition tests cover every allowed/disallowed transition
- [ ] All `BR‑04` role/key tests cover owner, rw member, ro member, rw key, ro key, unauthenticated
- [ ] No `# pragma: no cover` directives exist in the measured files without a matching note in `docs/08` §5

## 3. Deliverable for Phase 8

| Artifact | Location | Status |
|----------|----------|--------|
| Mutation testing documentation | `docs/11-mutation-testing.md` | ✅ Created (section 1‑2) |
| CI quality‑gate schema (YAML/JSON) | `.github/workflows/mutation.yml` (or equivalent) | ❌ Blocked until Windows‑compatible mutator available |
| Manual fault‑injection checklist | `docs/11-mutation-testing.md` §2.2 | ✅ Created |
| Mutation score badge (future) | `README.md` or `docs/11-mutation-testing.md` | ❌ Pending |

**Next steps to unblock Phase 8:**

1. **Install WSL 2** on the development machine (per the master prompt §12:
   "WSL assumed, absent" — but the user can install it).
2. **Re‑run `mutmut`** on the measured files and record the mutation score.
3. **Commit the CI workflow** `.github/workflows/mutation.yml` with the gate
   configuration.
4. If WSL is truly impossible, **replace `mutmut` with a manual fault‑injection
   script** that flips one Boolean at a time in `hc/api/models.py` and
   `hc/api/decorators.py`, and document the resulting "0% killed" status with
   a plan to strengthen the test suite (which is the actual goal of Phase 8
   anyway — *strengthen tests, not just run a tool*).

## 4. Mutation‑score target for this project

Given the current test suite (215 tests, 0 failures) and the measured files
(`hc/api/models.py`, `hc/api/decorators.py`), a realistic initial target
is **70% mutation killed**.  The 30% survivors would correspond to the
deliberate exclusions documented in `docs/08-unit-testing.md` §5 (form fields,
views, boilerplate).  As those exclusions are justified and potentially
reduced, the target can be raised to **80%**.

## Revision history

| Date | Change |
|------|--------|
| 2026‑11‑24 | Documentation drafted; `mutmut` installed but Windows‑incompatible; CI gate schema drafted; manual fallback described. |
| 2026‑11‑24 (future) | WSL installation → `mutmut` run → mutation score recorded → CI gate activated. |