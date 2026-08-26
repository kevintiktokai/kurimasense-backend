"""
Nothing blocking runs on the event loop, and nothing slow runs in the request.

These are the two rules behind the 26 August production profile, where a farmer
opening the dashboard waited over a minute:

    "path": "/field/c13a4c80…/state",   "duration_ms": 73743.01
    "path": "/field/805bdf95…/state",   "duration_ms": 61776.54
    "path": "/crops/Maize/varieties",   "duration_ms": 15295.13
    "path": "/climate/historical",      "duration_ms": 26026.80

The varieties call is the tell. It logged `Found 20 varieties` — twenty rows,
one indexed table — and took fifteen seconds. Nothing about that query is slow.
It was waiting, and while it waited it was itself blocking everything else,
because it was declared `async def` and ran psycopg2 straight on the event loop.

Render sets WEB_CONCURRENCY=1 by default on a one-CPU instance, and says so in
the deploy log. One worker means one event loop for the entire API. Under that,
a single blocking call is not slow for its own caller — it is slow for every
caller, and the effect compounds with concurrency. A dashboard opening seven
fields does not run seven requests concurrently; it runs them one after another,
each one holding the loop.

Both guards are lint-shaped: they fail on the *next* instance, not just the ones
that were fixed.
"""

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Handlers whose blocking work has been reviewed and is not yet moved off the
#: loop. Every entry is a known cost, not an exemption in principle — the point
#: of naming them here is that adding a new one is a deliberate act.
KNOWN_BLOCKING = {
    # A 152-line FastAPI BackgroundTask with awaits threaded through it. It runs
    # after the response, so it delays nobody's page directly; it does steal
    # loop time from concurrent requests. Restructuring it means separating the
    # satellite fetch from the database writes, which is a real change to the
    # code that records daily_logs, and is not something to do blind.
    "trigger_sentinel_analysis",
}


def _async_defs(tree: ast.AST):
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef):
            yield node


def _blocking_db_calls(fn: ast.AsyncFunctionDef) -> list[int]:
    """`get_db_connection()` calls in this coroutine's own body.

    Calls inside a nested plain `def` do not count: that is the shape of work
    handed to `run_in_threadpool` or `asyncio.to_thread`, which is exactly the
    fix. Distinguishing the two is the whole job of this function — a guard that
    could not tell them apart would flag every correct handler in the file and
    be switched off within a week.
    """
    found: list[int] = []

    def walk(node, inside_sync_def: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                walk(child, True)
                continue
            if (
                not inside_sync_def
                and isinstance(child, ast.Call)
                and getattr(child.func, "id", "") == "get_db_connection"
            ):
                found.append(child.lineno)
            walk(child, inside_sync_def)

    walk(fn, False)
    return found


def test_no_async_handler_queries_the_database_on_the_event_loop():
    tree = ast.parse((ROOT / "app.py").read_text())
    offenders = {
        fn.name: _blocking_db_calls(fn)
        for fn in _async_defs(tree)
        if _blocking_db_calls(fn) and fn.name not in KNOWN_BLOCKING
    }
    assert offenders == {}, (
        "psycopg2 is blocking and these handlers are `async def`, so every query "
        "here stalls the whole API. Either drop `async` (FastAPI threadpools a "
        "plain `def` handler) or move the query into a nested `def` and await it "
        f"through run_in_threadpool:\n  {offenders}"
    )


def test_the_guard_can_tell_a_threadpooled_query_from_a_blocking_one():
    # Without this, the test above is satisfied by a guard that sees nothing.
    # The first version of this check looked for `to_thread` anywhere in the
    # function and reported the chat routes as broken — they use Starlette's
    # `run_in_threadpool`, and were correct all along.
    blocking = ast.parse(
        "async def handler():\n"
        "    conn = get_db_connection()\n"
        "    return conn\n"
    ).body[0]
    threadpooled = ast.parse(
        "async def handler():\n"
        "    def _read():\n"
        "        conn = get_db_connection()\n"
        "        return conn\n"
        "    return await run_in_threadpool(_read)\n"
    ).body[0]

    assert _blocking_db_calls(blocking) == [2]
    assert _blocking_db_calls(threadpooled) == []


def test_coordinate_resolution_does_not_block_the_loop():
    # Every /climate/* route calls resolve_coordinates before it does anything
    # else. It was `async def` with psycopg2 inline, so six weather cards
    # serialised on this one lookup before any of them reached Open-Meteo —
    # /climate/historical at 26s for a request whose upstream fetch took 700ms.
    deps = (ROOT / "deps.py").read_text()
    tree = ast.parse(deps)
    resolve = next(
        n for n in tree.body
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "resolve_coordinates"
    )
    assert _blocking_db_calls(resolve) == []
    assert "_coords_from_field" in deps
    assert "asyncio.to_thread(_coords_from_field" in deps


# ---------------------------------------------------------------------------
# Nothing slow in the request path
# ---------------------------------------------------------------------------
def test_the_field_state_path_does_not_wait_for_a_language_model():
    # The 73 seconds. `/field/{id}/state` is on the path every screen takes, and
    # it awaited an LLM completion per field. Seven fields with seven different
    # crops and stages produced seven distinct cache keys, so the single-flight
    # that was supposed to collapse a dashboard fan-out could not: seven
    # completions, in the request, untimed.
    src = (ROOT / "proactive_intelligence.py").read_text()
    tree = ast.parse(src)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "generate_proactive_alerts"
    )
    awaited = {
        getattr(node.value.func, "attr", "")
        for node in ast.walk(fn)
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call)
    }
    assert "generate_ai_priorities_and_risks" not in awaited, (
        "the farmer is waiting on this request; the model call belongs behind it"
    )
    assert "priorities_if_cached" in src
    assert "refresh_priorities_soon" in src


def test_cached_priorities_never_call_the_model():
    # The contract that makes the above safe: a cache lookup that can quietly
    # fall through to a completion would put the 73 seconds straight back.
    brain = ast.parse((ROOT / "ai_brain.py").read_text())
    fn = next(
        n for n in ast.walk(brain)
        if isinstance(n, ast.FunctionDef) and n.name == "priorities_if_cached"
    )
    assert not any(isinstance(n, ast.Await) for n in ast.walk(fn)), (
        "priorities_if_cached must be a pure cache read"
    )


def test_the_background_refresh_is_bounded_and_held():
    src = (ROOT / "ai_brain.py").read_text()
    # A completion with no timeout can hang for as long as the upstream holds
    # the socket, and nothing awaits this task, so it would hang silently.
    assert "asyncio.wait_for(" in src
    assert "_AI_PRIORITIES_TIMEOUT" in src
    # asyncio keeps only a weak reference to a running task. Without a strong
    # one the garbage collector can cancel the refresh mid-flight and the cache
    # then never warms — a bug that presents as "the AI insights never appear"
    # with nothing in the logs at all.
    assert "_priorities_tasks.add(task)" in src
    assert "task.add_done_callback(_priorities_tasks.discard)" in src


def test_a_second_view_of_the_same_field_reuses_the_warmed_answer():
    import ai_brain

    ctx = {
        "crop_type": "Tobacco", "variety_name": "KRK26", "stage_name": "Reaping",
        "days_since_planting": 90, "weather": {"temperature": 24, "humidity": 60},
    }
    key = ai_brain._briefing_cache_key(ctx)
    brain = ai_brain.get_brain()
    ai_brain._briefing_cache.pop(key, None)
    try:
        assert brain.priorities_if_cached(ctx) is None, "cold cache must report a miss"

        warmed = {"actions": ["Top the crop"], "risks": []}
        ai_brain._briefing_cache[key] = (__import__("time").time(), warmed)
        assert brain.priorities_if_cached(ctx) == warmed
    finally:
        ai_brain._briefing_cache.pop(key, None)


def test_a_refresh_outside_an_event_loop_declines_rather_than_raising():
    # Called from a sync context — a background generator, a management command
    # — there is no loop to schedule onto. Returning False beats raising inside
    # a farmer's request.
    import ai_brain

    assert ai_brain.get_brain().refresh_priorities_soon({"crop_type": "Maize"}) is False
