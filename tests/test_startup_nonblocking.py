"""
Deploy-survival guards (Railway Express incident, July 2026).

Two invariants keep deploys promotable on platforms with boot health checks:
1. GET / answers 200 — Railway Express probes the root path (not configurable),
   so a missing root route can fail otherwise-healthy deploys.
2. The startup handler must not block: uvicorn binds the listen socket only
   after startup handlers return, and the ~40s probe window is shorter than
   init_db()'s schema self-heal against a remote DB. The handler must return
   quickly, delegating the heavy init to a background thread.
"""

import asyncio
import time

from fastapi.testclient import TestClient

import app as app_module


def test_root_route_answers_200():
    c = TestClient(app_module.app, raise_server_exceptions=False)
    r = c.get("/")
    assert r.status_code == 200, r.text
    assert r.json().get("status") == "ok"


def test_startup_handler_returns_fast(monkeypatch):
    """The handler must return in well under a second even if the underlying
    init work is slow — i.e. the slow work is dispatched off the handler
    (executor + background task), not awaited inline."""
    slow_called = {"n": 0}

    def _slow_init_db():
        slow_called["n"] += 1
        time.sleep(2)

    monkeypatch.setattr(app_module, "init_db", _slow_init_db)

    async def _run() -> float:
        start = time.monotonic()
        await app_module.startup_checks()
        elapsed = time.monotonic() - start
        # Give the background task a beat to dispatch into the executor.
        await asyncio.sleep(0.3)
        return elapsed

    elapsed = asyncio.run(_run())

    assert elapsed < 1.0, (
        f"startup_checks blocked for {elapsed:.1f}s — uvicorn cannot bind until "
        "it returns, and platform health checks will kill the deploy"
    )
    assert slow_called["n"] == 1


def test_start_commands_bind_dual_stack():
    """Railway probes over IPv6; an 0.0.0.0 bind is unreachable to it (the
    'app running but every probe refused' incident). Every committed start
    command must bind `::` (dual-stack)."""
    import json
    import pathlib

    root = pathlib.Path(app_module.__file__).parent
    assert "--host ::" in (root / "Procfile").read_text()
    assert "--host ::" in (root / "Dockerfile").read_text()
    rj = json.loads((root / "railway.json").read_text())
    assert "--host ::" in rj["deploy"]["startCommand"]
