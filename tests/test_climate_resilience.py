"""
The two ways the weather stopped reaching farmers on 26 August 2026.

Both were in code that already looked right. `climate_service` carried a full
resilience model — TTL cache, single-flight, serve-stale-on-error, retry with
backoff — and the production logs for that morning still show every climate
endpoint failing and half the notification cycle silently skipped.

FAULT 1 — "Event loop is closed"
--------------------------------
    [notifications.generators] weather fetch failed (-16.75,31.66): Event loop is closed
    [notifications.generators] irrigation failed for field f3a7dc8c…: Event loop is closed

One module-level `httpx.AsyncClient`, and a generator calling `asyncio.run`
once per field. Each call opened an event loop and closed it; the client and
its pooled connections stayed bound to the first one. Intermittent, because a
pool that happened to open a fresh connection succeeded and one that reused a
dead connection did not — so the cycle always reported *some* alerts generated
and never looked broken. The farms on the failing side of that coin simply
received no irrigation advice.

FAULT 2 — the ten-second 429
----------------------------
    HTTP/1.1 429 Too Many Requests
    "path": "/climate/spray-window", "duration_ms": 11482.96

Open-Meteo's free tier limits by IP and Render's egress IP is shared with every
other tenant on the instance. The retry policy treated 429 as transient and
tried four times with exponential backoff. That is 1 + 2 + 4 seconds of
sleeping — the `duration_ms` in those log lines is almost entirely backoff —
after which the route returned an empty card anyway. And each retry spent more
of the quota that was already exhausted, pushing recovery further out. The
farmer got a ten-second spinner and then nothing.

FAULT 3 — the cache that died at the worst moment
-------------------------------------------------
Stale-serve is what should have carried the app through fault 2. It lived
entirely in process memory, and at 09:55 the service deployed. New process,
empty cache, every key a miss with nothing behind it. The data needed to keep
the app useful had existed twenty minutes earlier.
"""

import asyncio
import time

import httpx
import pytest

import climate_service as cs


@pytest.fixture(autouse=True)
def _clean_state():
    """Each test starts with no cooldown and no cached weather."""
    cs._reset_rate_limit()
    cs._cache.clear()
    cs._inflight.clear()
    yield
    cs._reset_rate_limit()
    cs._cache.clear()
    cs._inflight.clear()


# ---------------------------------------------------------------------------
# Fault 1: the HTTP client must belong to the loop that is running
# ---------------------------------------------------------------------------
def test_each_event_loop_gets_its_own_client():
    # The production shape exactly: separate `asyncio.run` calls, as
    # services/notifications/generators makes once per field.
    async def grab():
        return cs._get_http()

    first = asyncio.run(grab())
    second = asyncio.run(grab())

    assert first is not second, (
        "a client shared across asyncio.run() calls is bound to a closed loop — "
        "this is the 'Event loop is closed' failure"
    )


def test_a_client_is_reused_within_one_loop():
    # The counterpart. Per-loop must not become per-call: a new connection pool
    # for every request would drop keep-alive and multiply the connection count
    # against an upstream that is already rate-limiting us.
    async def grab_twice():
        return cs._get_http(), cs._get_http()

    a, b = asyncio.run(grab_twice())
    assert a is b


def test_the_client_map_does_not_outlive_its_loops():
    # Keyed by the loop object in a WeakKeyDictionary, deliberately not by
    # id(loop): CPython reuses the id of a collected loop, so an id-keyed map
    # hands back the dead client for a fresh loop and reintroduces fault 1
    # while looking like a fix.
    import weakref

    assert isinstance(cs._http_by_loop, weakref.WeakKeyDictionary)

    for _ in range(5):
        asyncio.run(_noop_get_http())
    # Every loop is closed and unreferenced; entries go with them.
    assert len(cs._http_by_loop) <= 1


async def _noop_get_http():
    cs._get_http()


# ---------------------------------------------------------------------------
# Fault 2: a 429 must cost one call and no waiting
# ---------------------------------------------------------------------------
class _FakeResponse:
    def __init__(self, status_code: int, headers=None, payload=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload if payload is not None else {"ok": True}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{self.status_code}", request=None, response=None  # type: ignore[arg-type]
            )


class _CountingClient:
    """Stands in for httpx.AsyncClient, counting the calls it is asked to make."""

    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = 0

    async def get(self, url, params=None):
        self.calls += 1
        if len(self._responses) == 1:
            return self._responses[0]
        return self._responses.pop(0)


@pytest.fixture
def counting(monkeypatch):
    def install(*responses):
        client = _CountingClient(*responses)
        monkeypatch.setattr(cs, "_get_http", lambda: client)
        return client

    return install


def test_a_429_is_not_retried():
    # The whole fault. Four attempts against an exhausted per-IP quota do not
    # find a healthier backend; they spend more of the quota that ran out.
    assert 429 not in cs._RETRYABLE_STATUS


def test_a_429_costs_exactly_one_upstream_call(counting):
    client = counting(_FakeResponse(429))

    with pytest.raises(cs.ClimateRateLimited):
        asyncio.run(cs._get_json("https://example.invalid/forecast", {}))

    assert client.calls == 1, "a rate-limited call must not be repeated"


def test_a_429_returns_without_sleeping(counting):
    # `duration_ms: 11482.96` on /climate/spray-window was three backoff sleeps.
    # The farmer waited eleven seconds to be shown an empty card.
    counting(_FakeResponse(429))

    started = time.monotonic()
    with pytest.raises(cs.ClimateRateLimited):
        asyncio.run(cs._get_json("https://example.invalid/forecast", {}))
    elapsed = time.monotonic() - started

    assert elapsed < 1.0, f"a 429 took {elapsed:.1f}s; it must be immediate"


def test_a_429_stops_the_next_call_reaching_the_network_at_all(counting):
    client = counting(_FakeResponse(429))

    with pytest.raises(cs.ClimateRateLimited):
        asyncio.run(cs._get_json("https://example.invalid/forecast", {}))
    # Every subsequent caller during the cooldown — other endpoints, other
    # fields, the notification cycle — must not spend another unit of quota.
    for _ in range(5):
        with pytest.raises(cs.ClimateRateLimited):
            asyncio.run(cs._get_json("https://example.invalid/forecast", {}))

    assert client.calls == 1, "calls during the cooldown must not reach upstream"
    assert cs.rate_limit_cooldown_remaining() > 0


def test_retry_after_is_honoured_but_capped(counting):
    counting(_FakeResponse(429, headers={"Retry-After": "999999"}))
    with pytest.raises(cs.ClimateRateLimited):
        asyncio.run(cs._get_json("https://example.invalid/forecast", {}))

    # An unbounded Retry-After would pin the whole product to stale weather on
    # the strength of one unlucky response header.
    assert cs.rate_limit_cooldown_remaining() <= cs._RATE_LIMIT_COOLDOWN_MAX + 1


def test_a_sensible_retry_after_is_used_as_given(counting):
    counting(_FakeResponse(429, headers={"Retry-After": "30"}))
    with pytest.raises(cs.ClimateRateLimited):
        asyncio.run(cs._get_json("https://example.invalid/forecast", {}))

    remaining = cs.rate_limit_cooldown_remaining()
    assert 25 < remaining <= 31, f"expected ~30s cooldown, got {remaining}"


def test_a_garbage_retry_after_falls_back_to_the_default(counting):
    # "Retry-After: Wed, 21 Oct 2026 07:28:00 GMT" is legal HTTP and is not a
    # number. float() on it would raise inside the error path.
    counting(_FakeResponse(429, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}))
    with pytest.raises(cs.ClimateRateLimited):
        asyncio.run(cs._get_json("https://example.invalid/forecast", {}))

    assert cs.rate_limit_cooldown_remaining() > 0


def test_transient_server_errors_are_still_retried(counting):
    # Suppressing 429 retries must not suppress the retries that do help: a 503
    # is one unhealthy backend, and the next attempt usually lands elsewhere.
    client = counting(_FakeResponse(503), _FakeResponse(503), _FakeResponse(200))

    result = asyncio.run(cs._get_json("https://example.invalid/forecast", {}, retries=3))

    assert result == {"ok": True}
    assert client.calls == 3


# ---------------------------------------------------------------------------
# Fault 3: what the farmer sees while the upstream is unavailable
# ---------------------------------------------------------------------------
def test_a_rate_limited_fetch_serves_the_last_good_answer(counting):
    counting(_FakeResponse(429))

    async def scenario():
        # A good fetch lands first...
        await cs._cached("k", 0.0, _produces({"temperature": 24}))
        # ...then the upstream starts refusing. The farmer still gets weather.
        return await cs._cached("k", 0.0, _rate_limited_producer())

    assert asyncio.run(scenario()) == {"temperature": 24}


def test_a_location_we_have_never_fetched_reports_failure_rather_than_inventing_one():
    # The rule this codebase holds everywhere: decline rather than guess. There
    # is no plausible default for "what is the weather here" — the route turns
    # this into `available: false` and the card renders nothing.
    async def scenario():
        return await cs._cached("never-seen", 60.0, _rate_limited_producer())

    with pytest.raises(cs.ClimateRateLimited):
        asyncio.run(scenario())


def test_stale_data_survives_a_restart(monkeypatch):
    # The 09:55 deploy. Memory is empty because the process is new; the durable
    # tier is the only reason the farmer sees weather at all.
    monkeypatch.setattr(cs, "_load_stale", lambda key: (300.0, {"temperature": 19}))

    async def scenario():
        return await cs._cached("cold-start", 60.0, _rate_limited_producer())

    assert asyncio.run(scenario()) == {"temperature": 19}


def test_the_durable_tier_is_not_consulted_on_the_healthy_path(monkeypatch):
    # It is a fallback, not a read-through cache. Putting a database round trip
    # in front of every weather fetch would trade one outage for a slower app
    # every other day of the year.
    reads = []
    monkeypatch.setattr(cs, "_load_stale", lambda key: reads.append(key) or None)
    monkeypatch.setattr(cs, "_persist_stale", lambda *a, **k: None)

    asyncio.run(cs._cached("fresh", 60.0, _produces({"temperature": 30})))
    assert reads == []


def test_weather_older_than_the_cap_is_not_served(monkeypatch):
    # Weather from beyond _STALE_MAX_AGE is not weather, it is history — a
    # frost warning from last week is worse than no frost warning. The first
    # draft of this test monkeypatched _load_stale to return None and asserted
    # it got None, which proved only that the mock worked.
    monkeypatch.setattr(cs, "_load_stale", lambda key: None)
    ancient = time.time() - (cs._STALE_MAX_AGE + 60)
    cs._cache["ancient"] = (ancient, 60.0, {"temperature": 11})

    async def scenario():
        return await cs._cached("ancient", 60.0, _rate_limited_producer())

    with pytest.raises(cs.ClimateRateLimited):
        asyncio.run(scenario())


def test_weather_inside_the_cap_is_still_served(monkeypatch):
    # The counterpart: capping must not throw away data that is still useful.
    monkeypatch.setattr(cs, "_load_stale", lambda key: None)
    recent = time.time() - (cs._STALE_MAX_AGE / 2)
    cs._cache["recent"] = (recent, 60.0, {"temperature": 11})

    async def scenario():
        return await cs._cached("recent", 60.0, _rate_limited_producer())

    assert asyncio.run(scenario()) == {"temperature": 11}


def test_a_broken_database_never_breaks_the_weather(monkeypatch):
    # A durable cache that takes the request down with it when Postgres is
    # unwell is worse than no durable cache.
    def explode(*a, **k):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(cs, "get_db_connection", explode)

    assert cs._load_stale("anything") is None
    cs._persist_stale("anything", 60, {"x": 1})  # must not raise

    async def scenario():
        return await cs._cached("db-down", 60.0, _produces({"temperature": 21}))

    assert asyncio.run(scenario()) == {"temperature": 21}


# ---------------------------------------------------------------------------
# Wiring guard
# ---------------------------------------------------------------------------
def test_the_notification_generator_opens_one_loop_per_location_not_two():
    # Two `asyncio.run` calls back to back was the shape that exposed fault 1.
    # climate_service is now robust to it either way, but a generator that
    # churns a loop per upstream call is a standing invitation to the next
    # instance of this bug.
    import pathlib

    src = (
        pathlib.Path(__file__).resolve().parent.parent
        / "services" / "notifications" / "generators.py"
    ).read_text()

    weather = src[src.index("def generate_weather_alerts"):src.index("def generate_irrigation_recommendations")]
    assert weather.count("asyncio.run(") == 1, (
        "one event loop per location, not one per upstream call"
    )
    assert "_gather_weather" in weather


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _produces(value):
    async def producer():
        return value

    return producer


def _rate_limited_producer():
    async def producer():
        raise cs.ClimateRateLimited("Open-Meteo returned 429")

    return producer
