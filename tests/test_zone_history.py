"""
Zone history tests — services/zones/history.py.

The grid-comparability rule carries the most weight. Comparing zone 3 of a 2x2
with zone 3 of a 4x4 silently compares different pieces of ground and reports a
trend that does not exist — and a farmer might dig a drain because of it.
"""

import pytest

from services.zones.history import (
    BEHIND_THRESHOLD,
    MIN_SEASONS_FOR_PATTERN,
    build_zone_history,
    comparable_batches,
)


def batch(label, grid, zone_ndvis, season_id=None):
    """One season's zone analysis. `zone_ndvis` is index -> ndvi."""
    return {
        "season_id": season_id or f"s-{label}",
        "season_label": label,
        "grid_size": grid,
        "zones": [
            {"index": i, "label": f"Zone {i + 1}", "ndvi": v}
            for i, v in enumerate(zone_ndvis)
        ],
    }


def track(result, index):
    return next((z for z in result["zones"] if z["index"] == index), None)


# --- Grid comparability ------------------------------------------------------

def test_only_batches_sharing_a_grid_are_compared():
    comparable, skipped = comparable_batches([
        batch("2024/25", 2, [0.7, 0.7, 0.7, 0.4]),
        batch("2025/26", 2, [0.7, 0.7, 0.7, 0.4]),
        batch("2026/27", 4, [0.7] * 16),
    ])
    assert len(comparable) == 2
    assert len(skipped) == 1


def test_the_grid_with_the_most_seasons_wins():
    comparable, _ = comparable_batches([
        batch("a", 3, [0.7] * 9),
        batch("b", 2, [0.7] * 4),
        batch("c", 2, [0.7] * 4),
    ])
    assert all(b["grid_size"] == 2 for b in comparable)


def test_skipped_seasons_are_reported_not_silently_dropped():
    result = build_zone_history([
        batch("2024/25", 2, [0.7, 0.7, 0.7, 0.4]),
        batch("2025/26", 2, [0.7, 0.7, 0.7, 0.4]),
        batch("2026/27", 4, [0.7] * 16),
    ])
    assert any("different zone grid" in n for n in result["notes"])


def test_mismatched_grids_never_get_compared_by_index():
    # The dangerous silent bug: zone 3 of a 2x2 is the south-west quarter,
    # zone 3 of a 4x4 is somewhere else entirely.
    result = build_zone_history([
        batch("a", 2, [0.7, 0.7, 0.7, 0.3]),
        batch("b", 4, [0.7] * 16),
    ])
    # Only one comparable season remains, so no pattern is claimed.
    assert result["seasons_compared"] == 1
    assert result["zones"] == []


def test_batches_without_a_usable_grid_are_skipped():
    comparable, skipped = comparable_batches([{"season_label": "x", "zones": []}])
    assert comparable == []
    assert len(skipped) == 1


# --- Pattern detection -------------------------------------------------------

def test_a_zone_behind_every_season_is_called_persistent():
    result = build_zone_history([
        batch("2023/24", 2, [0.72, 0.72, 0.72, 0.40]),
        batch("2024/25", 2, [0.70, 0.71, 0.70, 0.38]),
        batch("2025/26", 2, [0.68, 0.69, 0.70, 0.35]),
    ])
    worst = track(result, 3)
    assert worst["verdict"] == "persistent"
    assert worst["seasons_behind"] == 3
    assert "soil test" in worst["action"]


def test_one_bad_season_is_not_called_a_soil_problem():
    # A single weak year is weather or management, not the ground — and
    # telling a farmer to dig it up would waste their money.
    result = build_zone_history([
        batch("2023/24", 2, [0.70, 0.71, 0.70, 0.70]),
        batch("2024/25", 2, [0.72, 0.72, 0.72, 0.38]),
        batch("2025/26", 2, [0.70, 0.70, 0.71, 0.70]),
    ])
    zone = track(result, 3)
    assert zone["verdict"] == "occasional"
    assert "not worth digging up" in zone["action"]


def test_a_zone_that_keeps_up_is_reported_as_consistent():
    result = build_zone_history([
        batch("2023/24", 2, [0.70, 0.70, 0.70, 0.70]),
        batch("2024/25", 2, [0.68, 0.69, 0.68, 0.69]),
    ])
    assert track(result, 0)["verdict"] == "consistent"
    assert track(result, 0)["action"] == ""


def test_a_single_season_cannot_establish_a_pattern():
    result = build_zone_history([batch("2025/26", 2, [0.72, 0.72, 0.72, 0.30])])
    assert result["zones"] == []
    assert any("at least two seasons" in n.lower() for n in result["notes"])


def test_no_history_is_handled():
    result = build_zone_history([])
    assert result["seasons_compared"] == 0
    assert result["zones"] == []


# --- Within-season comparison ------------------------------------------------

def test_each_season_is_judged_against_its_own_field_mean():
    # A dry year lowers every zone. What matters is whether the same corner
    # keeps ending up at the bottom of its own field.
    result = build_zone_history([
        batch("good year", 2, [0.80, 0.80, 0.80, 0.48]),
        batch("dry year", 2, [0.40, 0.40, 0.40, 0.08]),
    ])
    worst = track(result, 3)
    assert worst["verdict"] == "persistent"
    # The good year's healthy zones are not flagged despite the dry year being
    # far lower in absolute terms.
    assert track(result, 0)["verdict"] == "consistent"


def test_the_behind_threshold_matches_the_diagnosis_view():
    # One screen must not call a zone weak while the other calls it fine.
    from services.zones.diagnosis import MATERIAL_NDVI_GAP
    assert BEHIND_THRESHOLD == MATERIAL_NDVI_GAP


def test_unanalysed_zones_do_not_count_toward_a_verdict():
    result = build_zone_history([
        batch("a", 2, [0.70, 0.70, 0.70, None]),
        batch("b", 2, [0.70, 0.70, 0.70, None]),
    ])
    zone = track(result, 3)
    assert zone["seasons_compared"] == 0
    assert zone["verdict"] == "insufficient"


# --- Output ------------------------------------------------------------------

def test_worst_zones_come_first():
    result = build_zone_history([
        batch("a", 2, [0.72, 0.72, 0.55, 0.35]),
        batch("b", 2, [0.72, 0.72, 0.56, 0.34]),
    ])
    assert result["zones"][0]["index"] == 3


def test_points_run_oldest_to_newest():
    result = build_zone_history([
        batch("2025/26", 2, [0.7, 0.7, 0.7, 0.4]),
        batch("2023/24", 2, [0.7, 0.7, 0.7, 0.4]),
        batch("2024/25", 2, [0.7, 0.7, 0.7, 0.4]),
    ])
    labels = [p["season_label"] for p in track(result, 3)["points"]]
    assert labels == ["2023/24", "2024/25", "2025/26"]


def test_persistent_zones_are_called_out_at_the_field_level():
    result = build_zone_history([
        batch("a", 2, [0.72, 0.72, 0.72, 0.35]),
        batch("b", 2, [0.72, 0.72, 0.72, 0.34]),
    ])
    assert any("pay back every year" in n for n in result["notes"])


def test_history_serialises_for_the_api():
    result = build_zone_history([
        batch("a", 2, [0.72, 0.72, 0.72, 0.35]),
        batch("b", 2, [0.72, 0.72, 0.72, 0.34]),
    ])
    zone = result["zones"][0]
    assert set(zone) >= {"index", "label", "seasons_compared", "seasons_behind",
                         "verdict", "summary", "action", "points"}
    assert all("field_mean" in p for p in zone["points"])
