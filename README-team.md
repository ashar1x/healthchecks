# SQE Final Project — Team Working Notes

Team: Ashar Ahmed (24i-3072, area 1), Taimoor Khaliq (24i-3052, area 2), Ali Haider (24i-3102, area 3).
System under test: [healthchecks](https://github.com/healthchecks/healthchecks) (fork: https://github.com/ashar1x/healthchecks).
Baseline: tag `baseline` → commit `ac59dec93c5179cdff471894704f360d6ee5e02a`. Submission: **29 Nov 2026**.

Read [`docs/01-scope-and-test-basis.md`](docs/01-scope-and-test-basis.md) first — it defines scope, environment, commands, and the verified behavior matrix.

## Quick start (Windows, this machine)

```powershell
.\scripts\setup.ps1     # create .venv + install dependencies (once)
.\scripts\reset.ps1     # migrate + load synthetic seed data (safe to re-run)
.\scripts\start.ps1     # serve at http://localhost:8000  (stop with Ctrl+C)
```

Bash twins exist as `scripts/setup.sh`, `scripts/reset.sh`, `scripts/start.sh`, `scripts/seed.sh`.

**Important:** address the app as `http://localhost:8000` only. `127.0.0.1` is not in `ALLOWED_HOSTS` (Django 400), and some tools on this machine rewrite `Host` — use `curl --noproxy '*'`.

## Credentials (synthetic, local-only — see `.env.example`)

- Superuser: `admin@example.com` / `sqe-test-pass-2026`
- All seeded users share password `sqe-test-pass-2026`
- Main project rw key: `hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4`
- Main project ro key: `hcr_Z9y8X7w6V5u4T3s2R1q0P9o8N7m6`
- Other project rw key: `hcw_B2c3D4e5F6g7H8i9J0k1L2m3N4o5`

## Branches and commits

- `area1/ashar` — Ashar's working branch (Phase 1–2 first, then continues).
- `area2/taimoor`, `area3/ali` — created when each member starts; work happens in git worktrees (`../wt-taimoor`, `../wt-ali`), packaged as patches + `HANDOFF.md`, applied and committed by the member themselves (or by Ashar with their GitHub account when they hand it over).
- Commit format: `area<N>: <what> [REQ-x / BR-x / RISK-x]` (Phase 1 commits are plain `area1: ...` because requirement IDs arrive in Phase 2).
- Evidence rule: no fabricated evidence. Own tests live in `tests/team/`. Screenshots are only Playwright auto-captures or manually taken GitHub/SonarQube full-window shots.

## Test data (from `scripts/seed.py`)

| Check | Display status | How it's made |
|---|---|---|
| `seed-new` | new | never pinged |
| `seed-up` | up | last ping 1 h ago, timeout 1 d |
| `seed-grace` | grace | last ping 1 d 30 min ago → inside grace window |
| `seed-down` | down | last ping 1 d 2 h ago, alert_after in the past |
| `seed-paused` | paused | status=paused |
| `seed-paused-manual` | paused | status=paused + manual_resume=true |
| `other-up` | up | second project (cross-project access tests) |

Ping UUIDs are derived with `uuid5` from slugs, so ping URLs are stable across resets.

## Known environment quirks

- No WSL distribution installed (master prompt assumed WSL2) — Phase 8 mutation tool TBD (WSL / Docker / CI).
- Node.js/npm not installed — required from Phase 9 (Playwright, Lighthouse).
- `gh` CLI not installed — PR/issue creation is manual for now.
- Healthchecks overrides `createsuperuser`: use `--email ... --password ...` (no `--username`).
- API `pause`/`resume` routes have **no trailing slash**.
- No upstream `.github/workflows/` at baseline — Phase 10 pipeline starts from scratch.
