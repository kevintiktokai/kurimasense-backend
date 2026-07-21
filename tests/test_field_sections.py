"""
Zone-level field analysis tests: the pure sectioning geometry
(field_sections.py) and the route wiring (section_routes.py).
"""

import pytest
from fastapi.testclient import TestClient

import app as app_module
from field_sections import (
    clip_to_rect, compute_sections, ring_area, ring_centroid, section_label,
)


# A simple ~rectangular field near Harare (open ring, {lat, lon}).
RECT = [
    {"lat": -17.800, "lon": 31.000},
    {"lat": -17.800, "lon": 31.010},
    {"lat": -17.810, "lon": 31.010},
    {"lat": -17.810, "lon": 31.000},
]

# An L-shaped field: the NE quadrant is missing entirely.
L_SHAPE = [
    {"lat": -17.800, "lon": 31.000},
    {"lat": -17.800, "lon": 31.005},
    {"lat": -17.805, "lon": 31.005},
    {"lat": -17.805, "lon": 31.010},
    {"lat": -17.810, "lon": 31.010},
    {"lat": -17.810, "lon": 31.000},
]


# --- Geometry ----------------------------------------------------------------

def test_rect_splits_into_four_equal_compass_zones():
    sections = compute_sections(RECT, grid=2)
    assert [s["label"] for s in sections] == [
        "North-West", "North-East", "South-West", "South-East",
    ]
    # Equal quarters of a rectangle.
    for s in sections:
        assert s["area_share"] == pytest.approx(0.25, abs=0.01)
    # Shares always sum to ~1 (no double counting, no gaps).
    assert sum(s["area_share"] for s in sections) == pytest.approx(1.0, abs=0.02)


def test_north_zones_have_higher_latitude_than_south_zones():
    sections = {s["label"]: s for s in compute_sections(RECT, grid=2)}
    assert sections["North-West"]["centroid"]["lat"] > sections["South-West"]["centroid"]["lat"]
    assert sections["North-East"]["centroid"]["lon"] > sections["North-West"]["centroid"]["lon"]


def test_l_shape_drops_the_missing_quadrant():
    sections = compute_sections(L_SHAPE, grid=2)
    labels = [s["label"] for s in sections]
    assert "North-East" not in labels  # the notch — no field there
    assert set(labels) == {"North-West", "South-West", "South-East"}
    assert sum(s["area_share"] for s in sections) == pytest.approx(1.0, abs=0.03)


def test_centroids_fall_inside_field_bbox():
    for s in compute_sections(L_SHAPE, grid=2):
        c = s["centroid"]
        assert -17.810 <= c["lat"] <= -17.800
        assert 31.000 <= c["lon"] <= 31.010


def test_degenerate_polygons_return_empty():
    assert compute_sections([], grid=2) == []
    assert compute_sections(RECT[:2], grid=2) == []
    flat = [{"lat": -17.8, "lon": 31.0}, {"lat": -17.8, "lon": 31.1}, {"lat": -17.8, "lon": 31.2}]
    assert compute_sections(flat, grid=2) == []


def test_grid_three_uses_generic_labels():
    assert section_label(0, 0, 3) == "Zone R1C1"
    assert section_label(2, 2, 3) == "Zone R3C3"
    sections = compute_sections(RECT, grid=3)
    assert len(sections) == 9


def test_clip_to_rect_confines_ring():
    clipped = clip_to_rect(RECT, -17.805, -17.800, 31.000, 31.005)
    assert len(clipped) >= 3
    for p in clipped:
        assert -17.805 - 1e-9 <= p["lat"] <= -17.800 + 1e-9
        assert 31.000 - 1e-9 <= p["lon"] <= 31.005 + 1e-9
    assert ring_area(clipped) == pytest.approx(ring_area(RECT) / 4, rel=0.02)


def test_ring_centroid_of_rect_is_center():
    c = ring_centroid(RECT)
    assert c["lat"] == pytest.approx(-17.805, abs=1e-6)
    assert c["lon"] == pytest.approx(31.005, abs=1e-6)


# --- Route wiring ------------------------------------------------------------

def test_sections_routes_require_auth():
    c = TestClient(app_module.app, raise_server_exceptions=False)
    assert c.get("/fields/00000000-0000-0000-0000-000000000001/sections").status_code == 401
    assert c.post("/fields/00000000-0000-0000-0000-000000000001/sections/analyze").status_code == 401


def test_sections_grid_is_bounded():
    # The route caps grid via `le=MAX_GRID` so a field can't be sliced into
    # hundreds of unwalkable micro-zones; guard the constant + geometry.
    import section_routes
    assert section_routes.MAX_GRID == 3
    assert len(compute_sections(RECT, grid=section_routes.MAX_GRID)) == 9
