"""
Tests for services.auth.api_key_auth and routers/admin_api_keys.

Run:
    cd backend
    python -m pytest tests/test_api_key_auth.py -v
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import bcrypt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth import api_key_auth as auth_module  # noqa: E402
from services.auth.api_key_auth import (  # noqa: E402
    ApiKeyContext,
    DEFAULT_PER_DAY,
    DEFAULT_PER_MINUTE,
    KEY_PREFIX,
    _coerce_rate_override,
    api_key_rate_limit_key,
    generate_api_key,
    get_api_key_context,
    get_rate_limits_for_context,
    parse_raw_key,
    revoke_api_key,
    verify_api_key,
)
from routers import admin_api_keys as admin_module  # noqa: E402
from routers.admin_api_keys import router as admin_router  # noqa: E402


# --------------------------------------------------------------------------- #
# In-memory api_keys table
# --------------------------------------------------------------------------- #

@dataclass
class _ApiKeyRow:
    id: str
    tenant_id: str
    key_hash: str
    name: str
    key_id_hex: Optional[str] = None
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool = True
    rate_limit_override: Optional[Dict[str, int]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FakeAuthDB:
    def __init__(self) -> None:
        self.rows: List[_ApiKeyRow] = []
        self._next_id = 0

    def connect(self):
        return _Conn(self)


class _Conn:
    def __init__(self, db: FakeAuthDB) -> None:
        self._db = db

    def cursor(self, cursor_factory=None):
        return _Cursor(self._db)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class _Cursor:
    def __init__(self, db: FakeAuthDB) -> None:
        self._db = db
        self._last: Any = None
        self.rowcount = 0

    def execute(self, sql: str, params: Any = ()) -> None:
        s = " ".join(sql.split())

        # ---- INSERT new key ----
        if "INSERT INTO api_keys" in s and "RETURNING id" in s:
            tenant_id, key_hash, key_id_hex, name, expires_at, override = params
            self._db._next_id += 1
            new_id = f"key-{self._db._next_id:08d}"
            override_dict = None
            if override is not None:
                import json as _json
                override_dict = _json.loads(override) if isinstance(override, str) else override
            self._db.rows.append(_ApiKeyRow(
                id=new_id,
                tenant_id=tenant_id,
                key_hash=key_hash,
                key_id_hex=key_id_hex,
                name=name,
                expires_at=expires_at,
                rate_limit_override=override_dict,
            ))
            self._last = {"id": new_id}
            self.rowcount = 1
            return

        # ---- SELECT by key_id_hex (verify path) ----
        if "FROM api_keys WHERE key_id_hex" in s:
            (key_id_hex,) = params
            row = next((r for r in self._db.rows if r.key_id_hex == key_id_hex), None)
            self._last = (
                {
                    "id": row.id,
                    "tenant_id": row.tenant_id,
                    "key_hash": row.key_hash,
                    "name": row.name,
                    "expires_at": row.expires_at,
                    "is_active": row.is_active,
                    "rate_limit_override": row.rate_limit_override,
                }
                if row else None
            )
            return

        # ---- UPDATE last_used_at ----
        if "UPDATE api_keys SET last_used_at" in s:
            (key_id,) = params
            for r in self._db.rows:
                if r.id == key_id:
                    r.last_used_at = datetime.now(timezone.utc)
                    self.rowcount = 1
                    break
            self._last = None
            return

        # ---- UPDATE is_active = FALSE (revoke) ----
        if "UPDATE api_keys SET is_active = FALSE" in s:
            (key_id,) = params
            self.rowcount = 0
            for r in self._db.rows:
                if r.id == key_id:
                    r.is_active = False
                    self.rowcount = 1
                    break
            self._last = None
            return

        # ---- list_api_keys ----
        if "FROM api_keys WHERE tenant_id" in s and "ORDER BY created_at" in s:
            (tenant_id,) = params
            self._last = [
                {
                    "id": r.id,
                    "tenant_id": r.tenant_id,
                    "name": r.name,
                    "created_at": r.created_at,
                    "expires_at": r.expires_at,
                    "last_used_at": r.last_used_at,
                    "is_active": r.is_active,
                    "rate_limit_override": r.rate_limit_override,
                    "key_id_hex": r.key_id_hex,
                }
                for r in self._db.rows if r.tenant_id == tenant_id
            ]
            return

        self._last = None

    def fetchone(self):
        if isinstance(self._last, list):
            return self._last[0] if self._last else None
        return self._last

    def fetchall(self):
        if isinstance(self._last, list):
            return self._last
        return []

    def close(self):
        pass


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

TENANT_A = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def db(monkeypatch):
    fake = FakeAuthDB()
    monkeypatch.setattr(auth_module, "get_db_connection", fake.connect)
    return fake


@pytest.fixture
def admin_app(db, monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "admin-secret-token")
    app = FastAPI()
    app.include_router(admin_router)
    return TestClient(app)


# --------------------------------------------------------------------------- #
# parse_raw_key
# --------------------------------------------------------------------------- #

def test_parse_raw_key_accepts_well_formed_key():
    raw = f"{KEY_PREFIX}abcdef0123456789.somesecretpart"
    parsed = parse_raw_key(raw)
    assert parsed == ("abcdef0123456789", "somesecretpart")


def test_parse_raw_key_rejects_missing_prefix():
    assert parse_raw_key("abc.xyz") is None


def test_parse_raw_key_rejects_missing_secret():
    assert parse_raw_key(f"{KEY_PREFIX}abcdef0123456789.") is None


def test_parse_raw_key_rejects_short_id():
    assert parse_raw_key(f"{KEY_PREFIX}abc.secret") is None


def test_parse_raw_key_rejects_non_hex_id():
    assert parse_raw_key(f"{KEY_PREFIX}xyzxyzxyzxyzxyzx.secret") is None


# --------------------------------------------------------------------------- #
# Override coercion
# --------------------------------------------------------------------------- #

def test_coerce_rate_override_defaults_when_missing():
    assert _coerce_rate_override(None) == (DEFAULT_PER_MINUTE, DEFAULT_PER_DAY)


def test_coerce_rate_override_reads_dict_values():
    pm, pd = _coerce_rate_override({"per_minute": 250, "per_day": 50_000})
    assert pm == 250 and pd == 50_000


def test_coerce_rate_override_reads_json_string():
    pm, pd = _coerce_rate_override('{"per_minute": 5}')
    assert pm == 5
    assert pd == DEFAULT_PER_DAY  # untouched


def test_coerce_rate_override_ignores_non_positive():
    assert _coerce_rate_override({"per_minute": 0, "per_day": -10}) == (
        DEFAULT_PER_MINUTE, DEFAULT_PER_DAY,
    )


# --------------------------------------------------------------------------- #
# generate_api_key + verify_api_key roundtrip
# --------------------------------------------------------------------------- #

def test_generate_then_verify_roundtrip(db):
    raw, key_id = generate_api_key(tenant_id=TENANT_A, name="bank-acme", expires_days=30)
    assert raw.startswith(KEY_PREFIX)
    parsed = parse_raw_key(raw)
    assert parsed is not None
    assert len(parsed[0]) == 16

    ctx = verify_api_key(raw)
    assert ctx is not None
    assert ctx.tenant_id == TENANT_A
    assert ctx.key_id == key_id
    assert ctx.name == "bank-acme"
    assert ctx.rate_limit_per_minute == DEFAULT_PER_MINUTE
    assert ctx.rate_limit_per_day == DEFAULT_PER_DAY


def test_generate_with_overrides_round_trips(db):
    raw, _ = generate_api_key(
        tenant_id=TENANT_A,
        name="enterprise",
        rate_limit_override={"per_minute": 1000, "per_day": 500_000},
    )
    ctx = verify_api_key(raw)
    assert ctx is not None
    assert ctx.rate_limit_per_minute == 1000
    assert ctx.rate_limit_per_day == 500_000


def test_verify_returns_none_for_unknown_key(db):
    raw = f"{KEY_PREFIX}deadbeef00112233.bogus"
    assert verify_api_key(raw) is None


def test_verify_returns_none_for_wrong_secret(db):
    raw, _ = generate_api_key(tenant_id=TENANT_A, name="x")
    parsed = parse_raw_key(raw)
    assert parsed is not None
    forged = f"{KEY_PREFIX}{parsed[0]}.totally-wrong-secret"
    assert verify_api_key(forged) is None


def test_verify_returns_none_for_expired_key(db):
    raw, key_id = generate_api_key(tenant_id=TENANT_A, name="x")
    # Force the row to be expired in the past.
    db.rows[0].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert verify_api_key(raw) is None


def test_verify_returns_none_for_disabled_key(db):
    raw, _ = generate_api_key(tenant_id=TENANT_A, name="x")
    db.rows[0].is_active = False
    assert verify_api_key(raw) is None


def test_verify_updates_last_used_at(db):
    raw, _ = generate_api_key(tenant_id=TENANT_A, name="x")
    assert db.rows[0].last_used_at is None
    verify_api_key(raw)
    assert db.rows[0].last_used_at is not None


def test_generate_rejects_blank_name(db):
    with pytest.raises(ValueError):
        generate_api_key(tenant_id=TENANT_A, name="")


def test_generate_rejects_non_positive_expiry(db):
    with pytest.raises(ValueError):
        generate_api_key(tenant_id=TENANT_A, name="x", expires_days=0)


def test_revoke_marks_row_inactive(db):
    raw, key_id = generate_api_key(tenant_id=TENANT_A, name="x")
    assert revoke_api_key(key_id) is True
    assert db.rows[0].is_active is False
    assert verify_api_key(raw) is None
    # Second revoke is a no-op (returns False).
    assert revoke_api_key("does-not-exist") is False


# --------------------------------------------------------------------------- #
# get_api_key_context dependency
# --------------------------------------------------------------------------- #

def test_get_api_key_context_dependency_resolves_via_test_client(db):
    raw, _ = generate_api_key(tenant_id=TENANT_A, name="d")
    app = FastAPI()

    @app.get("/echo")
    def _echo(ctx: ApiKeyContext = __import__("fastapi").Depends(get_api_key_context)):
        return {"tenant_id": ctx.tenant_id, "name": ctx.name}

    client = TestClient(app)
    r = client.get("/echo", headers={"X-API-Key": raw})
    assert r.status_code == 200
    assert r.json()["tenant_id"] == TENANT_A
    assert r.json()["name"] == "d"

    r2 = client.get("/echo", headers={"X-API-Key": "garbage"})
    assert r2.status_code == 401

    r3 = client.get("/echo")
    assert r3.status_code == 401


# --------------------------------------------------------------------------- #
# api_key_rate_limit_key
# --------------------------------------------------------------------------- #

def test_rate_limit_key_buckets_by_key_id_hex():
    class _Req:
        def __init__(self, headers):
            self.headers = headers
            self.client = None
    raw = f"{KEY_PREFIX}abcdef0123456789.secret"
    bucket = api_key_rate_limit_key(_Req({"x-api-key": raw}))
    assert bucket == "key:abcdef0123456789"


def test_rate_limit_key_falls_back_to_ip_when_unkeyed():
    class _Client:
        host = "203.0.113.1"

    class _Req:
        def __init__(self):
            self.headers = {}
            self.client = _Client()

    bucket = api_key_rate_limit_key(_Req())
    assert bucket == "ip:203.0.113.1"


def test_get_rate_limits_for_context_format():
    ctx = ApiKeyContext(
        key_id="k", tenant_id=TENANT_A, name="n",
        rate_limit_per_minute=42, rate_limit_per_day=4242,
    )
    assert get_rate_limits_for_context(ctx) == ("42/minute", "4242/day")


# --------------------------------------------------------------------------- #
# Admin endpoints
# --------------------------------------------------------------------------- #

def test_admin_create_returns_raw_key_only_once(admin_app):
    r = admin_app.post(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "admin-secret-token"},
        json={"name": "bank-acme", "expires_days": 30},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["raw_key"].startswith(KEY_PREFIX)
    assert body["tenant_id"] == TENANT_A
    assert body["name"] == "bank-acme"
    assert body["expires_at"] is not None

    # The raw key must not appear in subsequent list responses.
    r2 = admin_app.get(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "admin-secret-token"},
    )
    assert r2.status_code == 200
    assert all("raw_key" not in k for k in r2.json()["keys"])


def test_admin_create_with_rate_limit_overrides_persists_them(admin_app, db):
    r = admin_app.post(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "admin-secret-token"},
        json={
            "name": "enterprise",
            "rate_limit_per_minute": 500,
            "rate_limit_per_day": 100_000,
        },
    )
    assert r.status_code == 201
    raw_key = r.json()["raw_key"]
    ctx = verify_api_key(raw_key)
    assert ctx is not None
    assert ctx.rate_limit_per_minute == 500
    assert ctx.rate_limit_per_day == 100_000


def test_admin_list_returns_metadata_only(admin_app):
    admin_app.post(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "admin-secret-token"},
        json={"name": "k1"},
    )
    admin_app.post(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "admin-secret-token"},
        json={"name": "k2"},
    )
    r = admin_app.get(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "admin-secret-token"},
    )
    assert r.status_code == 200
    body = r.json()
    names = {k["name"] for k in body["keys"]}
    assert names == {"k1", "k2"}


def test_admin_delete_marks_key_revoked(admin_app, db):
    create = admin_app.post(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "admin-secret-token"},
        json={"name": "to-revoke"},
    )
    key_id = create.json()["key_id"]
    raw = create.json()["raw_key"]

    r = admin_app.delete(
        f"/admin/api_keys/{key_id}",
        headers={"X-Admin-Token": "admin-secret-token"},
    )
    assert r.status_code == 200
    assert r.json()["revoked"] is True

    # Subsequent verification fails.
    assert verify_api_key(raw) is None

    # Deleting an unknown key returns 404.
    r2 = admin_app.delete(
        "/admin/api_keys/does-not-exist",
        headers={"X-Admin-Token": "admin-secret-token"},
    )
    assert r2.status_code == 404


def test_admin_endpoints_require_admin_token(admin_app):
    r = admin_app.post(
        f"/admin/tenants/{TENANT_A}/api_keys",
        json={"name": "no-auth"},
    )
    assert r.status_code == 401
    r = admin_app.post(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "wrong-token"},
        json={"name": "wrong-auth"},
    )
    assert r.status_code == 401


def test_admin_endpoints_503_when_token_not_configured(monkeypatch, db):
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    app = FastAPI()
    app.include_router(admin_router)
    client = TestClient(app)
    r = client.post(
        f"/admin/tenants/{TENANT_A}/api_keys",
        headers={"X-Admin-Token": "anything"},
        json={"name": "x"},
    )
    assert r.status_code == 503


# --------------------------------------------------------------------------- #
# Rate limiting via slowapi
# --------------------------------------------------------------------------- #

def test_slowapi_returns_429_when_rate_exceeded(db, monkeypatch):
    """
    Wire a tiny app with a 2/minute limit keyed on the API key, then verify
    the third request gets 429. Uses memory backend so it's deterministic.
    """
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from starlette.responses import JSONResponse

    raw, _ = generate_api_key(tenant_id=TENANT_A, name="rl-test")

    limiter = Limiter(key_func=api_key_rate_limit_key, default_limits=["2/minute"])
    app = FastAPI()
    app.state.limiter = limiter

    def _handler(request, exc):
        return JSONResponse(status_code=429, content={"detail": "rate-limited"})

    app.add_exception_handler(RateLimitExceeded, _handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/ping")
    def ping(ctx: ApiKeyContext = __import__("fastapi").Depends(get_api_key_context)):
        return {"ok": True}

    client = TestClient(app)
    headers = {"X-API-Key": raw}
    r1 = client.get("/ping", headers=headers)
    r2 = client.get("/ping", headers=headers)
    r3 = client.get("/ping", headers=headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
