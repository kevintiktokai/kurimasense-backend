"""Field-state performance invariants.

REGRESSION (July 2026): production logs showed GET /field/{id}/state taking
131,000-212,000 ms. Three compounding causes, one test file:

1. BLOCKING I/O ON THE EVENT LOOP. build_field_state is `async def` but issued
   ~8 blocking psycopg2 queries directly, so each request stalled the WHOLE
   loop for every one of them. The dashboard fans out to every field at once,
   so requests could not overlap — and a blocked loop also froze the in-flight
   Open-Meteo calls of every OTHER request while their retry timers ran.

2. AN UNCACHED LLM CALL PER FIELD. generate_ai_priorities_and_risks ran a
   ~1000-token completion on every single field-state request, so one dashboard
   load meant one completion per field.

3. A PER-FIELD WEATHER CACHE KEY. Coordinates were keyed at ~110 m, so no two
   fields ever shared a weather fetch — ~40x the upstream calls against one
   shared egress IP, which earned the sustained 429s whose backoff then cost
   seconds inside each request.
"""

import asyncio
import time
import types

import pytest


# ---------------------------------------------------------------------------
# 1. The event loop must stay responsive while the aggregator does its DB work
# ---------------------------------------------------------------------------
async def _test_blocking_db_reads_do_not_stall_the_event_loop_async(monkeypatch):
    """The real proof: run the aggregator with deliberately slow *blocking*
    reads and check a concurrent coroutine still gets scheduled promptly.

    Before the fix the heartbeat below could not tick at all until every read
    had finished, because they ran on the loop itself.
    """
    from services.field_state import aggregator as agg

    BLOCK = 0.20  # seconds of blocking work per read

    def slow_blocking(*a, **k):
        time.sleep(BLOCK)
        return []

    field_row = {
        "id": "f1", "name": "Probe", "crop_type": "Maize", "variety": "SC727",
        "tenant_id": None, "user_id": "u1", "polygon_coordinates": None,
        "planting_date": None, "area_ha": 1.0,
    }

    monkeypatch.setattr(agg, "resolve_access", lambda *a, **k: (time.sleep(BLOCK), field_row)[1])
    monkeypatch.setattr(agg, "_fetch_daily_logs", slow_blocking)
    monkeypatch.setattr(agg, "_fetch_input_count", lambda *a, **k: (time.sleep(BLOCK), 0)[1])
    monkeypatch.setattr(agg, "_fetch_plan_items", slow_blocking)
    monkeypatch.setattr(agg, "_fetch_scouting", slow_blocking)
    monkeypatch.setattr(agg, "_resolve_variety", lambda *a, **k: (time.sleep(BLOCK), (False, None))[1])
    monkeypatch.setattr(agg, "_fetch_yield", lambda *a, **k: (time.sleep(BLOCK), None)[1])

    # Keep the climate layer out of it entirely.
    import climate_service
    for name in ("get_current_weather", "get_daily_forecast", "get_agricultural_metrics"):
        monkeypatch.setattr(climate_service, name, lambda *a, **k: asyncio.sleep(0, result=None))
    monkeypatch.setattr(climate_service, "calculate_gdd", lambda *a, **k: asyncio.sleep(0, result=None))

    ticks = 0

    async def heartbeat():
        nonlocal ticks
        while True:
            await asyncio.sleep(0.02)
            ticks += 1

    hb = asyncio.create_task(heartbeat())
    try:
        await agg.build_field_state("f1", "u1", tenant_ids=[], is_admin=True)
    finally:
        hb.cancel()

    # ~7 * 0.20s = 1.4s of blocking work. On a free loop the heartbeat ticks
    # every 20ms (~70 times). If the reads ran ON the loop it would tick a
    # handful of times at most.
    assert ticks > 25, (
        f"event loop was starved during the aggregator's DB reads (only {ticks} ticks) "
        "— blocking psycopg2 calls are back on the loop"
    )


# ---------------------------------------------------------------------------
# 2. The daily briefing must be cached and single-flighted
# ---------------------------------------------------------------------------
async def _test_daily_briefing_is_cached_across_calls_async(monkeypatch):
    import ai_brain

    ai_brain._briefing_cache.clear()
    ai_brain._briefing_inflight.clear()

    calls = 0

    async def fake_uncached(self, ctx):
        nonlocal calls
        calls += 1
        return {"actions": [{"title": "A"}, {"title": "B"}], "risks": [{"name": "R"}]}

    monkeypatch.setattr(ai_brain.AgronomistBrain, "_generate_priorities_uncached", fake_uncached, raising=False)

    brain = ai_brain.AgronomistBrain.__new__(ai_brain.AgronomistBrain)
    ctx = {"crop_type": "Maize", "variety_name": "SC727", "stage_name": "V6",
           "days_since_planting": 40, "region": "II",
           "weather": {"temperature": 24.3, "humidity": 61, "precipitation": 0.2}}

    a = await ai_brain.AgronomistBrain.generate_ai_priorities_and_risks(brain, ctx)
    b = await ai_brain.AgronomistBrain.generate_ai_priorities_and_risks(brain, ctx)
    assert a == b
    assert calls == 1, "the daily briefing must not re-run the LLM for identical context"

    # Sensor jitter within a bucket must still hit the cache.
    jittered = dict(ctx, weather={"temperature": 24.4, "humidity": 62, "precipitation": 0.3})
    await ai_brain.AgronomistBrain.generate_ai_priorities_and_risks(brain, jittered)
    assert calls == 1, "weather jitter must not invalidate an otherwise identical briefing"

    # A real change (new growth stage) must produce a new briefing.
    await ai_brain.AgronomistBrain.generate_ai_priorities_and_risks(brain, dict(ctx, stage_name="VT"))
    assert calls == 2


async def _test_concurrent_fan_out_collapses_to_one_llm_call_async(monkeypatch):
    """A dashboard load over N fields must cost ONE completion, not N."""
    import ai_brain

    ai_brain._briefing_cache.clear()
    ai_brain._briefing_inflight.clear()

    calls = 0

    async def fake_uncached(self, ctx):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)          # a real completion is slow
        return {"actions": [{"t": 1}, {"t": 2}], "risks": [{"name": "R"}]}

    monkeypatch.setattr(ai_brain.AgronomistBrain, "_generate_priorities_uncached", fake_uncached, raising=False)
    brain = ai_brain.AgronomistBrain.__new__(ai_brain.AgronomistBrain)
    ctx = {"crop_type": "Maize", "variety_name": "SC727", "stage_name": "V6",
           "days_since_planting": 40, "region": "II",
           "weather": {"temperature": 24.0, "humidity": 60, "precipitation": 0.0}}

    results = await asyncio.gather(*[
        ai_brain.AgronomistBrain.generate_ai_priorities_and_risks(brain, dict(ctx)) for _ in range(20)
    ])
    assert all(r == results[0] for r in results)
    assert calls == 1, f"20 concurrent fields fired {calls} LLM completions; single-flight is broken"


async def _test_degraded_fallback_is_never_cached_async(monkeypatch):
    """One upstream blip must not pin 'Monitor Field' in front of the farmer
    for the whole TTL."""
    import ai_brain

    ai_brain._briefing_cache.clear()
    ai_brain._briefing_inflight.clear()

    seq = [
        {"actions": [{"title": "Monitor Field"}], "risks": []},          # fallback shape
        {"actions": [{"title": "A"}, {"title": "B"}], "risks": [{"n": 1}]},
    ]

    async def fake_uncached(self, ctx):
        return seq.pop(0)

    monkeypatch.setattr(ai_brain.AgronomistBrain, "_generate_priorities_uncached", fake_uncached, raising=False)
    brain = ai_brain.AgronomistBrain.__new__(ai_brain.AgronomistBrain)
    ctx = {"crop_type": "Maize", "variety_name": "X", "stage_name": "V6",
           "days_since_planting": 1, "region": "II", "weather": {}}

    first = await ai_brain.AgronomistBrain.generate_ai_priorities_and_risks(brain, ctx)
    assert first["actions"][0]["title"] == "Monitor Field"
    second = await ai_brain.AgronomistBrain.generate_ai_priorities_and_risks(brain, ctx)
    assert second["actions"][0]["title"] == "A", "the degraded fallback was cached"


# ---------------------------------------------------------------------------
# 3. Weather cache keys must be shared between nearby fields
# ---------------------------------------------------------------------------
def test_nearby_fields_share_one_weather_cache_key():
    import climate_service as cs

    # Two fields ~300 m apart on the same farm — previously two distinct keys,
    # therefore two Open-Meteo calls.
    a = cs._cache_key(-17.8201, 31.0502)
    b = cs._cache_key(-17.8228, 31.0530)
    assert a == b, "neighbouring fields must share one weather fetch"

    # Genuinely different locations must NOT collide (Harare vs Bulawayo).
    assert cs._cache_key(-17.82, 31.05) != cs._cache_key(-20.15, 28.58)


def test_snapped_coordinates_match_the_cache_key():
    """The coordinates actually FETCHED must be the ones the key describes,
    otherwise a cache entry holds data for whichever field asked first."""
    import climate_service as cs

    lat, lon = cs._snap_coords(-17.8201, 31.0502)
    assert cs._cache_key(lat, lon) == cs._cache_key(-17.8201, 31.0502)
    # Snapping is idempotent.
    assert cs._snap_coords(lat, lon) == (lat, lon)


def test_snap_grid_is_finer_than_the_weather_model():
    """Guard the accuracy trade-off: the grid must stay well under ~11 km."""
    import climate_service as cs

    assert 0 < cs._WEATHER_GRID_DEG <= 0.1, (
        "weather grid coarser than 0.1 deg (~11 km) would exceed the model's own resolution"
    )


# ---------------------------------------------------------------------------
# Sync wrappers — this repo has no pytest-asyncio, so coroutines are driven
# with asyncio.run (matching tests/test_startup_nonblocking.py).
# ---------------------------------------------------------------------------
def _run(coro):
    """Run a coroutine and leave a usable event loop installed afterwards.

    asyncio.run() calls set_event_loop(None) on exit, so any later test that
    still uses the deprecated implicit get_event_loop() would fail with
    "There is no current event loop" purely because of test ORDER. Restoring a
    fresh loop keeps this file from imposing that on the rest of the suite.
    """
    try:
        return asyncio.run(coro)
    finally:
        asyncio.set_event_loop(asyncio.new_event_loop())


def test_blocking_db_reads_do_not_stall_the_event_loop(monkeypatch):
    _run(_test_blocking_db_reads_do_not_stall_the_event_loop_async(monkeypatch))


def test_daily_briefing_is_cached_across_calls(monkeypatch):
    _run(_test_daily_briefing_is_cached_across_calls_async(monkeypatch))


def test_concurrent_fan_out_collapses_to_one_llm_call(monkeypatch):
    _run(_test_concurrent_fan_out_collapses_to_one_llm_call_async(monkeypatch))


def test_degraded_fallback_is_never_cached(monkeypatch):
    _run(_test_degraded_fallback_is_never_cached_async(monkeypatch))
