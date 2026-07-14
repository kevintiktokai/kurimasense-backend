"""
Mock-fallback policy tests (production-readiness pass 2).

In a deployed environment (DATABASE_URL set) a database outage must surface as
an honest 503 — not MOCK_FIELDS-style demo data presented to a signed-in user
as if it were real. Local development without DATABASE_URL keeps mock mode;
ALLOW_MOCK_FALLBACK overrides in either direction.
"""

import pytest
from fastapi.testclient import TestClient

import app as app_module
from deps import verify_token, mock_fallback_allowed


@pytest.fixture
def client():
    app_module.app.dependency_overrides[verify_token] = lambda: "00000000-0000-0000-0000-00000000f0f0"
    c = TestClient(app_module.app, raise_server_exceptions=False)
    yield c
    app_module.app.dependency_overrides.clear()


# --- Policy ------------------------------------------------------------------

def test_no_database_url_means_mock_mode(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ALLOW_MOCK_FALLBACK", raising=False)
    assert mock_fallback_allowed() is True


def test_database_url_disables_mock_mode(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@example/db")
    monkeypatch.delenv("ALLOW_MOCK_FALLBACK", raising=False)
    assert mock_fallback_allowed() is False


def test_explicit_override_wins_both_ways(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@example/db")
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "true")
    assert mock_fallback_allowed() is True

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
    assert mock_fallback_allowed() is False


# --- Endpoint behavior with the DB down --------------------------------------
# Simulate the outage explicitly (get_db_connection -> None and
# tenant_scoped_connection -> RuntimeError) so the tests hold regardless of
# what other modules in the suite patch. Policy is flipped via
# ALLOW_MOCK_FALLBACK.

@pytest.fixture
def db_down(monkeypatch):
    monkeypatch.setattr(app_module, "get_db_connection", lambda: None)

    def _raise(*_a, **_kw):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(app_module, "tenant_scoped_connection", _raise)


def test_fields_returns_503_when_fallback_disabled(client, db_down, monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
    r = client.get("/fields", headers={"Authorization": "Bearer t"})
    assert r.status_code == 503, r.text
    assert "try again" in r.json()["detail"].lower()


def test_fields_returns_mock_data_when_fallback_enabled(client, db_down, monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "true")
    r = client.get("/fields", headers={"Authorization": "Bearer t"})
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_user_profile_never_fabricates_in_production_mode(client, db_down, monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
    r = client.get("/user", headers={"Authorization": "Bearer t"})
    assert r.status_code == 503, r.text


def test_chat_history_returns_503_when_fallback_disabled(client, db_down, monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
    r = client.get("/chat/history", headers={"Authorization": "Bearer t"})
    assert r.status_code == 503, r.text


def test_create_field_returns_503_when_fallback_disabled(client, db_down, monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
    r = client.post(
        "/fields",
        json={"name": "F", "crop": "Maize", "coordinates": [], "area": 1},
        headers={"Authorization": "Bearer t"},
    )
    assert r.status_code == 503, r.text
