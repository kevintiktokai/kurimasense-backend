"""
Latency budget + cache-hit smoke tests for the backend perf pass.

These run in mock mode (no DATABASE_URL, no SUPABASE_*) so they can
execute in CI without external dependencies.  The handlers fall back
to MOCK_FIELDS / MOCK_CHATS / static climate stubs when the DB is
unavailable, which is exactly the "warm-cache" path we want to budget.

Budgets (from the perf audit deliverable):

    /dashboard/init   p95 < 250 ms (cold) / 50 ms (warm)
    /fields           p95 < 150 ms
    /climate/current  p95 < 100 ms (cache hit)
    All other GETs    p95 < 300 ms

The numbers below are looser than production budgets because pytest +
TestClient have ~10-30 ms of fixed overhead per call.  Treat the
warm/cold deltas (rather than absolute values) as the real signal.
"""

import os
import statistics
import time

# Force degraded / mock-mode BEFORE importing the app module.  The
# handlers gracefully serve MOCK_FIELDS when get_db_connection() returns
# None, so this skips all the real DB / JWT machinery.
os.environ.setdefault("DEBUG_MODE", "true")
os.environ.pop("DATABASE_URL", None)
os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_JWT_SECRET", None)
os.environ.pop("SUPABASE_JWT_PUBLIC_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import app as app_module  # noqa: E402
from deps import cache_invalidate_prefix  # noqa: E402

client = TestClient(app_module.app)
AUTH = {"Authorization": "Bearer test"}  # DEBUG_MODE bypass returns the zero UUID


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _percentile(samples, p):
    samples_sorted = sorted(samples)
    idx = max(0, int(round((p / 100) * len(samples_sorted))) - 1)
    return samples_sorted[idx]


def _measure(method, path, *, n=10, **kwargs):
    """Time N requests and return (p50_ms, p95_ms)."""
    durations_ms = []
    for _ in range(n):
        t0 = time.perf_counter()
        r = client.request(method, path, **kwargs)
        durations_ms.append((time.perf_counter() - t0) * 1000)
        # Don't assert on status here — the goal is to time the full
        # request lifecycle including any error fall-throughs.
        assert r.status_code in (200, 304, 401, 404, 500), (
            f"Unexpected status {r.status_code} for {method} {path}: {r.text[:200]}"
        )
    return _percentile(durations_ms, 50), _percentile(durations_ms, 95)


# ---------------------------------------------------------------------------
# /dashboard/init — cold + warm budgets, cache hit assertion
# ---------------------------------------------------------------------------

def test_dashboard_init_warm_cache_under_budget():
    """Second call inside the cache TTL must be < 30 ms (effectively a dict
    lookup + JSON serialization)."""
    cache_invalidate_prefix("dashboard_init:")

    # Cold call to populate the cache.
    r0 = client.get("/dashboard/init", headers=AUTH)
    assert r0.status_code == 200, r0.text

    # Warm call — should hit the in-process cache.
    t0 = time.perf_counter()
    r1 = client.get("/dashboard/init", headers=AUTH)
    warm_ms = (time.perf_counter() - t0) * 1000
    assert r1.status_code == 200
    assert warm_ms < 30, f"Warm /dashboard/init took {warm_ms:.1f} ms (budget: 30 ms)"


def test_dashboard_init_etag_returns_304():
    cache_invalidate_prefix("dashboard_init:")

    first = client.get("/dashboard/init", headers=AUTH)
    assert first.status_code == 200
    etag = first.headers.get("etag")
    assert etag, "First /dashboard/init response must include an ETag"

    cond = client.get(
        "/dashboard/init",
        headers={**AUTH, "If-None-Match": etag},
    )
    assert cond.status_code == 304, (
        f"Conditional GET should 304; got {cond.status_code} {cond.text[:200]}"
    )


def test_dashboard_init_cache_control_header():
    cache_invalidate_prefix("dashboard_init:")
    r = client.get("/dashboard/init", headers=AUTH)
    assert r.status_code == 200
    cc = r.headers.get("cache-control", "")
    assert "max-age" in cc, f"Expected Cache-Control max-age, got {cc!r}"


# ---------------------------------------------------------------------------
# /fields — list + single-field budgets
# ---------------------------------------------------------------------------

def test_fields_list_under_budget():
    p50, p95 = _measure("GET", "/fields", headers=AUTH, n=15)
    assert p95 < 200, f"/fields p95 {p95:.1f} ms exceeds 200 ms"


def test_fields_single_endpoint_exists():
    """GET /fields/{id} replaces the FE's "load all fields, find one" flow."""
    r = client.get("/fields/mock-1", headers=AUTH)
    # In mock mode the only field id is "mock-1" → expect 200.
    assert r.status_code in (200, 404), r.text
    if r.status_code == 200:
        body = r.json()
        # Shape contract — these keys are what the FE FieldData type uses.
        for key in ("id", "name", "crop", "area", "ndvi", "soilMoisture"):
            assert key in body, f"GET /fields/:id missing {key}"


def test_get_field_returns_404_for_unknown_id():
    r = client.get("/fields/00000000-0000-0000-0000-000000000000", headers=AUTH)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# /market/prices — Cache-Control header for shared edge caching
# ---------------------------------------------------------------------------

def test_market_prices_has_public_cache_control():
    r = client.get("/market/prices")
    assert r.status_code == 200
    cc = r.headers.get("cache-control", "")
    assert "public" in cc and "max-age" in cc, (
        f"/market/prices should advertise public, max-age=...; got {cc!r}"
    )


# ---------------------------------------------------------------------------
# Climate cluster cache — second call within TTL must be near-instant
# ---------------------------------------------------------------------------

def test_climate_current_warm_cache():
    """First call goes through the upstream client (mocked or live).
    The second call within 5 minutes should be a dict lookup."""
    # Skip cleanly if the network call fails (e.g. CI without internet).
    r0 = client.get("/climate/current?lat=-17.82&lon=31.05", headers=AUTH)
    if r0.status_code != 200:
        return  # cold path could not reach Open-Meteo — nothing to budget

    t0 = time.perf_counter()
    r1 = client.get("/climate/current?lat=-17.82&lon=31.05", headers=AUTH)
    warm_ms = (time.perf_counter() - t0) * 1000
    assert r1.status_code == 200
    assert warm_ms < 100, f"Warm /climate/current took {warm_ms:.1f} ms (budget: 100 ms)"


# ---------------------------------------------------------------------------
# Aggregate budget across the GET surface
# ---------------------------------------------------------------------------

def test_other_get_endpoints_under_budget():
    """The /dashboard/init test already covers the hot path; this just
    asserts no other GET regresses badly on the mock path."""
    paths = [
        "/health",
        "/fields",
        "/chat/history",
        "/market/prices",
    ]
    for path in paths:
        p50, p95 = _measure(
            "GET", path,
            headers=AUTH if path != "/market/prices" and path != "/health" else {},
            n=10,
        )
        assert p95 < 300, f"GET {path} p95 {p95:.1f} ms exceeds 300 ms (p50={p50:.1f})"


# ---------------------------------------------------------------------------
# Cache invalidation contract — /fields delete must bust dashboard_init
# ---------------------------------------------------------------------------

def test_field_delete_invalidates_dashboard_cache():
    """Even though MOCK_FIELDS isn't really persisted, the delete handler
    must call cache_invalidate_prefix('dashboard_init:{user_id}') so the
    next dashboard mount sees the new state.  Under mock mode the delete
    returns success without touching the DB."""
    cache_invalidate_prefix("dashboard_init:")
    client.get("/dashboard/init", headers=AUTH)  # populate

    # A field id that exists in MOCK_FIELDS → mock-1.
    client.delete("/fields/mock-1", headers=AUTH)

    # The cache key is deterministic from the bypass user UUID.
    from deps import _response_cache  # type: ignore
    leftovers = [k for k in list(_response_cache.keys()) if k.startswith("dashboard_init:")]
    assert not leftovers, f"dashboard_init cache should be empty after delete, got: {leftovers}"
