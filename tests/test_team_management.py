"""
Tests for team management + activities + assignments (migration 013).

Hermetic: exercise the pure authorization helpers and the route-level guards
with faked users — no DB, no network. DB-backed behaviours (last-admin
safeguard SQL, invite acceptance) are covered by the endpoint guards tested
here plus the constraint set in the migration itself.
"""

import pytest
from fastapi import HTTPException

from schemas import AuthenticatedUser
from auth_roles import (
    user_can_modify_field, user_can_manage_team, user_can_assign_fields,
)


def _user(member_role=None, role="institutional", tenant_ids=None, **kw):
    return AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000001",
        role=role,
        institutional_type="buyer" if role == "institutional" else None,
        tenant_id=(tenant_ids or ["t1"])[0] if tenant_ids != [] else None,
        tenant_ids=tenant_ids if tenant_ids is not None else ["t1"],
        member_role=member_role,
        **kw,
    )


# ── permission tiers ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("role,expected", [
    ("owner", True), ("admin", True),
    ("manager", False), ("agronomist", False), ("field_officer", False),
    ("analyst", False), ("viewer", False), ("officer", False), (None, False),
])
def test_manage_team_tier(role, expected):
    assert user_can_manage_team(_user(role)) is expected


def test_platform_admin_can_manage_any_team():
    assert user_can_manage_team(_user(None, role="admin", tenant_ids=[])) is True


@pytest.mark.parametrize("role,expected", [
    ("owner", True), ("admin", True), ("manager", True), ("officer", True),
    ("agronomist", False), ("field_officer", False), ("analyst", False),
    ("viewer", False), (None, False),
])
def test_assign_fields_tier(role, expected):
    assert user_can_assign_fields(_user(role)) is expected


@pytest.mark.parametrize("role,expected", [
    ("owner", True), ("admin", True), ("manager", True),
    ("agronomist", True), ("field_officer", True), ("officer", True),
    ("analyst", False), ("viewer", False),
])
def test_write_field_tier(role, expected):
    assert user_can_modify_field(_user(role), "t1") is expected


def test_write_field_requires_matching_tenant():
    assert user_can_modify_field(_user("owner"), "other-tenant") is False
    assert user_can_modify_field(_user("owner"), None) is False


# ── extended MemberRole vocabulary is accepted by the model ──────────────────

@pytest.mark.parametrize("role", [
    "owner", "admin", "manager", "agronomist", "field_officer",
    "analyst", "officer", "viewer",
])
def test_member_role_vocabulary(role):
    assert _user(role).member_role == role


# ── team route guards (no DB needed — they reject before any query) ──────────

def test_update_member_rejects_self_role_change():
    from team_routes import update_member
    from schemas import UpdateTeamMemberRequest
    me = _user("owner")
    with pytest.raises(HTTPException) as e:
        update_member(me.user_id, UpdateTeamMemberRequest(member_role="viewer"), me)
    assert e.value.status_code == 400


def test_update_member_rejects_self_suspension():
    from team_routes import update_member
    from schemas import UpdateTeamMemberRequest
    me = _user("admin")
    with pytest.raises(HTTPException) as e:
        update_member(me.user_id, UpdateTeamMemberRequest(status="suspended"), me)
    assert e.value.status_code == 400


def test_remove_member_rejects_self():
    from team_routes import remove_member
    me = _user("owner")
    with pytest.raises(HTTPException) as e:
        remove_member(me.user_id, me)
    assert e.value.status_code == 400


def test_team_management_requires_admin_role():
    from team_routes import list_invites
    with pytest.raises(HTTPException) as e:
        list_invites(_user("field_officer"))
    assert e.value.status_code == 403


def test_team_routes_require_tenant():
    from team_routes import list_members
    with pytest.raises(HTTPException) as e:
        list_members(_user("owner", tenant_ids=[]))
    assert e.value.status_code == 403


def test_assign_requires_manager_tier():
    from activity_routes import assign_field
    from schemas import AssignFieldRequest
    with pytest.raises(HTTPException) as e:
        assign_field("f1", AssignFieldRequest(assignee_user_id="u2"), _user("field_officer"))
    assert e.value.status_code == 403


def test_update_activity_requires_some_change():
    from activity_routes import update_activity
    from schemas import UpdateActivityRequest
    with pytest.raises(HTTPException) as e:
        update_activity("a1", UpdateActivityRequest(), _user("agronomist"))
    assert e.value.status_code == 400
