# Documented changes to the baseline

We imported the upstream Healthchecks commit tagged `baseline` and made no
silent edits to application source. Every change below went through a pull
request.

| Change | PR | Why |
|---|---|---|
| Phase 4 test-management documents | #1 | Added our own documents; no application code changed |
| Phase 8 mutation config, gate and tests | #3 | Fixed mutmut 3 configuration, added custom operators and stronger tests |
| Phase 9 browser/a11y tests and checks-screen fixes | #4 | Added tests and accessibility fixes to templates/CSS |
| Phase 10 security, performance and use-case tests | #5 | Added Area 3 scripts, docs and evidence |
| Final package (RCA, CI gate, viva notes, manifest, PDF) | #10 | Completed master-prompt phases 12–14 |
| Disable upstream workflows | this PR | `.github/workflows/ci.yml` is now the only gate; upstream workflows would run untuned matrices and publish images without our checks |

## Upstream workflows removed in this PR

- `tests.yml` — upstream matrix across four databases and four Python versions, not our test suite.
- `coverage.yml` — upstream Coveralls job with no threshold.
- `mypy.yml` — upstream type check with no relation to our rubric.
- `publish_docker_image.yml` — upstream image publishing without our quality gate.

No application behaviour is changed by this PR. The unified gate in
`ci.yml` runs our tests, mutation score, Sonar gate and artifact packaging.
