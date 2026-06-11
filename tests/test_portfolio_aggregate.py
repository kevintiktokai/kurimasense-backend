"""
Tests for the portfolio aggregate endpoint + service (MVP PR 2).

Pure logic (urgency/sort/summary/banding) is tested directly; the aggregation is
tested against a fake DB (the service reuses assemble_field_state, no network);
authorization is tested via TestClient with an overridden auth dependency.
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import portfolio_routes
import services.portfolio.aggregate as agg
from services.portfolio.aggregate import (
    derive_urgency, score_to_band, compute_summary, compute_portfolio_aggregate, TenantNotFound,
)
from schemas import AuthenticatedUser, PortfolioPriority

TENANT_ID = "6fd723f4-caff-42b7-a971-0e3ed992aa94"


# ---------------------------------------------------------------------------
# Fake DB routed by SQL
# ---------------------------------------------------------------------------
class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.last = ""

    def execute(self, sql, params=None):
        self.last = " ".join(sql.split())
        self.conn.calls.append(self.last)

    def fetchone(self):
        if "FROM tenants" in self.last:
            return self.conn.tenant
        return None

    def fetchall(self):
        if "FROM fields f" in self.last:
            return self.conn.fields
        if "FROM daily_logs" in self.last:
            return self.conn.logs
        if "FROM field_inputs" in self.last:
            return self.conn.inputs
        return []

    def close(self):
        pass


class FakeConn:
    def __init__(self, tenant, fields, logs=None, inputs=None):
        self.tenant = tenant
        self.fields = fields
        self.logs = logs or []
        self.inputs = inputs or []
        self.calls = []

    def cursor(self, *a, **k):
        return FakeCursor(self)

    def close(self):
        pass


def _tenant_row():
    return {"id": TENANT_ID, "name": "Test Institution", "institutional_type": "buyer"}


_DEFAULT_POLYGON = [{"lat": -17.0, "lon": 31.0}]


def _field(fid, name, *, grower_id=None, grower_name=None, ha=4.0, ndvi_days=None, polygon="__default__"):
    """A field row; ndvi_days=None means no observations (awaiting_data).
    Pass ``polygon=None`` for a field with no stored geometry."""
    return {
        "id": fid, "name": name, "crop_type": "tobacco_flue_cured", "crop": None,
        "variety": "KRK26", "size_hectares": ha, "natural_region": "II",
        "polygon_coordinates": _DEFAULT_POLYGON if polygon == "__default__" else polygon,
        "planting_date": "2026-02-01", "transplant_date": "2026-02-01", "is_transplanted": True,
        "user_id": "u1", "tenant_id": TENANT_ID, "grower_id": grower_id,
        "grower_name": grower_name, "created_at": "2026-06-01T00:00:00",
    }


def _log(fid, ndvi):
    return {"field_id": fid, "log_date": "2026-06-04", "ndvi": ndvi, "evi": ndvi - 0.03,
            "soil_moisture": 35, "cloud_cover": 5}


def _patch_db(monkeypatch, conn):
    import database
    monkeypatch.setattr(database, "get_db_connection", lambda: conn)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Pure logic
# ---------------------------------------------------------------------------
def test_urgency_thresholds():
    assert [derive_urgency(s) for s in (10, 30, 50, 70, 90, None)] == \
        ["critical", "high", "medium", "low", "low", "awaiting_data"]


def test_score_to_band_reuses_classifier():
    assert score_to_band(None) == (None, None)
    label, color = score_to_band(90)
    assert label == "Thriving" and color.startswith("#")


def test_summary_distribution_and_average():
    rows = [_field(f"f{i}", f"n{i}") for i in range(7)]
    states = [(90, []), (75, []), (60, []), (45, []), (30, []), (10, []), (None, [])]
    s = compute_summary(rows, states)
    d = s.score_distribution
    assert (d.thriving, d.strong, d.adequate, d.stressed, d.distressed, d.critical, d.awaiting_data) \
        == (1, 1, 1, 1, 1, 1, 1)
    assert s.fields_with_data == 6 and s.fields_awaiting_data == 1
    assert s.average_kurima_score == round((90 + 75 + 60 + 45 + 30 + 10) / 6, 1)


def test_summary_average_none_when_no_data():
    rows = [_field("f1", "n1")]
    s = compute_summary(rows, [(None, [])])
    assert s.average_kurima_score is None and s.fields_with_data == 0


# ---------------------------------------------------------------------------
# Aggregation (fake DB)
# ---------------------------------------------------------------------------
def test_empty_tenant(monkeypatch):
    _patch_db(monkeypatch, FakeConn(_tenant_row(), fields=[]))
    resp = _run(compute_portfolio_aggregate(TENANT_ID))
    assert resp.summary.total_fields == 0
    assert resp.priorities == []
    assert resp.summary.score_distribution.awaiting_data == 0
    assert resp.tenant.name == "Test Institution"


def test_tenant_not_found(monkeypatch):
    _patch_db(monkeypatch, FakeConn(tenant=None, fields=[]))
    with pytest.raises(TenantNotFound):
        _run(compute_portfolio_aggregate(TENANT_ID))


def test_awaiting_data_sorts_last_and_counts(monkeypatch):
    fields = [
        _field("f-healthy", "DEMO_SEED: A - Bindura - Flue-Cured", ha=2.0),
        _field("f-await", "DEMO_SEED: B - Karoi - Flue-Cured", ha=9.0),
    ]
    logs = [_log("f-healthy", 0.78)]  # only the first field has an observation
    _patch_db(monkeypatch, FakeConn(_tenant_row(), fields, logs=logs))
    resp = _run(compute_portfolio_aggregate(TENANT_ID))

    assert len(resp.priorities) == 2
    # the field with data is actionable → comes before the awaiting-data one
    assert resp.priorities[0].field_id == "f-healthy"
    assert resp.priorities[0].kurima_score is not None
    assert resp.priorities[-1].field_id == "f-await"
    assert resp.priorities[-1].urgency == "awaiting_data"
    assert resp.priorities[-1].kurima_score is None
    assert resp.priorities[-1].primary_concern == "Awaiting satellite observations"
    assert resp.summary.fields_awaiting_data == 1
    assert resp.summary.fields_with_data == 1
    # district parsed from the demo name
    assert resp.priorities[0].district in ("Bindura", "Karoi")


def test_grower_name_passthrough(monkeypatch):
    fields = [_field("f1", "Field 1", grower_id="g1", grower_name="Tafadzwa Moyo")]
    _patch_db(monkeypatch, FakeConn(_tenant_row(), fields, logs=[_log("f1", 0.6)]))
    resp = _run(compute_portfolio_aggregate(TENANT_ID))
    assert resp.priorities[0].grower_id == "g1"
    assert resp.priorities[0].grower_name == "Tafadzwa Moyo"
    assert resp.summary.total_growers == 1


def test_deterministic_sort(monkeypatch):
    fields = [_field(f"f{i}", f"DEMO_SEED: G{i} - Bindura - Flue-Cured", ha=float(i)) for i in range(6)]
    logs = [_log(f"f{i}", 0.2 + i * 0.1) for i in range(6)]
    conn = FakeConn(_tenant_row(), fields, logs=logs)
    _patch_db(monkeypatch, conn)
    order1 = [p.field_id for p in _run(compute_portfolio_aggregate(TENANT_ID)).priorities]
    _patch_db(monkeypatch, FakeConn(_tenant_row(), fields, logs=logs))
    order2 = [p.field_id for p in _run(compute_portfolio_aggregate(TENANT_ID)).priorities]
    assert order1 == order2
    # worst (lowest score) first within the actionable set
    scores = [p.kurima_score for p in _run(compute_portfolio_aggregate(TENANT_ID)).priorities if p.kurima_score is not None]
    assert scores == sorted(scores)


# ---------------------------------------------------------------------------
# Authorization (endpoint)
# ---------------------------------------------------------------------------
def _client(user: AuthenticatedUser, conn=None, monkeypatch=None):
    app = FastAPI()
    app.include_router(portfolio_routes.router)
    app.dependency_overrides[portfolio_routes.get_authenticated_user] = lambda: user
    if conn is not None and monkeypatch is not None:
        import database
        monkeypatch.setattr(database, "get_db_connection", lambda: conn)
    return TestClient(app, raise_server_exceptions=False)


def test_consumer_forbidden():
    c = _client(AuthenticatedUser(user_id="u", role="consumer", tenant_id="t", tenant_ids=["t"]))
    assert c.get("/portfolio/aggregate").status_code == 403


def test_institutional_no_tenant_400():
    c = _client(AuthenticatedUser(user_id="u", role="institutional", institutional_type="buyer", tenant_id=None, tenant_ids=[]))
    assert c.get("/portfolio/aggregate").status_code == 400


def test_institutional_other_tenant_403():
    c = _client(AuthenticatedUser(user_id="u", role="institutional", institutional_type="buyer", tenant_id=TENANT_ID, tenant_ids=[TENANT_ID]))
    assert c.get("/portfolio/aggregate?tenant_id=other").status_code == 403


def test_institutional_own_tenant_200(monkeypatch):
    user = AuthenticatedUser(user_id="u", role="institutional", institutional_type="buyer", tenant_id=TENANT_ID, tenant_ids=[TENANT_ID])
    c = _client(user, conn=FakeConn(_tenant_row(), fields=[]), monkeypatch=monkeypatch)
    r = c.get("/portfolio/aggregate")
    assert r.status_code == 200 and r.json()["tenant"]["id"] == TENANT_ID


def test_admin_any_tenant_200(monkeypatch):
    user = AuthenticatedUser(user_id="a", role="admin", tenant_id=None, tenant_ids=[])
    c = _client(user, conn=FakeConn(_tenant_row(), fields=[]), monkeypatch=monkeypatch)
    r = c.get(f"/portfolio/aggregate?tenant_id={TENANT_ID}")
    assert r.status_code == 200


def test_tenant_not_found_404(monkeypatch):
    user = AuthenticatedUser(user_id="a", role="admin", tenant_id=None, tenant_ids=[])
    c = _client(user, conn=FakeConn(tenant=None, fields=[]), monkeypatch=monkeypatch)
    assert c.get(f"/portfolio/aggregate?tenant_id={TENANT_ID}").status_code == 404


# ---------------------------------------------------------------------------
# Geometry + latest indices (Depth Sprint PR C) — additive payload extension
# ---------------------------------------------------------------------------
import time as _time

from services.portfolio.aggregate import compute_centroid


def test_compute_centroid_pure():
    # vertex mean of a square
    sq = [{"lat": 0, "lon": 0}, {"lat": 0, "lon": 2}, {"lat": 2, "lon": 2}, {"lat": 2, "lon": 0}]
    assert compute_centroid(sq) == {"lat": 1.0, "lon": 1.0}
    # malformed / empty / None never raise → None
    assert compute_centroid(None) is None
    assert compute_centroid([]) is None
    assert compute_centroid("nope") is None
    assert compute_centroid([{"x": 1}, {"lat": 1}]) is None       # missing lon
    assert compute_centroid([{"lat": "bad", "lon": "x"}]) is None  # non-numeric
    # mixed valid/invalid → averages only the valid vertices
    assert compute_centroid([{"lat": 1, "lon": 1}, {"bad": 0}]) == {"lat": 1.0, "lon": 1.0}


def _bbox(polygon):
    lats = [p["lat"] for p in polygon]
    lons = [p["lon"] for p in polygon]
    return min(lats), max(lats), min(lons), max(lons)


def test_field_with_polygon_returns_geometry_and_centroid_in_bbox(monkeypatch):
    poly = [
        {"lat": -17.10, "lon": 31.40}, {"lat": -17.10, "lon": 31.44},
        {"lat": -17.14, "lon": 31.44}, {"lat": -17.14, "lon": 31.40},
    ]
    fields = [_field("f1", "A", polygon=poly)]
    _patch_db(monkeypatch, FakeConn(_tenant_row(), fields, logs=[_log("f1", 0.6)]))
    resp = _run(compute_portfolio_aggregate(TENANT_ID))
    p = resp.priorities[0]
    assert p.polygon_coordinates == poly
    assert p.centroid is not None
    lat_min, lat_max, lon_min, lon_max = _bbox(poly)
    assert lat_min <= p.centroid["lat"] <= lat_max
    assert lon_min <= p.centroid["lon"] <= lon_max


def test_field_without_polygon_returns_none_and_stays_valid(monkeypatch):
    fields = [_field("f1", "A", polygon=None)]
    _patch_db(monkeypatch, FakeConn(_tenant_row(), fields, logs=[_log("f1", 0.6)]))
    resp = _run(compute_portfolio_aggregate(TENANT_ID))
    p = resp.priorities[0]
    assert p.polygon_coordinates is None
    assert p.centroid is None
    assert p.field_id == "f1"  # response otherwise intact


def test_latest_indices_populated_when_observed_and_none_when_awaiting(monkeypatch):
    fields = [_field("f-obs", "Observed"), _field("f-await", "Awaiting")]
    logs = [_log("f-obs", 0.71)]  # only the first field has an observation
    _patch_db(monkeypatch, FakeConn(_tenant_row(), fields, logs=logs))
    resp = _run(compute_portfolio_aggregate(TENANT_ID))
    by_id = {p.field_id: p for p in resp.priorities}
    assert by_id["f-obs"].latest_ndvi == 0.71
    assert by_id["f-obs"].latest_soil_moisture == 35     # from the daily_logs row
    assert by_id["f-await"].latest_ndvi is None
    assert by_id["f-await"].latest_soil_moisture is None


def test_40_fields_under_one_second(monkeypatch):
    fields = [_field(f"f{i}", f"DEMO_SEED: G{i} - Bindura - Flue-Cured", ha=float(i % 10 + 1)) for i in range(40)]
    logs = [_log(f"f{i}", 0.3 + (i % 50) / 100) for i in range(40)]
    _patch_db(monkeypatch, FakeConn(_tenant_row(), fields, logs=logs))
    t0 = _time.perf_counter()
    resp = _run(compute_portfolio_aggregate(TENANT_ID))
    elapsed = _time.perf_counter() - t0
    assert len(resp.priorities) == 40
    assert all(p.centroid is not None for p in resp.priorities)
    assert elapsed < 1.0, f"aggregate took {elapsed*1000:.0f}ms for 40 fields"
