"""
Regression tests for POST /fields tenant stamping.

Workstream 3 made ``fields.tenant_id`` NOT NULL, but ``create_field`` kept
inserting without it — so every consumer "add field" returned a 500:

    null value in column "tenant_id" of relation "fields" violates not-null
    constraint

These tests assert the INSERT now carries the caller's owner ``tenant_id``,
covering both the normal (membership exists) path and the auto-provision path
for a brand-new user who has no ``tenant_members`` row yet.

DB access is faked; the AI stack is imported via ``app`` but never exercised.
"""

import app
from deps import verify_token
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fake DB plumbing — fetchone() pops preset results in call order.
# ---------------------------------------------------------------------------
class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        self.conn.calls.append((" ".join(sql.split()), params))

    def fetchone(self):
        if self.conn.results:
            return self.conn.results.pop(0)
        return None

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeConn:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []
        self.committed = False
        self.rolled_back = False

    def cursor(self, *a, **k):
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def _client(conn):
    app.get_db_connection = lambda: conn  # type: ignore[assignment]
    app.app.dependency_overrides[verify_token] = lambda: "user-123"
    return TestClient(app.app, raise_server_exceptions=False)


def _insert_fields_call(conn):
    return [c for c in conn.calls if "INSERT INTO fields" in c[0]][0]


def test_create_field_stamps_existing_tenant_id():
    # tenant_members SELECT -> existing owner tenant; fields INSERT RETURNING id.
    conn = FakeConn(results=[{"tenant_id": "tenant-existing"}, {"id": "field-1"}])
    client = _client(conn)

    r = client.post("/fields", json={"name": "North Block", "crop": "Maize"})

    assert r.status_code == 200, r.text
    assert r.json() == {"status": "success", "id": "field-1"}

    sql, params = _insert_fields_call(conn)
    assert "tenant_id" in sql
    # user_id is the 5th bound param, tenant_id the 6th (see VALUES order).
    assert params[4] == "user-123"
    assert params[5] == "tenant-existing"
    # No tenant was provisioned because the user already had a membership.
    assert not any("INSERT INTO tenants" in c[0] for c in conn.calls)
    assert conn.committed


def test_create_field_blank_dates_stored_as_null():
    """An optional, untouched date input arrives as "" — Postgres rejects '' for
    type ``date`` and the whole INSERT 500s, so the field silently fails to save.
    The empty strings must be normalized to NULL before binding."""
    conn = FakeConn(results=[{"tenant_id": "tenant-existing"}, {"id": "field-3"}])
    client = _client(conn)

    r = client.post("/fields", json={
        "name": "Blank Date Block",
        "crop": "Maize",
        "plantingDate": "",
        "transplantDate": "",
    })

    assert r.status_code == 200, r.text

    sql, params = _insert_fields_call(conn)
    # planting_date is the 7th bound param, transplant_date the 8th (VALUES order).
    assert params[6] is None
    assert params[7] is None
    assert conn.committed


def test_create_field_keeps_real_dates():
    """A genuine date passes through untouched."""
    conn = FakeConn(results=[{"tenant_id": "tenant-existing"}, {"id": "field-4"}])
    client = _client(conn)

    r = client.post("/fields", json={
        "name": "Dated Block",
        "crop": "Maize",
        "plantingDate": "2026-06-24",
    })

    assert r.status_code == 200, r.text
    sql, params = _insert_fields_call(conn)
    assert params[6] == "2026-06-24"


def test_create_field_provisions_tenant_when_user_has_none():
    # tenant_members SELECT -> None (no membership) triggers provisioning:
    #   INSERT profiles (no fetch), SELECT name, INSERT tenants RETURNING id,
    #   INSERT tenant_members (no fetch), then fields INSERT RETURNING id.
    conn = FakeConn(results=[
        None,                       # tenant_members lookup: no row
        {"name": "User abcd"},      # profiles name lookup
        {"id": "tenant-new"},       # INSERT tenants RETURNING id
        {"id": "field-2"},          # INSERT fields RETURNING id
    ])
    client = _client(conn)

    r = client.post("/fields", json={"name": "South Block", "crop": "Wheat"})

    assert r.status_code == 200, r.text
    assert r.json() == {"status": "success", "id": "field-2"}

    # A consumer tenant + owner membership were created for the new user.
    assert any("INSERT INTO tenants" in c[0] for c in conn.calls)
    member_call = [c for c in conn.calls if "INSERT INTO tenant_members" in c[0]][0]
    assert member_call[1] == ("tenant-new", "user-123")

    sql, params = _insert_fields_call(conn)
    assert params[4] == "user-123"
    assert params[5] == "tenant-new"
