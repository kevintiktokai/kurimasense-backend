"""
Tests for season accumulations (Depth Sprint PR D).

Pure GDD/series math is tested directly; the endpoint is tested via TestClient
with the principal dependency overridden, the DB faked (drives resolve_access's
access matrix), and the weather provider mocked — no live network.
"""

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import season_routes
from services.season.accumulations import (
    gdd_params_for, compute_gdd, build_series, DailyWeather,
    DEFAULT_GDD_PARAMS,
)

FIELD_ID = "11111111-1111-1111-1111-111111111111"
TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
USER_ID = "user-1"


# ---------------------------------------------------------------------------
# GDD math
# ---------------------------------------------------------------------------

def test_gdd_base_cap_behaviour():
    # below base -> 0
    assert compute_gdd(8, 6, 10, 30) == 0.0
    # normal -> mean - base
    assert compute_gdd(24, 16, 10, 30) == 10.0          # mean 20
    # above cap -> capped at cap - base (mean 35 -> capped 30)
    assert compute_gdd(40, 30, 10, 30) == 20.0
    # exactly at cap
    assert compute_gdd(30, 30, 10, 30) == 20.0
    # cotton base
    assert compute_gdd(25, 20, 15.6, 30) == pytest.approx(22.5 - 15.6)
    # missing temps never raise
    assert compute_gdd(None, 10, 10, 30) == 0.0
    assert compute_gdd(20, None, 10, 30) == 0.0


def test_crop_base_lookup_with_default():
    assert gdd_params_for("tobacco_flue_cured") == (10.0, 30.0)
    assert gdd_params_for("tobacco_burley") == (10.0, 30.0)
    assert gdd_params_for("maize") == (10.0, 30.0)
    assert gdd_params_for("cotton") == (15.6, 30.0)
    assert gdd_params_for("soybean") == (10.0, 30.0)
    assert gdd_params_for("dragonfruit") == DEFAULT_GDD_PARAMS
    assert gdd_params_for(None) == DEFAULT_GDD_PARAMS
    assert gdd_params_for("") == DEFAULT_GDD_PARAMS


# ---------------------------------------------------------------------------
# Series builder
# ---------------------------------------------------------------------------

def _fixture_days():
    # 4 consecutive days; day 1 below base (gdd 0), day with rain, a hot day capped.
    return [
        DailyWeather("2026-02-01", tmax=8, tmin=6, precip=0.0),    # mean 7 < base -> 0 gdd
        DailyWeather("2026-02-02", tmax=24, tmin=16, precip=12.0), # mean 20 -> gdd 10
        DailyWeather("2026-02-03", tmax=40, tmin=30, precip=3.5),  # mean 35 -> capped gdd 20
        DailyWeather("2026-02-04", tmax=22, tmin=18, precip=0.0),  # mean 20 -> gdd 10
    ]


def test_series_totals_count_and_continuity():
    series, total_gdd, total_precip = build_series(_fixture_days(), base=10, cap=30)
    assert len(series) == 4
    # per-day gdd
    assert [d["gdd"] for d in series] == [0.0, 10.0, 20.0, 10.0]
    # cumulative gdd monotonic non-decreasing and correct
    assert [d["gdd_cumulative"] for d in series] == [0.0, 10.0, 30.0, 40.0]
    # cumulative precip
    assert [d["precip_cumulative"] for d in series] == [0.0, 12.0, 15.5, 15.5]
    # totals match the last cumulative
    assert total_gdd == 40.0
    assert total_precip == 15.5
    # date continuity preserved (one entry per provided day, in order)
    assert [d["date"] for d in series] == ["2026-02-01", "2026-02-02", "2026-02-03", "2026-02-04"]


def test_series_cumulative_monotonic_and_handles_missing():
    days = [
        DailyWeather("2026-03-01", tmax=None, tmin=None, precip=None),  # all missing
        DailyWeather("2026-03-02", tmax=26, tmin=14, precip=-2.0),      # negative precip clamped
    ]
    series, total_gdd, total_precip = build_series(days, base=10, cap=30)
    assert series[0]["gdd"] == 0.0 and series[0]["precip_mm"] == 0.0
    assert series[1]["gdd"] == 10.0
    assert series[1]["precip_mm"] == 0.0  # negative clamped
    # cumulative never decreases
    cums = [d["gdd_cumulative"] for d in series]
    assert cums == sorted(cums)


def test_empty_series():
    series, total_gdd, total_precip = build_series([], base=10, cap=30)
    assert series == [] and total_gdd == 0.0 and total_precip == 0.0


# ---------------------------------------------------------------------------
# Endpoint — auth matrix + window, with faked DB + mocked provider
# ---------------------------------------------------------------------------

class _FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        pass

    def fetchone(self):
        return self.conn.row

    def close(self):
        pass


class _FakeConn:
    def __init__(self, row):
        self.row = row

    def cursor(self, *a, **k):
        return _FakeCursor(self)

    def close(self):
        pass


def _field_row(*, tenant_id=TENANT_A, user_id=USER_ID, planting_date="2026-02-01", crop_type="tobacco_flue_cured"):
    return {
        "id": FIELD_ID, "user_id": user_id, "tenant_id": tenant_id, "grower_id": None,
        "name": "Test Field", "crop_type": crop_type, "variety": "KRK26",
        "planting_date": planting_date, "transplant_date": planting_date, "is_transplanted": True,
        "size_hectares": 6, "polygon_coordinates": [{"lat": -17.19, "lon": 31.47}],
        "fertilizer_history": None, "health_score": None,
    }


def _patch(monkeypatch, row, *, history=None):
    import database
    monkeypatch.setattr(database, "get_db_connection", lambda: _FakeConn(row))

    async def fake_history(lat, lon, start, end):
        return history if history is not None else [
            {"date": "2026-02-01", "tmax": 8, "tmin": 6, "precip": 0.0},
            {"date": "2026-02-02", "tmax": 24, "tmin": 16, "precip": 12.0},
            {"date": "2026-02-03", "tmax": 40, "tmin": 30, "precip": 3.5},
        ]
    monkeypatch.setattr(season_routes.climate_service, "get_daily_history", fake_history)


def _client(principal):
    app = FastAPI()
    app.include_router(season_routes.router)
    app.dependency_overrides[season_routes.get_principal] = lambda: principal
    return TestClient(app, raise_server_exceptions=False)


def test_consumer_own_field_200_via_legacy_fallback(monkeypatch):
    _patch(monkeypatch, _field_row(tenant_id=None, user_id=USER_ID))
    c = _client({"requester_id": USER_ID, "tenant_ids": [], "is_admin": False})
    r = c.get(f"/field/{FIELD_ID}/season-accumulations")
    assert r.status_code == 200
    body = r.json()
    assert body["field_id"] == FIELD_ID
    assert body["crop_type"] == "tobacco_flue_cured"
    assert body["gdd_base_c"] == 10.0 and body["gdd_cap_c"] == 30.0
    assert body["total_gdd"] == 30.0          # 0 + 10 + 20 from the mocked 3 days
    assert body["total_precip_mm"] == 15.5
    assert len(body["series"]) == 3
    assert body["days_elapsed"] > 0


def test_cross_tenant_403(monkeypatch):
    _patch(monkeypatch, _field_row(tenant_id=TENANT_A, user_id="someone-else"))
    c = _client({"requester_id": "other-user", "tenant_ids": [TENANT_B], "is_admin": False})
    r = c.get(f"/field/{FIELD_ID}/season-accumulations")
    assert r.status_code == 403


def test_institutional_own_tenant_200(monkeypatch):
    _patch(monkeypatch, _field_row(tenant_id=TENANT_A, user_id="grower-x"))
    c = _client({"requester_id": "officer", "tenant_ids": [TENANT_A], "is_admin": False})
    r = c.get(f"/field/{FIELD_ID}/season-accumulations")
    assert r.status_code == 200
    assert r.json()["planting_date"] == "2026-02-01"


def test_admin_any_field_200(monkeypatch):
    _patch(monkeypatch, _field_row(tenant_id=TENANT_A, user_id="grower-x"))
    c = _client({"requester_id": "admin", "tenant_ids": [], "is_admin": True})
    assert c.get(f"/field/{FIELD_ID}/season-accumulations").status_code == 200


def test_unknown_field_404(monkeypatch):
    _patch(monkeypatch, None)
    c = _client({"requester_id": USER_ID, "tenant_ids": [], "is_admin": False})
    assert c.get(f"/field/{FIELD_ID}/season-accumulations").status_code == 404


def test_null_planting_date_422(monkeypatch):
    _patch(monkeypatch, _field_row(tenant_id=None, user_id=USER_ID, planting_date=None))
    c = _client({"requester_id": USER_ID, "tenant_ids": [], "is_admin": False})
    r = c.get(f"/field/{FIELD_ID}/season-accumulations")
    assert r.status_code == 422
    assert "planting_date" in r.json()["detail"]


def test_cotton_uses_its_base(monkeypatch):
    _patch(monkeypatch, _field_row(tenant_id=None, user_id=USER_ID, crop_type="cotton"))
    c = _client({"requester_id": USER_ID, "tenant_ids": [], "is_admin": False})
    body = c.get(f"/field/{FIELD_ID}/season-accumulations").json()
    assert body["gdd_base_c"] == 15.6 and body["gdd_cap_c"] == 30.0
