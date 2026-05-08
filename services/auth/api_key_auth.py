"""
API key auth for the institutional B2B endpoints.

Key format
----------
Raw API key:  ks_<key_id_hex>.<random_secret>
  - key_id_hex: 16 hex chars stored in api_keys.key_id_hex (indexed). Used
    for fast row lookup. Embedding the lookup id in the raw key lets us
    avoid scanning the table on every request.
  - random_secret: URL-safe base64 of 32 random bytes. Bcrypt-hashed and
    stored in api_keys.key_hash; never persisted in plaintext.
  - The full raw key is shown to the user exactly once (at create time)
    and never reproducible afterwards.

Verification
------------
parse → look up by key_id_hex → bcrypt.checkpw(secret, key_hash) → context.
On success, last_used_at is bumped and an ApiKeyContext is returned
(tenant_id + per-key rate-limit overrides). On failure, None.

Admin auth
----------
The admin management endpoints share an X-Admin-Token header validated
against the ADMIN_API_TOKEN env var. constant-time comparison.
"""
from __future__ import annotations

import json
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import bcrypt
from fastapi import Header, HTTPException, Request, status
from psycopg2.extras import RealDictCursor

from database import get_db_connection

logger = logging.getLogger(__name__)

KEY_PREFIX = "ks_"
DEFAULT_PER_MINUTE = 100
DEFAULT_PER_DAY = 10_000


# --------------------------------------------------------------------------- #
# Context
# --------------------------------------------------------------------------- #

@dataclass
class ApiKeyContext:
    """The authenticated API key context handed to route handlers."""
    key_id: str          # api_keys.id
    tenant_id: str
    name: str
    rate_limit_per_minute: int
    rate_limit_per_day: int


# --------------------------------------------------------------------------- #
# Raw-key generation / parsing
# --------------------------------------------------------------------------- #

def _new_secret() -> str:
    """32 bytes of randomness, URL-safe base64, stripped of '=' padding."""
    return secrets.token_urlsafe(32)


def _new_key_id_hex() -> str:
    """16 hex chars (8 random bytes)."""
    return secrets.token_hex(8)


def _format_raw_key(key_id_hex: str, secret: str) -> str:
    return f"{KEY_PREFIX}{key_id_hex}.{secret}"


def parse_raw_key(raw: str) -> Optional[Tuple[str, str]]:
    """Return (key_id_hex, secret), or None if the format doesn't match."""
    if not raw or not raw.startswith(KEY_PREFIX):
        return None
    body = raw[len(KEY_PREFIX):]
    if "." not in body:
        return None
    key_id_hex, secret = body.split(".", 1)
    if not key_id_hex or not secret:
        return None
    if len(key_id_hex) != 16 or any(c not in "0123456789abcdef" for c in key_id_hex.lower()):
        return None
    return key_id_hex.lower(), secret


def _bcrypt_hash(secret: str) -> str:
    return bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _bcrypt_verify(secret: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(secret.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# Rate-limit override JSONB shape
# --------------------------------------------------------------------------- #

def _coerce_rate_override(raw: Any) -> Tuple[int, int]:
    """Resolve a (per_minute, per_day) tuple from a rate_limit_override blob."""
    per_min = DEFAULT_PER_MINUTE
    per_day = DEFAULT_PER_DAY
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = None
    if isinstance(raw, dict):
        if isinstance(raw.get("per_minute"), int) and raw["per_minute"] > 0:
            per_min = raw["per_minute"]
        if isinstance(raw.get("per_day"), int) and raw["per_day"] > 0:
            per_day = raw["per_day"]
    return per_min, per_day


# --------------------------------------------------------------------------- #
# DB ops
# --------------------------------------------------------------------------- #

def generate_api_key(
    tenant_id: str,
    name: str,
    expires_days: Optional[int] = None,
    rate_limit_override: Optional[Dict[str, int]] = None,
) -> Tuple[str, str]:
    """
    Mint a new API key. Returns (raw_key, key_id).

    The raw key is shown ONCE to the caller and never reproducible after
    return. Only the bcrypt hash of its secret is persisted.
    """
    if not name:
        raise ValueError("name is required")
    secret = _new_secret()
    key_id_hex = _new_key_id_hex()
    raw_key = _format_raw_key(key_id_hex, secret)
    key_hash = _bcrypt_hash(secret)

    expires_at: Optional[datetime] = None
    if expires_days is not None:
        if expires_days <= 0:
            raise ValueError("expires_days must be positive")
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

    override_json = json.dumps(rate_limit_override) if rate_limit_override else None

    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Database unavailable — cannot create API key")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            INSERT INTO api_keys (
                tenant_id, key_hash, key_id_hex, name,
                expires_at, rate_limit_override, is_active
            )
            VALUES (%s::uuid, %s, %s, %s, %s, %s::jsonb, TRUE)
            RETURNING id
            """,
            (tenant_id, key_hash, key_id_hex, name, expires_at, override_json),
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
    finally:
        conn.close()
    return raw_key, str(row["id"])


def verify_api_key(raw_key: Optional[str]) -> Optional[ApiKeyContext]:
    """
    Validate a raw API key. Returns the ApiKeyContext on success, None otherwise.
    Updates last_used_at on success (best-effort — failures here don't reject
    the request).
    """
    if not raw_key:
        return None
    parsed = parse_raw_key(raw_key)
    if parsed is None:
        return None
    key_id_hex, secret = parsed

    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT id, tenant_id, key_hash, name, expires_at, is_active,
                   rate_limit_override
            FROM api_keys
            WHERE key_id_hex = %s
            """,
            (key_id_hex,),
        )
        row = cursor.fetchone()
        if not row or not row.get("is_active"):
            cursor.close()
            return None
        expires_at = row.get("expires_at")
        if expires_at is not None and expires_at < datetime.now(timezone.utc):
            cursor.close()
            return None
        if not _bcrypt_verify(secret, row["key_hash"]):
            cursor.close()
            return None

        # Best-effort last_used_at bump.
        try:
            cursor.execute(
                "UPDATE api_keys SET last_used_at = NOW() WHERE id = %s",
                (row["id"],),
            )
            conn.commit()
        except Exception as e:  # noqa: BLE001
            logger.warning("api_key.last_used_update_failed key_id=%s err=%s", row["id"], e)
            conn.rollback()

        per_min, per_day = _coerce_rate_override(row.get("rate_limit_override"))
        cursor.close()
        return ApiKeyContext(
            key_id=str(row["id"]),
            tenant_id=str(row["tenant_id"]),
            name=row.get("name") or "",
            rate_limit_per_minute=per_min,
            rate_limit_per_day=per_day,
        )
    finally:
        conn.close()


def revoke_api_key(key_id: str) -> bool:
    """Mark a key inactive. Returns True iff a row was updated."""
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Database unavailable")
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE api_keys SET is_active = FALSE WHERE id = %s::uuid",
            (key_id,),
        )
        updated = cursor.rowcount
        conn.commit()
        cursor.close()
    finally:
        conn.close()
    return updated > 0


def list_api_keys(tenant_id: str) -> List[Dict[str, Any]]:
    """Return non-secret metadata for every key bound to a tenant."""
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Database unavailable")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT id, tenant_id, name, created_at, expires_at, last_used_at,
                   is_active, rate_limit_override, key_id_hex
            FROM api_keys
            WHERE tenant_id = %s::uuid
            ORDER BY created_at DESC
            """,
            (tenant_id,),
        )
        rows = list(cursor.fetchall())
        cursor.close()
    finally:
        conn.close()
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append({
            "id": str(r["id"]),
            "tenant_id": str(r["tenant_id"]),
            "name": r["name"],
            "created_at": r["created_at"],
            "expires_at": r["expires_at"],
            "last_used_at": r["last_used_at"],
            "is_active": r["is_active"],
            "rate_limit_override": r["rate_limit_override"],
            "key_id_hex": r["key_id_hex"],
        })
    return out


# --------------------------------------------------------------------------- #
# FastAPI dependency
# --------------------------------------------------------------------------- #

def get_api_key_context(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> ApiKeyContext:
    """
    FastAPI dependency. Reads X-API-Key, verifies it, returns the context.
    Stashes the context on `request.state.api_key_context` so the slowapi
    keyfunc can read it without re-querying the DB.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    ctx = verify_api_key(x_api_key)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )
    request.state.api_key_context = ctx
    return ctx


def get_rate_limits_for_context(ctx: ApiKeyContext) -> Tuple[str, str]:
    """slowapi-compatible "<n>/<period>" strings for per-minute and per-day."""
    return f"{ctx.rate_limit_per_minute}/minute", f"{ctx.rate_limit_per_day}/day"


def api_key_rate_limit_key(request: Request) -> str:
    """
    slowapi keyfunc — bucket by API key.

    Runs as middleware (before the auth dependency), so we extract the
    key_id_hex straight from the raw X-API-Key header rather than waiting
    for ApiKeyContext. Falls back to a per-IP bucket for un-keyed traffic
    so anonymous callers can't drain the global default-limits pool.
    """
    raw = request.headers.get("x-api-key")
    if raw:
        parsed = parse_raw_key(raw)
        if parsed is not None:
            key_id_hex, _ = parsed
            return f"key:{key_id_hex}"
        return f"raw:{raw[:32]}"
    client = request.client
    return f"ip:{client.host if client else 'unknown'}"


# --------------------------------------------------------------------------- #
# Admin auth (placeholder — env-var shared secret)
# --------------------------------------------------------------------------- #

def _constant_time_eq(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def require_admin(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
) -> None:
    """
    Admin auth dependency. Validates X-Admin-Token against ADMIN_API_TOKEN.
    The env var must be set in production; a missing/empty value rejects
    every request (fail closed).
    """
    expected = os.environ.get("ADMIN_API_TOKEN", "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin auth not configured",
        )
    if not x_admin_token or not _constant_time_eq(x_admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )
