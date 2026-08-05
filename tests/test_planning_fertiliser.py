"""
Fertiliser programme tests — services/planning/fertiliser.py.

Exercises the prose parsers against the real maize profile (the profiles store
human-written rates and timings, so the parsers must survive them) and the
soil-driven adjustments that carry real money: lime before phosphorus, and
split nitrogen on leaching soils.
"""

from datetime import date

import pytest

from crop_profiles.maize import MAIZE_PROFILE
from services.planning.fertiliser import (
    build_fertiliser_programme,
    parse_days_after_planting,
    parse_rate,
    parse_stage_code,
)


PLANTING = date(2026, 11, 15)


# --- Parsers -----------------------------------------------------------------
@pytest.mark.parametrize("text,low,high,unit", [
    ("200-300 kg/ha", 200.0, 300.0, "kg"),
    ("150-200 kg AN/ha (52-69 kg N)", 150.0, 200.0, "kg"),
    ("2 kg ZnSO4/ha in 200L water", 2.0, 2.0, "kg"),
    ("1-3 t/ha based on soil test", 1.0, 3.0, "t"),
])
def test_parse_rate_handles_real_profile_strings(text, low, high, unit):
    assert parse_rate(text) == (low, high, unit)


def test_parse_rate_survives_unparseable_text():
    assert parse_rate("As per soil test") == (None, None, None)
    assert parse_rate(None) == (None, None, None)
    assert parse_rate("") == (None, None, None)


def test_parse_days_takes_the_start_of_the_window():
    # Scheduling the opening of the window is deliberate: being early costs
    # far less than being late.
    assert parse_days_after_planting("V4-V6 (28-42 days after planting)") == 28


def test_parse_days_returns_none_when_absent():
    assert parse_days_after_planting("At planting, placed 5 cm beside seed") is None
    assert parse_days_after_planting(None) is None


def test_parse_stage_code_finds_growth_stages():
    assert parse_stage_code("V4-V6 (28-42 days after planting)") == "V4"
    assert parse_stage_code("V8-V10 (optional)") == "V8"
    assert parse_stage_code("At planting") is None


# --- Programme shape ---------------------------------------------------------
def test_maize_programme_has_basal_and_top_dress_in_date_order():
    p = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=2.4
    )
    keys = [s.key for s in p.steps]
    assert "basal" in keys
    assert "top_dress_1" in keys
    days = [s.days_after_planting for s in p.steps if s.days_after_planting is not None]
    assert days == sorted(days)


def test_basal_is_dated_to_the_planting_date():
    p = build_fertiliser_programme(MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0)
    basal = next(s for s in p.steps if s.key == "basal")
    assert basal.days_after_planting == 0
    assert basal.scheduled_date == PLANTING.isoformat()


def test_top_dress_gets_a_real_calendar_date():
    # "V4-V6" is not an instruction a farmer can act on; a date is.
    p = build_fertiliser_programme(MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0)
    td = next(s for s in p.steps if s.key == "top_dress_1")
    assert td.days_after_planting == 28
    assert td.scheduled_date == date(2026, 12, 13).isoformat()
    assert td.stage_code == "V4"


def test_second_top_dress_is_dated_from_a_stage_range():
    # Its timing is "V8-V10" with no explicit day range, and the profile's own
    # stage code is the range "V7-V10" — a substring match misses ("V8" is not
    # in "V7-V10") and leaves the step undated. On leaching soils this is the
    # application that matters most, so an undated step is a real failure.
    p = build_fertiliser_programme(MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0)
    td2 = next(s for s in p.steps if s.key == "top_dress_2")
    assert td2.days_after_planting == 42       # start of the V7-V10 stage
    assert td2.scheduled_date == date(2026, 12, 27).isoformat()


def test_every_non_conditional_step_gets_a_date():
    p = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0,
        soil_texture="sandy loam",
    )
    undated = [s.key for s in p.steps if s.scheduled_date is None]
    assert undated == [], f"steps left undated: {undated}"


@pytest.mark.parametrize("target,profile_code,expected", [
    ("V8", "V7-V10", True),     # inside a range — the case that was broken
    ("V7", "V7-V10", True),     # lower bound
    ("V10", "V7-V10", True),    # upper bound
    ("V6", "V7-V10", False),    # below
    ("V11", "V7-V10", False),   # above
    ("V3", "V1-V3", True),
    ("R3", "R2-R4", True),
    ("V3", "R2-R4", False),     # wrong letter
    ("VT", "VT", True),
    ("VT", "V7-V10", False),    # non-numeric codes match only exactly
])
def test_stage_range_matching(target, profile_code, expected):
    from services.planning.fertiliser import _stage_matches
    assert _stage_matches(target, profile_code) is expected


def test_amounts_are_scaled_to_the_field_area():
    p = build_fertiliser_programme(MAIZE_PROFILE, planting_date=PLANTING, area_hectares=2.4)
    basal = next(s for s in p.steps if s.key == "basal")
    assert basal.rate_low == 200.0
    assert basal.amount_low == pytest.approx(480.0)   # 200 kg/ha x 2.4 ha
    assert basal.amount_high == pytest.approx(720.0)  # 300 kg/ha x 2.4 ha


def test_missing_area_yields_rates_only_and_says_so():
    p = build_fertiliser_programme(MAIZE_PROFILE, planting_date=PLANTING)
    basal = next(s for s in p.steps if s.key == "basal")
    assert basal.amount_low is None
    assert any("area is unknown" in w for w in p.warnings)


def test_missing_planting_date_keeps_relative_timing_and_warns():
    p = build_fertiliser_programme(MAIZE_PROFILE, area_hectares=1.0)
    td = next(s for s in p.steps if s.key == "top_dress_1")
    assert td.days_after_planting == 28
    assert td.scheduled_date is None
    assert any("no planting date" in w.lower() for w in p.warnings)


# --- Lime / pH ---------------------------------------------------------------
def test_acid_soil_makes_lime_required_and_explains_the_p_lockup():
    # MAIZE_PROFILE.critical_ph_low is the threshold below which P is locked up.
    acid = float(MAIZE_PROFILE.critical_ph_low) - 0.5
    p = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, soil_ph=acid
    )
    lime = next(s for s in p.steps if s.key == "liming")
    assert lime.optional is False
    assert "locked up" in lime.why
    assert any("pH" in a for a in p.adjustments)


def test_lime_is_scheduled_well_before_planting():
    acid = float(MAIZE_PROFILE.critical_ph_low) - 0.5
    p = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, soil_ph=acid
    )
    lime = next(s for s in p.steps if s.key == "liming")
    # Lime needs months of lead time — surfacing it at planting is useless.
    assert lime.days_after_planting < 0
    assert lime.scheduled_date < PLANTING.isoformat()


def test_acid_soil_warns_that_basal_phosphorus_is_wasted():
    acid = float(MAIZE_PROFILE.critical_ph_low) - 0.5
    p = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, soil_ph=acid
    )
    assert any("locked" in w for w in p.warnings)


def test_healthy_ph_leaves_lime_optional_and_raises_no_warning():
    p = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, soil_ph=6.2
    )
    lime = next(s for s in p.steps if s.key == "liming")
    assert lime.optional is True
    assert not any("locked" in w for w in p.warnings)


# --- Nitrogen splitting on sandy soils ---------------------------------------
def test_sandy_soil_promotes_the_second_top_dress_to_recommended():
    sandy = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, soil_texture="sandy loam"
    )
    td2 = next(s for s in sandy.steps if s.key == "top_dress_2")
    assert td2.optional is False
    assert any("water table" in a for a in sandy.adjustments)


def test_clay_soil_leaves_the_second_top_dress_optional():
    clay = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, soil_texture="heavy clay"
    )
    td2 = next(s for s in clay.steps if s.key == "top_dress_2")
    assert td2.optional is True


def test_sandy_soil_explains_the_leaching_loss_on_the_first_top_dress():
    p = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, soil_texture="sand"
    )
    td1 = next(s for s in p.steps if s.key == "top_dress_1")
    assert "leaches" in td1.why
    # The original scientific basis from the profile must survive the prepend.
    assert "N demand peaks" in td1.why


def test_irrigation_and_high_yield_target_also_promote_the_second_top_dress():
    irrigated = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, irrigated=True
    )
    assert next(s for s in irrigated.steps if s.key == "top_dress_2").optional is False

    high_target = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0, target_yield_t_ha=10.0
    )
    assert next(s for s in high_target.steps if s.key == "top_dress_2").optional is False


# --- Foliar / robustness -----------------------------------------------------
def test_foliar_is_conditional_not_scheduled_work():
    p = build_fertiliser_programme(MAIZE_PROFILE, planting_date=PLANTING, area_hectares=1.0)
    foliar = next(s for s in p.steps if s.key == "foliar")
    assert foliar.optional is True
    assert "deficiency" in (foliar.conditional_on or "")


def test_profile_without_a_schedule_degrades_gracefully():
    class Bare:
        crop_name = "Mystery"
        fertilizer_schedule = None

    p = build_fertiliser_programme(Bare(), planting_date=PLANTING, area_hectares=1.0)
    assert p.steps == []
    assert any("No fertiliser schedule" in w for w in p.warnings)


def test_programme_serialises_for_the_api():
    d = build_fertiliser_programme(
        MAIZE_PROFILE, planting_date=PLANTING, area_hectares=2.4, soil_texture="sandy loam"
    ).to_dict()
    assert d["area_hectares"] == 2.4
    assert d["planting_date"] == PLANTING.isoformat()
    assert d["steps"]
    assert all("why" in s for s in d["steps"])
