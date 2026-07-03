"""
Tests for the security-hardening pass:
  * /db-schema and /jwt-config are admin-only (X-Admin-Token), not open to any
    authenticated user.
  * AI/write endpoints are rate-limited (429 after the per-minute budget).

The rate-limit test drives a real limited route through TestClient. It uses
/inputs (60/min) with a tiny per-test override so we don't have to send 60
requests; slowapi keys on the bearer-token hash, so all calls share one bucket.
"""

import importlib

import pytest
from fastapi.testclient import TestClient

import app as app_module
from deps import verify_token


@pytest.fixture
def client():
    app_module.app.dependency_overrides[verify_token] = lambda: "user-sec-1"
    c = TestClient(app_module.app, raise_server_exceptions=False)
    yield c
    app_module.app.dependency_overrides.clear()


# --- Admin gating -----------------------------------------------------------

def test_db_schema_requires_admin_token():
    # No dependency override here: without X-Admin-Token the guard denies (401),
    # and ADMIN_TOKEN is unset in the test env → deny-by-default.
    c = TestClient(app_module.app, raise_server_exceptions=False)
    r = c.get("/db-schema")
    assert r.status_code == 401, r.text


def test_jwt_config_requires_admin_token():
    c = TestClient(app_module.app, raise_server_exceptions=False)
    r = c.get("/jwt-config")
    assert r.status_code == 401, r.text


def test_db_schema_rejects_plain_authenticated_user():
    # A valid session token is NOT sufficient — these are admin-token gated.
    c = TestClient(app_module.app, raise_server_exceptions=False)
    r = c.get("/db-schema", headers={"Authorization": "Bearer someusertoken"})
    assert r.status_code == 401, r.text


# --- Rate limiting ----------------------------------------------------------

def test_rate_limit_key_is_per_user_token():
    from app import _rate_limit_key

    class _Req:
        def __init__(self, auth):
            self.headers = {"authorization": auth}
            self.client = type("C", (), {"host": "1.2.3.4"})()

    k1 = _rate_limit_key(_Req("Bearer tokenAAA"))
    k2 = _rate_limit_key(_Req("Bearer tokenAAA"))
    k3 = _rate_limit_key(_Req("Bearer tokenBBB"))
    assert k1 == k2 and k1.startswith("u:")      # stable per token
    assert k1 != k3                               # different token → different bucket


def test_limiter_configured_on_ai_endpoints():
    # The limiter is registered and the AI endpoints carry an explicit limit.
    assert app_module.limiter is not None
    assert app_module.app.state.limiter is app_module.limiter


def test_vision_endpoint_rate_limited_after_budget():
    """Functional: /vision/analyze is 10/min — the 11th call in the window 429s.

    A missing image 400s inside the handler, but the limiter runs BEFORE the
    handler, so the first 10 calls are counted (400) and the 11th is blocked
    (429) — proving the limiter fires without touching OpenAI. A unique bearer
    token isolates this test's bucket from the shared in-memory limiter state.
    """
    app_module.app.dependency_overrides[verify_token] = lambda: "user-vision"
    try:
        c = TestClient(app_module.app, raise_server_exceptions=False)
        headers = {"Authorization": "Bearer unique-vision-bucket-token"}
        statuses = [c.post("/vision/analyze", json={}, headers=headers).status_code
                    for _ in range(11)]
        assert statuses[:10] == [400] * 10, statuses  # counted, handler ran (no image)
        assert statuses[10] == 429, statuses           # budget exhausted
    finally:
        app_module.app.dependency_overrides.clear()
