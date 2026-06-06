"""
Tests for the tenant + grower data model (Workstream 3, Block 3).

Covers the new, isolated, testable surface without the AI stack:
  - field access helpers + aggregator.resolve_access (authorization),
  - admin tenant-management endpoints,
  - institutional grower-management endpoints.

Migration idempotency/backfill (J.1-2) requires a live Postgres and is skipped
without DATABASE_URL. Field<->grower linking on POST/PATCH /fields (J.23-25)
lives in app.py (which can't be imported here without openai) and is part of the
documented app.py long-tail — see docs/tenant_model_audit.md "Block 2 status".
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import admin_routes
import grower_routes
from auth_roles import user_can_access_field, user_can_modify_field
from schemas import AuthenticatedUser
import services.field_state.aggregator as agg


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------
class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        self.conn.calls.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.conn.one.pop(0) if self.conn.one else None

    def fetchall(self):
        return self.conn.many

    @property
    def rowcount(self):
        return self.conn.rowcount

    def close(self):
        pass


class FakeConn:
    def __init__(self, one=None, many=None, rowcount=1):
        self.one = list(one or [])
        self.many = many or []
        self.rowcount = rowcount
        self.calls = []
        self.committed = False

    def cursor(self, *a, **k):
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        pass


def _au(**kw):
    base = dict(user_id="u1", role="consumer")
    base.update(kw)
    return AuthenticatedUser(**base)


# ===========================================================================
# Authorization helpers (J.3-9)
# ===========================================================================
def test_consumer_can_access_own_tenant_field():
    u = _au(role="consumer", tenant_id="T1", tenant_ids=["T1"], member_role="owner")
    assert user_can_access_field(u, "T1") is True


def test_consumer_cannot_access_other_tenant_field():
    u = _au(role="consumer", tenant_id="T1", tenant_ids=["T1"], member_role="owner")
    assert user_can_access_field(u, "T2") is False


def test_institutional_access_within_and_across_tenants():
    u = _au(role="institutional", institutional_type="buyer",
            tenant_id="T9", tenant_ids=["T9"], member_role="officer")
    assert user_can_access_field(u, "T9") is True
    assert user_can_access_field(u, "TX") is False


def test_admin_can_access_any_field():
    u = _au(role="admin", tenant_ids=[])
    assert user_can_access_field(u, "anything") is True


def test_officer_can_modify_viewer_cannot():
    officer = _au(role="institutional", institutional_type="buyer", tenant_ids=["T1"], member_role="officer")
    viewer = _au(role="institutional", institutional_type="buyer", tenant_ids=["T1"], member_role="viewer")
    assert user_can_modify_field(officer, "T1") is True
    assert user_can_modify_field(viewer, "T1") is False
    # admin can always modify
    assert user_can_modify_field(_au(role="admin", tenant_ids=[]), "T1") is True


# resolve_access (404 vs 403) with tenant context, DB faked --------------------
def _patch_db(monkeypatch, conn):
    import database
    monkeypatch.setattr(database, "get_db_connection", lambda: conn)


def test_resolve_access_consumer_own_field(monkeypatch):
    _patch_db(monkeypatch, FakeConn(one=[{"id": "f1", "user_id": "u1", "tenant_id": "T1"}]))
    row = agg.resolve_access("f1", "u1", tenant_ids=["T1"])
    assert row["id"] == "f1"


def test_resolve_access_other_consumer_field_403(monkeypatch):
    _patch_db(monkeypatch, FakeConn(one=[{"id": "f1", "user_id": "other", "tenant_id": "T2"}]))
    with pytest.raises(agg.FieldAccessDenied):
        agg.resolve_access("f1", "u1", tenant_ids=["T1"])


def test_resolve_access_institutional_same_tenant(monkeypatch):
    _patch_db(monkeypatch, FakeConn(one=[{"id": "f1", "user_id": "creator", "tenant_id": "T9"}]))
    row = agg.resolve_access("f1", "officer-user", tenant_ids=["T9"])
    assert row["tenant_id"] == "T9"


def test_resolve_access_admin_any(monkeypatch):
    _patch_db(monkeypatch, FakeConn(one=[{"id": "f1", "user_id": "x", "tenant_id": "TZ"}]))
    row = agg.resolve_access("f1", "admin-user", tenant_ids=[], is_admin=True)
    assert row["id"] == "f1"


def test_resolve_access_missing_404(monkeypatch):
    _patch_db(monkeypatch, FakeConn(one=[None]))
    with pytest.raises(agg.FieldNotFound):
        agg.resolve_access("ghost", "u1", tenant_ids=["T1"])


# ===========================================================================
# Tenant management endpoints (J.10-15)
# ===========================================================================
def _admin_client(conn, token="secret-admin"):
    app = FastAPI()
    app.include_router(admin_routes.router)
    os.environ["ADMIN_TOKEN"] = token
    admin_routes.get_db_connection = lambda: conn  # type: ignore
    return TestClient(app, raise_server_exceptions=False)


_TENANT_ROW = {
    "id": "T1", "name": "Northern Tobacco", "tenant_type": "institutional",
    "institutional_type": "buyer", "created_at": "2026-06-06T00:00:00",
    "updated_at": "2026-06-06T00:00:00", "deleted_at": None,
}


def test_admin_creates_tenant():
    client = _admin_client(FakeConn(one=[_TENANT_ROW]))
    r = client.post("/admin/tenants", headers={"X-Admin-Token": "secret-admin"},
                    json={"name": "Northern Tobacco", "tenant_type": "institutional", "institutional_type": "buyer"})
    assert r.status_code == 200
    assert r.json()["tenant_type"] == "institutional"


def test_admin_create_institutional_requires_type():
    client = _admin_client(FakeConn())
    r = client.post("/admin/tenants", headers={"X-Admin-Token": "secret-admin"},
                    json={"name": "X", "tenant_type": "institutional"})
    assert r.status_code == 400


def test_admin_lists_tenants_filter_by_type():
    conn = FakeConn(many=[_TENANT_ROW])
    client = _admin_client(conn)
    r = client.get("/admin/tenants?tenant_type=institutional", headers={"X-Admin-Token": "secret-admin"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    # the type filter was applied as a bound parameter (not interpolated)
    assert any("tenant_type = %s" in sql and params == ("institutional",) for sql, params in conn.calls)


def test_admin_adds_member():
    member = {"tenant_id": "T1", "user_id": "u9", "member_role": "officer", "joined_at": "2026-06-06T00:00:00"}
    client = _admin_client(FakeConn(one=[member]))
    r = client.post("/admin/tenants/T1/members", headers={"X-Admin-Token": "secret-admin"},
                    json={"user_id": "u9", "member_role": "officer"})
    assert r.status_code == 200
    assert r.json()["member_role"] == "officer"


def test_admin_changes_member_role():
    member = {"tenant_id": "T1", "user_id": "u9", "member_role": "viewer", "joined_at": "2026-06-06T00:00:00"}
    client = _admin_client(FakeConn(one=[member]))
    r = client.patch("/admin/tenants/T1/members/u9", headers={"X-Admin-Token": "secret-admin"},
                     json={"member_role": "viewer"})
    assert r.status_code == 200
    assert r.json()["member_role"] == "viewer"


def test_admin_removes_member():
    client = _admin_client(FakeConn(rowcount=1))
    r = client.delete("/admin/tenants/T1/members/u9", headers={"X-Admin-Token": "secret-admin"})
    assert r.status_code == 204


def test_admin_tenants_requires_token():
    client = _admin_client(FakeConn())
    assert client.get("/admin/tenants").status_code == 401


# ===========================================================================
# Grower management endpoints (J.16-22)
# ===========================================================================
def _grower_client(conn, user: AuthenticatedUser):
    app = FastAPI()
    app.include_router(grower_routes.router)
    app.dependency_overrides[grower_routes.require_institutional] = lambda: user
    grower_routes.get_db_connection = lambda: conn  # type: ignore
    return TestClient(app, raise_server_exceptions=False)


_GROWER_ROW = {
    "id": "G1", "tenant_id": "T1", "name": "Tafadzwa M", "phone": None, "email": None,
    "coordinates": None, "claimed_by_user_id": None, "created_by_user_id": "u1",
    "notes": None, "created_at": "2026-06-06T00:00:00", "updated_at": "2026-06-06T00:00:00",
}
OWNER = AuthenticatedUser(user_id="u1", role="institutional", institutional_type="buyer",
                          tenant_id="T1", tenant_ids=["T1"], member_role="owner")
OFFICER = AuthenticatedUser(user_id="u2", role="institutional", institutional_type="buyer",
                            tenant_id="T1", tenant_ids=["T1"], member_role="officer")
VIEWER = AuthenticatedUser(user_id="u3", role="institutional", institutional_type="buyer",
                           tenant_id="T1", tenant_ids=["T1"], member_role="viewer")


def test_owner_creates_grower():
    client = _grower_client(FakeConn(one=[_GROWER_ROW]), OWNER)
    r = client.post("/tenants/me/growers", json={"name": "Tafadzwa M"})
    assert r.status_code == 200
    assert r.json()["name"] == "Tafadzwa M"


def test_officer_creates_grower():
    client = _grower_client(FakeConn(one=[_GROWER_ROW]), OFFICER)
    r = client.post("/tenants/me/growers", json={"name": "Tafadzwa M"})
    assert r.status_code == 200


def test_viewer_cannot_create_grower():
    client = _grower_client(FakeConn(one=[_GROWER_ROW]), VIEWER)
    r = client.post("/tenants/me/growers", json={"name": "Tafadzwa M"})
    assert r.status_code == 403


def test_grower_list_returns_active_only():
    # The fake returns whatever 'many' holds; assert the query filters deleted_at.
    conn = FakeConn(many=[_GROWER_ROW])
    client = _grower_client(conn, OWNER)
    r = client.get("/tenants/me/growers")
    assert r.status_code == 200 and len(r.json()) == 1
    assert any("deleted_at IS NULL" in sql for sql, _ in conn.calls)


def test_patch_grower_updates():
    existing = dict(_GROWER_ROW)
    updated = dict(_GROWER_ROW, name="New Name")
    # _fetch_grower opens its own conn (existing), then the UPDATE opens another.
    # Both use the same monkeypatched conn instance; queue both fetchone results.
    conn = FakeConn(one=[existing, updated])
    client = _grower_client(conn, OWNER)
    r = client.patch("/tenants/me/growers/G1", json={"name": "New Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"


def test_delete_grower_soft_deletes():
    conn = FakeConn(rowcount=1)
    client = _grower_client(conn, OWNER)
    r = client.delete("/tenants/me/growers/G1")
    assert r.status_code == 204
    assert any("deleted_at = NOW()" in sql for sql, _ in conn.calls)


# ===========================================================================
# Migration idempotency / backfill (J.1-2) — live DB only
# ===========================================================================
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="no DATABASE_URL")
def test_migrations_idempotent_and_backfill():
    import psycopg2
    import migrate_create_tenants
    import migrate_backfill_consumer_tenants
    import migrate_fields_to_tenants

    for _ in range(2):  # run twice → idempotent
        migrate_create_tenants.migrate()
        migrate_backfill_consumer_tenants.migrate()
        migrate_fields_to_tenants.migrate()

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fields WHERE tenant_id IS NULL")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT (SELECT COUNT(*) FROM profiles WHERE role='consumer'),"
                " (SELECT COUNT(*) FROM tenants WHERE tenant_type='consumer')")
    consumers, consumer_tenants = cur.fetchone()
    assert consumers == consumer_tenants
    cur.execute("SELECT COUNT(*) FROM profiles p LEFT JOIN tenant_members tm ON tm.user_id=p.id"
                " WHERE tm.user_id IS NULL AND p.role!='admin'")
    assert cur.fetchone()[0] == 0
    conn.close()
