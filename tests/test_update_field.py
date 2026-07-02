"""
Tests for PATCH /fields/{id} — field editing (Phase 4, field management).

Covers the validation branches (which run before any DB access) and the
happy-path UPDATE construction: whitelist mapping, crop-change re-derivation of
is_transplanted, and empty-string date normalization. The DB is faked by
overriding ``app.tenant_scoped_connection`` with a context manager that yields a
recording fake connection.
"""

from contextlib import contextmanager

import app
from deps import verify_token
from fastapi.testclient import TestClient


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        self.conn.calls.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.conn.results.pop(0) if self.conn.results else None

    def close(self):
        pass


class FakeConn:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []
        self.committed = False

    def cursor(self, *a, **k):
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def _client_with_db(conn, tenant_ids=("tenant-1",)):
    @contextmanager
    def fake_scope(user_id):
        yield conn, list(tenant_ids)

    app.tenant_scoped_connection = fake_scope  # type: ignore[assignment]
    app.app.dependency_overrides[verify_token] = lambda: "user-123"
    return TestClient(app.app, raise_server_exceptions=False)


def _plain_client():
    app.app.dependency_overrides[verify_token] = lambda: "user-123"
    return TestClient(app.app, raise_server_exceptions=False)


def _update_call(conn):
    return [c for c in conn.calls if "UPDATE fields" in c[0]][0]


def test_empty_payload_rejected():
    client = _plain_client()
    r = client.patch("/fields/f-1", json={})
    assert r.status_code == 400
    assert "No editable fields" in r.json()["detail"]


def test_blank_name_rejected():
    client = _plain_client()
    r = client.patch("/fields/f-1", json={"name": "   "})
    assert r.status_code == 400
    assert "cannot be empty" in r.json()["detail"]


def test_updates_whitelisted_columns_only():
    row = {"id": "f-1", "name": "New Name", "crop_type": "Maize", "variety": "SC 727",
           "planting_date": None, "transplant_date": None, "is_transplanted": False,
           "fertilizer_history": None}
    conn = FakeConn(results=[row])
    client = _client_with_db(conn)

    r = client.patch("/fields/f-1", json={"name": "New Name", "variety": "SC 727",
                                          "unknown_field": "ignored"})
    assert r.status_code == 200, r.text
    sql, params = _update_call(conn)
    assert "name = %s" in sql and "variety = %s" in sql
    assert "unknown_field" not in sql
    assert conn.committed


def test_crop_change_rederives_transplant_status():
    # Switching to a direct-seeded crop must set is_transplanted False and null
    # any stale transplant date.
    row = {"id": "f-1", "name": "F", "crop_type": "Maize", "variety": None,
           "planting_date": None, "transplant_date": None, "is_transplanted": False,
           "fertilizer_history": None}
    conn = FakeConn(results=[row])
    client = _client_with_db(conn)

    r = client.patch("/fields/f-1", json={"crop": "Maize"})
    assert r.status_code == 200, r.text
    sql, _ = _update_call(conn)
    assert "is_transplanted = %s" in sql
    assert "transplant_date = NULL" in sql


def test_transplanted_crop_sets_flag_true():
    row = {"id": "f-1", "name": "F", "crop_type": "Tomato", "variety": None,
           "planting_date": None, "transplant_date": None, "is_transplanted": True,
           "fertilizer_history": None}
    conn = FakeConn(results=[row])
    client = _client_with_db(conn)

    r = client.patch("/fields/f-1", json={"crop": "Tomato"})
    assert r.status_code == 200, r.text
    sql, params = _update_call(conn)
    assert "is_transplanted = %s" in sql
    # is_transplanted True must be among the bound params, transplant_date NOT nulled.
    assert True in params
    assert "transplant_date = NULL" not in sql


def test_missing_field_returns_404():
    conn = FakeConn(results=[None])  # UPDATE ... RETURNING found nothing
    client = _client_with_db(conn)
    r = client.patch("/fields/f-x", json={"name": "X"})
    assert r.status_code == 404


def test_blank_date_normalized_to_null():
    row = {"id": "f-1", "name": "F", "crop_type": "Maize", "variety": None,
           "planting_date": None, "transplant_date": None, "is_transplanted": False,
           "fertilizer_history": None}
    conn = FakeConn(results=[row])
    client = _client_with_db(conn)

    r = client.patch("/fields/f-1", json={"plantingDate": ""})
    assert r.status_code == 200, r.text
    sql, params = _update_call(conn)
    # The bound planting_date value must be None, not "".
    assert None in params
