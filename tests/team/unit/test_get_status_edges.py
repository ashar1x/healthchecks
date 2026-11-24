"""Equivalence partitions and helper branches around Check.get_status (FR-10, BR-02).

Complements the MCC table (test_get_status_mcc.py):

  * stored-status equivalence partition: status in (new, paused, down) is one
    partition (docs/01 BR-02 C3) - "new" is realised throughout the MCC table,
    here the other two representatives;
  * get_grace_start per check kind (simple / cron / oncalendar), the
    with_started min() rule and the never-elapses rule;
  * going_down_after, cached_status, clamped_last_duration (FR-08 display).

D1: direct calls on unsaved Check() objects, frozen time (tick=False),
no sleeping, no production changes.
"""
from __future__ import annotations

from datetime import datetime, timedelta as td, timezone

import pytest
import time_machine

from hc.api.models import Check

NOW = datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)
GRACE = td(hours=1)
TIMEOUT = td(days=1)


def make_check(**kwargs) -> Check:
    fields: dict = dict(kind="simple", status="up", timeout=TIMEOUT, grace=GRACE, tz="UTC")
    fields.update(kwargs)
    return Check(**fields)


@pytest.mark.parametrize("status", ["paused", "down"])
def test_FR10_BR02_status_partition_stored_status_returned_as_is(status: str) -> None:
    """EP: stored status in (new, paused, down) -> returned unchanged.

    "new" is covered by every MCC row with A4 = 1 (e.g. R0011111).
    """
    check = make_check(status=status, last_ping=NOW - TIMEOUT - 2 * GRACE)
    with time_machine.travel(NOW, tick=False):
        assert check.get_status() == status


def test_FR10_BR02_get_grace_start_simple_up_is_last_ping_plus_timeout() -> None:
    check = make_check(last_ping=NOW - TIMEOUT)
    with time_machine.travel(NOW, tick=False):
        assert check.get_grace_start(with_started=False) == NOW
        # last_start is None -> the with_started branch is skipped, same result
        assert check.get_grace_start(with_started=True) == NOW


@pytest.mark.parametrize("status", ["new", "paused", "down"])
def test_FR10_BR02_get_grace_start_none_for_non_up_status(status: str) -> None:
    """get_grace_start returns None for every non-up state (docstring contract)."""
    check = make_check(status=status, last_ping=NOW - TIMEOUT)  # no last_start
    with time_machine.travel(NOW, tick=False):
        assert check.get_grace_start(with_started=False) is None
        assert check.get_grace_start(with_started=True) is None


@pytest.mark.parametrize("status", ["new", "paused"])
def test_FR10_BR02_get_grace_start_with_started_returns_last_start_for_non_up(
    status: str,
) -> None:
    """Observed: the with_started min() rule only skips status=down, so a
    new/paused check with last_start set returns last_start, not None
    (hc/api/models.py:334). Asserted as observed."""
    last_start = NOW - GRACE // 2
    check = make_check(status=status, last_ping=NOW - TIMEOUT, last_start=last_start)
    with time_machine.travel(NOW, tick=False):
        assert check.get_grace_start(with_started=True) == last_start


def test_FR10_BR02_get_grace_start_cron_up_is_next_scheduled_run() -> None:
    check = make_check(kind="cron", schedule="0 0 * * *", last_ping=NOW)
    with time_machine.travel(NOW, tick=False):
        grace_start = check.get_grace_start(with_started=False)
    assert grace_start == datetime(2026, 11, 25, 0, 0, tzinfo=timezone.utc)


def test_FR10_BR02_get_grace_start_oncalendar_up_is_next_scheduled_run() -> None:
    check = make_check(kind="oncalendar", schedule="2027-01-01 00:00:00", last_ping=NOW)
    with time_machine.travel(NOW, tick=False):
        grace_start = check.get_grace_start(with_started=False)
    assert grace_start == datetime(2027, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_FR10_BR02_get_grace_start_oncalendar_without_next_run_is_none() -> None:
    """A schedule with no occurrence after last_ping never elapses -> None.

    This is the witness for MCC condition A5 (grace_start is None), row R0010111.
    """
    check = make_check(kind="oncalendar", schedule="2020-01-01 00:00:00", last_ping=NOW)
    with time_machine.travel(NOW, tick=False):
        assert check.get_grace_start(with_started=False) is None


def test_FR10_BR02_get_grace_start_with_started_takes_earlier_last_start() -> None:
    """with_started=True returns min(next elapse, last_start) when last_start wins."""
    last_start = NOW - GRACE // 2
    check = make_check(last_ping=NOW - TIMEOUT, last_start=last_start)
    with time_machine.travel(NOW, tick=False):
        assert check.get_grace_start(with_started=True) == last_start


def test_FR10_BR02_get_grace_start_with_started_skips_when_status_down() -> None:
    """The min() rule is skipped for status=down (condition status != 'down')."""
    check = make_check(status="down", last_ping=NOW - TIMEOUT, last_start=NOW - GRACE // 2)
    with time_machine.travel(NOW, tick=False):
        assert check.get_grace_start(with_started=True) is None


def test_FR10_BR02_going_down_after_adds_grace_to_grace_start() -> None:
    check = make_check(last_ping=NOW - TIMEOUT - GRACE // 2)
    with time_machine.travel(NOW, tick=False):
        assert check.going_down_after() == (NOW - GRACE // 2) + GRACE


def test_FR10_BR02_going_down_after_none_without_grace_start() -> None:
    check = make_check(status="new")
    with time_machine.travel(NOW, tick=False):
        assert check.going_down_after() is None


def test_FR10_BR02_cached_status_reports_down_after_grace_end() -> None:
    check = make_check(last_ping=NOW - TIMEOUT - 2 * GRACE)
    with time_machine.travel(NOW, tick=False):
        assert check.cached_status == "down"


@pytest.mark.parametrize(
    "last_duration,expected",
    [
        (td(minutes=5), td(minutes=5)),  # below MAX_DURATION (72h): clamp passes it through
        (td(hours=73), None),           # above MAX_DURATION: clamped to None
        (None, None),                   # not set
    ],
)
def test_FR08_BR03_clamped_last_duration(last_duration: td | None, expected: td | None) -> None:
    check = make_check()
    check.last_duration = last_duration
    assert check.clamped_last_duration() == expected
