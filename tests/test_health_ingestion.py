"""
Tests for routers/health.py — /health/ingestion freshness probe.

Run:
    cd backend
    python -m pytest tests/test_health_ingestion.py -v
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers import health as health_module  # noqa: E402
from routers.health import INGESTION_FRESH_HOURS, _is_fresh, router as health_router  # noqa: E402


# --------------------------------------------------------------------------- #
# Fake DB returning whatever the test specifies for the aggregate query
# --------------------------------------------------------------------------- #

@dataclass
class FakeStats:
    last_run_at: Optional[datetime]
    rows_last_24h: int = 0
    fields_with_data_24h: int = 0
    rejected_observations_24h: int = 0


class FakeDB:
    def __init__(self, stats: FakeStats) -> None:
        self.stats = stats

    def connect(self):
        return _Conn(self)


class _Conn:
    def __init__(self, db: FakeDB) -> None:
        self._db = db

    def cursor(self, cursor_factory=None):
        return _Cursor(self._db)

    def close(self):
        pass


class _Cursor:
    def __init__(self, db: FakeDB) -> None:
        self._db = db
        self._last: Any = None

    def execute(self, sql: str, params: Any = ()) -> None:
        s = " ".join(sql.split())
        if "FROM daily_logs" in s and "MAX(created_at)" in s:
            stats = self._db.stats
            self._last = {
                "last_run_at": stats.last_run_at,
                "rows_last_24h": stats.rows_last_24h,
                "fields_with_data_24h": stats.fields_with_data_24h,
                "rejected_observations_24h": stats.rejected_observations_24h,
            }
        else:
            self._last = None

    def fetchone(self):
        return self._last

    def close(self):
        pass


@pytest.fixture
def client_factory(monkeypatch):
    def _build(stats: FakeStats) -> TestClient:
        db = FakeDB(stats)
        monkeypatch.setattr(health_module, "get_db_connection", db.connect)
        app = FastAPI()
        app.include_router(health_router)
        return TestClient(app)
    return _build


# --------------------------------------------------------------------------- #
# Pure helper
# --------------------------------------------------------------------------- #

def test_is_fresh_true_within_window():
    now = datetime.now(timezone.utc)
    assert _is_fresh(now - timedelta(hours=2), now) is True


def test_is_fresh_false_outside_window():
    now = datetime.now(timezone.utc)
    assert _is_fresh(now - timedelta(hours=INGESTION_FRESH_HOURS + 1), now) is False


def test_is_fresh_handles_naive_timestamps():
    now = datetime.now(timezone.utc)
    naive = (now - timedelta(hours=1)).replace(tzinfo=None)
    assert _is_fresh(naive, now) is True


def test_is_fresh_false_for_none():
    assert _is_fresh(None, datetime.now(timezone.utc)) is False


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #

def test_endpoint_reports_ok_when_recent_run_present(client_factory):
    now = datetime.now(timezone.utc)
    client = client_factory(FakeStats(
        last_run_at=now - timedelta(hours=2),
        rows_last_24h=12_345,
        fields_with_data_24h=200,
        rejected_observations_24h=42,
    ))
    r = client.get("/health/ingestion")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["fresh"] is True
    assert body["freshness_window_hours"] == INGESTION_FRESH_HOURS
    assert body["rows_last_24h"] == 12_345
    assert body["fields_with_data_24h"] == 200
    assert body["rejected_observations_24h"] == 42
    assert body["last_run_at"] is not None


def test_endpoint_reports_stale_when_run_is_old(client_factory):
    now = datetime.now(timezone.utc)
    client = client_factory(FakeStats(
        last_run_at=now - timedelta(hours=INGESTION_FRESH_HOURS + 5),
        rows_last_24h=0,
    ))
    r = client.get("/health/ingestion")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "stale"
    assert body["fresh"] is False


def test_endpoint_reports_unknown_when_no_runs(client_factory):
    client = client_factory(FakeStats(last_run_at=None))
    r = client.get("/health/ingestion")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "unknown"
    assert body["last_run_at"] is None
    assert body["fresh"] is False
    assert body["rows_last_24h"] == 0


def test_endpoint_503_when_db_unavailable(monkeypatch):
    monkeypatch.setattr(health_module, "get_db_connection", lambda: None)
    app = FastAPI()
    app.include_router(health_router)
    client = TestClient(app)
    r = client.get("/health/ingestion")
    assert r.status_code == 503
