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


def test_grid_three_splits_into_nine_directional_zones():
    # Superseded the old "Zone R1C1" naming: row/column labels told a farmer
    # nothing about where to walk, which is the whole job of a zone name.
    assert section_label(0, 0, 3) == "North-West"
    assert section_label(2, 2, 3) == "South-East"
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
    # hundreds of unwalkable micro-zones. The cap moved from 3 to 4 when grid
    # size started scaling with field area (a 60 ha block needs more than nine
    # zones to stay walkable) — what matters is that a cap still exists and
    # stays small, not the exact number.
    import section_routes
    assert 2 <= section_routes.MAX_GRID <= 4
    zones = compute_sections(RECT, grid=section_routes.MAX_GRID)
    assert len(zones) == section_routes.MAX_GRID ** 2


# --- Zone naming (directional, auto-generated) --------------------------------

from field_sections import suggest_grid_size, WALKABLE_ZONE_HA  # noqa: E402


def test_two_by_two_keeps_the_plain_compass_corners():
    assert section_label(0, 0, 2) == "North-West"
    assert section_label(0, 1, 2) == "North-East"
    assert section_label(1, 0, 2) == "South-West"
    assert section_label(1, 1, 2) == "South-East"


def test_three_by_three_gives_a_full_compass_rose_with_a_centre():
    labels = [[section_label(r, c, 3) for c in range(3)] for r in range(3)]
    assert labels == [
        ["North-West", "North", "North-East"],
        ["West", "Centre", "East"],
        ["South-West", "South", "South-East"],
    ]


def test_zones_are_never_named_by_row_and_column():
    # "Zone R2C3" tells a farmer nothing about where to walk.
    for grid in (2, 3, 4, 5):
        for r in range(grid):
            for c in range(grid):
                label = section_label(r, c, grid)
                assert not label.startswith("Zone R"), f"{grid}x{grid} produced {label}"
                assert label.strip()


def test_corners_stay_in_the_corners_at_every_grid_size():
    # Evaluating cells at their centre keeps the bands symmetric; using the
    # leading edge made "West" two columns wide and "East" one.
    for grid in (3, 4, 5, 6):
        assert section_label(0, 0, grid).startswith("North-West")
        assert section_label(0, grid - 1, grid).startswith("North-East")
        assert section_label(grid - 1, 0, grid).startswith("South-West")
        assert section_label(grid - 1, grid - 1, grid).startswith("South-East")


def test_large_grids_number_within_a_sector():
    # A sector holding several cells must distinguish them, but still point
    # somewhere: "North-East 2", not "Zone R1C4".
    label = section_label(0, 0, 5)
    assert label.startswith("North-West")
    assert label[-1].isdigit()


def test_every_zone_in_a_grid_gets_a_unique_name():
    for grid in (2, 3, 4, 5, 6):
        labels = [section_label(r, c, grid) for r in range(grid) for c in range(grid)]
        assert len(set(labels)) == len(labels), f"duplicate names at {grid}x{grid}"


def test_numbering_follows_the_reading_order_of_the_zone_list():
    # North to south, west to east — so "North-West 2" is the one after
    # "North-West 1" in the list the farmer is looking at.
    assert section_label(0, 0, 5) == "North-West 1"
    assert section_label(0, 1, 5) == "North-West 2"
    assert section_label(1, 0, 5) == "North-West 3"


# --- Grid sizing --------------------------------------------------------------

def test_small_fields_stay_at_four_zones():
    # Quartering a 2 ha plot is already fine-grained guidance.
    assert suggest_grid_size(1.5) == 2
    assert suggest_grid_size(8) == 2


def test_large_fields_get_more_zones_so_each_stays_walkable():
    # A fixed 2x2 turns a 400 ha block into four 100 ha slabs, which is not
    # guidance — "the North-East is stressed" has to narrow something down.
    assert suggest_grid_size(25) > 2
    assert suggest_grid_size(60) > suggest_grid_size(10)


def test_zone_size_is_driven_toward_something_walkable():
    for area in (12, 30, 55):
        grid = suggest_grid_size(area)
        assert area / (grid * grid) <= WALKABLE_ZONE_HA * 1.01


def test_grid_is_capped_so_the_farmer_reads_places_not_a_heatmap():
    assert suggest_grid_size(400) <= 4
    assert suggest_grid_size(10_000) <= 4
    assert suggest_grid_size(400, max_grid=6) <= 6


def test_unknown_area_falls_back_to_four_zones():
    assert suggest_grid_size(None) == 2
    assert suggest_grid_size(0) == 2
    assert suggest_grid_size(-5) == 2
