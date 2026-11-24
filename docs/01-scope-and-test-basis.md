# 01 — Scope and Test Basis

Phase 1 created the baseline and environment (§1, §2, §10–§13). Phase 2 added the workflow analysis, functional requirements, business rules, roles, assumptions and use-case list (§3–§9). Every later phase (test plan, tests, traceability, defects) traces back to this file.

## 1. System under test

| Item | Value |
|---|---|
| System | Healthchecks — a web-based Monitoring/Management Information System (cron job monitoring: HTTP(S) ping endpoints, status badges, alerting channels, team/project access control) |
| Upstream repository | https://github.com/healthchecks/healthchecks |
| Team repository (fork) | https://github.com/ashar1x/healthchecks |
| License | BSD 3-clause — "Copyright (c) 2015, Pēteris Caune and other contributors" (see `LICENSE`) |
| Baseline tag | `baseline` |
| Baseline commit | `ac59dec93c5179cdff471894704f360d6ee5e02a` |
| Baseline commit date | Fri Nov 20 13:56:30 2026 +0200 — "Fix the 'List Checks' API call to handle NUL bytes in query parameters" |
| Working branch (area 1) | `area1/ashar` |
| Application framework | Django 6.1.3 (Python), settings module `hc.settings` |
| Default database | SQLite `hc.sqlite` (gitignored) |

Why this system qualifies as an MIS: it is an existing, open-source, web-based system that collects operational data (check pings, statuses, downtime history), stores it, presents it to users (dashboard, badges, reports, metrics), and triggers notifications — i.e. management information and alerting for monitored jobs. Confirmation of acceptability with the instructor: **pending (informal confirmation only)**.

## 2. Environment and tool versions (measured 2026-11-22)

| Tool | Version | Notes |
|---|---|---|
| Windows | win32 (host) | WSL: **no distribution installed** — see §12 conflicts |
| Python | 3.12.10 | virtual environment at `.venv/` |
| Django | 6.1.3 | pinned in `requirements.txt` |
| Docker | 29.9.2 | available, not required for Phases 1–7 |
| Git | 2.54.0.windows.1 | identity: Ashar Ahmed <asharahmedd05@gmail.com> |
| Node.js / npm | **not installed** | required from Phase 9 (Playwright, Lighthouse) — user action item |
| gh CLI | **not installed** | PR/issue creation will be manual or via install — user action item |
| pandoc | **not installed** | report DOCX produced by other means |
| pycurl 7.49.0 | installed from Windows wheel | README's `--compile` path not needed on Windows |

## 3. Workflows

Two related workflows in one module (the checks module), per brief section 1.

### WF1 — Check management (dashboard UI + HTTP API)

Starting condition: a seeded database; an authenticated user with read-write access to the project (or an rw API key `hcw_…`); the project has free check slots (local limit, see BR-01).

| Step | User action | Expected outcome | Failing path (expected rejection) |
|---|---|---|---|
| 1. Create | Dashboard: POST `checks/add/` with name, timeout, grace. API: `POST /api/v3/checks/` with `{name, timeout, grace}` | Check created; dashboard 302 → project checks list; API 201 + check JSON (200 if the `unique` lookup matched an existing check) | timeout/grace outside 60..31536000 → API 400 `{"error": ...}`, dashboard 400 (FR-06); missing/wrong API key → 401; read-only key → 401; project limit reached → API 403, dashboard 400; unauthenticated dashboard user → 302 login |
| 2. Edit | Dashboard: POST `checks/<uuid>/timeout/` (timeout, grace, schedule). API: `POST /api/v3/checks/<uuid>` | Values updated; `alert_after` recomputed (`going_down_after`); dashboard 302 → details, API 200 + check JSON | Same bound rejections as create; read-only key → 401; read-only member → 403 (`PermissionDenied`); another project's check → 403; unknown UUID → 404 |
| 3. Pause | Dashboard: POST `checks/<uuid>/pause/`. API: `POST /api/v3/checks/<uuid>/pause` (**no trailing slash**) | status → `paused`, `last_start`/`alert_after` cleared, a Flip is recorded; repeat is idempotent (API returns 200 with the unchanged check, no second flip; dashboard redirects without a flip) | read-only key → 401 `wrong api key`; read-only member → 403; unknown UUID → 404; other project's check → 403 |
| 4. Resume | Dashboard: POST `checks/<uuid>/resume/`. API: `POST /api/v3/checks/<uuid>/resume` | status → `new`, `last_ping`/`last_start`/`alert_after` cleared, Flip recorded; 200 (API) / 302 (dashboard) | Resume when **not** paused → API **409** `check is not paused`; dashboard → **400** (same condition, different code — inconsistency logged as candidate defect, A-03); read-only key → 401; read-only member → 403 |
| 5. Delete | Dashboard: POST `checks/<uuid>/remove/`. API: `DELETE /api/v3/checks/<uuid>` | Check renamed to a throwaway UUID/slug then deleted (`rename_and_delete`, so pings during deletion cannot resurrect it); API 200 + last check JSON, dashboard 302 → checks list | read-only key → 401; read-only member → 403; other project's check → 403; unknown UUID → 404 |
| 6. List / fetch | Dashboard: `GET /tv/`, `GET /projects/<code>/checks/`. API: `GET /api/v3/checks/`, `GET /api/v3/checks/<uuid>` | Only the key's (or user's) project checks are returned; ro key and rw key both may read | missing/wrong key → 401; other project's check by UUID → 403; unknown UUID → 404; NUL byte in `tag`/`slug` query → 400 |

### WF2 — Ping and status lifecycle (monitoring side of the same records)

Starting condition: a check exists with a known ping UUID (or project `ping_key` + slug); no authentication required for pinging.

| Step | User action | Expected outcome | Failing path (expected rejection) |
|---|---|---|---|
| 1. Success ping | `GET /ping/<uuid>/` (or `POST`, or `/ping/<ping_key>/<slug>/`) | HTTP 200 `OK`; `last_ping` = now; `n_pings` +1; status → `up` (Flip recorded if it changed); `alert_after` = `going_down_after()` | unknown UUID → 404 `not found`; unknown ping_key/slug → 404 (auto-create only with `?create=1`, and only below 2× the check limit); uppercase slug → 400 |
| 2. Fail ping | `GET /ping/<uuid>/fail` or `GET /ping/<uuid>/<exitstatus>` with exitstatus ≥ 1 | 200 `OK`; status → `down`; Flip with reason `fail` | exitstatus > 255 → 400 `invalid url format`; exitstatus not an integer → 404 (route mismatch) |
| 3. Start ping | `GET /ping/<uuid>/start` | 200 `OK`; `last_start` = now; `last_ping` unchanged; display can show `started` (within grace of start) | same as success ping |
| 4. Duration | start ping, then success ping with matching `rid` | `last_duration` = success time − start time; `last_start` cleared | rid mismatch on fail, or success without rid → `last_start` cleared without duration (code, models.py:529–533) |
| 5. Time passes (no ping) | wait past `timeout` + `grace` (or read `get_status` at seeded timestamps) | display status: within schedule+timeout → `up`; inside grace window → `grace`; past grace end → `down`; never pinged → `new` | n/a (read-only derivation) |
| 6. Ping a paused check | ping a check whose status is `paused` | `manual_resume=false` → check leaves `paused` (goes `up`/`down`); `manual_resume=true` → ping recorded as `ign`, status **stays `paused`**, `n_pings` still +1 | documented in `templates/docs/configuring_checks.md:98-102` and `templates/docs/api.md:465-470` |
| 7. Method filter | check configured `methods="POST"`, ping arrives by GET | action becomes `ign` (ping recorded, status unchanged), still 200 (code, `hc/api/views.py:233-234`) | n/a |
| 8. Cross-workflow read-back | after any of the above, `GET /api/v3/checks/<uuid>` | returned JSON `status`, `last_ping`, `timeout`, `grace`, `n_pings` match the rule | same access rules as WF1 step 6 |

## 4. Shared records

The shared record between WF1 and WF2 is **the `Check` row** — specifically `timeout`, `grace`, `status`, `last_ping` and `n_pings`. WF1 changes `timeout`/`grace`/`status`; WF2 reads `timeout`/`grace` to derive the displayed status and writes `status`/`last_ping`/`n_pings`. This is the record the brief asks for ("one record or value that one workflow changes and the other uses").

Legend: **R** = reads, **W** = writes, **—** = not involved.

| Operation | name | timeout | grace | status | last_ping | n_pings | manual_resume | last_start / last_duration |
|---|---|---|---|---|---|---|---|---|
| WF1 create | W | W | W | W (initial `new`) | — | — | R (default false) | — |
| WF1 edit (timeout/grace) | — | W | W | R (recomputes `alert_after`) | — | — | — | — |
| WF1 pause | — | — | — | W → `paused` | — | — | — | W (clears `last_start`) |
| WF1 resume | — | — | — | W → `new` | W (clears) | — | — | W (clears) |
| WF1 delete | W (renamed) | — | — | — | — | — | — | — |
| WF1 list/fetch | R | R | R | R | R | R | R | R |
| WF2 success/fail ping | — | R (via `going_down_after`) | R | W → `up`/`down` | W | W (+1) | R (paused rule) | R/W (duration) |
| WF2 start ping | — | — | — | R | — | W (+1) | R | W |
| WF2 time passes (read) | — | R | R | R (derived `grace`/`down`) | R | — | R | R |
| WF2 ping while paused | — | — | — | W (or unchanged if `manual_resume`) | W (unless `ign`) | W (+1) | R | — |

Cross-workflow test consequence (feeds Phase 7): changing `timeout`/`grace` in WF1 must change what WF2's time-passage and ping read-back show; pausing in WF1 must change WF2's ping outcome; deleting in WF1 must make WF2's old ping UUID return 404.

## 5. Functional requirements (FR-01 … FR-12)

12 requirements — at least 3 per workflow (brief: minimum 8 / 3). Expected behaviour sourced from repository documentation (`templates/docs/api.md`, `templates/docs/configuring_checks.md`) or, where documentation is silent, a justified assumption in §9.2.

### WF1 — Check management

| ID | Requirement | Expected behaviour | Source |
|---|---|---|---|
| FR-01 | A member creates a check with name, timeout and grace, via dashboard or API | Check appears in the project's list with status `new`; API returns 201 | docs `api.md:642` (201 Created); code `hc/api/views.py:459-480`, `hc/front/views.py:529-555` |
| FR-02 | A member edits a check's name, timeout or grace | Values persisted; `alert_after` recomputed from the new timeout/grace; API returns 200, dashboard 302 | docs `api.md:955` (200 OK); code `hc/api/views.py:520-538`, `hc/front/views.py:606-640` |
| FR-03 | A member pauses and resumes a check | Pause → `paused`; resume → `new`; both record a Flip; repeat pause is idempotent | docs `api.md:1023-1036` (pause 200), `api.md:1094-1119` (resume 200, 409); code `hc/api/views.py:565-611` |
| FR-04 | A member deletes a check | Check removed after rename-to-throwaway; pinging the old UUID afterwards returns 404; API returns 200 with the final JSON | docs `api.md` Delete section (200/401/403/404); code `hc/api/views.py:541-550`, `hc/api/models.py:382-404` |
| FR-05 | The API lists and fetches only the checks of the key's project | `GET /api/v3/checks/` returns only that project's checks; another project's check by UUID → 403 | observed live (Phase 1 test 8); code `hc/api/views.py:430-456, 504-505` |
| FR-06 | An invalid timeout or grace is rejected | timeout/grace < 60 or > 31536000 → 400 with an error message; check not created/modified | docs `api.md:423,434` ("Minimum: 60 (one minute), maximum: 31536000 (365 days)"); code `hc/api/views.py:69,80`, `hc/front/forms.py:51,54`; observed live (tests 15–17) |

### WF2 — Ping and status lifecycle

| ID | Requirement | Expected behaviour | Source |
|---|---|---|---|
| FR-07 | A success ping marks the check `up` and records `last_ping` | 200 `OK`; `last_ping` = ping time; `n_pings` +1; Flip `up` if status changed | code `hc/api/models.py:521-545`; observed live (test 9) |
| FR-08 | A start ping followed by a success ping records the duration | `last_duration` = success − start when `rid` matches; `last_start` cleared | code `hc/api/models.py:517-528` |
| FR-09 | A fail ping marks the check `down` | exitstatus ≥ 1 or `/fail` → status `down`, Flip with reason `fail`, 200 | code `hc/api/views.py:230-231`, `hc/api/models.py:535-539`; observed live (test 19) |
| FR-10 | A check with no ping past timeout + grace shows `down`; inside the grace window shows `grace` | derived display status from `get_status()`; never-pinged → `new` | code `hc/api/models.py:355-380` (`get_status`); seeded evidence (Phase 1: `seed-grace`, `seed-down`) |
| FR-11 | A ping to a paused check follows the paused + manual-resume rule | `manual_resume=false` → leaves `paused`; `manual_resume=true` → ping recorded `ign`, stays `paused` | docs `configuring_checks.md:98-102`, `api.md:465-470`; code `hc/api/models.py:514-515` |
| FR-12 | A ping to an unknown UUID is rejected; a missing or wrong API key gets 401 | unknown ping UUID → 404; missing/wrong key on API reads/writes → 401 `missing api key` / `wrong api key` | code `hc/api/views.py:205-209`, `hc/api/decorators.py:57,61,80,84`; observed live (tests 3, 4, 10) |

## 6. Business rules (BR-01 … BR-04)

All four required rule types are present: a boundary/limit (BR-01), a decision with ≥2 Boolean conditions (BR-02), a change-of-state rule (BR-03), and permissions (BR-04).

### BR-01 — Boundary or limit

**Conditions (exact):**
1. `timeout` must satisfy `60 ≤ timeout ≤ 31536000` seconds (60 s … 365 days) — inclusive on both ends.
2. `grace` must satisfy `60 ≤ grace ≤ 31536000` seconds — inclusive on both ends.
3. Per-account check limit: a project may hold at most `owner_profile.check_limit` checks. **In our environment `USE_PAYMENTS=False` (`hc/settings.py:74`), so freshly created profiles get `check_limit = 10000` (`hc/accounts/models.py:73-79`); the model field default is 20 (`hc/accounts/models.py:90`) and is what applies when payments are enabled.** The limit is checked against the **project owner's** profile (`Project.num_checks_available` → `owner_profile`, `hc/accounts/models.py:478-479`).
4. Auto-provisioned pings (`/ping/<ping_key>/<slug>?create=1`) may exceed the limit only up to 2× (`profile.num_checks_used() >= profile.check_limit * 2` → 404, `hc/api/views.py:290`).

**Rejection behaviour:** API create/update → 400 `{"error": …}` for bounds (`hc/api/views.py:462-464, 526-529`); dashboard → 400 (`hc/front/forms.py` bounds via `AddCheckForm`/`TimeoutForm`); limit reached → API create 403 (`hc/api/views.py:469-470`), dashboard add 400 (`hc/front/views.py:533-534`).

**Source:** documentation `templates/docs/api.md:423,434`; code as cited. **Observed:** 59 → 400, 31536001 → 400, 60 → 201 (Phase 1 tests 15–17). Test just below / at / above each bound (59/60/61 and 31536000/31536001 are the three-point BVA set; note 31536000 itself must be accepted — A-04).

### BR-02 — Decision with two or more Boolean conditions

**`Check.get_status()` (`hc/api/models.py:355-380`)** — the display-status decision, evaluated in order:

| # | Condition (exact) | Outcome |
|---|---|---|
| C1 | `last_start` is set **AND** `now ≥ last_start + grace` | `down` |
| C2 | `last_start` is set **AND** `now < last_start + grace` **AND** `with_started=True` | `started` |
| C3 | stored `status ∈ {new, paused, down}` | return stored status |
| C4 | `grace_start is None` (next elapse never) | `up` |
| C5 | `now ≥ grace_start + grace` (grace end) | `down` |
| C6 | `now ≥ grace_start` | `grace` |
| C7 | otherwise | `up` |

**Paused + manual-resume rule in `Check.ping` (`hc/api/models.py:514-515`):**
`status == "paused" AND manual_resume == True` → `action` overwritten to `"ign"` (ping logged, status unchanged). If either condition is false, the ping applies normally — i.e. a paused check with `manual_resume=false` **leaves the paused state when pinged**.

**Source:** code as cited; documented in `templates/docs/api.md:465-470` and `templates/docs/configuring_checks.md:98-102`. Decision-table testing must cover all combinations of the Boolean conditions; MCC/MC/DC in Phase 5 targets this function.

### BR-03 — Change of state

**States:** `new`, `up`, `grace` (derived), `down`, `paused`, plus derived `started` (display only).

| From → To | Trigger | Allowed? | Source |
|---|---|---|---|
| `new` → `up` | success ping | yes | `hc/api/models.py:535-539` |
| `new`/`up` → `down` | fail ping (exitstatus ≥ 1 or `/fail`) | yes | same |
| `up` → `grace` | time passes into grace window (derived) | yes | `hc/api/models.py:377-378` |
| `up`/`grace` → `down` | time passes beyond grace end (derived) | yes | `hc/api/models.py:374-375` |
| any → `paused` | pause action (dashboard or API) | yes | `hc/api/views.py:578-583`, `hc/front/views.py:842-847` |
| `paused` → `new` | resume action | yes | `hc/api/views.py:603-609`, `hc/front/views.py:867-873` |
| `paused` → `up`/`down` | ping with `manual_resume=false` | yes | docs `configuring_checks.md:98-102`; `hc/api/models.py:535-539` |
| `paused` → `paused` | ping with `manual_resume=true` (recorded `ign`) | yes, no state change | `hc/api/models.py:514-515` |
| `paused` → `paused` | pause again (repeat request) | **idempotent no-op**: API 200 with unchanged check and **no second Flip**; dashboard early-redirect, no flip | `hc/api/views.py:573-575`, `hc/front/views.py:837-839` |
| not `paused` → `paused` | resume attempt | **disallowed**: API **409** `check is not paused`; dashboard **400** — same condition, two different codes (candidate defect, A-03); no state change in either case | `hc/api/views.py:600-601`, `hc/front/views.py:864-865` |
| `down` → `up` | success ping | yes | `hc/api/models.py:535-539` |

**Source:** code as cited; pause/resume documented in `templates/docs/api.md:1023-1119`. Where the documentation is silent (repeat-pause idempotency, exact status codes for the dashboard path) → assumptions A-01, A-02, A-03 in §9.2. State-transition testing must cover every allowed transition and at least one disallowed transition from each state.

### BR-04 — Permissions (two roles with different permissions, plus key roles)

| Action | Project owner | rw member (`role=w`) | ro member (`role=r`) | rw API key (`hcw_`) | ro API key (`hcr_`) | Unauthenticated | Other project's user/key |
|---|---|---|---|---|---|---|---|
| List/fetch own checks (dashboard) | ✅ | ✅ | ✅ (read) | — | — | ❌ 302 login | ❌ 404/403 |
| List/fetch via API | — | — | — | ✅ 200 | ✅ 200 | ❌ 401 | own project only; other project's check UUID → **403** |
| Create / edit check | ✅ | ✅ | ❌ **403** | ✅ 201/200 | ❌ **401** | ❌ 302/401 | ❌ 401/403 |
| Pause / resume / delete | ✅ | ✅ | ❌ **403** | ✅ 200 | ❌ **401** `wrong api key` | ❌ 302/401 | ❌ **403** (cross-project), 404 unknown |
| Ping (WF2) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (ping endpoints are unauthenticated by design) | ✅ (needs only the UUID) |
| Unknown UUID (ping or API) | 404 | 404 | 404 | 404 | 404 | 404 | 404 |

**Conditions (exact):** dashboard write views call `_get_rw_check_for_user`, which raises `PermissionDenied` (403) when the membership's `is_rw` is false (`hc/front/views.py:140-145`, `hc/accounts/models.py:636`); superuser and project owner are always rw (`hc/front/views.py:130-134`). API `authorize` accepts only rw keys and rejects ro keys on writes with 401 (`hc/api/decorators.py:33-68`); `authorize_read` accepts both and sets `readonly` for `hcr_` keys (`hc/api/decorators.py:71-93`). Missing key → 401 `missing api key`; unknown/wrong key → 401 `wrong api key`; a key reaching another project's check → 403 (`hc/api/views.py:504-505, 523-524, 546-547, 570-571, 597-598`).

**Observed:** Phase 1 tests 3, 4, 6, 7, 8 match this table.

## 7. Roles and permissions (summary)

Six principals, per master prompt (owner, rw member, ro member, API rw key, API ro key, unauthenticated + other-project principal):

1. **Project owner** — implicit read-write on own project's checks, channels, settings; owns the profile that carries the check limit.
2. **Read-write member (`Member.role = "w"`)** — same check mutations as the owner within the project.
3. **Read-only member (`Member.role = "r"`)** — may view the dashboard and checks; every write view raises 403.
4. **rw API key (`hcw_…`)** — full API read + write on its own project.
5. **ro API key (`hcr_…`)** — API read only; any write attempt → 401.
6. **Unauthenticated / other-project principal** — unauthenticated dashboard → login redirect; unauthenticated API → 401; another project's credentials → 403 on a known check UUID, and never see other projects' data in listings.

(The full matrix is §6 BR-04.)

## 8. Use case list (fixes the numbering for all members)

Two use cases per member, browser end-to-end, each with ≥2 alternative and ≥2 exception flows (Phase 9/10). Phase 2 fixes this list; renumbering stops here.

| UC | Owner | Title | Primary workflow |
|---|---|---|---|
| UC-01 | Ashar (area 1) | Create and configure a check, then watch its status evolve | WF1 → WF2 |
| UC-02 | Ashar (area 1) | Pause a check, ping it both ways, resume it | WF1 ⇄ WF2 |
| UC-03 | Taimoor (area 2) | Create and edit a check through the API, verify read-back | WF1 |
| UC-04 | Taimoor (area 2) | Drive a check from `new` to `down` to `up` using pings | WF2 |
| UC-05 | Ali (area 3) | A read-only member manages checks and is denied writes | WF1 (permission flows) |
| UC-06 | Ali (area 3) | Recover a failed check: fail ping, alert window, success ping | WF2 |

## 9. Test basis

### 9.1 Sources used

| Source | What it gives us |
|---|---|
| Brief `SQE_Final_Project Fall 2026.md` | scope rules, required artefacts, marking rubric |
| Team master prompt `SQE_Final_Project_Master_Prompt_for_the_Agentic_AI.md` | phase order, area ownership, commit/evidence rules |
| `README.md` (upstream) | setup, run, reset commands (verified, see §12) |
| `templates/docs/api.md` (served at `/docs/api/`) | documented API operations and status codes: create 201/200/400/401/403 (`:642-655`), update 200/400/401/403/404 (`:955-968`), pause 200/401/403/404 (`:1035-1044`), resume 200/401/403/404/409 (`:1106-1119`), timeout/grace bounds (`:423,434`), `manual_resume` semantics (`:465-470`) |
| `templates/docs/configuring_checks.md:98-102` | "Pinging a Paused Check": default auto-resume vs sticky paused state |
| `templates/docs/introduction.md:56-57` | status vocabulary incl. Paused |
| Code: `hc/api/views.py`, `hc/api/models.py`, `hc/api/decorators.py` | exact conditions, status codes, `Spec` bounds, `get_status`, `ping` |
| Code: `hc/front/views.py`, `hc/front/forms.py` | dashboard equivalents and their status-code differences |
| Code: `hc/accounts/models.py` | API key lookup, roles (`is_rw`), check limits |
| Live verification (Phase 1, §11) | 19 observed request/response pairs, server log agreeing line-for-line |

### 9.2 Assumption log

| ID | Assumption | Why needed | Justification / status |
|---|---|---|---|
| A-01 | Repeating pause on an already-paused check is an idempotent success (200, no second Flip) | docs only say "200 — successfully paused"; they do not describe repeats | Code comment states the early return exists to avoid a duplicate flip (`hc/api/views.py:573-575`); verified live (200, status unchanged). Downtime calculation (`Check.downtimes`) depends on one flip per transition |
| A-02 | Repeating resume on a non-paused check must change **no** state | docs document API 409 (`api.md:1118-1119`) but not the dashboard | Verified live for API (409, no state change); dashboard path returns 400 with no state change (code `hc/front/views.py:864-865`) |
| A-03 | **Candidate defect:** the same rejection (resume a non-paused check) returns 409 via API but 400 via dashboard | inconsistent status codes for one condition | Not documented either way; to be logged in the defect phase (GitHub Issue) and decided with the team |
| A-04 | Bounds are inclusive: timeout/grace of exactly 60 and exactly 31536000 are accepted | docs say "Minimum: 60 … maximum: 31536000" — inclusivity not stated | pydantic `ge=60, le=31536000` and Django `min_value/max_value` are inclusive; verified live for 60 (201). 31536000 to be tested in Phase 7 |
| A-05 | Effective local check limit is 10000, not the field default 20 | limit testing needs the real number | `USE_PAYMENTS=False` by default (`hc/settings.py:74`) → new profiles get 10000 (`hc/accounts/models.py:73-79`). Tests will set `profile.check_limit` explicitly (same approach as upstream's own tests) to hit the boundary |
| A-06 | Ping endpoints are intentionally unauthenticated (knowledge of the UUID is the capability) | no doc statement found | Ping URLs are published to cron jobs by design (README/docs); tested as an observation, not a defect, unless the security phase decides otherwise |
| A-07 | `exitstatus > 255` is rejected with 400 and exitstatus 1–255 means fail | route accepts `<int:exitstatus>` | Code `hc/api/views.py:211-212, 230-231`; verified live (256 → 400, 1 → 200) |

### 9.3 Open questions for the team

1. WSL vs Docker vs CI for Phase 8 mutation testing (master prompt assumes WSL; machine has none).
2. Node.js installation before Phase 9 (Playwright, Lighthouse, axe-core) — **owner: Ashar (user action)**.
3. `gh` CLI absent: PR/issue creation manual until installed — affects defect logging (Phase 11) and the blocked-PR evidence (Phase 10).
4. API coverage criteria definition — owner: Taimoor, in `docs/03-test-plan.md` (Phase 4).
5. Healthchecks-as-MIS acceptability + API coverage criteria with the instructor — pending.
6. Viva date and weekly report day unknown; submission date 29 Nov 2026 confirmed.
7. Defect numbering/ID scheme (GitHub Issue numbers vs `DEF-xx`) — owner: Ali, Phase 4/11.

## 10. Reproduction commands and seeded test data

All commands run from the repository root. PowerShell variants are what we use on this machine; `.sh` twins are kept for portability.

| Step | One command | Pass looks like |
|---|---|---|
| Install | `.\scripts\setup.ps1` | `setup done: Python 3.12.10`, exits 0 |
| Reset + seed | `.\scripts\reset.ps1` | prints `reset complete` and 7 check rows with expected display statuses |
| Seed only (idempotent) | `.\scripts\seed.ps1` | same 7 rows, re-running changes nothing |
| Start server | `.\scripts\start.ps1` | serving at `http://localhost:8000` |

Seeded synthetic data (all local, committed in `scripts/seed.py`, credentials in `.env.example`):

- Accounts, password `sqe-test-pass-2026`: `admin@example.com` (superuser), `owner@example.com`, `member-rw@example.com`, `member-ro@example.com`, `other-owner@example.com`.
- Main project API keys: write `hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4`, read `hcr_Z9y8X7w6V5u4T3s2R1q0P9o8N7m6`. Second project write key `hcw_B2c3D4e5F6g7H8i9J0k1L2m3N4o5` (cross-project tests).
- Checks (timeout 1 day, grace 1 hour): `seed-new` (new), `seed-up` (up), `seed-grace` (grace), `seed-down` (down), `seed-paused`, `seed-paused-manual` (paused + manual_resume), plus `other-up` in the second project. Ping UUIDs are `uuid5`-derived from slugs → stable across resets.

Repeatability proof (2026-11-22): `reset.sh` run twice back-to-back; both runs applied all migrations from scratch and printed identical seed output. `seed.sh` run twice in a row is equally stable.

## 11. Live behavior verification (2026-11-22, against runserver)

Server log and curl results agree line-for-line. URLs use `http://localhost:8000` with `curl --noproxy '*'` (see §12).

| # | Request | Expected | Observed |
|---|---|---|---|
| 1 | `GET /accounts/login/` | 200 | 200 |
| 2 | `GET /` | 302 → login | 302 → `/accounts/login/` |
| 3 | `GET /api/v3/checks/` no key | 401 | 401 |
| 4 | `GET /api/v3/checks/` wrong key | 401 | 401 |
| 5 | `GET /api/v3/checks/` rw key | 200, 7 checks, correct display statuses | 200 (new/up/grace/down/paused/paused/up) |
| 6 | `GET /api/v3/checks/` ro key | 200 (read allowed) | 200 |
| 7 | `POST .../pause` ro key (write) | 401 | 401 `wrong api key` |
| 8 | `GET /api/v3/checks/` other-project key | 200, only that project's checks | 200 |
| 9 | `GET /ping/<seed-new uuid>/` | 200 "OK", status new→up | 200 OK; re-list shows `up` |
| 10 | `GET /ping/<bad uuid>/` | 404 | 404 |
| 11 | `POST .../pause` rw key | 200 | 200 |
| 12 | `POST .../pause` again (already paused) | 200 (idempotent, A-01) | 200 |
| 13 | `POST .../resume` paused check | 200 | 200 |
| 14 | `POST .../resume` not-paused check | 409 (A-02) | 409 `check is not paused` |
| 15 | `POST /api/v3/checks/` timeout=59 | 400 | 400 |
| 16 | `POST /api/v3/checks/` timeout=31536001 | 400 | 400 |
| 17 | `POST /api/v3/checks/` timeout=60 (boundary) | 201 | 201 |
| 18 | `GET /ping/<uuid>/256` (exitstatus > 255) | 400 | 400 |
| 19 | `GET /ping/<uuid>/1` (exitstatus fail) | 200, check goes down | 200 |

## 12. README vs. reality (documented mismatches)

1. **WSL assumed, absent.** The team master prompt assumes WSL2 Ubuntu. `wsl -l -v` reports no installed distribution. We run Windows-native in `.venv`; the `.ps1` scripts are the primary path. Phase 8 (mutation testing) tool choice still open: install WSL, use Docker, or use CI.
2. **`127.0.0.1` is rejected.** `ALLOWED_HOSTS=['localhost']`, so the app must be addressed as `http://localhost:8000`, never `http://127.0.0.1:8000` (Django returns 400 DisallowedHost). `scripts/start.*` binds `127.0.0.1:8000` for the socket but the Host header must be `localhost`.
3. **Host header rewriting.** Some requests from this machine arrive with `Host: kubernetes.docker.internal` (system/proxy rewrite; no `HTTP_PROXY`/`HTTPS_PROXY` env vars set — only `NO_PROXY=127.0.0.1,localhost,::1`). Workaround: always call with `curl --noproxy '*'` and `localhost`.
4. **`createsuperuser` is custom.** Healthchecks replaces Django's command (`hc/accounts/management/commands/createsuperuser.py`): it takes `--email` and `--password`, and has no `--username`/`--noinput`. Working invocation: `manage.py createsuperuser --email admin@example.com --password sqe-test-pass-2026`.
5. **README targets Debian/Ubuntu.** `sudo apt install python3-venv`, `source .venv/bin/activate`, `pip install pycurl --compile` are not the Windows path; on Windows the pycurl wheel installs directly and activation is `.venv\Scripts\Activate.ps1`.
6. **No upstream CI workflows.** `.github/workflows/` does not exist at the baseline, so Phase 10 (pipeline) starts from scratch rather than extending an existing one.
7. **`pause`/`resume` API routes have no trailing slash** (`/api/v3/checks/<uuid>/pause`, not `.../pause/`); the trailing-slash variant 404s.

## 13. Source review summary (where each rule lives)

| Concern | File | Key finding |
|---|---|---|
| API routes | `hc/api/urls.py` | v1/v2/v3; `pause`/`resume` no trailing slash; ping by UUID and by slug; exitstatus segment `<int:exitstatus>` |
| Auth (API) | `hc/api/decorators.py` | missing key → 401, wrong key → 401; ro key (`hcr_`) on write → 401; `authorize` vs `authorize_read` |
| API key lookup | `hc/accounts/models.py` (`ProjectManager.for_api_key`) | hashed keys by 8-char prefix + HMAC compare; legacy plaintext fallback (our seeded keys use it) |
| Roles | `hc/accounts/models.py` (`Member.is_rw`), `hc/front/views.py` (`_get_rw_check_for_user`) | roles r/w/m; UI write on non-rw → `PermissionDenied` 403; superuser and project owner always rw |
| Spec validation | `hc/api/views.py` (`Spec` pydantic model) | `timeout`/`grace` `ge=60, le=31536000`; `slug` pattern `^[a-z0-9-_]*$`; `methods` only `""` or `"POST"` |
| Form validation | `hc/front/forms.py` (`AddCheckForm`, `TimeoutForm`) | same bounds 60..31536000 seconds |
| Status rules | `hc/api/models.py` (`Check.get_status`, `get_grace_start`, `going_down_after`) | derived display status: new/up/grace/down/started; grace window between grace start and grace end |
| Ping handling | `hc/api/models.py` (`Check.ping`), `hc/api/views.py` (`ping`) | atomic `select_for_update`; paused+manual_resume → `ign`; exitstatus>255 → 400, >0 → fail; `methods="POST"` non-POST → `ign`; CORS `*` |
| Pause/resume | `hc/api/views.py`, `hc/front/views.py` | API: pause idempotent 200, resume not-paused → 409; front: resume not-paused → 400 (inconsistency — candidate defect A-03) |
| Check limit | `hc/accounts/models.py`, `hc/api/views.py:469`, `hc/front/views.py:533` | `check_limit` field default 20, but 10000 in local env (A-05); API → 403, dashboard → 400 when exhausted |
| Settings | `hc/settings.py` | `SITE_ROOT`/`PING_ENDPOINT` default `http://localhost:8000`; DB default `hc.sqlite`; `USE_PAYMENTS=False` |
