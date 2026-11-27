# 12 — Usability and Accessibility Evaluation (Phase 9)

## 1. Scope, environment and tools

The two workflows selected in Phase 1 (create a check; pause/resume a check)
were exercised through the browser on the local Healthchecks instance with
synthetic seed data (`scripts/seed.py`), not by human participants.

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 22.23.4 | test runtime |
| `@playwright/test` | 1.65.1 | automated browser tests, Chromium via installed Google Chrome |
| `@axe-core/playwright` | 4.14.1 | full axe-core scans |
| Lighthouse | 13.6.0 | accessibility, best practices, SEO |
| Python / Django | 3.12 / 6.1 | application under test |

Reproduce with:

```bash
bash scripts/setup.sh && bash scripts/seed.sh && bash scripts/start.sh
npm install
npm run test:e2e
npm run axe            # AXE_LABEL=before|after
npm run lighthouse -- before|after
```

The Playwright config starts the Django server if it is not already running,
logs in as `owner@example.com` / `sqe-test-pass-2026` in global setup and
stores the session in `tests/e2e/.auth/user.json`.

## 2. Use case specifications

### UC1 — Create a check

**Preconditions:** owner is logged in; project `SQE Test Project` exists with
available check slots. **Postcondition:** a new check exists in the project
and is displayed with status "new" in the checks table.

| Flow | Steps | Expected outcome |
|------|-------|------------------|
| Main | open checks → Add Check → name, slug, period 1 day → Save | confirmation: new row with the entered name |
| Alt 1 | choose Cron and enter a cron expression | schedule shown as cron on the new check |
| Alt 2 | use "Use Suggested" for the slug and add tags | slug normalised, tags visible on the new row |
| Exc 1 | set Period to 366 days | browser blocks submit with "Must not exceed 365 days"; after correcting to 1 day the check is created |
| Exc 2 | force an out-of-range `timeout` POST | server returns bare HTTP 400 with no field-level message (weakness recorded below) |

### UC2 — Pause and resume a check

**Preconditions:** check `seed-paused-manual` is paused and has an active
Resume link. **Postcondition:** after resume the check is "new"/ready for
pings; after pause it is paused again with no duplicate flip.

| Flow | Steps | Expected outcome |
|------|-------|------------------|
| Main | open details → Resume Now → Pause | status text changes to "ready for pings", then to "paused"; API read-back shows `paused` |
| Alt 1 | pause an `up` check from the details screen | status becomes paused, pause button disabled |
| Alt 2 | pause an already paused check | no second flip (idempotent) |
| Exc 1 | resume a check that is not paused via API | HTTP 409 "check is not paused" |
| Exc 2 | read-only member attempts to pause | HTTP 403 (dashboard) / 401 (API key) |

The two Playwright scripts automate each use case's main flow and one
exception flow, as required by Phase 9. The alternative and remaining
exception flows are asserted by the Phase 5 pytest suite
(`tests/team/unit/test_pause_resume.py`, `test_validation_bva.py`) and are
listed here for the use-case component of the report.

## 3. Browser test results

`npm run test:e2e` → **7 passed** (4 browser tests + 3 axe scans):

1. UC1 — create a check with test data and read back the confirmation
2. UC1 — BR-01 rejected period explains the correction, then succeeds
3. UC1 — keyboard navigation reaches the required fields and the submit
   button in order, then submits with Enter
4. UC2 — resume a paused check, pause it again and verify the API postcondition
5-7. axe full scans of the checks screen, Add Check modal and details screen

HTML report: `evidence/phase9/playwright-report/index.html`.

## 4. Lighthouse and axe-core results

Lighthouse was run with the authenticated session cookie on the checks screen
and the check-details screen. axe-core performed a full-page scan of both
screens plus the Add Check modal. Findings found by both tools are counted
once in the table below.

| Issue (deduplicated) | Found by | Impact | Fix / status |
|----------------------|----------|--------|--------------|
| No `<main>` landmark | both | Screen-reader users cannot jump to main content | Added `<main>` in `templates/base.html`; **fixed** |
| No level-one heading on checks | axe | Document outline unclear | Added visually hidden `<h1>` on checks page; **fixed** |
| Icon buttons without names (22 nodes) | both | Screen readers announce unnamed buttons | `aria-label` on pause buttons and filter dropdown; **fixed on checks** |
| Search input unlabelled | both | Field purpose unknown to assistive tech | `aria-label="Search checks"`; **fixed** |
| Low contrast (primary button, footer links) | both | Text hard to read for low-vision users | Darker button colour and underlined links in `static/css/accessibility-fixes.css`; **fixed on checks** |
| Links distinguished by colour only | both | Link not identifiable without colour perception | Underlined footer links; **fixed** |
| Empty table headers | axe | Column purpose missing | `scope="col"` added; header cells are still empty for the icon column — **partly fixed** |
| `<td>` without header association | Lighthouse | Large table hard to navigate | `scope="col"` added to all `<th>`; residual header association still reported — **partly fixed** |
| Content outside landmarks (`region`) | axe | Screen-reader navigation degraded | Main landmark reduced it to one region; **partly fixed** |
| 403 console error | Lighthouse | JS error noise | Tracked as residual risk (favicon/static request) |
| Modal selects without names | axe (modal) | Form fields unclear | Out of scope of the single-screen fix; documented |
| Missing meta description (details) | Lighthouse | Poor search snippet | Out of scope of the single-screen fix; documented |

### Before/after comparison

| Screen / tool | Before | After |
|---------------|--------|-------|
| Lighthouse accessibility — checks | **72** | **100** |
| Lighthouse best practices — checks | 96 | 96 |
| Lighthouse SEO — checks | 100 | 100 |
| Lighthouse accessibility — details | 86 | 88 (shared `<main>` fix) |
| axe violations — checks | 8 | **2** |
| axe violations — Add Check modal | 6 | 6 (not the fixed screen) |
| axe violations — details | 4 | 4 (not the fixed screen) |

The fixed screen is the checks page. Changes: `templates/base.html` (main
landmark), `templates/front/checks.html` (h1, labels),
`templates/front/checks_table.html` (button names, table header scopes) and
`static/css/accessibility-fixes.css` (contrast and underlining). No application
behaviour was changed; the browser tests were rerun after the fix and still
pass.

## 5. Evidence

- `evidence/phase9/playwright-report/index.html` — Playwright report
- `evidence/phase9/axe-before-*.json/.md`, `axe-after-*.json/.md` — full axe scans
- `evidence/phase9/lighthouse-before-*.json/.md`, `lighthouse-after-*.json/.md`
  — Lighthouse reports
- `evidence/phase9/lighthouse-before-summary.md`, `lighthouse-after-summary.md`

## 6. Residual risk

Remaining axe findings are confined to the Add Check modal and details page,
plus two minor table-header findings on the fixed screen. They are recorded
with impact and proposed fixes in §4 rather than silently ignored. The
bare HTTP 400 on server-side validation errors (Exc 2) remains a usability
weakness: the application does not explain what to correct, so the automated
test uses the client-side BR-01 message instead.

## 7. Revision history

| Date | Change |
|------|--------|
| 2026-11-26 | Initial Phase 9 browser tests, axe/Lighthouse before/after reports and checks-screen accessibility fix |
