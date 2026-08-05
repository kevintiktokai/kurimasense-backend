"""
Season-over-season history tests — services/seasons/history.py.

The core claim under test is that seasons become comparable only once they are
re-indexed to days after their own planting date. Everything else (peaks,
trends, plain-language deltas) is built on that, so the alignment tests carry
the most weight.
"""

import pytest

from services.seasons.history import (
    MIN_MEANINGFUL_NDVI,
    MIN_OBS_FOR_CONFIDENT_PEAK,
    align_observations,
    build_field_history,
    group_observations_by_season,
    summarise_season,
)


def obs(date_str, ndvi=None, evi=None):
    return {"log_date": date_str, "ndvi": ndvi, "evi": evi}


def season(sid, planted, **kw):
    return {
        "id": sid,
        "status": "closed",
        "crop_type": "Maize",
        "planting_date": planted,
        "season_label": kw.pop("label", None),
        **kw,
    }


# --- Alignment ---------------------------------------------------------------

def test_observations_are_reindexed_to_crop_age():
    points = align_observations("2026-11-15", [
        obs("2026-11-15", 0.20),
        obs("2026-12-15", 0.55),
        obs("2027-01-14", 0.78),
    ])
    assert [p.days_after_planting for p in points] == [0, 30, 60]


def test_two_seasons_planted_on_different_dates_align_on_the_same_axis():
    # The whole point: a crop planted 15 Nov and one planted 2 Dec are at
    # different stages on any calendar day, but day 30 is day 30 for both.
    a = align_observations("2026-11-15", [obs("2026-12-15", 0.55)])
    b = align_observations("2026-12-02", [obs("2027-01-01", 0.61)])
    assert a[0].days_after_planting == b[0].days_after_planting == 30


def test_observations_before_planting_are_dropped():
    # They belong to the previous crop; keeping them would draw a phantom
    # canopy at "day -20" that was never this season's.
    points = align_observations("2026-11-15", [
        obs("2026-10-20", 0.62),   # previous crop
        obs("2026-11-20", 0.24),
    ])
    assert len(points) == 1
    assert points[0].days_after_planting == 5


def test_points_come_back_oldest_first_regardless_of_input_order():
    points = align_observations("2026-11-15", [
        obs("2027-01-14", 0.78), obs("2026-11-25", 0.30), obs("2026-12-15", 0.55),
    ])
    assert [p.days_after_planting for p in points] == [10, 30, 60]


def test_no_planting_date_means_nothing_can_be_aligned():
    assert align_observations(None, [obs("2026-12-15", 0.55)]) == []


def test_malformed_dates_and_values_are_skipped_not_fatal():
    points = align_observations("2026-11-15", [
        obs("not-a-date", 0.5),
        {"ndvi": 0.5},                      # no date at all
        obs("2026-12-15", None),            # clouded observation
        obs("2026-12-25", "0.61"),          # numeric string from the driver
    ])
    assert [p.days_after_planting for p in points] == [30, 40]
    assert points[0].ndvi is None
    assert points[1].ndvi == pytest.approx(0.61)


# --- Season summary ----------------------------------------------------------

def test_peak_and_timing_are_reported_in_crop_age():
    h = summarise_season(season("s1", "2026-11-15"), [
        obs("2026-11-25", 0.30), obs("2026-12-15", 0.55),
        obs("2027-01-04", 0.82), obs("2027-01-24", 0.70),
        obs("2027-02-13", 0.45),
    ])
    assert h.peak_ndvi == 0.82
    assert h.days_to_peak == 50
    assert h.observation_count == 5


def test_sparse_seasons_are_shown_but_their_peak_is_not_trusted():
    # Cloud can hide the real peak; a thin season must not be compared as if
    # its best observation were its maximum.
    h = summarise_season(season("s1", "2026-11-15"), [
        obs("2026-12-15", 0.55), obs("2027-01-04", 0.62),
    ])
    assert h.peak_ndvi == 0.62
    assert h.peak_is_confident is False

    dense = summarise_season(season("s2", "2026-11-15"), [
        obs(f"2026-12-{d:02d}", 0.5 + d / 100) for d in range(1, 1 + MIN_OBS_FOR_CONFIDENT_PEAK)
    ])
    assert dense.peak_is_confident is True


def test_a_season_that_never_established_a_canopy_reports_no_peak():
    # Bare soil sits around 0.15-0.2 — calling that a "peak" would invent a crop.
    h = summarise_season(season("s1", "2026-11-15"), [
        obs("2026-12-15", 0.18), obs("2027-01-04", MIN_MEANINGFUL_NDVI - 0.01),
    ])
    assert h.peak_ndvi is None
    assert h.days_to_peak is None
    assert h.mean_ndvi is not None   # the mean is still a fact


def test_establishment_and_yield_carry_through_to_the_summary():
    h = summarise_season(
        season("s1", "2026-11-15", target_population_per_ha=44000,
               established_population_per_ha=41000, yield_tonnes_per_ha="5.4"),
        [obs("2026-12-15", 0.55)],
    )
    assert h.target_population_per_ha == 44000
    assert h.established_population_per_ha == 41000
    assert h.yield_tonnes_per_ha == pytest.approx(5.4)


def test_summary_serialises_for_the_api():
    d = summarise_season(season("s1", "2026-11-15", label="2026/27 Summer"),
                         [obs("2026-12-15", 0.55)]).to_dict()
    assert d["season_label"] == "2026/27 Summer"
    assert d["points"][0]["days_after_planting"] == 30


# --- Field history -----------------------------------------------------------

def _three_seasons():
    seasons = [
        season("s1", "2026-11-15", label="2026/27", yield_tonnes_per_ha=6.2),
        season("s2", "2025-11-24", label="2025/26", yield_tonnes_per_ha=5.0),
        season("s3", "2024-11-20", label="2024/25", yield_tonnes_per_ha=4.1),
    ]
    logs = {
        "s1": [obs("2027-01-04", 0.82), obs("2026-12-15", 0.55)],
        "s2": [obs("2026-01-20", 0.70), obs("2025-12-24", 0.50)],
        "s3": [obs("2025-01-18", 0.61), obs("2024-12-20", 0.45)],
    }
    return seasons, logs


def test_history_is_newest_season_first():
    seasons, logs = _three_seasons()
    h = build_field_history("f1", seasons, logs)
    assert [s.season_label for s in h.seasons] == ["2026/27", "2025/26", "2024/25"]


def test_seasons_without_a_planting_date_are_excluded():
    # No planting date means no crop age, so nothing can be aligned or compared.
    seasons = [season("s1", "2026-11-15"), season("s2", None)]
    h = build_field_history("f1", seasons, {"s1": [obs("2026-12-15", 0.55)]})
    assert [s.season_id for s in h.seasons] == ["s1"]


def test_yield_difference_is_stated_in_plain_language():
    seasons, logs = _three_seasons()
    h = build_field_history("f1", seasons, logs)
    joined = " ".join(h.comparisons)
    assert "1.2 t/ha more" in joined


def test_establishment_difference_is_called_out_when_both_measured():
    seasons = [
        season("s1", "2026-11-15", label="2026/27", established_population_per_ha=42000),
        season("s2", "2025-11-24", label="2025/26", established_population_per_ha=33000),
    ]
    h = build_field_history("f1", seasons, {})
    joined = " ".join(h.comparisons)
    assert "9,000 plants/ha more" in joined


def test_canopy_is_not_compared_when_a_seasons_peak_is_unreliable():
    # Two thin seasons: neither peak is confident, so no canopy claim is made.
    seasons = [
        season("s1", "2026-11-15", label="A"),
        season("s2", "2025-11-15", label="B"),
    ]
    logs = {"s1": [obs("2026-12-15", 0.80)], "s2": [obs("2025-12-15", 0.40)]}
    h = build_field_history("f1", seasons, logs)
    assert not any("canopy" in c for c in h.comparisons)


def test_trend_uses_yield_when_available():
    seasons, logs = _three_seasons()          # 4.1 -> 5.0 -> 6.2
    assert build_field_history("f1", seasons, logs).trend == "improving"


def test_declining_yields_are_reported_as_declining():
    seasons = [
        season("s1", "2026-11-15", yield_tonnes_per_ha=3.2),
        season("s2", "2025-11-15", yield_tonnes_per_ha=4.4),
        season("s3", "2024-11-15", yield_tonnes_per_ha=5.5),
    ]
    assert build_field_history("f1", seasons, {}).trend == "declining"


def test_small_yield_movements_read_as_stable():
    seasons = [
        season("s1", "2026-11-15", yield_tonnes_per_ha=5.1),
        season("s2", "2025-11-15", yield_tonnes_per_ha=5.0),
    ]
    assert build_field_history("f1", seasons, {}).trend == "stable"


def test_trend_falls_back_to_canopy_when_no_yields_recorded():
    seasons = [
        season("s1", "2026-11-15"), season("s2", "2025-11-15"),
    ]
    logs = {
        "s1": [obs(f"2026-12-{d:02d}", 0.80) for d in range(1, 8)],
        "s2": [obs(f"2025-12-{d:02d}", 0.55) for d in range(1, 8)],
    }
    assert build_field_history("f1", seasons, logs).trend == "improving"


def test_a_single_season_has_no_trend_and_no_comparison():
    h = build_field_history("f1", [season("s1", "2026-11-15")], {})
    assert h.trend == "unknown"
    assert h.comparisons == []


def test_observations_are_attributed_to_the_season_running_at_the_time():
    seasons = [
        season("s1", "2026-11-15"),
        season("s2", "2025-11-20"),
    ]
    grouped = group_observations_by_season(seasons, [
        obs("2026-12-15", 0.55),   # during s1
        obs("2026-01-10", 0.60),   # during s2
        obs("2025-11-25", 0.30),   # during s2, just after planting
        obs("2024-06-01", 0.40),   # before any recorded season
    ])
    assert len(grouped["s1"]) == 1
    assert len(grouped["s2"]) == 2
    # The pre-history observation belongs to a season we have no record of.
    assert sum(len(v) for v in grouped.values()) == 3


def test_an_observation_on_planting_day_belongs_to_the_new_season():
    seasons = [season("s1", "2026-11-15"), season("s2", "2025-11-20")]
    grouped = group_observations_by_season(seasons, [obs("2026-11-15", 0.2)])
    assert len(grouped["s1"]) == 1
    assert grouped["s2"] == []


def test_attribution_ignores_stored_season_id_and_uses_dates():
    # Rows predating the backfill carry no season_id; deriving from dates keeps
    # history correct without depending on it having run.
    seasons = [season("s1", "2026-11-15")]
    grouped = group_observations_by_season(seasons, [
        {"log_date": "2026-12-15", "ndvi": 0.55, "season_id": None},
    ])
    assert len(grouped["s1"]) == 1


def test_seasons_without_planting_dates_get_no_observations():
    grouped = group_observations_by_season(
        [season("s1", None)], [obs("2026-12-15", 0.55)]
    )
    assert grouped == {}


def test_empty_field_history_is_safe():
    h = build_field_history("f1", [], {})
    assert h.seasons == []
    assert h.trend == "unknown"
    assert h.to_dict()["field_id"] == "f1"
