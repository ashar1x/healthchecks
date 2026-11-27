"""Controlled failure and recovery for the state-changing pause operation."""
from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from hc.api.models import Check, Flip


class DependencyUnavailableError(Exception):
    """Test double for an unavailable downstream dependency."""


def test_FR03_BR03_pause_recovers_without_duplicate_flip(
    client: Client, api_keys, check: Check, monkeypatch: pytest.MonkeyPatch
) -> None:
    url = reverse("hc-api-pause", args=[check.code])

    def fail_before_write(self, new_status, reason="", mark_as_processed=False) -> None:
        raise DependencyUnavailableError

    with monkeypatch.context() as patcher:
        patcher.setattr(Check, "create_flip", fail_before_write)
        with pytest.raises(DependencyUnavailableError):
            client.post(
                url,
                data=b"",
                content_type="application/json",
                headers={"X-Api-Key": api_keys["rw"]},
            )

    check.refresh_from_db()
    assert check.status == "new"
    assert Flip.objects.filter(owner=check).count() == 0

    response = client.post(
        url,
        data=b"",
        content_type="application/json",
        headers={"X-Api-Key": api_keys["rw"]},
    )
    assert response.status_code == 200
    check.refresh_from_db()
    assert check.status == "paused"
    assert Flip.objects.filter(owner=check).count() == 1
