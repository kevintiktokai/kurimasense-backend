"""
Season lifecycle + rotation analysis tests — services/seasons/lifecycle.py.

The rotation half is the part that unlocks residue-inoculum disease risk, so it
is tested against the shapes the crop profiles actually reason about
(consecutive maize, family-level breaks, minimum tillage).
"""

import pytest

from services.seasons.lifecycle import (
    STATUS_ABANDONED,
    STATUS_ACTIVE,
    STATUS_CLOSED,
    STATUS_HARVESTED,
    STATUS_PLANNED,
    InvalidTransition,
    assert_transition,
    can_transition,
    crop_family,
    derive_season_label,
    is_break_crop,
    is_live,
    summarise_rotation,
)

from datetime import date


# --- Lifecycle ---------------------------------------------------------------
def test_happy_path_transitions_are_allowed():
    assert can_transition(STATUS_PLANNED, STATUS_ACTIVE)
    assert can_transition(STATUS_ACTIVE, STATUS_HARVESTED)
    assert can_transition(STATUS_HARVESTED, STATUS_CLOSED)


def test_a_season_can_be_abandoned_until_the_crop_is_off():
    assert can_transition(STATUS_PLANNED, STATUS_ABANDONED)
    assert can_transition(STATUS_ACTIVE, STATUS_ABANDONED)
    assert not can_transition(STATUS_HARVESTED, STATUS_ABANDONED)


def test_closed_seasons_are_terminal():
    # Rewriting a finished season would silently corrupt every rotation and
    # calibration conclusion drawn from it.
    for target in (STATUS_ACTIVE, STATUS_PLANNED, STATUS_HARVESTED, STATUS_ABANDONED):
        assert not can_transition(STATUS_CLOSED, target)


def test_skipping_a_step_is_rejected_with_a_useful_message():
    with pytest.raises(InvalidTransition) as exc:
        assert_transition(STATUS_PLANNED, STATUS_CLOSED)
    assert "cannot become" in str(exc.value)
    assert STATUS_ACTIVE in str(exc.value)


def test_unknown_statuses_are_rejected():
    with pytest.raises(InvalidTransition):
        assert_transition("banana", STATUS_ACTIVE)
    with pytest.raises(InvalidTransition):
        assert_transition(STATUS_PLANNED, "banana")


def test_only_active_seasons_mirror_onto_the_field():
    assert is_live(STATUS_ACTIVE)
    assert not is_live(STATUS_PLANNED)
    assert not is_live(STATUS_CLOSED)


# --- Season labels -----------------------------------------------------------
def test_summer_season_label_straddles_the_new_year():
    # A crop planted in Nov 2026 is harvested in 2027; farmers call it 2026/27.
    assert derive_season_label(date(2026, 11, 15)) == "2026/27 Summer"
    assert derive_season_label(date(2027, 1, 10)) == "2026/27 Summer"


def test_winter_season_sits_inside_one_year():
    assert derive_season_label(date(2026, 5, 20)) == "2026 Winter"


def test_no_planting_date_gives_no_label():
    assert derive_season_label(None) is None


# --- Crop families -----------------------------------------------------------
def test_families_group_crops_that_share_pathogens():
    assert crop_family("Maize") == crop_family("Sorghum") == "cereal_grass"
    assert crop_family("Soybean") == crop_family("Groundnuts") == "legume"
    assert crop_family("Tobacco") == crop_family("Tomato") == "solanaceae"


def test_unknown_crop_has_no_family():
    assert crop_family("dragonfruit") is None
    assert crop_family(None) is None


def test_break_crop_is_judged_on_family_not_name():
    # Maize -> sorghum looks like a rotation but shares grass pathogens.
    assert is_break_crop("sorghum", "maize") is False
    assert is_break_crop("soybean", "maize") is True
    assert is_break_crop("maize", "maize") is False


# --- Rotation analysis -------------------------------------------------------
def _season(crop, year, status=STATUS_CLOSED, **kw):
    return {
        "id": f"{crop}-{year}",
        "crop_type": crop,
        "status": status,
        "planting_date": f"{year}-11-15",
        **kw,
    }


def test_empty_history_is_unknown_and_says_what_would_fix_it():
    s = summarise_rotation([])
    assert s.rotation_risk == "unknown"
    assert s.seasons_recorded == 0
    assert any("Adding past seasons" in r for r in s.risk_reasons)


def test_planned_seasons_are_ignored_because_they_left_no_residue():
    s = summarise_rotation([
        _season("maize", 2026, status=STATUS_PLANNED),
        _season("soybean", 2025),
    ])
    assert s.seasons_recorded == 1
    assert s.current_crop == "soybean"


def test_history_is_ordered_newest_first():
    s = summarise_rotation([
        _season("maize", 2023),
        _season("soybean", 2025),
        _season("maize", 2024),
    ])
    assert [h["crop_type"] for h in s.history] == ["soybean", "maize", "maize"]
    assert s.current_crop == "soybean"


def test_three_consecutive_maize_crops_is_high_risk_and_names_the_diseases():
    s = summarise_rotation(
        [_season("maize", y) for y in (2025, 2024, 2023)],
        candidate_crop="maize",
    )
    assert s.rotation_risk == "high"
    assert s.consecutive_same_crop == 3
    joined = " ".join(s.risk_reasons)
    assert "Grey Leaf Spot" in joined
    assert "Diplodia" in joined


def test_a_third_consecutive_crop_is_moderate_risk():
    s = summarise_rotation(
        [_season("maize", y) for y in (2025, 2024)],
        candidate_crop="maize",
    )
    assert s.rotation_risk == "moderate"
    assert "break crop" in " ".join(s.risk_reasons).lower()


def test_rotating_to_a_non_host_is_low_risk():
    s = summarise_rotation(
        [_season("maize", y) for y in (2025, 2024, 2023)],
        candidate_crop="soybean",
    )
    assert s.rotation_risk == "low"
    assert s.consecutive_same_crop == 0


def test_same_family_rotation_is_a_weaker_break_than_it_looks():
    # maize -> sorghum -> maize is three grass crops in a row.
    s = summarise_rotation(
        [_season("maize", 2025), _season("sorghum", 2024), _season("maize", 2023)],
        candidate_crop="wheat",
    )
    assert s.consecutive_same_family == 3
    assert s.rotation_risk == "moderate"
    assert "family" in " ".join(s.risk_reasons)


def test_minimum_tillage_escalates_moderate_risk_to_high():
    ploughed = summarise_rotation(
        [_season("maize", y) for y in (2025, 2024)],
        candidate_crop="maize", tillage_practice="conventional",
    )
    min_till = summarise_rotation(
        [_season("maize", y) for y in (2025, 2024)],
        candidate_crop="maize", tillage_practice="minimum",
    )
    assert ploughed.rotation_risk == "moderate"
    assert min_till.rotation_risk == "high"


def test_minimum_tillage_on_high_risk_explains_the_ploughing_benefit():
    s = summarise_rotation(
        [_season("maize", y) for y in (2025, 2024, 2023)],
        candidate_crop="maize", tillage_practice="no_till",
    )
    assert s.rotation_risk == "high"
    assert "60-80%" in " ".join(s.risk_reasons)


def test_years_since_tracks_each_crops_last_appearance():
    s = summarise_rotation([
        _season("maize", 2025), _season("soybean", 2024), _season("maize", 2023),
    ])
    assert s.years_since["maize"] == 0
    assert s.years_since["soybean"] == 1


def test_last_nitrogen_fixing_crop_is_surfaced():
    s = summarise_rotation([
        _season("maize", 2025), _season("groundnuts", 2024),
    ])
    assert s.last_n_fixing_crop == "groundnuts"


def test_no_legume_in_history_reports_none():
    s = summarise_rotation([_season("maize", y) for y in (2025, 2024)])
    assert s.last_n_fixing_crop is None


def test_summary_serialises_for_the_api():
    d = summarise_rotation(
        [_season("maize", y) for y in (2025, 2024, 2023)], candidate_crop="maize"
    ).to_dict()
    assert d["rotation_risk"] == "high"
    assert d["seasons_recorded"] == 3
    assert len(d["history"]) == 3
    assert d["history"][0]["family"] == "cereal_grass"
