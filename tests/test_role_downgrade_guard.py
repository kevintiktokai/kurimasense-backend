"""
Institutional role downgrade guard (Depth fix).

A member of an institutional tenant must resolve to role 'institutional' even if
profiles.role was reset to 'consumer' by a stray profile write — tenant
membership wins, so an institutional owner can't be silently downgraded (which
would route them to the consumer dashboard and hide their portfolio).

Pure-ish unit tests: the new helper is tested against a fake DB; the promotion
in get_authenticated_user is tested by mocking its sub-lookups + a fake `deps`
module (the real one pulls the AI stack and isn't importable here).
"""

import sys
import types

import auth_roles
from auth_roles import fetch_primary_institutional_tenant, get_authenticated_user


# ---------------------------------------------------------------------------
# Fake DB (fetchone-driven), mirroring tests/test_user_roles.py
# ---------------------------------------------------------------------------
class _Cur:
    def __init__(self, conn): self.conn = conn
    def execute(self, sql, params=None): self.conn.calls.append((" ".join(sql.split()), params))
    def fetchone(self): return self.conn.results.pop(0) if self.conn.results else None
    def fetchall(self): return []
    def close(self): pass


class _Conn:
    def __init__(self, results=None): self.results = list(results or []); self.calls = []
    def cursor(self, *a, **k): return _Cur(self)
    def close(self): pass


# ---------------------------------------------------------------------------
# fetch_primary_institutional_tenant
# ---------------------------------------------------------------------------
def test_returns_type_and_name_for_institutional_member(monkeypatch):
    conn = _Conn(results=[{"institutional_type": "buyer", "name": "Kurima"}])
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: conn)
    assert fetch_primary_institutional_tenant("u") == ("buyer", "Kurima")
    # query filters to institutional, non-deleted tenants
    sql = conn.calls[0][0]
    assert "tenant_type = 'institutional'" in sql and "deleted_at IS NULL" in sql


def test_none_when_no_institutional_membership(monkeypatch):
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: _Conn(results=[]))
    assert fetch_primary_institutional_tenant("u") is None


def test_defaults_type_when_tenant_type_missing(monkeypatch):
    conn = _Conn(results=[{"institutional_type": None, "name": "Acme"}])
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: conn)
    # invalid/missing institutional_type still yields a valid type so the
    # promoted AuthenticatedUser passes validation
    assert fetch_primary_institutional_tenant("u") == ("buyer", "Acme")


def test_coerces_invalid_type(monkeypatch):
    conn = _Conn(results=[{"institutional_type": "banker", "name": "Acme"}])
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: conn)
    assert fetch_primary_institutional_tenant("u") == ("buyer", "Acme")


def test_degrades_without_db(monkeypatch):
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: None)
    assert fetch_primary_institutional_tenant("u") is None


# ---------------------------------------------------------------------------
# get_authenticated_user promotion
# ---------------------------------------------------------------------------
def _fake_deps(monkeypatch, user_id="user-1"):
    m = types.ModuleType("deps")
    m.verify_token = lambda authorization=None: user_id
    monkeypatch.setitem(sys.modules, "deps", m)


def test_consumer_profile_promoted_when_institutional_member(monkeypatch):
    _fake_deps(monkeypatch)
    monkeypatch.setattr(auth_roles, "fetch_or_create_role", lambda uid: ("consumer", None, None))
    monkeypatch.setattr(auth_roles, "fetch_tenant_context", lambda uid: ("t1", ["t1"], "owner"))
    monkeypatch.setattr(auth_roles, "fetch_primary_institutional_tenant", lambda uid: ("buyer", "Kurima"))

    user = get_authenticated_user("Bearer x")
    assert user.role == "institutional"
    assert user.institutional_type == "buyer"
    assert user.tenant_name == "Kurima"
    assert user.member_role == "owner"


def test_no_promotion_when_not_institutional_member(monkeypatch):
    _fake_deps(monkeypatch)
    monkeypatch.setattr(auth_roles, "fetch_or_create_role", lambda uid: ("consumer", None, None))
    monkeypatch.setattr(auth_roles, "fetch_tenant_context", lambda uid: ("t1", ["t1"], "viewer"))
    monkeypatch.setattr(auth_roles, "fetch_primary_institutional_tenant", lambda uid: None)

    user = get_authenticated_user("Bearer x")
    assert user.role == "consumer"
    assert user.institutional_type is None


def test_no_promotion_without_tenant(monkeypatch):
    _fake_deps(monkeypatch)
    monkeypatch.setattr(auth_roles, "fetch_or_create_role", lambda uid: ("consumer", None, None))
    monkeypatch.setattr(auth_roles, "fetch_tenant_context", lambda uid: (None, [], None))
    # guard must not even consult the institutional lookup when there's no tenant
    called = {"n": 0}
    def _spy(uid): called["n"] += 1; return ("buyer", "X")
    monkeypatch.setattr(auth_roles, "fetch_primary_institutional_tenant", _spy)

    user = get_authenticated_user("Bearer x")
    assert user.role == "consumer"
    assert called["n"] == 0


def test_admin_not_demoted_or_reclassified(monkeypatch):
    _fake_deps(monkeypatch)
    monkeypatch.setattr(auth_roles, "fetch_or_create_role", lambda uid: ("admin", None, None))
    monkeypatch.setattr(auth_roles, "fetch_tenant_context", lambda uid: ("t1", ["t1"], "owner"))
    called = {"n": 0}
    monkeypatch.setattr(auth_roles, "fetch_primary_institutional_tenant",
                        lambda uid: (called.__setitem__("n", called["n"] + 1) or ("buyer", "X")))

    user = get_authenticated_user("Bearer x")
    assert user.role == "admin"
    assert called["n"] == 0  # admins skip the guard entirely


def test_already_institutional_skips_extra_lookup(monkeypatch):
    _fake_deps(monkeypatch)
    monkeypatch.setattr(auth_roles, "fetch_or_create_role", lambda uid: ("institutional", "lender", "Stanbic"))
    monkeypatch.setattr(auth_roles, "fetch_tenant_context", lambda uid: ("t1", ["t1"], "officer"))
    called = {"n": 0}
    monkeypatch.setattr(auth_roles, "fetch_primary_institutional_tenant",
                        lambda uid: (called.__setitem__("n", called["n"] + 1) or ("buyer", "X")))

    user = get_authenticated_user("Bearer x")
    assert user.role == "institutional"
    assert user.institutional_type == "lender"   # original profile values kept
    assert user.tenant_name == "Stanbic"
    assert called["n"] == 0  # no redundant query for an already-institutional user
