"""FR-01/FR-02/FR-04 API create, update and delete with read-back."""
from __future__ import annotations

import json

from django.test import Client

from hc.api.models import Check


def test_FR01_create_check_via_api_and_read_back(
    client: Client, api_keys: dict[str, str]
) -> None:
    response = client.post(
        "/api/v3/checks/",
        data=json.dumps({"name": "api-crud-create", "timeout": 3600, "grace": 600}),
        content_type="application/json",
        headers={"X-Api-Key": api_keys["rw"]},
    )
    assert response.status_code == 201

    listing = client.get("/api/v3/checks/", headers={"X-Api-Key": api_keys["rw"]})
    created = next(item for item in listing.json()["checks"] if item["name"] == "api-crud-create")
    assert created["status"] == "new"
    assert created["timeout"] == 3600
    assert created["grace"] == 600


def test_FR02_update_timeout_via_api_and_read_back(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    response = client.post(
        f"/api/v3/checks/{check.code}",
        data=json.dumps({"timeout": 7200}),
        content_type="application/json",
        headers={"X-Api-Key": api_keys["rw"]},
    )
    assert response.status_code == 200

    listing = client.get("/api/v3/checks/", headers={"X-Api-Key": api_keys["rw"]})
    updated = next(item for item in listing.json()["checks"] if item["name"] == check.name)
    assert updated["timeout"] == 7200


def test_FR04_delete_check_via_api_and_read_back(
    client: Client, api_keys: dict[str, str], check: Check
) -> None:
    response = client.delete(
        f"/api/v3/checks/{check.code}", headers={"X-Api-Key": api_keys["rw"]}
    )
    assert response.status_code == 200

    listing = client.get("/api/v3/checks/", headers={"X-Api-Key": api_keys["rw"]})
    assert all(item["name"] != check.name for item in listing.json()["checks"])
