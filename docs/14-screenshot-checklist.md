# 14 — Screenshot Checklist for the Final PDF Report

> **Instructor rule (26 Nov 2026):** *"Wherever screenshots are required, you must
> perform the task yourself and capture the actual results. AI-generated screenshots
> or screenshots obtained through an AI agent performing the task on your behalf
> will result in ZERO MARKS for the corresponding requirement."*
>
> Every screenshot below must be captured by a **team member performing the task
> live**. No cropping, no annotation on the original. Full window, **URL bar and
> system clock visible**. Save originals to `evidence/screenshots/manual/`.
> If an annotated copy is wanted, keep the original beside it and label the copy.

## A. Manual screenshots — human performs the task (required)

| # | Screenshot | Rubric component (marks) | How to capture |
|---|------------|--------------------------|----------------|
| A1 | **SonarQube dashboard** — full window, URL + clock visible | Static analysis and metrics (5) | Open `http://localhost:9000` while analysis is loaded; full-window capture. API JSON in `evidence/raw/` stays the primary evidence. |
| A2 | **GitHub Actions run — mutation gate PASSED** (green tick, workflow name visible) | Mutation analysis and CI gate (8) | Open the Actions run for a PR touching `hc/`; full-window capture with URL + clock. |
| A3 | **GitHub PR correctly BLOCKED by the CI gate** (red X, required check failing) | Mutation analysis and CI gate (8) — *"a correctly blocked pull request"* is an explicit rubric item | Open a PR that fails the gate (e.g. a branch with a weakened test); full-window capture. Keep the PR open in the repo as evidence. |
| A4 | **Fail-then-pass fix run** — the failing run and the subsequent passing run | Mutation analysis and CI gate (8) — *"one fail-then-pass fix"* | Two captures: the red run before the fix, the green run after. |
| A5 | **Lighthouse score — BEFORE (checks screen)** — score panel 72 visible | Usability and accessibility (5) — before/after comparison | DevTools → Lighthouse → Accessibility/Best practices/SEO while logged in, or screenshot of the saved HTML report. Perform the run yourself. |
| A6 | **Lighthouse score — AFTER (checks screen)** — score panel 100 visible | Usability and accessibility (5) | Same as A5 after the fix. |
| A7 | **axe-core report — BEFORE (8 violations)** | Usability and accessibility (5) | Browser extension or the accessibility.dev report of the saved JSON; full window. |
| A8 | **axe-core report — AFTER (2 violations)** | Usability and accessibility (5) | Same as A7 after the fix. |
| A9 | **Checks screen — BEFORE accessibility fix** (the raw page as it was) | Usability and accessibility (5) | Log in at `127.0.0.1:8000`, open checks, capture before deploying the fix (use `git stash` / previous commit if needed). |
| A10 | **Checks screen — AFTER accessibility fix** (h1, labels, contrast visible) | Usability and accessibility (5) | Same screen after the fix. |
| A11 | **GitHub Issues list — defect log** (severity/priority labels visible) | Defect management and RCA (7) | Open the Issues tab; full-window capture with URL + clock. |
| A12 | **GitHub branch protection / required checks settings** | Mutation analysis and CI gate (8) — proves the gate cannot be bypassed | Repo → Settings → Branches; full-window capture with URL + clock. |

## B. Playwright screenshots — captured when YOU run the tests

Run `npm run test:e2e` yourself on your machine; the screenshots land in the
Playwright report/trace. The test run must be yours, not a teammate's copy of
the report.

| # | Screenshot | Rubric component (marks) | Source test |
|---|------------|--------------------------|-------------|
| B1 | **Check created confirmation** (UC1) | Use case test automation (6); Usability (5) | `create-check.spec.js` |
| B2 | **BR-01 rejection message** — "Must not exceed 365 days" | Use case test automation (6); Usability (5) | `create-check.spec.js` |
| B3 | **Corrected value succeeds after rejection** | Use case test automation (6) | `create-check.spec.js` |
| B4 | **Keyboard focus order** through required fields → submit | Usability and accessibility (5) — *"automated task and keyboard tests"* | `create-check.spec.js` (Tab navigation) |
| B5 | **Access denied / 403** for the denied role action | Defensive security (6) — at least one denied action | role/access test |
| B6 | **Paused → resumed → paused status read-back** (UC2) | Use case test automation (6) | `pause-resume.spec.js` |
| B7 | **Playwright HTML report — 7 passed summary** | Use case test automation (6) | `evidence/phase9/playwright-report/index.html` opened in a browser |

## C. Optional supporting screenshots (only if space allows)

| # | Screenshot | Rubric component | Note |
|---|------------|------------------|------|
| C1 | k6 run summary (p95, RPS, failed %) | Performance and recovery (5) | Raw k6 output is the primary evidence; screenshot is supporting only. |
| C2 | ZAP alert export summary | Defensive security (6) | Brief says *"an exported alert file, not a screenshot alone"* — export first. |
| C3 | Coverage HTML report (100% statement/branch) | White-box unit testing (16) | `evidence/coverage.html` screenshot is supporting; XML is primary. |
| C4 | Test-data generator producing 24 cases | Test data generation (7) | Terminal capture acceptable; `spec/test_data.json` is primary. |

## Rules recap

1. **Perform the task yourself** — the person who screenshots must be the one
   running the tool or the browser at that moment. AI agents must not produce
   these images (zero marks otherwise).
2. **Full window, URL + clock visible**, no cropping, no annotation on the
   original. Save to `evidence/screenshots/manual/`.
3. **Machine evidence first** — JSON, HTML reports and logs stay the primary
   evidence; screenshots are supporting (`evidence/manifest.csv` lists all items).
4. Each screenshot is cited in the PDF by its `evidence/manifest.csv` ID.

## Status

| Category | Count | Done |
|----------|-------|------|
| A — manual (required) | 12 | ⬜ |
| B — Playwright (run tests yourself) | 7 | ⬜ |
| C — optional supporting | 4 | ⬜ |
