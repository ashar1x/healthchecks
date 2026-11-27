# 13 — Defensive Security Assessment (Area 3)

## 1. Scope and tools

Local copy only, synthetic accounts from `scripts/seed.py`. No live production
system was touched.

| Tool | Version | Use |
|------|---------|-----|
| OWASP ZAP | 2.17.0 (daemon, passive scanners) | passive scan of traffic proxied from Playwright workflows + spider of the login screen |
| `@playwright/test` | 1.65.1 | access-decision checks and proxy traffic generation |
| pip-audit | 2.10.1 | dependency audit of `requirements.txt` + `requirements-dev.txt` |

Reproduce: start ZAP on `127.0.0.1:8090`, run `node tests/e2e/zap-traffic.mjs`
(Chrome proxied through ZAP), poll `/JSON/pscan/view/recordsToScan/` until 0,
then read `/JSON/alert/view/alerts/`. Access matrix:
`npx playwright test tests/e2e/access-control.spec.js`.

## 2. Access matrix (Playwright)

Five decisions across two roles and both workflows. Full evidence:
`evidence/security/access-matrix.json` and `.md`.

| Role | Surface | Action | Expected | Observed | Result |
|------|---------|--------|----------|----------|--------|
| owner (rw) | dashboard | open Add Check | allowed | allowed | PASS |
| read-only member | dashboard | open Add Check | denied | denied | PASS |
| rw API key | API | pause check | 200 | 200 | PASS |
| ro API key | API | pause check | 401 | 401 | PASS |
| read-only member | dashboard | pause check button | denied | denied | PASS |

These decisions cover **RISK-03 / RISK-04** (unauthorised state change and
cross-project key misuse). Source corroboration: `hc/api/decorators.py`
(`authorize`, `authorize_read`) and `hc/front/views.py`
(`_get_rw_check_for_user`, `pause`/`resume`) enforce the same role rules.

## 3. OWASP ZAP passive scan

Raw report: `evidence/security/zap-alerts.json` (498 alerts).

| Risk | Alerts |
|------|-------:|
| Informational | 43 |
| Low | 342 |
| Medium | 112 |
| High | 1 |

Most findings are repetitions of the same root causes across the static files
served by the Django **development** server:

| Finding (deduplicated) | Count | Impact | Proposed fix | Status |
|---|---:|---|---|---|
| Server leaks version via `Server` header | 215 | Fingerprinting of the dev stack | Use the production WSGI/ASGI server and strip the header before release | Residual (dev-only) |
| CSP header not set | 110 | No defence in depth against injected scripts | Add `Content-Security-Policy` in the deployment proxy/settings | Residual |
| `X-Content-Type-Options` missing on static files | 95 | MIME sniffing risk | Add the header at the static-file layer | Residual (Django sends it on dynamic responses — verified by `curl -I`) |
| Timestamp disclosure | 24 | Minor information leak | Version static assets without exposing filesystem timestamps | Residual |
| User-controllable HTML attribute (potential XSS) | 15 | Needs review of template escaping | Reviewed: values are Django-auto-escaped; no raw user HTML in the measured screens | Verified control |
| Session management response identified | 10 | Expected behaviour of login | No action; documented | Verified control |
| Suspicious comments in static assets | 8 | Informational | Upstream asset cleanup | Residual |
| `csrftoken` cookie without HttpOnly | 7 | Token readable by JS | Django default; set `CSRF_COOKIE_HTTPONLY=True` if no client script needs the token | Residual |
| Vulnerable JS library (`static/js/purify.min.js`) | 2 | **High** — known vulnerable DOMPurify version | Upgrade the vendored library from upstream before release | Open — highest priority |

## 4. Session cookie control (second corroborated control)

Observed `Set-Cookie` for the login response:
`csrftoken=...; expires=...; Path=/; SameSite=Lax`. ZAP correctly flags the
absence of `HttpOnly` on `csrftoken`; Django's session cookie remains `HttpOnly`
by default (`hc/settings.py` does not override `SESSION_COOKIE_HTTPONLY`). The
`SameSite=Lax` attribute is present, limiting cross-site sending. This is
recorded as a specific finding with a proposed fix, not silently ignored.

## 5. Dependency audit

`pip-audit` checked **54** pinned packages from both requirements files:
**0 known vulnerabilities**. Raw output: `evidence/security/pip-audit.json`.
`npm audit` checked the `package.json`/lockfile introduced for Playwright:
**0 vulnerabilities** in all severity bands (`evidence/security/npm-audit.json`).

## 6. Residual risk and links

- Highest-priority open item: upgrade the vendored DOMPurify asset (High ZAP
  finding) before the release decision.
- Development-server header leaks and missing CSP are deployment
  configuration items; they do not affect the seeded local test environment.
- Links to risk register: RISK-03, RISK-04 (access decisions, verified) and
  RISK-02 (business-rule integrity through role checks).
- GitHub Issues are disabled in this repository, so security observations are
  recorded here and in the evidence files rather than as Issues.

## 7. Revision history

| Date | Change |
|------|--------|
| 2026-11-27 | Initial defensive security assessment: access matrix, ZAP passive, pip-audit |
