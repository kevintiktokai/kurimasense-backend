"""
Tests for the observability layer: structured JSON logs, request-id
propagation, and Sentry degrading to a no-op without a DSN.
"""

import json
import logging

from fastapi.testclient import TestClient

import observability as obs


def test_json_formatter_emits_valid_json_with_request_id():
    obs.request_id_ctx.set("req-123")
    rec = logging.LogRecord("kurimasense", logging.INFO, __file__, 1, "hello", None, None)
    rec.request_id = obs.request_id_ctx.get()
    line = obs.JsonLogFormatter().format(rec)
    parsed = json.loads(line)
    assert parsed["msg"] == "hello"
    assert parsed["level"] == "INFO"
    assert parsed["request_id"] == "req-123"


def test_json_formatter_includes_structured_extras():
    rec = logging.LogRecord("kurimasense", logging.INFO, __file__, 1, "evt", None, None)
    rec.event = "request_completed"
    rec.duration_ms = 12.5
    parsed = json.loads(obs.JsonLogFormatter().format(rec))
    assert parsed["event"] == "request_completed"
    assert parsed["duration_ms"] == 12.5


def test_configure_logging_is_idempotent():
    obs._configured = False
    obs.configure_logging()
    obs.configure_logging()  # second call must be a no-op, not stack handlers
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, obs.JsonLogFormatter)


def test_capture_exception_is_noop_without_sentry():
    # No SENTRY_DSN in the test env → must not raise.
    obs.capture_exception(ValueError("boom"))


def test_request_id_header_is_added():
    import app as app_module
    c = TestClient(app_module.app, raise_server_exceptions=False)
    r = c.get("/health")
    assert "X-Request-ID" in r.headers
    assert len(r.headers["X-Request-ID"]) >= 8


def test_request_id_is_propagated_from_client():
    import app as app_module
    c = TestClient(app_module.app, raise_server_exceptions=False)
    r = c.get("/health", headers={"X-Request-ID": "trace-abc"})
    assert r.headers.get("X-Request-ID") == "trace-abc"
