"""State-transition tests for Check.ping (FR-07, FR-08, FR-09, FR-11 / BR-03).

Covers every ping-driven transition of the docs/01 section 6 BR-03 table plus
the disallowed attempt, and the paused + manual_resume decision as a full
2x2 decision table (both rule conditions independently):

  paused  manual_resume  ping applied?   result           test
  yes     yes            no  (-> 'ign')   stays paused     ..._manual_resume_true...
  yes     no             yes              leaves paused   ..._paused_without_manual_resume...
  no      yes            yes              normal ping      ..._manual_resume_flag_alone...
  no      no             yes              normal ping      ..._success_ping_sets_up...

D1: Check.ping is called directly on the model (DB is required because ping
runs in a transaction with select_for_update); time is frozen (tick=False),
never slept.  RISK-15: ping count and ping log are read back after every run.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta as td, timezone

import pytest
import time_machine

from django.contrib.auth.models import User

from hc.accounts.models import Profile, Project
from hc.api.models import Check, Flip, Ping

T0 = datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)
T1 = T0 + td(minutes=10)
GRACE = td(hours=1)
TIMEOUT = td(days=1)


def do_ping(
    check: Check,
    action: str = "success",
    *,
    when: datetime = T0,
    rid: uuid.UUID | None = None,
    exitstatus: int | None = None,
    body: bytes = b"",
) -> None:
    with time_machine.travel(when, tick=False):
        check.ping("127.0.0.1", "https", "GET", "sqe-unit-tests/1.0", body, action, rid, exitstatus)
    check.refresh_from_db()


def set_status(check: Check, status: str, **fields) -> None:
    Check.objects.filter(id=check.id).update(status=status, **fields)
    check.refresh_from_db()


def test_FR07_BR03_success_ping_sets_up_and_records_alert_window(check: Check) -> None:
    do_ping(check, "success")

    assert check.status == "up"
    assert check.n_pings == 1
    assert check.last_ping == T0
    # alert window: ping + timeout + grace (BR-02 derived from the new state)
    assert check.alert_after == T0 + TIMEOUT + GRACE

    flip = Flip.objects.get(owner=check)
    assert (flip.old_status, flip.new_status) == ("new", "up")
    assert flip.created == T0

    # RISK-15 read-back: one ping in, one row in the log, count and n agree
    ping = Ping.objects.get(owner=check)
    assert (check.n_pings, ping.n) == (1, 1)
    assert ping.created == T0


def test_FR09_BR03_fail_ping_sets_down_with_fail_flip_and_exitstatus(check: Check) -> None:
    do_ping(check, "fail", exitstatus=1)

    assert check.status == "down"
    assert check.last_ping == T0
    flip = Flip.objects.get(owner=check)
    assert (flip.old_status, flip.new_status, flip.reason) == ("new", "down", "fail")
    ping = Ping.objects.get(owner=check)
    assert ping.exitstatus == 1


def test_FR07_BR03_success_ping_on_down_check_returns_up(check: Check) -> None:
    """Allowed transition: down -> up (success ping)."""
    set_status(check, "down")
    do_ping(check, "success")
    assert check.status == "up"
    flip = Flip.objects.get(owner=check)
    assert (flip.old_status, flip.new_status) == ("down", "up")


def test_FR08_BR03_start_ping_marks_running_and_success_records_duration(check: Check) -> None:
    """Allowed: start ping -> 'started' display; matching rid success closes it."""
    rid = uuid.uuid4()
    do_ping(check, "start", rid=rid)

    assert check.last_start == T0
    assert check.last_start_rid == rid
    assert check.status == "new"  # start does not change the stored status
    with time_machine.travel(T0, tick=False):
        assert check.get_status(with_started=True) == "started"
    assert check.last_ping is None  # "Don't update last_ping field"

    do_ping(check, "success", rid=rid, when=T1)
    assert check.last_start is None
    assert check.last_duration == T1 - T0
    assert check.last_ping == T1
    assert check.status == "up"


def test_FR08_BR03_fail_ping_clears_running_state_regardless_of_rid(check: Check) -> None:
    """Running state exits on fail even when the rid does not match."""
    do_ping(check, "start", rid=uuid.uuid4())
    do_ping(check, "fail", rid=uuid.uuid4(), when=T1)

    assert check.last_start is None
    assert check.last_duration is None
    assert check.status == "down"


def test_FR08_BR03_success_ping_without_rid_clears_running_state(check: Check) -> None:
    """Running state exits on success with no rid (rid is None branch)."""
    do_ping(check, "start", rid=uuid.uuid4())
    do_ping(check, "success", rid=None, when=T1)

    assert check.last_start is None
    assert check.last_duration is None
    assert check.status == "up"


def test_FR08_BR03_success_ping_with_other_rid_keeps_running_state(check: Check) -> None:
    """Success with a *different* non-null rid leaves last_start untouched
    (another ping may still belong to the running probe)."""
    rid = uuid.uuid4()
    do_ping(check, "start", rid=rid)
    do_ping(check, "success", rid=uuid.uuid4(), when=T1)

    assert check.last_start == T0
    assert check.last_duration is None
    assert check.status == "up"


def test_FR11_BR03_manual_resume_true_ping_is_ignored_and_stays_paused(check: Check) -> None:
    """Decision rule (BR-02/BR-03): paused AND manual_resume -> action 'ign'.

    Status unchanged, no flip, ping logged with kind 'ign', last_ping not set.
    """
    set_status(check, "paused", manual_resume=True)
    do_ping(check, "success")

    assert check.status == "paused"
    assert check.last_ping is None
    assert check.n_pings == 1
    assert Flip.objects.filter(owner=check).count() == 0
    ping = Ping.objects.get(owner=check)
    assert ping.kind == "ign"


@pytest.mark.parametrize(
    "action,expected_status,expected_reason",
    [("success", "up", ""), ("fail", "down", "fail")],
)
def test_FR11_BR03_paused_without_manual_resume_leaves_paused_state(
    check: Check, action: str, expected_status: str, expected_reason: str
) -> None:
    """Second rule condition false: paused check leaves paused when pinged."""
    set_status(check, "paused", manual_resume=False)
    do_ping(check, action)

    assert check.status == expected_status
    flip = Flip.objects.get(owner=check)
    assert flip.old_status == "paused"
    assert flip.new_status == expected_status
    assert flip.reason == expected_reason


def test_FR11_BR03_manual_resume_flag_alone_does_not_ignore_ping(check: Check) -> None:
    """First rule condition false: manual_resume on a non-paused check is a
    normal ping (the rule needs paused AND manual_resume)."""
    set_status(check, "new", manual_resume=True)
    do_ping(check, "success")
    assert check.status == "up"


def test_FR07_BR03_repeated_pings_increment_count_and_log_every_ping(check: Check) -> None:
    """RISK-15: after two successes the counter and the log agree."""
    do_ping(check, "success")
    do_ping(check, "success", when=T1)

    assert check.n_pings == 2
    assert [p.n for p in Ping.objects.order_by("n")] == [1, 2]
    assert Ping.objects.filter(owner=check).count() == 2


def test_FR07_BR03_ping_records_metadata_truncates_ua_and_confirmation_link(
    check: Check,
) -> None:
    """Ping row stores the connection metadata; UA > 200 chars is truncated;
    a body containing 'confirm' sets has_confirmation_link."""
    long_ua = "u" * 300
    with time_machine.travel(T0, tick=False):
        check.ping(
            "10.0.0.1", "https", "POST", long_ua, b"please CONFIRM", "success", None
        )
    check.refresh_from_db()

    assert check.has_confirmation_link is True
    ping = Ping.objects.get(owner=check)
    assert (ping.remote_addr, ping.scheme, ping.method) == ("10.0.0.1", "https", "POST")
    assert ping.ua == "u" * 200
    assert ping.body_raw == b"please CONFIRM"


def test_FR07_BR03_no_confirmation_link_for_plain_body(check: Check) -> None:
    do_ping(check, "success", body=b"hello")
    check.refresh_from_db()
    assert check.has_confirmation_link is False


def test_FR07_BR03_ping_reaching_100_prunes_old_pings(
    db, owner: User, project: Project, check: Check
) -> None:
    """Every 100th ping prunes pings beyond the profile's ping_log_limit."""
    profile = Profile.objects.for_user(owner)
    profile.ping_log_limit = 1
    profile.save(update_fields=("ping_log_limit",))

    # Old ping rows below the future threshold (n_pings will become 100)
    for n in (1, 2):
        Ping.objects.create(
            owner=check, n=n, created=T0 - td(days=30),
            remote_addr="127.0.0.1", scheme="https", method="GET", ua="",
        )
    Check.objects.filter(id=check.id).update(n_pings=99)
    check.refresh_from_db()

    do_ping(check, "success")

    assert check.n_pings == 100
    # threshold = 100 - 1 = 99 -> old rows (n <= 99) gone, current ping kept
    assert [p.n for p in Ping.objects.filter(owner=check).order_by("n")] == [100]


def test_FR07_BR03_prune_of_empty_ping_log_is_a_no_op(check: Check) -> None:
    """prune() handles the empty log (Ping.DoesNotExist -> pass) without error."""
    check.prune()
    assert Ping.objects.filter(owner=check).count() == 0
