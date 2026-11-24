"""Seed the local Healthchecks database with deterministic synthetic test data.

Run from the repository root, after `manage.py migrate`:

    .venv/Scripts/python.exe scripts/seed.py   (Windows)
    .venv/bin/python scripts/seed.py           (Linux/macOS)

The seed is idempotent: running it twice leaves the same state. Time-dependent
fields (last_ping, alert_after) are recomputed relative to the current time on
every run, so each check keeps showing the intended status. No sleeping is used.

Accounts (password for every account: sqe-test-pass-2026, see .env.example):

    admin@example.com        superuser, used for /admin/ and privileged UI checks
    owner@example.com        owns the main test project (implicit read-write)
    member-rw@example.com    read-write member of the main project (role "w")
    member-ro@example.com    read-only member of the main project (role "r")
    other-owner@example.com  owns the second project (cross-project checks)

API keys (fixed, synthetic, local only):

    main project write key:  hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4
    main project read key:   hcr_Z9y8X7w6V5u4T3s2R1q0P9o8N7m6
    other project write key: hcw_B2c3D4e5F6g7H8i9J0k1L2m3N4o5
    other project read key:  hcr_C3d4E5f6G7h8I9j0K1l2M3n4O5p6

Checks in the main project (timeout 1 day, grace 1 hour unless stated):

    seed-new              status "new", never pinged
    seed-up               status "up",   last ping 1 hour ago
    seed-grace            status "up",   last ping 1 day 30 minutes ago -> shows "grace"
    seed-down             status "up",   last ping 1 day 2 hours ago    -> shows "down"
    seed-paused           status "paused"
    seed-paused-manual    status "paused" with manual_resume = true

Second project: one check, other-up (status "up", last ping 1 hour ago).

Every check code (ping UUID) is derived with uuid5 from its slug, so ping URLs
are stable across resets.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import timedelta as td

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hc.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.utils.timezone import now  # noqa: E402

from hc.accounts.models import Member, Project  # noqa: E402
from hc.api.models import Check  # noqa: E402

PASSWORD = "sqe-test-pass-2026"
MAIN_RW_KEY = "hcw_A1b2C3d4E5f6G7h8I9j0K1l2M3n4"
MAIN_RO_KEY = "hcr_Z9y8X7w6V5u4T3s2R1q0P9o8N7m6"
OTHER_RW_KEY = "hcw_B2c3D4e5F6g7H8i9J0k1L2m3N4o5"
OTHER_RO_KEY = "hcr_C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
NS = uuid.NAMESPACE_URL


def upsert_user(username: str, email: str, *, superuser: bool = False) -> User:
    user = User.objects.filter(email=email).first()
    if user is None:
        user = User(username=username, email=email)
    user.set_password(PASSWORD)
    user.is_superuser = superuser
    user.is_staff = superuser
    user.save()
    return user


def upsert_project(owner: User, name: str, badge_key: str, ping_key: str,
                   rw_key: str, ro_key: str) -> Project:
    project, _created = Project.objects.get_or_create(
        owner=owner,
        name=name,
        defaults={"badge_key": badge_key, "ping_key": ping_key},
    )
    project.api_key = rw_key
    project.api_key_readonly = ro_key
    project.save(update_fields=("api_key", "api_key_readonly"))
    return project


def upsert_check(project: Project, slug: str, *, status: str,
                 last_ping, alert_after, n_pings: int = 0,
                 manual_resume: bool = False) -> Check:
    code = uuid.uuid5(NS, "sqe-seed:" + slug)
    timeout, grace = td(days=1), td(hours=1)
    fields = {
        "project": project,
        "name": slug,
        "slug": slug,
        "kind": "simple",
        "timeout": timeout,
        "grace": grace,
        "status": status,
        "last_ping": last_ping,
        "alert_after": alert_after,
        "n_pings": n_pings,
        "manual_resume": manual_resume,
        "last_start": None,
    }
    check, _created = Check.objects.get_or_create(code=code, defaults=fields)
    for field, value in fields.items():
        setattr(check, field, value)
    check.save(update_fields=list(fields))
    return check


def main() -> None:
    t = now()

    upsert_user("admin", "admin@example.com", superuser=True)
    owner = upsert_user("owner", "owner@example.com")
    member_rw = upsert_user("member-rw", "member-rw@example.com")
    member_ro = upsert_user("member-ro", "member-ro@example.com")
    other_owner = upsert_user("other-owner", "other-owner@example.com")

    main_project = upsert_project(
        owner, "SQE Test Project", "sqebadgekeymain000001",
        "sqepingkeymain00000001", MAIN_RW_KEY, MAIN_RO_KEY,
    )
    other_project = upsert_project(
        other_owner, "Other Project", "sqebadgekeyother000001",
        "sqepingkeyother0000001", OTHER_RW_KEY, OTHER_RO_KEY,
    )

    Member.objects.get_or_create(user=member_rw, project=main_project,
                                 defaults={"role": "w"})
    Member.objects.get_or_create(user=member_ro, project=main_project,
                                 defaults={"role": "r"})

    one_hour, one_day = td(hours=1), td(days=1)
    checks = [
        upsert_check(main_project, "seed-new", status="new",
                     last_ping=None, alert_after=None),
        upsert_check(main_project, "seed-up", status="up",
                     last_ping=t - one_hour,
                     alert_after=t - one_hour + one_day + one_hour,
                     n_pings=1),
        upsert_check(main_project, "seed-grace", status="up",
                     last_ping=t - one_day - td(minutes=30),
                     alert_after=t + td(minutes=30),
                     n_pings=1),
        upsert_check(main_project, "seed-down", status="up",
                     last_ping=t - one_day - td(hours=2),
                     alert_after=t - one_hour,
                     n_pings=1),
        upsert_check(main_project, "seed-paused", status="paused",
                     last_ping=t - td(hours=2), alert_after=None, n_pings=1),
        upsert_check(main_project, "seed-paused-manual", status="paused",
                     last_ping=t - td(hours=2), alert_after=None, n_pings=1,
                     manual_resume=True),
        upsert_check(other_project, "other-up", status="up",
                     last_ping=t - one_hour,
                     alert_after=t - one_hour + one_day + one_hour,
                     n_pings=1),
    ]

    print("Seed complete. Accounts (password: %s):" % PASSWORD)
    for email in ("admin@example.com", "owner@example.com",
                  "member-rw@example.com", "member-ro@example.com",
                  "other-owner@example.com"):
        print("  ", email)
    print("Main project API keys:")
    print("   write:", MAIN_RW_KEY)
    print("   read: ", MAIN_RO_KEY)
    print("Other project write key:", OTHER_RW_KEY)
    print("Checks (persisted status vs display status from get_status()):")
    for check in checks:
        print("   %-22s persisted=%-7s display=%s" % (
            check.slug, check.status, check.get_status()))


if __name__ == "__main__":
    main()
