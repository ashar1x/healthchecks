"""API key and role checks through Django's test client (FR-05, FR-12 / BR-04).

Master prompt D1: "Test the API and role rules through Django's test client".
Exercises hc/api/decorators.py (authorize, authorize_read, cors, _get_api_version)
exactly as the measured file in .coveragerc:

  * missing / short key      -> 401 "missing api key"
  * wrong key                -> 401 "wrong api key"
  * rw key reads, ro key reads (readonly payload: unique_key, no ping_url)
  * ro key cannot write      -> 401 (authorize accepts rw only)
  * key in the POST body     -> accepted; bad JSON / non-object -> 400
  * another project's key    -> 403 on this project's check
  * unknown UUID             -> 404
  * /api/v1/ /v2/ /v3/       -> request version reflected in update_url
  * CORS preflight (OPTIONS) -> 204 with headers; wrong method -> 405
"""
from __future__ import annotations

import json
import uuid

import pytest

from django.test import Client

from hc.api.models import Check

pytestmark = pytest.mark.django_db


def pause_url(check: Check) -> str:
    from django.urls import reverse

    return reverse("hc-api-pause", args=[check.code])


def test_FR12_BR04_missing_or_short_api_key_returns_401(client: Client) -> None:
    response = client.get("/api/v3/checks/")
    assert response.status_code == 401
    assert response.json() == {"error": "missing api key"}

    response = client.get("/api/v3/checks/", headers={"X-Api-Key": "short"})
    assert response.status_code == 401
    assert response.json() == {"error": "missing api key"}


def test_FR12_BR04_wrong_api_key_returns_401(client: Client) -> None:
    response = client.get("/api/v3/checks/", headers={"X-Api-Key": "x" * 32})
    assert response.status_code == 401
    assert response.json() == {"error": "wrong api key"}


def test_FR05_BR04_readonly_key_reads_with_readonly_payload(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    rw = client.get("/api/v3/checks/", headers={"X-Api-Key": api_keys["rw"]})
    ro = client.get("/api/v3/checks/", headers={"X-Api-Key": api_keys["ro"]})
    assert rw.status_code == 200 and ro.status_code == 200

    rw_item = rw.json()["checks"][0]
    ro_item = ro.json()["checks"][0]
    # rw payload carries the write URLs; ro payload only the unique_key
    assert rw_item["uuid"] == str(check.code)
    assert rw_item["ping_url"].endswith(str(check.code))
    assert "unique_key" not in rw_item
    assert "uuid" not in ro_item
    assert "ping_url" not in ro_item
    assert ro_item["unique_key"]


def test_FR03_BR04_readonly_key_cannot_pause(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    """authorize() on a write endpoint accepts rw keys only (BR-04 row)."""
    # Explicit empty JSON body: the test client otherwise sends a multipart
    # boundary as the body, which the JSON-only API rejects with 400.
    response = client.post(
        pause_url(check), data=b"", content_type="application/json",
        headers={"X-Api-Key": api_keys["ro"]},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "wrong api key"}
    check.refresh_from_db()
    assert check.status == "new"  # no state change


def test_FR03_BR04_api_key_in_post_body_is_accepted(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    """authorize() falls back to the JSON body for POST requests."""
    response = client.post(
        pause_url(check),
        data=json.dumps({"api_key": api_keys["rw"]}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "paused"


def test_FR12_BR04_unparseable_or_non_object_body_returns_400(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    response = client.post(
        pause_url(check), data="{not json", content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json() == {"error": "could not parse request body"}

    response = client.post(pause_url(check), data="[1, 2]", content_type="application/json")
    assert response.status_code == 400
    assert response.json() == {"error": "json validation error: value is not an object"}
    check.refresh_from_db()
    assert check.status == "new"


def test_FR05_BR04_other_projects_key_is_forbidden(
    client: Client, other_project_keys: dict[str, str], check: Check
) -> None:
    from django.urls import reverse

    url = reverse("hc-api-single", args=[check.code])
    response = client.get(url, headers={"X-Api-Key": other_project_keys["rw"]})
    assert response.status_code == 403


def test_FR12_BR04_unknown_check_uuid_returns_404(
    client: Client, api_keys: dict[str, str]
) -> None:
    from django.urls import reverse

    url = reverse("hc-api-single", args=[uuid.uuid4()])
    response = client.get(url, headers={"X-Api-Key": api_keys["rw"]})
    assert response.status_code == 404


@pytest.mark.parametrize("version", [1, 2, 3])
def test_FR05_BR04_api_version_is_set_from_url(
    client: Client, api_keys: dict[str, str], check: Check, version: int
) -> None:
    """/api/vN/ sets request.v; to_dict stamps it into update_url."""
    response = client.get(
        f"/api/v{version}/checks/", headers={"X-Api-Key": api_keys["rw"]}
    )
    assert response.status_code == 200
    item = response.json()["checks"][0]
    assert f"/api/v{version}/checks/" in item["update_url"]


def test_FR05_BR04_cors_preflight_and_disallowed_method(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    preflight = client.options(pause_url(check))
    assert preflight.status_code == 204
    assert preflight["Access-Control-Allow-Origin"] == "*"
    assert preflight["Access-Control-Allow-Headers"] == "X-Api-Key"
    assert "POST" in preflight["Access-Control-Allow-Methods"]

    wrong_method = client.get(pause_url(check))  # cors("POST") only
    assert wrong_method.status_code == 405
    assert wrong_method["Access-Control-Allow-Origin"] == "*"
