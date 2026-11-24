"""Pause and resume: allowed and disallowed state transitions (FR-03 / BR-03, BR-04).

The same rules are asserted on both surfaces through Django's test client
(master prompt D1), which is also where the BR-03 disallowed transitions live
("not paused -> resume attempt"):

  API   (hc/api/views.py:565-611)      dashboard (hc/front/views.py:832-875)
  pause already paused  -> 200, no 2nd flip   -> 302 redirect, no 2nd flip
  resume non-paused     -> 409                -> 400        [candidate defect A-03]
  resume paused         -> 200, status 'new'  -> 302, status 'new'
  ro key                -> 401                ro member -> 403, anon -> 302 login
  other project's key   -> 403                unknown check -> 404

A-03 is asserted as OBSERVED behaviour with a comment; it is filed as a defect
in Phase 11, not silently normalised here.
"""
from __future__ import annotations

from datetime import datetime, timedelta as td, timezone

import pytest
import time_machine

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from hc.api.models import Check, Flip

NOW = datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)
GRACE = td(hours=1)
TIMEOUT = td(days=1)


def api_pause(check: Check) -> str:
    return reverse("hc-api-pause", args=[check.code])


def api_resume(check: Check) -> str:
    return reverse("hc-api-resume", args=[check.code])


def make_paused(check: Check, **fields) -> None:
    Check.objects.filter(id=check.id).update(status="paused", **fields)
    check.refresh_from_db()


def post_api(client: Client, url: str, key: str):
    """POST with an explicit empty JSON body.

    The test client otherwise sends a multipart boundary as the body, which
    the JSON-only authorize() correctly rejects with 400 - a test artifact,
    not app behaviour (probed: empty JSON body -> the expected 401/200).
    """
    return client.post(
        url, data=b"", content_type="application/json", headers={"X-Api-Key": key}
    )


# ---------------------------------------------------------------- API surface


def test_FR03_BR03_api_pause_sets_paused_and_marks_flip_processed(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    response = post_api(client, api_pause(check), api_keys["rw"])
    assert response.status_code == 200
    assert response.json()["status"] == "paused"

    check.refresh_from_db()
    assert (check.status, check.last_start, check.alert_after) == ("paused", None, None)
    flip = Flip.objects.get(owner=check)
    assert (flip.old_status, flip.new_status) == ("new", "paused")
    assert flip.processed == flip.created  # pause flips are pre-processed


def test_FR03_BR03_api_repeat_pause_is_idempotent_without_second_flip(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    first = post_api(client, api_pause(check), api_keys["rw"])
    second = post_api(client, api_pause(check), api_keys["rw"])
    assert first.status_code == 200 and second.status_code == 200
    assert second.json()["status"] == "paused"
    assert Flip.objects.filter(owner=check).count() == 1  # no second flip


def test_FR03_BR03_api_resume_returns_paused_check_to_new(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    make_paused(check, last_ping=NOW - TIMEOUT)
    response = post_api(client, api_resume(check), api_keys["rw"])
    assert response.status_code == 200
    assert response.json()["status"] == "new"

    check.refresh_from_db()
    assert check.status == "new"
    assert check.last_ping is None  # resume clears ping history references
    flip = Flip.objects.latest("created")
    assert flip.new_status == "new"


@pytest.mark.parametrize("status", ["new", "up", "down"])
def test_FR03_BR03_api_resume_is_disallowed_for_non_paused_states(
    client: Client, api_keys: dict[str, str], check: Check, status: str
) -> None:
    """BR-03 disallowed transition: resume from a non-paused state -> 409,
    no state change, no flip (hc/api/views.py:600-601)."""
    Check.objects.filter(id=check.id).update(status=status)
    check.refresh_from_db()

    response = post_api(client, api_resume(check), api_keys["rw"])
    assert response.status_code == 409
    assert response.content == b"check is not paused"

    check.refresh_from_db()
    assert check.status == status
    assert Flip.objects.filter(owner=check).count() == 0


def test_FR03_BR03_api_resume_is_disallowed_while_in_grace_window(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    """Disallowed from the derived state 'grace' too: stored status is 'up'
    inside the grace window, resume is still refused and the display status
    stays 'grace'."""
    grace_start = NOW - GRACE // 2
    Check.objects.filter(id=check.id).update(
        status="up", last_ping=grace_start - TIMEOUT
    )
    check.refresh_from_db()
    with time_machine.travel(NOW, tick=False):
        assert check.get_status() == "grace"

    response = post_api(client, api_resume(check), api_keys["rw"])
    assert response.status_code == 409

    check.refresh_from_db()
    with time_machine.travel(NOW, tick=False):
        assert check.get_status() == "grace"


def test_FR03_BR04_readonly_key_cannot_pause(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    response = post_api(client, api_pause(check), api_keys["ro"])
    assert response.status_code == 401
    check.refresh_from_db()
    assert check.status == "new"


def test_FR03_BR04_other_projects_key_cannot_pause(
    client: Client, other_project_keys: dict[str, str], check: Check
) -> None:
    response = post_api(client, api_pause(check), other_project_keys["rw"])
    assert response.status_code == 403
    check.refresh_from_db()
    assert check.status == "new"


def test_FR12_BR04_unknown_check_pause_returns_404(
    client: Client, api_keys: dict[str, str]
) -> None:
    import uuid as uuid_module

    url = reverse("hc-api-pause", args=[uuid_module.uuid4()])
    response = post_api(client, url, api_keys["rw"])
    assert response.status_code == 404


# ----------------------------------------------------------- dashboard surface


def test_FR03_BR03_dashboard_pause_and_resume_redirect(
    client: Client, owner: User, check: Check
) -> None:
    client.force_login(owner)

    paused = client.post(reverse("hc-pause", args=[check.code]))
    assert paused.status_code == 302
    check.refresh_from_db()
    assert check.status == "paused"

    resumed = client.post(reverse("hc-resume", args=[check.code]))
    assert resumed.status_code == 302
    check.refresh_from_db()
    assert check.status == "new"
    assert check.last_ping is None


def test_FR03_BR03_dashboard_repeat_pause_is_idempotent_without_second_flip(
    client: Client, owner: User, check: Check
) -> None:
    client.force_login(owner)
    client.post(reverse("hc-pause", args=[check.code]))
    client.post(reverse("hc-pause", args=[check.code]))
    assert Flip.objects.filter(owner=check).count() == 1
    check.refresh_from_db()
    assert check.status == "paused"


def test_FR03_BR03_dashboard_resume_disallowed_for_non_paused_returns_400(
    client: Client, owner: User, check: Check
) -> None:
    """Same condition as the API's 409, dashboard returns 400.

    [Candidate defect A-03 - filed in Phase 11.] Behaviour asserted as observed.
    """
    client.force_login(owner)
    response = client.post(reverse("hc-resume", args=[check.code]))
    assert response.status_code == 400
    check.refresh_from_db()
    assert check.status == "new"
    assert Flip.objects.filter(owner=check).count() == 0


def test_FR03_BR04_readonly_member_cannot_pause_dashboard(
    client: Client, ro_member: User, check: Check
) -> None:
    client.force_login(ro_member)
    response = client.post(reverse("hc-pause", args=[check.code]))
    assert response.status_code == 403
    check.refresh_from_db()
    assert check.status == "new"


def test_FR03_BR04_rw_member_can_pause_dashboard(
    client: Client, rw_member: User, check: Check
) -> None:
    client.force_login(rw_member)
    response = client.post(reverse("hc-pause", args=[check.code]))
    assert response.status_code == 302
    check.refresh_from_db()
    assert check.status == "paused"


def test_FR03_BR04_unauthenticated_dashboard_pause_redirects_to_login(
    client: Client, check: Check
) -> None:
    response = client.post(reverse("hc-pause", args=[check.code]))
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")
    check.refresh_from_db()
    assert check.status == "new"
