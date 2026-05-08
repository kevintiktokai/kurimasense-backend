"""
Unit tests for routers/portfolio.py — updated for the bcrypt + key_id_hex
auth flow in services.auth.api_key_auth.

Run:
    cd backend
    python -m pytest tests/test_portfolio_api.py -v
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import bcrypt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers import portfolio as portfolio_module  # noqa: E402
from routers.portfolio import (  # noqa: E402
    classify_risk,
    compute_field_risk_score,
    detect_anomaly,
    project_yield_for_field,
    router as portfolio_router,
)
from services.auth import api_key_auth as auth_module  # noqa: E402
from services.auth.api_key_auth import KEY_PREFIX  # noqa: E402


# --------------------------------------------------------------------------- #
# Fake DB
# --------------------------------------------------------------------------- #

@dataclass
class _ApiKeyRow:
    id: str
    tenant_id: str
    key_id_hex: str
    key_hash: str
    name: str = "test"
    is_active: bool = True
    expires_at: Optional[datetime] = None
    rate_limit_override: Optional[Dict[str, int]] = None


@dataclass
class _FieldRow:
    id: str
    user_id: str
    crop_type: str = "Maize"
    size_hectares: float = 5.0
    health_score: Optional[float] = 80
    natural_region: str = "II"


@dataclass
class _DailyLogRow:
    field_id: str
    log_date: date
    ndvi: Optional[float] = None
    evi: Optional[float] = None
    indices: Optional[Dict[str, Any]] = None
    cloud_pct: Optional[float] = None
    observation_quality: Optional[str] = "good"


class FakeDB:
    def __init__(self) -> None:
        self.api_keys: List[_ApiKeyRow] = []
        self.fields: List[_FieldRow] = []
        self.daily_logs: List[_DailyLogRow] = []

    def connect(self):
        return _FakeConn(self)


class _FakeConn:
    def __init__(self, db: FakeDB) -> None:
        self._db = db

    def cursor(self, cursor_factory=None):
        return _FakeCursor(self._db)

    def close(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass


class _FakeCursor:
    def __init__(self, db: FakeDB) -> None:
        self._db = db
        self._last: Any = None
        self.rowcount = 0

    def execute(self, sql: str, params: Any = ()) -> None:
        s = " ".join(sql.split())

        # ---- api_keys lookup by key_id_hex (verify_api_key flow) ----
        if "FROM api_keys WHERE key_id_hex" in s:
            (key_id_hex,) = params
            row = next((k for k in self._db.api_keys if k.key_id_hex == key_id_hex), None)
            if row is None:
                self._last = None
                return
            self._last = {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "key_hash": row.key_hash,
                "name": row.name,
                "expires_at": row.expires_at,
                "is_active": row.is_active,
                "rate_limit_override": row.rate_limit_override,
            }
            return

        # ---- last_used_at touch ----
        if "UPDATE api_keys SET last_used_at" in s:
            (key_id,) = params
            for r in self._db.api_keys:
                if r.id == key_id:
                    self.rowcount = 1
                    break
            self._last = None
            return

        # ---- field user_id lookup (indices_history tenant check) ----
        if "SELECT user_id FROM fields WHERE id" in s:
            (field_id,) = params
            row = next((f for f in self._db.fields if f.id == field_id), None)
            self._last = {"user_id": row.user_id} if row else None
            return

        # ---- daily_logs history ----
        if "FROM daily_logs WHERE field_id" in s and "log_date BETWEEN" in s:
            field_id, start_date, end_date = params
            rows = []
            for dl in self._db.daily_logs:
                if dl.field_id != field_id:
                    continue
                if dl.log_date < start_date or dl.log_date > end_date:
                    continue
                rows.append({
                    "log_date": dl.log_date,
                    "ndvi": dl.ndvi,
                    "evi": dl.evi,
                    "indices": dl.indices,
                    "cloud_pct": dl.cloud_pct,
                    "observation_quality": dl.observation_quality,
                })
            rows.sort(key=lambda r: r["log_date"])
            self._last = rows
            return

        # ---- field id list per tenant ----
        if "SELECT id FROM fields WHERE user_id" in s:
            (tenant_id,) = params
            self._last = [{"id": f.id} for f in self._db.fields if f.user_id == tenant_id]
            return

        # ---- tenant fields aggregation ----
        if "FROM fields f WHERE f.user_id" in s and "AVG(ndvi)" in s:
            tenant_id, crop_filter, crop_filter2 = params
            rows: List[Dict[str, Any]] = []
            for f in self._db.fields:
                if f.user_id != tenant_id:
                    continue
                if crop_filter is not None and crop_filter.strip("%").lower() not in (f.crop_type or "").lower():
                    continue
                cutoff = date.today() - timedelta(days=7)
                logs = [
                    dl for dl in self._db.daily_logs
                    if dl.field_id == f.id and dl.log_date >= cutoff
                ]
                ndvis = [dl.ndvi for dl in logs if dl.ndvi is not None]
                ndmis = [
                    (dl.indices or {}).get("optical", {}).get("ndmi")
                    for dl in logs if dl.indices is not None
                ]
                ndmis = [v for v in ndmis if v is not None]
                clouds = [dl.cloud_pct for dl in logs if dl.cloud_pct is not None]
                rows.append({
                    "id": f.id,
                    "crop_type": f.crop_type,
                    "size_hectares": f.size_hectares,
                    "health_score": f.health_score,
                    "district": f.natural_region or "Unknown",
                    "recent_ndvi": (sum(ndvis) / len(ndvis)) if ndvis else None,
                    "recent_ndmi": (sum(ndmis) / len(ndmis)) if ndmis else None,
                    "recent_cloud_pct": (sum(clouds) / len(clouds)) if clouds else None,
                })
            self._last = rows
            return

        # ---- risk score aggregation ----
        if "FROM fields f WHERE f.id = ANY" in s:
            (field_ids,) = params
            rows = []
            cutoff = date.today() - timedelta(days=14)
            for f in self._db.fields:
                if f.id not in field_ids:
                    continue
                logs = [dl for dl in self._db.daily_logs if dl.field_id == f.id and dl.log_date >= cutoff]
                ndvis = [dl.ndvi for dl in logs if dl.ndvi is not None]
                ndmis = [
                    (dl.indices or {}).get("optical", {}).get("ndmi")
                    for dl in logs if dl.indices is not None
                ]
                ndmis = [v for v in ndmis if v is not None]
                clouds = [dl.cloud_pct for dl in logs if dl.cloud_pct is not None]
                rows.append({
                    "id": f.id,
                    "user_id": f.user_id,
                    "health_score": f.health_score,
                    "recent_ndvi": (sum(ndvis) / len(ndvis)) if ndvis else None,
                    "recent_ndmi": (sum(ndmis) / len(ndmis)) if ndmis else None,
                    "recent_cloud_pct": (sum(clouds) / len(clouds)) if clouds else None,
                })
            self._last = rows
            return

        self._last = None

    def fetchone(self):
        if isinstance(self._last, list):
            return self._last[0] if self._last else None
        return self._last

    def fetchall(self):
        if isinstance(self._last, list):
            return self._last
        return []

    def close(self):
        pass


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"


def _mint_key_for(db: FakeDB, tenant_id: str) -> str:
    """Mint a real-format raw key and store the bcrypt hash in the fake DB."""
    key_id_hex = "abcdef0123456789" if tenant_id == TENANT_A else "fedcba9876543210"
    secret = "test-secret-" + tenant_id[:8]
    raw = f"{KEY_PREFIX}{key_id_hex}.{secret}"
    key_hash = bcrypt.hashpw(secret.encode(), bcrypt.gensalt(rounds=4)).decode()
    db.api_keys.append(
        _ApiKeyRow(
            id=f"key-{tenant_id[:4]}",
            tenant_id=tenant_id,
            key_id_hex=key_id_hex,
            key_hash=key_hash,
        )
    )
    return raw


@pytest.fixture
def db(monkeypatch):
    fake = FakeDB()
    # The auth module and the portfolio module both call get_db_connection.
    monkeypatch.setattr(auth_module, "get_db_connection", fake.connect)
    monkeypatch.setattr(portfolio_module, "get_db_connection", fake.connect)
    return fake


@pytest.fixture
def keys(db):
    return {
        "A": _mint_key_for(db, TENANT_A),
        "B": _mint_key_for(db, TENANT_B),
    }


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(portfolio_router)
    return TestClient(app)


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #

def test_classify_risk_buckets():
    assert classify_risk(0.75, 80)[0] == "low"
    assert classify_risk(0.50, 70)[0] == "medium"
    assert classify_risk(0.30, 60)[0] == "high"
    assert classify_risk(0.20, 60)[0] == "critical"
    assert classify_risk(None, None)[0] == "high"


def test_compute_risk_score_increases_with_stress():
    healthy = compute_field_risk_score(ndvi=0.75, ndmi=0.30, cloud_pct=5, health_score=80)[0]
    stressed = compute_field_risk_score(ndvi=0.30, ndmi=0.05, cloud_pct=5, health_score=40)[0]
    assert stressed > healthy
    assert 0.0 <= healthy <= 1.0
    assert 0.0 <= stressed <= 1.0


def test_compute_risk_score_no_data_returns_conservative():
    score, factors = compute_field_risk_score(
        ndvi=None, ndmi=None, cloud_pct=None, health_score=None
    )
    assert score == 0.6
    assert "No data" in factors[0]


def test_detect_anomaly_flags_ndvi_drop():
    points = [
        {"ndvi": 0.75}, {"ndvi": 0.74}, {"ndvi": 0.73},
        {"ndvi": 0.45}, {"ndvi": 0.42}, {"ndvi": 0.40},
    ]
    a = detect_anomaly(points, "ndvi", threshold=0.15, days_back=14)
    assert a is not None
    assert a.drop > 0.15


def test_detect_anomaly_no_flag_when_stable():
    points = [{"ndvi": 0.7 + i * 0.001} for i in range(8)]
    assert detect_anomaly(points, "ndvi", threshold=0.15, days_back=14) is None


def test_project_yield_for_field_uses_default_yields():
    y, c = project_yield_for_field(crop_type="Maize", size_hectares=2.0, recent_ndvi=0.72)
    assert y > 5.0
    assert c > 0


def test_project_yield_for_field_no_ndvi_falls_back():
    y, c = project_yield_for_field(crop_type="Maize", size_hectares=2.0, recent_ndvi=None)
    assert c == 0.4
    assert y < 6.0


# --------------------------------------------------------------------------- #
# Auth wiring
# --------------------------------------------------------------------------- #

def test_missing_api_key_returns_401(keys, client):
    r = client.get(f"/portfolio/{TENANT_A}/yield_forecast")
    assert r.status_code == 401
    assert "Missing X-API-Key" in r.json()["detail"]


def test_invalid_format_api_key_returns_401(keys, client):
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": "garbage-not-a-key"},
    )
    assert r.status_code == 401


def test_disabled_api_key_returns_401(keys, client, db):
    db.api_keys[0].is_active = False
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 401


def test_expired_api_key_returns_401(keys, client, db):
    db.api_keys[0].expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 401


def test_wrong_tenant_returns_403(keys, client):
    # Tenant B's key against Tenant A's URL.
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": keys["B"]},
    )
    assert r.status_code == 403


# --------------------------------------------------------------------------- #
# yield_forecast
# --------------------------------------------------------------------------- #

def test_yield_forecast_groups_by_district(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, crop_type="Maize", size_hectares=10.0, natural_region="II"))
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A, crop_type="Maize", size_hectares=20.0, natural_region="II"))
    db.fields.append(_FieldRow(id="f3", user_id=TENANT_A, crop_type="Maize", size_hectares=15.0, natural_region="III"))
    today = date.today()
    for fid, ndvi in [("f1", 0.72), ("f2", 0.68), ("f3", 0.40)]:
        db.daily_logs.append(_DailyLogRow(field_id=fid, log_date=today, ndvi=ndvi))

    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    by_district = {d["district_name"]: d for d in body["districts"]}
    assert set(by_district.keys()) == {"II", "III"}
    assert by_district["II"]["n_fields"] == 2
    assert by_district["II"]["total_area_ha"] == 30.0
    assert by_district["II"]["projected_yield_tonnes_per_ha"] > by_district["III"]["projected_yield_tonnes_per_ha"]


def test_yield_forecast_filters_by_crop(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, crop_type="Maize"))
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A, crop_type="Tobacco"))
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast?crop=Maize",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 200
    total = sum(d["n_fields"] for d in r.json()["districts"])
    assert total == 1


# --------------------------------------------------------------------------- #
# risk_summary
# --------------------------------------------------------------------------- #

def test_risk_summary_distributes_fields_across_buckets(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, health_score=85))
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A, health_score=65))
    db.fields.append(_FieldRow(id="f3", user_id=TENANT_A, health_score=40))
    db.fields.append(_FieldRow(id="f4", user_id=TENANT_A, health_score=20))
    today = date.today()
    db.daily_logs.append(_DailyLogRow(field_id="f1", log_date=today, ndvi=0.75))
    db.daily_logs.append(_DailyLogRow(field_id="f2", log_date=today, ndvi=0.50))
    db.daily_logs.append(_DailyLogRow(field_id="f3", log_date=today, ndvi=0.35))
    db.daily_logs.append(_DailyLogRow(field_id="f4", log_date=today, ndvi=0.20))

    r = client.get(
        f"/portfolio/{TENANT_A}/risk_summary",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 200
    body = r.json()
    rd = body["risk_distribution"]
    assert (rd["low"], rd["medium"], rd["high"], rd["critical"]) == (1, 1, 1, 1)


# --------------------------------------------------------------------------- #
# anomalies
# --------------------------------------------------------------------------- #

def test_anomalies_flags_dropping_ndvi(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A))
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A))
    today = date.today()
    for i in range(8):
        ndvi = 0.75 if i < 4 else 0.40
        db.daily_logs.append(_DailyLogRow(field_id="f1", log_date=today - timedelta(days=8 - i), ndvi=ndvi))
    for i in range(8):
        db.daily_logs.append(_DailyLogRow(field_id="f2", log_date=today - timedelta(days=8 - i), ndvi=0.70))

    r = client.get(
        f"/portfolio/{TENANT_A}/anomalies?days_back=14&threshold=0.15",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 200
    flagged = {a["field_id"] for a in r.json()["anomalies"]}
    assert "f1" in flagged
    assert "f2" not in flagged


def test_anomalies_threshold_param_validated(keys, client):
    r = client.get(
        f"/portfolio/{TENANT_A}/anomalies?threshold=0",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# indices_history
# --------------------------------------------------------------------------- #

def test_field_indices_history_returns_sorted_points(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A))
    today = date.today()
    db.daily_logs.append(_DailyLogRow(
        field_id="f1", log_date=today - timedelta(days=2), ndvi=0.65,
        indices={"optical": {"ndvi": 0.65, "evi": 0.4, "ndre": 0.3, "ndmi": 0.25, "savi": 0.5}},
    ))
    db.daily_logs.append(_DailyLogRow(
        field_id="f1", log_date=today - timedelta(days=1), ndvi=0.68,
        indices={"optical": {"ndvi": 0.68, "evi": 0.42, "ndre": 0.32, "ndmi": 0.28, "savi": 0.52}},
    ))

    r = client.get(
        f"/field/f1/indices_history?start_date={today - timedelta(days=5)}&end_date={today}",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["points"]) == 2
    assert body["points"][0]["log_date"] < body["points"][1]["log_date"]
    assert body["points"][0]["ndre"] == pytest.approx(0.3)


def test_field_indices_history_blocks_cross_tenant_access(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_B))
    today = date.today()
    r = client.get(
        f"/field/f1/indices_history?start_date={today - timedelta(days=5)}&end_date={today}",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 403


def test_field_indices_history_404_for_unknown_field(keys, client):
    today = date.today()
    r = client.get(
        f"/field/missing-field/indices_history?start_date={today - timedelta(days=5)}&end_date={today}",
        headers={"X-API-Key": keys["A"]},
    )
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# risk_score (POST)
# --------------------------------------------------------------------------- #

def test_risk_score_returns_per_field_scores(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, health_score=85))
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A, health_score=30))
    today = date.today()
    db.daily_logs.append(_DailyLogRow(
        field_id="f1", log_date=today, ndvi=0.75, cloud_pct=2.0,
        indices={"optical": {"ndmi": 0.30}},
    ))
    db.daily_logs.append(_DailyLogRow(
        field_id="f2", log_date=today, ndvi=0.30, cloud_pct=10.0,
        indices={"optical": {"ndmi": 0.05}},
    ))

    r = client.post(
        f"/portfolio/{TENANT_A}/risk_score",
        headers={"X-API-Key": keys["A"]},
        json={"field_ids": ["f1", "f2"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["scores"]["f2"]["score"] > body["scores"]["f1"]["score"]


def test_risk_score_marks_other_tenant_fields_as_unknown(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, health_score=80))
    db.fields.append(_FieldRow(id="fX", user_id=TENANT_B, health_score=80))
    r = client.post(
        f"/portfolio/{TENANT_A}/risk_score",
        headers={"X-API-Key": keys["A"]},
        json={"field_ids": ["f1", "fX"]},
    )
    body = r.json()
    assert body["scores"]["fX"]["score"] == 1.0


def test_risk_score_marks_missing_fields(keys, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, health_score=80))
    r = client.post(
        f"/portfolio/{TENANT_A}/risk_score",
        headers={"X-API-Key": keys["A"]},
        json={"field_ids": ["f1", "ghost"]},
    )
    body = r.json()
    assert body["scores"]["ghost"]["score"] == 1.0


def test_risk_score_requires_at_least_one_id(keys, client):
    r = client.post(
        f"/portfolio/{TENANT_A}/risk_score",
        headers={"X-API-Key": keys["A"]},
        json={"field_ids": []},
    )
    assert r.status_code == 422
