# 01 — Scope and Test Basis

Phase 1 deliverable. This document fixes what we are testing, on what baseline, with what tools, and what the source review found. Every later phase (requirements, test design, execution, defect log) traces back to this file.

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
| Windows | win32 (host) | WSL: **no distribution installed** — see §5 conflicts |
| Python | 3.12.10 | virtual environment at `.venv/` |
| Django | 6.1.3 | pinned in `requirements.txt` |
| Docker | 29.9.2 | available, not required for Phases 1–7 |
| Git | 2.54.0.windows.1 | identity: Ashar Ahmed <asharahmedd05@gmail.com> |
| Node.js / npm | **not installed** | required from Phase 9 (Playwright, Lighthouse) — user action item |
| gh CLI | **not installed** | PR/issue creation will be manual or via install — user action item |
| pandoc | **not installed** | report DOCX produced by other means |
| pycurl 7.49.0 | installed from Windows wheel | README's `--compile` path not needed on Windows |

## 3. Reproducible run / seed / reset commands

All commands run from the repository root. The PowerShell variants are what we actually use on this machine; the `.sh` twins are kept for portability.

| Step | One command | Pass looks like |
|---|---|---|
| Install | `.\scripts\setup.ps1` | `setup done: Python 3.12.10`, exits 0 |
| Reset + seed | `.\scripts\reset.ps1` | prints `reset complete` and 7 check rows with expected display statuses |
| Seed only (idempotent) | `.\scripts\seed.ps1` | same 7 rows, re-running changes nothing |
| Start server | `.\scripts\start.ps1` | serving at `http://localhost:8000` |

Seeded synthetic data (all local, all committed in `scripts/seed.py`, credentials in `.env.example`):

- Accounts, password `sqe-test-pass-2026`: `admin@example.com` (superuser), `owner@example.com`, `member-rw@example.com`, `member-ro@example.com`, `other-owner@example.com`.
- Main project API keys: write `hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4`, read `hcr_Z9y8X7w6V5u4T3s2R1q0P9o8N7m6`. Second project write key `hcw_B2c3D4e5F6g7H8i9J0k1L2m3N4o5` (cross-project 403/404 tests).
- Checks (timeout 1 day, grace 1 hour): `seed-new` (new), `seed-up` (up), `seed-grace` (grace), `seed-down` (down), `seed-paused`, `seed-paused-manual` (paused + manual_resume), plus `other-up` in the second project. Ping UUIDs are `uuid5`-derived from slugs → stable across resets.

Repeatability proof (2026-11-22): `reset.sh` run twice back-to-back; both runs applied all migrations from scratch and printed identical seed output (7 checks, same display statuses). `seed.sh` run twice in a row is equally stable.

## 4. Live behavior verification (2026-11-22, against runserver)

The server log and the curl results agree line-for-line. Test URLs use `http://localhost:8000` with `curl --noproxy '*'` (see §5).

| # | Request | Expected | Observed |
|---|---|---|---|
| 1 | `GET /accounts/login/` | 200 | 200 |
| 2 | `GET /` | 302 → login | 302 → `/accounts/login/` |
| 3 | `GET /api/v3/checks/` no key | 401 | 401 |
| 4 | `GET /api/v3/checks/` wrong key | 401 | 401 |
| 5 | `GET /api/v3/checks/` rw key | 200, 7 checks, correct display statuses | 200 (statuses new/up/grace/down/paused/paused/up) |
| 6 | `GET /api/v3/checks/` ro key | 200 (read allowed) | 200 |
| 7 | `POST .../pause` ro key (write) | 401 | 401 `wrong api key` |
| 8 | `GET /api/v3/checks/` other-project key | 200, only that project's checks | 200 |
| 9 | `GET /ping/<seed-new uuid>/` | 200 "OK", status new→up | 200 OK; re-list shows `up` |
| 10 | `GET /ping/<bad uuid>/` | 404 | 404 |
| 11 | `POST .../pause` rw key | 200 | 200 |
| 12 | `POST .../pause` again (already paused) | 200 (idempotent) | 200 |
| 13 | `POST .../resume` paused check | 200 | 200 |
| 14 | `POST .../resume` not-paused check | 409 | 409 `check is not paused` |
| 15 | `POST /api/v3/checks/` timeout=59 | 400 | 400 |
| 16 | `POST /api/v3/checks/` timeout=31536001 | 400 | 400 |
| 17 | `POST /api/v3/checks/` timeout=60 (boundary) | 201 | 201 |
| 18 | `GET /ping/<uuid>/256` (exitstatus > 255) | 400 | 400 |
| 19 | `GET /ping/<uuid>/1` (exitstatus fail) | 200, check goes down | 200 |

## 5. README vs. reality (documented mismatches)

1. **WSL assumed, absent.** The team master prompt assumes WSL2 Ubuntu. `wsl -l -v` reports no installed distribution. We run Windows-native in `.venv`; the `.ps1` scripts are the primary path. Phase 8 (mutation testing) tool choice still open: install WSL, use Docker, or use CI.
2. **`127.0.0.1` is rejected.** `ALLOWED_HOSTS=['localhost']`, so the app must be addressed as `http://localhost:8000`, never `http://127.0.0.1:8000` (Django returns 400 DisallowedHost). `scripts/start.*` binds `127.0.0.1:8000` for the socket but the Host header must be `localhost`.
3. **Host header rewriting.** Some requests from this machine arrive with `Host: kubernetes.docker.internal` (system/proxy rewrite; no `HTTP_PROXY`/`HTTPS_PROXY` env vars set — only `NO_PROXY=127.0.0.1,localhost,::1`). Workaround: always call with `curl --noproxy '*'` and `localhost`.
4. **`createsuperuser` is custom.** Healthchecks replaces Django's command (`hc/accounts/management/commands/createsuperuser.py`): it takes `--email` and `--password`, and has no `--username`/`--noinput`. Working invocation: `manage.py createsuperuser --email admin@example.com --password sqe-test-pass-2026`.
5. **README targets Debian/Ubuntu.** `sudo apt install python3-venv`, `source .venv/bin/activate`, `pip install pycurl --compile` are not the Windows path; on Windows the pycurl wheel installs directly and activation is `.venv\Scripts\Activate.ps1`.
6. **No upstream CI workflows.** `.github/workflows/` does not exist at the baseline, so Phase 10 (pipeline) starts from scratch rather than extending an existing one.
7. **`pause`/`resume` API routes have no trailing slash** (`/api/v3/checks/<uuid>/pause`, not `.../pause/`); the trailing-slash variant 404s.

## 6. Source review summary (where each rule lives)

| Concern | File | Key finding |
|---|---|---|
| API routes | `hc/api/urls.py` | v1/v2/v3; `pause`/`resume` no trailing slash; ping by UUID and by slug; exitstatus segment `<int:exitstatus>` |
| Auth (API) | `hc/api/decorators.py` | missing key → 401, wrong key → 401; ro key (`hcr_`) on write → 401; `authorize` vs `authorize_read` |
| API key lookup | `hc/accounts/models.py` (`ProjectManager.for_api_key`) | hashed keys by 8-char prefix + HMAC compare; legacy plaintext fallback (our seeded keys use it) |
| Roles | `hc/accounts/models.py` (`Member.is_rw`), `hc/front/views.py` (`_get_rw_check_for_user`) | roles r/w/m; UI write on non-rw → `PermissionDenied` 403; superuser and project owner always rw |
| Spec validation | `hc/api/views.py` (`Spec` pydantic model) | `timeout`/`grace` `ge=60, le=31536000`; `slug` pattern `^[a-z0-9-_]*$`; `methods` only `""` or `"POST"` |
| Form validation | `hc/front/forms.py` (`AddCheckForm`) | same bounds 60..31536000 seconds |
| Status rules | `hc/api/models.py` (`Check.get_status`, `get_grace_start`, `going_down_after`) | derived display status: new/up/grace/down/paused; grace window between timeout expiry and alert_after |
| Ping handling | `hc/api/models.py` (`Check.ping`), `hc/api/views.py` (`ping`) | atomic `select_for_update`; paused+manual_resume → `ign` ping; exitstatus>255 → 400, >0 → fail; method enforcement; CORS `*` |
| Pause/resume | `hc/api/views.py`, `hc/front/views.py` | API: pause idempotent 200, resume not-paused → 409; front: resume not-paused → 400 (inconsistency — candidate defect, to be logged in later phase) |
| Check limit | `hc/accounts/models.py` | `check_limit` default 20; `add_check` → 400 when exhausted |
| Settings | `hc/settings.py` | `SITE_ROOT`/`PING_ENDPOINT` default `http://localhost:8000`; DB default `hc.sqlite` |

## 7. Open items / conflicts to resolve

- WSL vs Docker vs CI for Phase 8 mutation testing (master prompt assumes WSL).
- Node.js install required before Phase 9 (Playwright screenshots, Lighthouse).
- `gh` CLI absent: PR/issue creation will be manual until installed.
- Healthchecks-as-MIS acceptability: instructor confirmation pending.
- API coverage criteria for Taimoor's area: to be confirmed with instructor.
- Viva date and weekly report day: unknown; submission date 29 Nov 2026 confirmed.
