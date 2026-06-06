"""
Tests for the role-tagging foundation (Workstream 1).

These import only the light modules (schemas, auth_roles, admin_routes,
database) — never app.py / ai_brain — so they run without the AI stack.
DB access is faked; the live-migration idempotency test skips when there is no
DATABASE_URL.
"""

import os

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

import auth_roles
import admin_routes
import me_routes
from auth_roles import (
    require_consumer, require_institutional, require_admin,
    get_authenticated_user, fetch_or_create_role,
)
from schemas import AuthenticatedUser, UpdateUserRoleRequest, UpdateUserRoleResponse


# ---------------------------------------------------------------------------
# Fake DB plumbing
# ---------------------------------------------------------------------------
class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        self.conn.calls.append((" ".join(sql.split()), params))
        self.conn.last_sql = sql

    def fetchone(self):
        # Pop the next preset result, default None.
        if self.conn.results:
            return self.conn.results.pop(0)
        return None

    def close(self):
        pass


class FakeConn:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []
        self.committed = False
        self.rolled_back = False
        self.last_sql = ""

    def cursor(self, *a, **k):
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


# ===========================================================================
# 1. Migration idempotency (live DB — skipped without DATABASE_URL)
# ===========================================================================
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="no DATABASE_URL")
def test_migration_idempotent():
    import psycopg2
    import migrate_user_roles

    def schema_snapshot():
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name='profiles'
              AND column_name IN ('role','institutional_type','tenant_name')
            ORDER BY column_name
            """
        )
        cols = cur.fetchall()
        cur.execute("SELECT count(*) FROM profiles")
        n = cur.fetchone()[0]
        conn.close()
        return cols, n

    migrate_user_roles.migrate()
    snap1 = schema_snapshot()
    migrate_user_roles.migrate()  # second run
    snap2 = schema_snapshot()
    assert snap1 == snap2, "schema/data changed on the second migration run"


# ===========================================================================
# 2. Default role for new users
# ===========================================================================
def test_new_user_gets_consumer_default(monkeypatch):
    conn = FakeConn(results=[None])  # SELECT returns no profile row
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: conn)
    role, inst, tenant = fetch_or_create_role("11111111-1111-1111-1111-111111111111")
    assert (role, inst, tenant) == ("consumer", None, None)
    # An INSERT of a default consumer profile was attempted.
    assert any("INSERT INTO profiles" in sql and "'consumer'" in sql for sql, _ in conn.calls)


def test_legacy_role_coerced_to_consumer(monkeypatch):
    conn = FakeConn(results=[{"role": "smallholder", "institutional_type": None, "tenant_name": None}])
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: conn)
    role, inst, tenant = fetch_or_create_role("u")
    assert role == "consumer"  # legacy free-text value normalised


def test_institutional_role_resolved(monkeypatch):
    conn = FakeConn(results=[{"role": "institutional", "institutional_type": "buyer", "tenant_name": "Northern Tobacco"}])
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: conn)
    role, inst, tenant = fetch_or_create_role("u")
    assert (role, inst, tenant) == ("institutional", "buyer", "Northern Tobacco")


def test_role_lookup_degrades_without_db(monkeypatch):
    monkeypatch.setattr(auth_roles, "get_db_connection", lambda: None)
    assert fetch_or_create_role("u") == ("consumer", None, None)


# ===========================================================================
# 3. Admin endpoint
# ===========================================================================
def _admin_client(conn, token="secret-admin"):
    monkey_app = FastAPI()
    monkey_app.include_router(admin_routes.router)
    os.environ["ADMIN_TOKEN"] = token
    admin_routes.get_db_connection = lambda: conn  # type: ignore
    return TestClient(monkey_app, raise_server_exceptions=False)


def test_admin_flip_to_institutional(monkeypatch):
    conn = FakeConn(results=[{
        "role": "institutional", "institutional_type": "buyer",
        "tenant_name": "Northern Tobacco", "updated_at": "2026-06-06T00:00:00",
    }])
    client = _admin_client(conn)
    r = client.post(
        "/admin/users/abc/role",
        headers={"X-Admin-Token": "secret-admin"},
        json={"role": "institutional", "institutional_type": "buyer", "tenant_name": "Northern Tobacco"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "institutional"
    assert body["institutional_type"] == "buyer"
    assert body["tenant_name"] == "Northern Tobacco"
    # Parameterized UPDATE persisted the institutional values.
    update_call = [c for c in conn.calls if "UPDATE profiles" in c[0]][0]
    assert update_call[1] == ("institutional", "buyer", "Northern Tobacco", "abc")


def test_admin_institutional_requires_type():
    conn = FakeConn()
    client = _admin_client(conn)
    r = client.post(
        "/admin/users/abc/role",
        headers={"X-Admin-Token": "secret-admin"},
        json={"role": "institutional"},
    )
    assert r.status_code == 400


def test_admin_missing_token():
    conn = FakeConn()
    client = _admin_client(conn)
    r = client.post("/admin/users/abc/role", json={"role": "consumer"})
    assert r.status_code == 401


def test_admin_wrong_token():
    conn = FakeConn()
    client = _admin_client(conn, token="right-token")
    r = client.post(
        "/admin/users/abc/role",
        headers={"X-Admin-Token": "WRONG"},
        json={"role": "consumer"},
    )
    assert r.status_code == 401


def test_admin_user_not_found():
    conn = FakeConn(results=[None])  # UPDATE ... RETURNING yields no row
    client = _admin_client(conn)
    r = client.post(
        "/admin/users/ghost/role",
        headers={"X-Admin-Token": "secret-admin"},
        json={"role": "consumer"},
    )
    assert r.status_code == 404


def test_admin_flip_back_clears_institutional_fields():
    conn = FakeConn(results=[{
        "role": "consumer", "institutional_type": None,
        "tenant_name": None, "updated_at": "2026-06-06T00:00:00",
    }])
    client = _admin_client(conn)
    # Caller wrongly includes institutional fields with a consumer role.
    r = client.post(
        "/admin/users/abc/role",
        headers={"X-Admin-Token": "secret-admin"},
        json={"role": "consumer", "institutional_type": "buyer", "tenant_name": "X"},
    )
    assert r.status_code == 200
    update_call = [c for c in conn.calls if "UPDATE profiles" in c[0]][0]
    # institutional_type and tenant_name were cleared to None.
    assert update_call[1] == ("consumer", None, None, "abc")


def test_admin_get_role():
    conn = FakeConn(results=[{
        "role": "institutional", "institutional_type": "lender",
        "tenant_name": "AFC", "updated_at": "2026-06-06T00:00:00",
    }])
    client = _admin_client(conn)
    r = client.get("/admin/users/abc/role", headers={"X-Admin-Token": "secret-admin"})
    assert r.status_code == 200
    assert r.json()["institutional_type"] == "lender"


def test_admin_get_role_not_found():
    conn = FakeConn(results=[None])  # SELECT yields no profile row
    client = _admin_client(conn)
    r = client.get("/admin/users/ghost/role", headers={"X-Admin-Token": "secret-admin"})
    assert r.status_code == 404


def test_admin_token_unset_denies_all():
    # Safe default: with ADMIN_TOKEN unset, even a matching-looking header is denied.
    saved = os.environ.pop("ADMIN_TOKEN", None)
    try:
        app = FastAPI()
        app.include_router(admin_routes.router)
        admin_routes.get_db_connection = lambda: FakeConn()  # type: ignore
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/admin/users/abc/role", headers={"X-Admin-Token": "anything"})
        assert r.status_code == 401
    finally:
        if saved is not None:
            os.environ["ADMIN_TOKEN"] = saved


# ===========================================================================
# 3b. GET /me/role (Workstream 2)
# ===========================================================================
def _me_client(user: AuthenticatedUser):
    app = FastAPI()
    app.include_router(me_routes.router)
    app.dependency_overrides[me_routes.get_authenticated_user] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def test_me_role_returns_consumer():
    client = _me_client(AuthenticatedUser(user_id="u1", role="consumer"))
    r = client.get("/me/role")
    assert r.status_code == 200
    assert r.json() == {"user_id": "u1", "role": "consumer",
                        "institutional_type": None, "tenant_name": None,
                        "tenant_id": None, "tenant_ids": [], "member_role": None}


def test_me_role_returns_institutional_context():
    client = _me_client(AuthenticatedUser(
        user_id="u2", role="institutional", institutional_type="buyer", tenant_name="Northern Tobacco"))
    r = client.get("/me/role")
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "institutional"
    assert body["institutional_type"] == "buyer"
    assert body["tenant_name"] == "Northern Tobacco"


# ===========================================================================
# 4. AuthenticatedUser model validation
# ===========================================================================
def test_authuser_rejects_invalid_role():
    with pytest.raises(ValidationError):
        AuthenticatedUser(user_id="u", role="superadmin")  # type: ignore


def test_authuser_rejects_invalid_institutional_type():
    with pytest.raises(ValidationError):
        AuthenticatedUser(user_id="u", role="institutional", institutional_type="banker")  # type: ignore


def test_authuser_institutional_requires_type():
    with pytest.raises(ValidationError):
        AuthenticatedUser(user_id="u", role="institutional")


def test_authuser_consumer_ok():
    u = AuthenticatedUser(user_id="u", role="consumer")
    assert u.role == "consumer" and u.institutional_type is None


# ===========================================================================
# 5. Role guards
# ===========================================================================
def _guard_client(user: AuthenticatedUser):
    app = FastAPI()

    @app.get("/needs-consumer")
    def needs_consumer(u: AuthenticatedUser = Depends(require_consumer)):
        return {"role": u.role}

    @app.get("/needs-institutional")
    def needs_institutional(u: AuthenticatedUser = Depends(require_institutional)):
        return {"role": u.role}

    @app.get("/needs-admin")
    def needs_admin(u: AuthenticatedUser = Depends(require_admin)):
        return {"role": u.role}

    app.dependency_overrides[get_authenticated_user] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def test_consumer_blocked_from_institutional_endpoint():
    client = _guard_client(AuthenticatedUser(user_id="u", role="consumer"))
    assert client.get("/needs-institutional").status_code == 403


def test_institutional_blocked_from_consumer_endpoint():
    client = _guard_client(AuthenticatedUser(user_id="u", role="institutional", institutional_type="buyer"))
    assert client.get("/needs-consumer").status_code == 403


def test_institutional_allowed_on_institutional_endpoint():
    client = _guard_client(AuthenticatedUser(user_id="u", role="institutional", institutional_type="buyer"))
    r = client.get("/needs-institutional")
    assert r.status_code == 200 and r.json()["role"] == "institutional"


def test_admin_does_not_pass_consumer_or_institutional_guards():
    # Documented decision: admin is a distinct tier; guards check role equality.
    client = _guard_client(AuthenticatedUser(user_id="u", role="admin"))
    assert client.get("/needs-consumer").status_code == 403
    assert client.get("/needs-institutional").status_code == 403
    assert client.get("/needs-admin").status_code == 200
