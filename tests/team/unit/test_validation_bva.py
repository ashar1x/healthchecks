"""Equivalence partitioning and 3-point boundary values for timeout/grace (FR-01, FR-06 / BR-01).

BR-01: timeout and grace must be within 60..31536000 seconds, on the dashboard
(AddCheckForm, hc/front/forms.py:51,54) and in the API (Spec, hc/api/views.py:61).

Techniques (master prompt Phase 5 rule 3):
  * EP: one valid partition (in-range) and one invalid partition per violated
    constraint (below minimum, above maximum, wrong type, missing) - one
    invalid value per test;
  * 3-point BVA: just below, at, just above every limit
    (59/60/61 and 31535999/31536000/31536001) for each field.

The form is called directly (unit); the API boundary is asserted through the
test client (D1).  This file is behaviour evidence for BR-01; the API Spec and
the form live outside the measured coverage files (justification in
docs/08-unit-testing.md section 5).
"""
from __future__ import annotations

import json

import pytest

from datetime import timedelta as td

from django.test import Client

from hc.front.forms import AddCheckForm

MIN = 60
MAX = 31536000
THREE_POINT = [MIN - 1, MIN, MIN + 1, MAX - 1, MAX, MAX + 1]


def form_data(**overrides) -> dict:
    data = {
        "name": "bva check",
        "kind": "simple",
        "timeout": 60,
        "grace": 60,
        "tz": "UTC",
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize("field", ["timeout", "grace"])
@pytest.mark.parametrize("value", THREE_POINT, ids=[str(v) for v in THREE_POINT])
def test_FR06_BR01_add_check_form_three_point_bva(field: str, value: int) -> None:
    form = AddCheckForm(data=form_data(**{field: value}))
    in_range = MIN <= value <= MAX

    assert form.is_valid() is in_range
    if in_range:
        assert form.cleaned_data[field] == td(seconds=value)
    else:
        assert field in form.errors


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("timeout", "abc", "wrong type: not an integer"),
        ("grace", "-1", "below minimum after parsing"),
        ("timeout", None, "missing required field"),
    ],
    ids=["wrong-type", "negative", "missing"],
)
def test_FR06_BR01_add_check_form_invalid_partitions(
    field: str, value, reason: str
) -> None:
    data = form_data()
    if value is None:
        data.pop(field)
    else:
        data[field] = value

    form = AddCheckForm(data=data)
    assert form.is_valid() is False
    assert field in form.errors


@pytest.mark.parametrize(
    "field,value,expected_status",
    [
        ("timeout", MIN - 1, 400),       # just below minimum
        ("timeout", MIN, 201),           # at minimum
        ("timeout", MAX + 1, 400),       # just above maximum
        ("timeout", MAX, 201),           # at maximum
        ("grace", MIN - 1, 400),
        ("grace", MIN, 201),
        ("grace", MAX + 1, 400),
        ("grace", MAX, 201),
    ],
    ids=lambda p: f"{p}" if isinstance(p, int) else None,
)
def test_FR06_BR01_api_create_enforces_timeout_grace_bounds(
    client: Client,
    api_keys: dict[str, str],
    field: str,
    value: int,
    expected_status: int,
) -> None:
    payload = {"name": "api bva", "timeout": MIN, "grace": MIN, field: value}
    response = client.post(
        "/api/v3/checks/",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Api-Key": api_keys["rw"]},
    )
    assert response.status_code == expected_status
    if expected_status == 400:
        assert "error" in response.json()
    else:
        assert response.json()["status"] == "new"
