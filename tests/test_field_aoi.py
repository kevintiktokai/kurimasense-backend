"""
Unit tests for services/satellite/field_aoi.py.

Run:
    cd backend
    python -m pytest tests/test_field_aoi.py -v
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.satellite import field_aoi  # noqa: E402
from services.satellite.field_aoi import (  # noqa: E402
    CACHE_TTL_DAYS,
    FieldNotFoundError,
    _build_aoi_from_field,
    _build_circular_aoi,
    _build_polygon_from_vertices,
    _normalize_coords,
    _polygon_to_aoi_dict,
    get_field_aoi,
)


# --------------------------------------------------------------------------- #
# Fake DB infrastructure
# --------------------------------------------------------------------------- #

class _FakeCursor:
    """Records queries and returns scripted rows / behaves like RealDictCursor."""

    def __init__(self, db: "_FakeDB") -> None:
        self._db = db
        self._last_result: Optional[Dict[str, Any]] = None
        self.executed: List[Tuple[str, tuple]] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        self.executed.append((sql, params))
        sql_norm = " ".join(sql.split())
        if "FROM field_aoi_cache" in sql_norm:
            field_id = params[1]
            ttl = params[0]
            row = self._db.cache.get(field_id)
            if row is None:
                self._last_result = None
                return
            is_fresh = row["age_days"] < ttl
            self._last_result = {
                "field_id": field_id,
                "bbox": row["bbox"],
                "geometry": row["geometry"],
                "area_ha": row["area_ha"],
                "last_updated": "fake",
                "is_fresh": is_fresh,
            }
        elif "FROM fields" in sql_norm:
            field_id = params[0]
            self._last_result = self._db.fields.get(field_id)
        elif "INSERT INTO field_aoi_cache" in sql_norm:
            field_id, bbox_json, geometry_json, area_ha = params
            self._db.cache[field_id] = {
                "bbox": json.loads(bbox_json),
                "geometry": json.loads(geometry_json),
                "area_ha": area_ha,
                "age_days": 0,
            }
            self._last_result = None
        else:
            self._last_result = None

    def fetchone(self) -> Optional[Dict[str, Any]]:
        return self._last_result

    def close(self) -> None:
        pass


class _FakeConn:
    def __init__(self, db: "_FakeDB") -> None:
        self._db = db
        self.committed = False

    def cursor(self, cursor_factory=None) -> _FakeCursor:
        return _FakeCursor(self._db)

    def commit(self) -> None:
        self.committed = True

    def close(self) -> None:
        pass


class _FakeDB:
    def __init__(self) -> None:
        self.fields: Dict[str, Dict[str, Any]] = {}
        self.cache: Dict[str, Dict[str, Any]] = {}

    def connect(self):
        return _FakeConn(self)


@pytest.fixture
def fake_db(monkeypatch):
    db = _FakeDB()
    monkeypatch.setattr(field_aoi, "get_db_connection", db.connect)
    return db


# --------------------------------------------------------------------------- #
# Helpers — unit tests for pure builders
# --------------------------------------------------------------------------- #

def test_normalize_coords_lat_lon_dicts():
    raw = [{"lat": -17.8, "lon": 31.0}, {"lat": -17.7, "lon": 31.1}]
    assert _normalize_coords(raw) == [(31.0, -17.8), (31.1, -17.7)]


def test_normalize_coords_lat_lng_dicts():
    raw = [{"lat": -17.8, "lng": 31.0}]
    assert _normalize_coords(raw) == [(31.0, -17.8)]


def test_normalize_coords_array_pairs():
    raw = [[31.0, -17.8], [31.1, -17.7]]
    assert _normalize_coords(raw) == [(31.0, -17.8), (31.1, -17.7)]


def test_normalize_coords_handles_none_and_garbage():
    assert _normalize_coords(None) == []
    assert _normalize_coords("not-json") == []
    assert _normalize_coords([{"lat": 1}, "weird", 5]) == []


def test_build_polygon_closes_ring_if_open():
    coords = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    poly = _build_polygon_from_vertices(coords)
    ring = list(poly.exterior.coords)
    assert ring[0] == ring[-1]
    assert len(ring) == 5


def test_build_polygon_leaves_already_closed_ring_intact():
    coords = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    poly = _build_polygon_from_vertices(coords)
    assert len(list(poly.exterior.coords)) == 5


def test_build_circular_aoi_radius_matches_area_formula():
    area_ha = 5.0
    poly = _build_circular_aoi(31.0, -17.8, area_ha)
    aoi = _polygon_to_aoi_dict(poly)
    assert aoi["area_ha"] == pytest.approx(area_ha, rel=0.01)
    expected_radius_m = math.sqrt(area_ha * 10_000.0 / math.pi)
    minx, miny, maxx, maxy = poly.bounds
    # Width in degrees ≈ 2*r / (cos(lat)*111320)
    width_deg = maxx - minx
    expected_width_deg = (2 * expected_radius_m) / (
        math.cos(math.radians(-17.8)) * 111_320.0
    )
    assert width_deg == pytest.approx(expected_width_deg, rel=0.01)


# --------------------------------------------------------------------------- #
# get_field_aoi — full flow
# --------------------------------------------------------------------------- #

def test_polygon_field_builds_aoi_and_writes_cache(fake_db):
    field_id = "11111111-1111-1111-1111-111111111111"
    fake_db.fields[field_id] = {
        "polygon_coordinates": [
            {"lat": -17.80, "lon": 31.00},
            {"lat": -17.80, "lon": 31.01},
            {"lat": -17.79, "lon": 31.01},
            {"lat": -17.79, "lon": 31.00},
        ],
        "size_hectares": 12.34,
    }

    aoi = get_field_aoi(field_id)

    assert aoi["type"] == "Polygon"
    # Outer ring is closed.
    ring = aoi["coordinates"][0]
    assert ring[0] == ring[-1]
    assert ring[0] == [31.00, -17.80]
    # bbox is [minLon, minLat, maxLon, maxLat]
    assert aoi["bbox"][0] == pytest.approx(31.00)
    assert aoi["bbox"][1] == pytest.approx(-17.80)
    assert aoi["bbox"][2] == pytest.approx(31.01)
    assert aoi["bbox"][3] == pytest.approx(-17.79)
    # ~1.1 km × 1.1 km tile near the equator → ≈ 117 ha; just sanity check > 0.
    assert aoi["area_ha"] > 0
    # Cache row was written.
    assert field_id in fake_db.cache
    assert fake_db.cache[field_id]["bbox"] == aoi["bbox"]


def test_point_field_builds_circular_aoi(fake_db):
    field_id = "22222222-2222-2222-2222-222222222222"
    fake_db.fields[field_id] = {
        "polygon_coordinates": [{"lat": -17.80, "lon": 31.00}],
        "size_hectares": 4.0,
    }

    aoi = get_field_aoi(field_id)

    assert aoi["type"] == "Polygon"
    assert aoi["area_ha"] == pytest.approx(4.0, rel=0.02)
    minx, miny, maxx, maxy = aoi["bbox"]
    # Center of the circle ≈ original point.
    assert (minx + maxx) / 2 == pytest.approx(31.00, abs=1e-6)
    assert (miny + maxy) / 2 == pytest.approx(-17.80, abs=1e-6)
    assert field_id in fake_db.cache


def test_two_coordinate_field_builds_circular_aoi_at_centroid(fake_db):
    field_id = "33333333-3333-3333-3333-333333333333"
    fake_db.fields[field_id] = {
        "polygon_coordinates": [
            {"lat": -17.80, "lon": 31.00},
            {"lat": -17.78, "lon": 31.02},
        ],
        "size_hectares": 2.0,
    }

    aoi = get_field_aoi(field_id)

    assert aoi["type"] == "Polygon"
    assert aoi["area_ha"] == pytest.approx(2.0, rel=0.02)
    minx, miny, maxx, maxy = aoi["bbox"]
    # Circle centered on midpoint of the two input points.
    assert (minx + maxx) / 2 == pytest.approx(31.01, abs=1e-6)
    assert (miny + maxy) / 2 == pytest.approx(-17.79, abs=1e-6)


def test_few_coords_without_size_raises(fake_db):
    field_id = "44444444-4444-4444-4444-444444444444"
    fake_db.fields[field_id] = {
        "polygon_coordinates": [{"lat": -17.80, "lon": 31.00}],
        "size_hectares": None,
    }

    with pytest.raises(ValueError):
        get_field_aoi(field_id)


def test_unknown_field_raises_field_not_found(fake_db):
    with pytest.raises(FieldNotFoundError):
        get_field_aoi("55555555-5555-5555-5555-555555555555")


def test_cache_hit_returns_cached_without_touching_fields_table(fake_db):
    field_id = "66666666-6666-6666-6666-666666666666"
    fake_db.cache[field_id] = {
        "bbox": [10.0, 20.0, 11.0, 21.0],
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[10.0, 20.0], [10.0, 21.0], [11.0, 21.0], [11.0, 20.0], [10.0, 20.0]]],
        },
        "area_ha": 1234.5,
        "age_days": 5,  # < CACHE_TTL_DAYS
    }
    # Intentionally no fields entry — must be served from cache only.

    aoi = get_field_aoi(field_id)

    assert aoi["bbox"] == [10.0, 20.0, 11.0, 21.0]
    assert aoi["area_ha"] == 1234.5
    assert aoi["coordinates"][0][0] == [10.0, 20.0]


def test_stale_cache_falls_through_to_fields(fake_db):
    field_id = "77777777-7777-7777-7777-777777777777"
    fake_db.cache[field_id] = {
        "bbox": [0.0, 0.0, 1.0, 1.0],
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]]],
        },
        "area_ha": 999.0,
        "age_days": CACHE_TTL_DAYS + 1,  # stale
    }
    fake_db.fields[field_id] = {
        "polygon_coordinates": [
            {"lat": -17.80, "lon": 31.00},
            {"lat": -17.80, "lon": 31.01},
            {"lat": -17.79, "lon": 31.01},
            {"lat": -17.79, "lon": 31.00},
        ],
        "size_hectares": 100.0,
    }

    aoi = get_field_aoi(field_id)

    # Got a real AOI from fields, not the stale cache.
    assert aoi["bbox"][0] == pytest.approx(31.00)
    # Cache row was rewritten with the fresh bbox.
    assert fake_db.cache[field_id]["bbox"][0] == pytest.approx(31.00)


def test_cache_miss_then_subsequent_call_hits_cache(fake_db):
    field_id = "88888888-8888-8888-8888-888888888888"
    fake_db.fields[field_id] = {
        "polygon_coordinates": [
            {"lat": -17.80, "lon": 31.00},
            {"lat": -17.80, "lon": 31.01},
            {"lat": -17.79, "lon": 31.01},
        ],
        "size_hectares": None,
    }

    first = get_field_aoi(field_id)
    # Now wipe the fields entry to prove the second call hits cache only.
    del fake_db.fields[field_id]
    second = get_field_aoi(field_id)
    assert first["bbox"] == second["bbox"]
    assert first["area_ha"] == pytest.approx(second["area_ha"])
