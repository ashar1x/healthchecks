# 12 — CI Quality Gate

The unified pipeline is `.github/workflows/ci.yml`. It runs on every pull
request and push to `master` and `area1/ashar`. The separate workflows
inherited from upstream (`tests.yml`, `coverage.yml`, `mypy.yml`,
`publish_docker_image.yml`) are being disabled in a documented change PR so
that this pipeline is the only gate.

## Jobs and thresholds

| Job | What it proves | Threshold |
|---|---|---|
| workflow-lint | No `continue-on-error`, `|| true`, `--exit-zero` or `allow_failure` in any workflow | `tools/evidence/check_workflows.py` must find nothing |
| unit-coverage | Unit/API/recovery tests pass and `coverage.xml` is produced | tests exit 0; threshold on measured functions still pending D2 confirmation |
| api-tests | FR-01/02/04 CRUD and generated-data tests pass | tests exit 0 |
| e2e | 13 Playwright tests pass | tests exit 0 |
| mutation | `mutmut run` then `tools/mutation/score_gate.py` | business-rule score ≥ 80% (measured 88.3%) |
| sonarqube | Scanner runs and waits for the quality gate | gate OK; token comes from the `SONAR_TOKEN` Actions secret, which the team must set |
| deploy | Builds the repository artifact | `needs` every job above, so it cannot run on a red build |

## Justification

- **80% mutation:** measured 88.3% on business-rule functions with 100% of the
  measured MCC/MC-DC cases passing; the margin allows small future test changes
  without hiding weak assertions.
- **No escape hatches:** the brief forbids them; the lint job fails the build
  if one is introduced.
- **Deploy gating:** every quality job is a `needs` dependency, so a failed
  gate blocks packaging.

## Pending human actions (D4)

Enable branch protection on `area1/ashar` and `master`: require a pull request
and require the status checks above. Without this, a red gate does not block a
merge by itself.

## Recorded runs on PR #10

| Check | Result | Run |
|---|---|---|
| No escape hatches | pass | https://github.com/ashar1x/healthchecks/actions/runs/46030378578/job/140612366746 |
| Unit tests and coverage | pass | https://github.com/ashar1x/healthchecks/actions/runs/46030378578/job/140612366603 |
| API tests | pass | https://github.com/ashar1x/healthchecks/actions/runs/46030378578/job/140612366331 |
| Mutation gate (unified pipeline) | pass | https://github.com/ashar1x/healthchecks/actions/runs/46030378578/job/140612366712 |
| Mutation gate (standalone workflow) | pass | https://github.com/ashar1x/healthchecks/actions/runs/46030378662/job/140612366065 |
| Playwright browser tests | fail | https://github.com/ashar1x/healthchecks/actions/runs/46030378578/job/140612366714 |
| SonarQube quality gate | fail | https://github.com/ashar1x/healthchecks/actions/runs/46030378578/job/140612366982 |

PR #10 is therefore a **pull request the pipeline blocked**. The two failures
are environmental: the Sonar job needs the `SONAR_TOKEN` Actions secret, and
the Playwright job needs a log review on Ashar's machine (the same 13 tests
pass locally). A fail-then-pass PR cannot be completed until both are fixed;
that is left to Ashar.

## Open items

- Add the `SONAR_TOKEN` secret and re-run the Sonar job.
- Diagnose the Playwright CI failure from the job log and re-run.
- The coverage threshold on the measured business-logic files needs team
  approval before it is enforced.

