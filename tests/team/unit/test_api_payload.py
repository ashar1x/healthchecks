"""Full read-back assertions for the Check API payload (FR-02, BR-04).

The Phase 5 suite asserted response status codes and single fields, so mutmut
found many surviving mutants in ``Check.to_dict``: a change to a serialised
field was not observed by any assertion.  These tests read back every field of
a freshly created check through the API and assert the exact values, plus the
readonly variant (unique_key instead of the rw-only URLs).  They also pin the
``clamped_last_duration`` boundary at exactly MAX_DURATION.
"""
from __future__ import annotations

from datetime import timedelta as td

from django.conf import settings
from django.test import Client

from hc.api.models import MAX_DURATION, Check


def test_api_check_payload_exact_fields(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    response = client.get(
        f"/api/v3/checks/{check.code}", headers={"X-Api-Key": api_keys["rw"]}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "unit check"
    assert data["slug"] == ""
    assert data["tags"] == ""
    assert data["desc"] == ""
    assert data["grace"] == 3600
    assert data["timeout"] == 86400
    assert data["n_pings"] == 0
    assert data["status"] == "new"
    assert data["started"] is False
    assert data["last_ping"] is None
    assert data["next_ping"] is None
    assert data["manual_resume"] is False
    assert data["methods"] == ""
    assert data["subject"] == ""
    assert data["subject_fail"] == ""
    assert data["start_kw"] == ""
    assert data["success_kw"] == ""
    assert data["failure_kw"] == ""
    assert data["filter_subject"] is False
    assert data["filter_body"] is False
    assert data["filter_http_body"] is False
    assert data["filter_default_fail"] is False

    assert data["badge_url"] == f"{settings.SITE_ROOT}/b/2/{check.badge_key}.svg"
    assert data["uuid"] == str(check.code)
    assert data["ping_url"] == settings.PING_ENDPOINT + str(check.code)
    assert data["update_url"] == f"{settings.SITE_ROOT}/api/v3/checks/{check.code}"
    assert data["pause_url"] == data["update_url"] + "/pause"
    assert data["resume_url"] == data["update_url"] + "/resume"
    assert data["channels"] == ""
    assert "unique_key" not in data


def test_api_check_payload_readonly_key_returns_unique_key(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    response = client.get(
        f"/api/v3/checks/{check.code}", headers={"X-Api-Key": api_keys["ro"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unique_key"] == check.unique_key
    assert "uuid" not in data
    assert "ping_url" not in data
    assert "update_url" not in data


def test_clamped_last_duration_at_maximum_returns_none(check: Check) -> None:
    """BR-01 duration limit: the comparison is strictly less-than MAX_DURATION."""
    check.last_duration = MAX_DURATION
    assert check.clamped_last_duration() is None

    check.last_duration = MAX_DURATION - td(seconds=1)
    assert check.clamped_last_duration() == MAX_DURATION - td(seconds=1)
