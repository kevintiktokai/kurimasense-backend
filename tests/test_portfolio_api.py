"""
Unit tests for routers/portfolio.py.

Run:
    cd backend
    python -m pytest tests/test_portfolio_api.py -v

Uses FastAPI's TestClient with a hand-rolled fake DB (no real psycopg2).
"""
from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers import portfolio as portfolio_module  # noqa: E402
from routers.portfolio import (  # noqa: E402
    _hash_api_key,
    classify_risk,
    compute_field_risk_score,
    detect_anomaly,
    project_yield_for_field,
    router as portfolio_router,
)


# --------------------------------------------------------------------------- #
# Fake DB (parameterised by test fixtures)
# --------------------------------------------------------------------------- #

@dataclass
class _ApiKeyRow:
    tenant_id: str
    key_hash: str
    is_active: bool = True
    expires_at: Optional[datetime] = None


@dataclass
class _FieldRow:
    id: str
    user_id: str  # tenant_id
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

    def execute(self, sql: str, params: Any = ()) -> None:
        s = " ".join(sql.split())

        # ---- api_keys lookups ----
        if "FROM api_keys a LEFT JOIN fields f" in s:
            field_id, key_hash = params
            api_row = next(
                (k for k in self._db.api_keys if k.key_hash == key_hash), None
            )
            if api_row is None:
                self._last = None
                return
            field_row = next((f for f in self._db.fields if f.id == field_id), None)
            self._last = {
                "tenant_id": api_row.tenant_id,
                "is_active": api_row.is_active,
                "expires_at": api_row.expires_at,
                "user_id": field_row.user_id if field_row else None,
            }
            return
        if "FROM api_keys" in s:
            (key_hash,) = params
            api_row = next(
                (k for k in self._db.api_keys if k.key_hash == key_hash), None
            )
            if api_row is None:
                self._last = None
                return
            self._last = {
                "tenant_id": api_row.tenant_id,
                "is_active": api_row.is_active,
                "expires_at": api_row.expires_at,
            }
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
                # 7-day NDVI/NDMI/cloud means.
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

        # ---- daily_logs history per field ----
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
# App & client
# --------------------------------------------------------------------------- #

@pytest.fixture
def db(monkeypatch):
    fake = FakeDB()
    monkeypatch.setattr(portfolio_module, "get_db_connection", fake.connect)
    return fake


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(portfolio_router)
    return TestClient(app)


TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"
KEY_A = "tk_test_aaaaaaaa"
KEY_B = "tk_test_bbbbbbbb"


@pytest.fixture
def seed(db):
    db.api_keys.append(_ApiKeyRow(tenant_id=TENANT_A, key_hash=_hash_api_key(KEY_A)))
    db.api_keys.append(_ApiKeyRow(tenant_id=TENANT_B, key_hash=_hash_api_key(KEY_B)))
    return db


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #

def test_hash_api_key_uses_sha256():
    raw = "secret-token"
    expected = hashlib.sha256(raw.encode()).hexdigest()
    assert _hash_api_key(raw) == expected


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
    assert y > 5.0  # base 6.0 × 1.0 factor
    assert c > 0


def test_project_yield_for_field_no_ndvi_falls_back():
    y, c = project_yield_for_field(crop_type="Maize", size_hectares=2.0, recent_ndvi=None)
    assert c == 0.4
    assert y < 6.0


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #

def test_missing_api_key_returns_401(seed, client):
    r = client.get(f"/portfolio/{TENANT_A}/yield_forecast")
    assert r.status_code == 401
    assert "Missing X-API-Key" in r.json()["detail"]


def test_invalid_api_key_returns_401(seed, client):
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": "totally-bogus"},
    )
    assert r.status_code == 401
    assert "Invalid API key" in r.json()["detail"]


def test_disabled_api_key_returns_401(seed, client, db):
    db.api_keys[0].is_active = False
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 401
    assert "disabled" in r.json()["detail"].lower()


def test_expired_api_key_returns_401(seed, client, db):
    db.api_keys[0].expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 401
    assert "expired" in r.json()["detail"].lower()


def test_wrong_tenant_returns_403(seed, client):
    # Use Tenant B's key against Tenant A's URL.
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": KEY_B},
    )
    assert r.status_code == 403
    assert "tenant" in r.json()["detail"].lower()


# --------------------------------------------------------------------------- #
# yield_forecast
# --------------------------------------------------------------------------- #

def test_yield_forecast_groups_by_district(seed, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, crop_type="Maize", size_hectares=10.0, natural_region="II"))
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A, crop_type="Maize", size_hectares=20.0, natural_region="II"))
    db.fields.append(_FieldRow(id="f3", user_id=TENANT_A, crop_type="Maize", size_hectares=15.0, natural_region="III"))
    today = date.today()
    for fid, ndvi in [("f1", 0.72), ("f2", 0.68), ("f3", 0.40)]:
        db.daily_logs.append(_DailyLogRow(field_id=fid, log_date=today, ndvi=ndvi))

    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["tenant_id"] == TENANT_A
    by_district = {d["district_name"]: d for d in body["districts"]}
    assert set(by_district.keys()) == {"II", "III"}
    assert by_district["II"]["n_fields"] == 2
    assert by_district["II"]["total_area_ha"] == 30.0
    assert by_district["III"]["n_fields"] == 1
    # Region II has both healthy NDVIs → factor 1.0; Region III is stressed.
    assert by_district["II"]["projected_yield_tonnes_per_ha"] > by_district["III"]["projected_yield_tonnes_per_ha"]
    band = by_district["II"]["confidence_band"]
    assert band["low"] < band["mid"] < band["high"]


def test_yield_forecast_filters_by_crop(seed, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, crop_type="Maize"))
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A, crop_type="Tobacco"))
    r = client.get(
        f"/portfolio/{TENANT_A}/yield_forecast?crop=Maize",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 200
    total = sum(d["n_fields"] for d in r.json()["districts"])
    assert total == 1


# --------------------------------------------------------------------------- #
# risk_summary
# --------------------------------------------------------------------------- #

def test_risk_summary_distributes_fields_across_buckets(seed, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, health_score=85))   # low
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A, health_score=65))   # medium
    db.fields.append(_FieldRow(id="f3", user_id=TENANT_A, health_score=40))   # high
    db.fields.append(_FieldRow(id="f4", user_id=TENANT_A, health_score=20))   # critical
    today = date.today()
    db.daily_logs.append(_DailyLogRow(field_id="f1", log_date=today, ndvi=0.75))
    db.daily_logs.append(_DailyLogRow(field_id="f2", log_date=today, ndvi=0.50))
    db.daily_logs.append(_DailyLogRow(field_id="f3", log_date=today, ndvi=0.35))
    db.daily_logs.append(_DailyLogRow(field_id="f4", log_date=today, ndvi=0.20))

    r = client.get(
        f"/portfolio/{TENANT_A}/risk_summary",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_fields"] == 4
    rd = body["risk_distribution"]
    assert rd["low"] == 1
    assert rd["medium"] == 1
    assert rd["high"] == 1
    assert rd["critical"] == 1
    flagged = {a["field_id"]: a for a in body["fields_with_alerts"]}
    assert "f3" in flagged and "f4" in flagged
    assert flagged["f4"]["risk_level"] == "critical"


# --------------------------------------------------------------------------- #
# anomalies
# --------------------------------------------------------------------------- #

def test_anomalies_flags_dropping_ndvi(seed, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A))
    db.fields.append(_FieldRow(id="f2", user_id=TENANT_A))
    today = date.today()
    # Field 1: NDVI plunges over the window → anomaly.
    for i in range(8):
        ndvi = 0.75 if i < 4 else 0.40
        db.daily_logs.append(
            _DailyLogRow(field_id="f1", log_date=today - timedelta(days=8 - i), ndvi=ndvi)
        )
    # Field 2: NDVI stable → no anomaly.
    for i in range(8):
        db.daily_logs.append(
            _DailyLogRow(field_id="f2", log_date=today - timedelta(days=8 - i), ndvi=0.70)
        )

    r = client.get(
        f"/portfolio/{TENANT_A}/anomalies?days_back=14&threshold=0.15",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 200
    body = r.json()
    flagged_field_ids = {a["field_id"] for a in body["anomalies"]}
    assert "f1" in flagged_field_ids
    assert "f2" not in flagged_field_ids
    f1_anoms = [a for a in body["anomalies"] if a["field_id"] == "f1"]
    assert any(a["index"] == "ndvi" for a in f1_anoms)


def test_anomalies_threshold_param_validated(seed, client, db):
    r = client.get(
        f"/portfolio/{TENANT_A}/anomalies?threshold=0",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 422  # threshold must be > 0


# --------------------------------------------------------------------------- #
# indices_history
# --------------------------------------------------------------------------- #

def test_field_indices_history_returns_sorted_points(seed, client, db):
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
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["points"]) == 2
    assert body["points"][0]["log_date"] < body["points"][1]["log_date"]
    assert body["points"][0]["ndvi"] == pytest.approx(0.65)
    assert body["points"][0]["ndre"] == pytest.approx(0.3)


def test_field_indices_history_blocks_cross_tenant_access(seed, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_B))  # owned by B
    today = date.today()
    r = client.get(
        f"/field/f1/indices_history?start_date={today - timedelta(days=5)}&end_date={today}",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 403


def test_field_indices_history_404_for_unknown_field(seed, client, db):
    today = date.today()
    r = client.get(
        f"/field/missing-field/indices_history?start_date={today - timedelta(days=5)}&end_date={today}",
        headers={"X-API-Key": KEY_A},
    )
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# risk_score (POST)
# --------------------------------------------------------------------------- #

def test_risk_score_returns_per_field_scores(seed, client, db):
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
        headers={"X-API-Key": KEY_A},
        json={"field_ids": ["f1", "f2"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert set(body["scores"].keys()) == {"f1", "f2"}
    assert body["scores"]["f2"]["score"] > body["scores"]["f1"]["score"]
    assert any("Low NDVI" in f for f in body["scores"]["f2"]["primary_factors"])


def test_risk_score_marks_other_tenant_fields_as_unknown(seed, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, health_score=80))
    db.fields.append(_FieldRow(id="fX", user_id=TENANT_B, health_score=80))  # other tenant

    r = client.post(
        f"/portfolio/{TENANT_A}/risk_score",
        headers={"X-API-Key": KEY_A},
        json={"field_ids": ["f1", "fX"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["scores"]["fX"]["score"] == 1.0
    assert "not in tenant" in body["scores"]["fX"]["primary_factors"][0].lower()


def test_risk_score_marks_missing_fields(seed, client, db):
    db.fields.append(_FieldRow(id="f1", user_id=TENANT_A, health_score=80))
    r = client.post(
        f"/portfolio/{TENANT_A}/risk_score",
        headers={"X-API-Key": KEY_A},
        json={"field_ids": ["f1", "ghost"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["scores"]["ghost"]["score"] == 1.0
    assert "not found" in body["scores"]["ghost"]["primary_factors"][0].lower()


def test_risk_score_requires_at_least_one_id(seed, client):
    r = client.post(
        f"/portfolio/{TENANT_A}/risk_score",
        headers={"X-API-Key": KEY_A},
        json={"field_ids": []},
    )
    assert r.status_code == 422
