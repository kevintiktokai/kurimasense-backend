"""
KurimaSense Shared Dependencies
================================
Extracted from app.py to enable modular route architecture.

Contains:
- JWT token verification
- Response caching utilities
- Shared helper functions
- Mock data constants
"""

import os
import re
import json
import time
import hashlib
import urllib.request
import urllib.error
import logging
from datetime import datetime
from typing import List, Optional

import jwt
from fastapi import HTTPException, Header
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from database import get_db_connection
from ai_brain import FieldContext
from proactive_intelligence import calculate_growth_stage

load_dotenv()

logger = logging.getLogger("kurimasense")

# ---------------------------------------------------------------------------
# Supabase / JWT Configuration
# ---------------------------------------------------------------------------
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
SUPABASE_JWT_PUBLIC_KEY = os.environ.get("SUPABASE_JWT_PUBLIC_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")

# ---------------------------------------------------------------------------
# In-memory response cache (stdlib only, no Redis required)
# ---------------------------------------------------------------------------
_response_cache: dict = {}
_token_cache: dict = {}


def cache_get(key: str):
    entry = _response_cache.get(key)
    if not entry:
        return None
    data, expires_at = entry
    if time.time() > expires_at:
        del _response_cache[key]
        return None
    return data


def cache_set(key: str, data, ttl_seconds: int = 300):
    _response_cache[key] = (data, time.time() + ttl_seconds)
    # Evict expired entries when cache grows too large
    if len(_response_cache) > 100:
        now = time.time()
        stale = [k for k, (_, exp) in _response_cache.items() if now > exp]
        for k in stale:
            del _response_cache[k]


def cache_invalidate_prefix(prefix: str):
    keys = [k for k in _response_cache if k.startswith(prefix)]
    for k in keys:
        del _response_cache[k]


# ---------------------------------------------------------------------------
# JWKS Helpers
# ---------------------------------------------------------------------------
_jwks_keys = None
_jwks_fetch_time = None


def fetch_jwks_keys():
    """Fetch JWKS keys from Supabase with proper authentication."""
    global _jwks_keys, _jwks_fetch_time

    if _jwks_keys and _jwks_fetch_time:
        if (datetime.now() - _jwks_fetch_time).total_seconds() < 3600:
            return _jwks_keys

    if not SUPABASE_URL:
        return None

    jwks_url = f"{SUPABASE_URL}/auth/v1/jwks"
    try:
        headers = {'User-Agent': 'KurimaSense/1.0'}
        if SUPABASE_ANON_KEY:
            headers['apikey'] = SUPABASE_ANON_KEY
        req = urllib.request.Request(jwks_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            jwks_data = json.loads(response.read().decode())
            _jwks_keys = jwks_data.get('keys', [])
            _jwks_fetch_time = datetime.now()
            return _jwks_keys
    except urllib.error.HTTPError as e:
        logger.error(f"JWKS fetch HTTP error: {e.code} - {e.reason}")
        return None
    except Exception as e:
        logger.error(f"JWKS fetch error: {type(e).__name__}: {e}")
        return None


def get_signing_key_from_jwks(token):
    """Get the signing key for a token from JWKS."""
    keys = fetch_jwks_keys()
    if not keys:
        return None
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        for key_data in keys:
            if kid and key_data.get('kid') != kid:
                continue
            from jwt.algorithms import ECAlgorithm, RSAAlgorithm
            kty = key_data.get('kty')
            if kty == 'EC':
                return ECAlgorithm.from_jwk(json.dumps(key_data))
            elif kty == 'RSA':
                return RSAAlgorithm.from_jwk(json.dumps(key_data))
        return None
    except Exception as e:
        logger.error(f"Error extracting key from JWKS: {type(e).__name__}: {e}")
        return None


# ---------------------------------------------------------------------------
# Token Verification (FastAPI Dependency)
# ---------------------------------------------------------------------------
def verify_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Verify Supabase JWT token and return user_id.
    Supports HS256 (symmetric) and ES256/RS256 (asymmetric) via JWKS.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        parts = authorization.split()
        if len(parts) != 2:
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        scheme, token = parts
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        # Token cache lookup
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        _cached_token = _token_cache.get(token_hash)
        if _cached_token:
            _cached_user_id, _cached_exp = _cached_token
            if time.time() < _cached_exp:
                return _cached_user_id
            else:
                del _token_cache[token_hash]

        # Development bypass — requires explicit opt-in via DEBUG_MODE env var
        if os.environ.get("DEBUG_MODE", "").lower() == "true":
            if not SUPABASE_JWT_SECRET and not SUPABASE_JWT_PUBLIC_KEY and not SUPABASE_URL:
                return "00000000-0000-0000-0000-000000000000"

        # Get token algorithm
        try:
            unverified_header = jwt.get_unverified_header(token)
            token_alg = unverified_header.get('alg', 'HS256')
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token header")

        payload = None
        last_error = None

        # Strategy 1: HS256 with JWT secret
        if SUPABASE_JWT_SECRET and token_alg == 'HS256':
            try:
                payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except jwt.InvalidTokenError as e:
                last_error = str(e)

        # Strategy 2: Configured public key
        if payload is None and SUPABASE_JWT_PUBLIC_KEY and token_alg in ['RS256', 'ES256']:
            try:
                public_key = SUPABASE_JWT_PUBLIC_KEY.replace("\\n", "\n")
                payload = jwt.decode(token, public_key, algorithms=[token_alg], audience="authenticated")
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except jwt.InvalidTokenError as e:
                last_error = str(e)

        # Strategy 3: JWKS
        if payload is None and token_alg in ['RS256', 'ES256'] and SUPABASE_URL:
            try:
                signing_key = get_signing_key_from_jwks(token)
                if signing_key:
                    payload = jwt.decode(token, signing_key, algorithms=[token_alg], audience="authenticated")
                else:
                    last_error = "Could not get signing key from JWKS"
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except Exception as e:
                last_error = f"JWKS: {str(e)}"

        # Strategy 4: ES256 with JWT secret directly
        if payload is None and token_alg == 'ES256' and SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token, SUPABASE_JWT_SECRET, algorithms=["ES256"],
                    audience="authenticated", options={"verify_signature": True}
                )
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except Exception:
                pass

        if payload is None:
            error_msg = f"Token verification failed for {token_alg}"
            if last_error:
                error_msg += f": {last_error}"
            raise HTTPException(status_code=401, detail=error_msg)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload: missing user ID")

        # Cache verified token
        exp_unix = payload.get("exp", time.time() + 3600)
        if len(_token_cache) > 10000:
            _now = time.time()
            _expired = [k for k, (_, e) in _token_cache.items() if _now > e]
            for k in _expired:
                del _token_cache[k]
        _token_cache[token_hash] = (user_id, exp_unix)

        return user_id

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid authorization header: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected token verification error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


# ---------------------------------------------------------------------------
# User Language Helper
# ---------------------------------------------------------------------------
def get_user_language(user_id: str) -> Optional[str]:
    """Fetch user's preferred language from the profiles table."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT preferred_language FROM profiles WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            cursor.close()
            if row and row.get('preferred_language'):
                return row['preferred_language']
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Shared Helpers
# ---------------------------------------------------------------------------
def get_health_status(score) -> str:
    """Convert health score to status string."""
    if score is None:
        return "Unknown"
    score = float(score)
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Moderate"
    if score >= 20:
        return "Poor"
    return "Critical"


async def get_field_context(field_id: str, user_id: str) -> FieldContext:
    """
    Build FieldContext from database for AI Brain.
    Includes variety info, growth stage, and transplant support.
    """
    context = FieldContext(field_id=field_id)

    try:
        # tenant_scoped_connection arms the RLS GUCs (FORCE-ready) — fields /
        # daily_logs policies scope by the caller's tenants.
        from tenancy import tenant_scoped_connection, rls_tenant_only
        with tenant_scoped_connection(user_id) as (conn, tenant_ids):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            # Scope the field to the caller. Flag-off (default) keeps the exact
            # legacy user_id filter — a byte-identical no-op on deploy. Flag-on
            # (RLS_TENANT_ONLY) scopes by tenant membership instead and never
            # references fields.user_id, so the column can be dropped. Both keep
            # an app-level filter, so this is safe with FORCE off. See
            # docs/rls_force_runbook.md Step C.
            if rls_tenant_only():
                scope_sql, scope_param = "f.tenant_id = ANY(%s::uuid[])", tenant_ids
            else:
                scope_sql, scope_param = "f.user_id = %s", user_id
            # Use LEFT JOIN LATERAL instead of 2 correlated subqueries — single index scan
            cursor.execute(f"""
                SELECT
                    f.name, f.crop_type, f.planting_date, f.variety, f.health_score,
                    f.transplant_date, f.is_transplanted, f.fertilizer_history,
                    latest.ndvi as current_ndvi,
                    latest.soil_moisture as soil_moisture
                FROM fields f
                LEFT JOIN LATERAL (
                    SELECT ndvi, soil_moisture
                    FROM daily_logs
                    WHERE field_id = f.id
                    ORDER BY log_date DESC
                    LIMIT 1
                ) latest ON true
                WHERE f.id = %s::uuid AND {scope_sql}
            """, (field_id, scope_param))

            row = cursor.fetchone()
            cursor.close()

        if row:
            context.field_name = row.get("name")
            context.crop_type = row.get("crop_type")
            context.variety = row.get("variety")
            context.planting_date = row["planting_date"].isoformat() if row.get("planting_date") else None
            context.current_ndvi = row.get("current_ndvi")
            context.soil_moisture = row.get("soil_moisture")
            context.health_status = get_health_status(row.get("health_score"))

            if row.get("planting_date") and row.get("crop_type"):
                try:
                    transplant_date = row.get("transplant_date")
                    is_transplanted = row.get("is_transplanted", False)
                    growth_stage = calculate_growth_stage(
                        planting_date=row["planting_date"],
                        variety_name=row.get("variety") or "Generic",
                        crop_type=row.get("crop_type"),
                        transplant_date=transplant_date,
                        is_transplanted=is_transplanted
                    )
                    context.growth_stage = f"{growth_stage.stage_name} ({growth_stage.days_since_planting}d, {growth_stage.progress_percent:.0f}%)"
                    if growth_stage.risks:
                        context.recent_alerts = growth_stage.risks[:3]
                except Exception as e:
                    logger.warning(f"Growth stage calculation failed: {e}")

            # Enrich the AI's field awareness with the farmer's own stored records
            # (Phase 5): the fertilizer plan + recently logged activities. These
            # feed FieldContext.recent_activities, which to_prompt_section already
            # renders, so the advisor never asks the farmer to repeat what
            # KurimaSense already knows. Extensible: append further analytics
            # (scouting, previous recommendations, …) to recent_activities here.
            activities: List[str] = []
            fert = (row.get("fertilizer_history") or "").strip()
            if fert:
                activities.append(f"Fertilizer plan on record: {fert}")
            try:
                from database import get_recent_field_activity
                activities.extend(get_recent_field_activity(field_id, user_id=user_id) or [])
            except Exception as e:
                logger.warning(f"Recent-activity fetch failed: {e}")
            if activities:
                context.recent_activities = activities[:6]

    except Exception as e:
        # RuntimeError (DB unavailable) and query errors both degrade to the
        # bare context; tenant_scoped_connection handles rollback + release.
        logger.error(f"Field context fetch error: {e}")

    return context


async def resolve_coordinates(field_id: str = None, lat: float = None, lon: float = None, user_id: str = None) -> tuple:
    """
    Resolve coordinates from field_id, explicit lat/lon, or default to Zimbabwe.
    """
    default_lat, default_lon = -17.82, 31.05

    if field_id:
        try:
            # FORCE-ready: fields policy scopes by the caller's tenants. Flag-off
            # keeps the legacy user_id filter byte-identical; flag-on scopes by
            # tenant and drops the fields.user_id reference (see rls_force_runbook).
            from tenancy import tenant_scoped_connection, rls_tenant_only
            with tenant_scoped_connection(user_id) as (conn, tenant_ids):
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                if rls_tenant_only():
                    scope_sql, scope_param = "tenant_id = ANY(%s::uuid[])", tenant_ids
                else:
                    scope_sql, scope_param = "user_id = %s::uuid", user_id
                cursor.execute(
                    f"SELECT polygon_coordinates FROM fields WHERE id = %s::uuid AND {scope_sql}",
                    (field_id, scope_param),
                )
                row = cursor.fetchone()
                cursor.close()

            if row and row.get('polygon_coordinates'):
                coords = row['polygon_coordinates']
                if isinstance(coords, list) and len(coords) > 0:
                    lats = [p['lat'] for p in coords]
                    lons = [p['lon'] for p in coords]
                    return sum(lats) / len(lats), sum(lons) / len(lons)
        except RuntimeError:
            # DB unavailable — check mock fields
            for f in MOCK_FIELDS:
                if f.get("id") == field_id:
                    loc = f.get("location")
                    if loc:
                        return loc["lat"], loc["lon"]
        except Exception as e:
            logger.warning(f"Field lookup error: {e}")

    if lat is not None and lon is not None:
        return lat, lon

    return default_lat, default_lon


# ---------------------------------------------------------------------------
# Mock Data (used when DB is unavailable)
# ---------------------------------------------------------------------------
MOCK_INPUTS: list = []

MOCK_CHATS = [
    {
        "role": "ai",
        "content": "Hello! I'm your KurimaSense AI Agronomist. I've analyzed your satellite data for the week. Where should we start?",
        "timestamp": "2024-03-24T08:00:00"
    }
]

MOCK_FIELDS = [
    {
        "id": "mock-1",
        "name": "Home Field (Offline)",
        "crop": "Maize",
        "area": 12.5,
        "ndvi": 0.72,
        "soilMoisture": 48,
        "healthStatus": "Good",
        "lastSatellitePass": "2024-03-15",
        "location": {"lat": -17.82, "lon": 31.05},
        "coordinates": []
    }
]


# ---------------------------------------------------------------------------
# Startup Validation
# ---------------------------------------------------------------------------
def validate_environment():
    """Validate required environment variables at startup. Log warnings for missing optional vars."""
    issues = []

    # Required for AI functionality
    if not os.environ.get("OPENAI_API_KEY"):
        issues.append("OPENAI_API_KEY not set — AI chat, vision, and RAG will fail")

    # Required for persistence
    if not os.environ.get("DATABASE_URL"):
        issues.append("DATABASE_URL not set — running in degraded/mock mode")

    # Auth configuration
    debug_mode = os.environ.get("DEBUG_MODE", "").lower() == "true"
    has_auth = any([SUPABASE_JWT_SECRET, SUPABASE_JWT_PUBLIC_KEY, SUPABASE_URL])
    if not has_auth and not debug_mode:
        issues.append(
            "No JWT auth configured (SUPABASE_JWT_SECRET / SUPABASE_JWT_PUBLIC_KEY / SUPABASE_URL) "
            "and DEBUG_MODE is not enabled — all authenticated endpoints will return 401"
        )

    for issue in issues:
        logger.warning(f"ENV WARNING: {issue}")

    return issues
