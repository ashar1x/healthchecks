# RCA-01 — DEF-01: vulnerable vendored DOMPurify asset

**Defect:** ZAP passive scan reports `Vulnerable JS Library` (High) on
`/static/js/purify.min.js` (`evidence/security/zap-alerts.json`).

**Severity:** High. **Priority:** P1. **Status:** New. **Risk:** RISK-03/RISK-04.
**Corrective action:** upgrade the vendored file from the upstream release.
**Preventive action:** add a dependency check for vendored JavaScript to the CI
workflow so a future vendored copy cannot drift.

## 5 Whys

1. Why is there a High alert? Because the vendored `purify.min.js` matches a
   known-vulnerable version.
2. Why is that version vendored? The upstream Healthchecks repository ships it
   under `static/js/`; we inherited it with the baseline commit.
3. Why was it not caught earlier? Our Phase 3 Sonar scan covered Python metrics
   and the first security work in Phase 11 came after the functional phases.
4. Why did Phase 11 catch it? ZAP passive scanning was added as a proxy in
   front of the Playwright workflows, so static assets were inspected.
5. Why is it still open? Upgrading a vendored asset changes upstream code and
   must go through a documented pull request with a failing check first.

## Fishbone source

`docs/17-defects/rca-01-fishbone.dot` is the text source. Regenerate with
`dot -Tsvg docs/17-defects/rca-01-fishbone.dot -o docs/17-defects/rca-01-fishbone.svg`.
