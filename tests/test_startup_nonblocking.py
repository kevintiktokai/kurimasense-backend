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
    init work is slow — i.e. the slow work runs on a background thread."""
    slow_called = {"n": 0}

    def _slow_init_db():
        slow_called["n"] += 1
        time.sleep(5)

    monkeypatch.setattr(app_module, "init_db", _slow_init_db)

    start = time.monotonic()
    app_module.startup_checks()
    elapsed = time.monotonic() - start

    assert elapsed < 1.0, (
        f"startup_checks blocked for {elapsed:.1f}s — uvicorn cannot bind until "
        "it returns, and platform health checks will kill the deploy"
    )
    # Give the daemon thread a beat to prove the work was actually dispatched.
    time.sleep(0.2)
    assert slow_called["n"] == 1
