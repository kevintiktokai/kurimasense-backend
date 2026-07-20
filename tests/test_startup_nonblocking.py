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


def test_start_commands_use_portable_launcher():
    """Railway probes over IPv6 (0.0.0.0 is unreachable to it) while IPv4-only
    environments crash on a hard-coded `::` bind — so every committed start
    command must go through main.py's runtime host detection, never a
    hard-coded uvicorn --host."""
    import json
    import pathlib

    root = pathlib.Path(app_module.__file__).parent
    assert "python main.py" in (root / "Procfile").read_text()
    assert '"main.py"' in (root / "Dockerfile").read_text()
    rj = json.loads((root / "railway.json").read_text())
    assert rj["deploy"]["startCommand"] == "python main.py"


def test_pick_bind_host_prefers_ipv6_and_falls_back(monkeypatch):
    import socket as socket_module

    import main as main_module

    # Explicit override always wins.
    monkeypatch.setenv("UVICORN_HOST", "127.0.0.1")
    assert main_module.pick_bind_host() == "127.0.0.1"
    monkeypatch.delenv("UVICORN_HOST")

    # No IPv6 support compiled in → IPv4.
    monkeypatch.setattr(socket_module, "has_ipv6", False)
    assert main_module.pick_bind_host() == "0.0.0.0"

    # IPv6 "supported" but the stack refuses to bind (disabled at OS level,
    # as in this sandbox / some containers) → IPv4 fallback, not a crash.
    monkeypatch.setattr(socket_module, "has_ipv6", True)

    class _RefusingSocket:
        def __init__(self, *a, **kw):
            pass

        def bind(self, addr):
            raise OSError("cannot assign requested address")

        def close(self):
            pass

    monkeypatch.setattr(socket_module, "socket", _RefusingSocket)
    assert main_module.pick_bind_host() == "0.0.0.0"
