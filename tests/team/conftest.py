"""Shared fixtures for the team's test suites (tests/team/).

Unit tests call business logic directly (D1); client tests exercise API and
role rules through Django's test client.  Fixtures build the smallest state
that matches docs/01-scope-and-test-basis.md (roles: project owner, rw member,
ro member, rw key, ro key - BR-04).
"""
from __future__ import annotations

import pytest
from django.contrib.auth.models import User

from hc.accounts.models import Member, Profile, Project
from hc.api.models import Check


@pytest.fixture
def owner(db) -> User:
    """Project owner (always read-write, docs/01 section 7)."""
    return User.objects.create(username="owner", email="owner@example.com")


@pytest.fixture
def project(db, owner: User) -> Project:
    # badge_key is unique with no default: upstream always sets it explicitly,
    # a second project with "" would hit UNIQUE constraint failed.
    project = Project.objects.create(name="SQE project", owner=owner, badge_key="sqe")
    # The app creates profiles lazily (Profile.objects.for_user); do it here so
    # check-limit logic in API views sees a real profile. Local default (no
    # payments) sets check_limit = 10000 (docs/01 assumption A-05).
    Profile.objects.for_user(owner)
    return project


@pytest.fixture
def api_keys(project: Project) -> dict[str, str]:
    """Fresh rw and ro API keys (raw values as presented to the user)."""
    rw_key = project.set_api_key()
    ro_key = project.set_api_key_readonly()
    project.save(update_fields=("api_key", "api_key_readonly"))
    return {"rw": rw_key, "ro": ro_key}


@pytest.fixture
def check(project: Project) -> Check:
    """A freshly created check in status 'new' (FR-01 state)."""
    return Check.objects.create(project=project, name="unit check")


@pytest.fixture
def rw_member(db, project: Project) -> User:
    user = User.objects.create(username="rw-member", email="rw@example.com")
    Member.objects.create(user=user, project=project, role=Member.Role.REGULAR)
    return user


@pytest.fixture
def ro_member(db, project: Project) -> User:
    user = User.objects.create(username="ro-member", email="ro@example.com")
    Member.objects.create(user=user, project=project, role=Member.Role.READONLY)
    return user


@pytest.fixture
def other_project_keys(db) -> dict[str, str]:
    """A second, unrelated project's rw key (cross-project checks, BR-04)."""
    other_owner = User.objects.create(username="other-owner", email="other@example.com")
    other_project = Project.objects.create(
        name="Other project", owner=other_owner, badge_key="other"
    )
    Profile.objects.for_user(other_owner)
    rw_key = other_project.set_api_key()
    other_project.save(update_fields=("api_key",))
    return {"rw": rw_key}
