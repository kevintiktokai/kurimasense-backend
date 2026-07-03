"""
Observability: structured JSON logging, per-request correlation IDs, and
optional Sentry error tracking.

Design goals
------------
* One structured log line per event (JSON to stdout — Render/most platforms
  ingest that directly), so logs are queryable instead of free-text prints.
* A request id threaded through every log line of a request (contextvar +
  logging filter), surfaced to clients as the ``X-Request-ID`` response header,
  so a user-reported error maps to exactly the lines that produced it.
* Sentry is opt-in via ``SENTRY_DSN`` and fully degradable — absent the DSN (or
  the SDK), everything still runs; ``capture_exception`` is a no-op.

Nothing here requires secrets to function; Sentry simply stays dormant.
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import sys
import uuid

# The current request's correlation id. "-" outside a request.
request_id_ctx: "contextvars.ContextVar[str]" = contextvars.ContextVar("request_id", default="-")

logger = logging.getLogger("kurimasense")


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


class _RequestIdFilter(logging.Filter):
    """Attach the current request id to every record so the formatter can emit it."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonLogFormatter(logging.Formatter):
    """Render each record as a single JSON object."""

    # Standard LogRecord attributes we don't want to duplicate into "extra".
    _RESERVED = set(vars(logging.makeLogRecord({})).keys()) | {"request_id", "message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "msg": record.getMessage(),
        }
        # Structured extras passed via logger.info(..., extra={...}).
        for k, v in record.__dict__.items():
            if k not in self._RESERVED and not k.startswith("_"):
                payload[k] = v
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_configured = False


def configure_logging() -> None:
    """Install the JSON handler + request-id filter on the root logger. Idempotent.

    Level comes from ``LOG_LEVEL`` (default INFO). Safe to call at import and at
    startup; only the first call takes effect.
    """
    global _configured
    if _configured:
        return
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(_RequestIdFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Uvicorn's access log duplicates our request_completed line — quiet it.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    _configured = True


def init_sentry() -> bool:
    """Initialise Sentry if ``SENTRY_DSN`` is set and the SDK is available.

    Returns True when active. Never raises — observability must not be able to
    take the app down.
    """
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
            environment=os.getenv("ENVIRONMENT", "production"),
            send_default_pii=False,
        )
        logger.info("Sentry initialised", extra={"component": "observability"})
        return True
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Sentry init failed: {e}")
        return False


def capture_exception(exc: BaseException) -> None:
    """Forward an exception to Sentry if configured; no-op otherwise.

    ``sentry_sdk.capture_exception`` is itself a no-op when the SDK was never
    initialised (no DSN), so no client check is needed — and we avoid the
    deprecated Hub API.
    """
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except Exception:  # pragma: no cover - never let telemetry raise
        pass
