"""
Execution-quality tests — services/planning/execution.py.

The point under test: three identical task ticks can be three completely
different seasons. Urea banded, urea broadcast onto dry soil, and urea followed
by a downpour on sand all read the same in farm_tasks and differ enormously in
what the crop actually receives.
"""

import pytest

from services.planning.execution import (
    LEACHING_LOSS,
    RAIN_TOO_LITTLE_MM,
    RAIN_TOO_MUCH_MM,
    VOLATILISATION_LOSS,
    ExecutionAssessment,
    assess_application,
    is_leaching_soil,
    is_nitrogen,
    is_urea,
    summarise_season_execution,
)


# --- Classification ----------------------------------------------------------

@pytest.mark.parametrize("value", ["Urea", "AN", "Ammonium Nitrate", "CAN", "urea top dress"])
def test_nitrogen_products_are_recognised(value):
    assert is_nitrogen(value) is True


def test_non_nitrogen_inputs_are_not_assessed_as_nitrogen():
    assert is_nitrogen("Glyphosate") is False
    assert is_nitrogen("Lime") is False
    assert is_nitrogen(None) is False


def test_bare_an_matches_as_a_word_not_a_substring():
    # "manure" and "planting" both contain the letters.
    assert is_nitrogen("manure") is False
    assert is_nitrogen("an") is True


def test_urea_is_distinguished_from_other_nitrogen():
    # Only urea volatilises off the surface; AN does not behave the same way.
    assert is_urea("Urea") is True
    assert is_urea("Ammonium Nitrate") is False


def test_leaching_soils_are_recognised():
    assert is_leaching_soil("sandy loam") is True
    assert is_leaching_soil("sand") is True
    assert is_leaching_soil("heavy clay") is False
    assert is_leaching_soil(None) is False


# --- Not enough recorded -----------------------------------------------------

def test_an_unrecorded_application_is_not_guessed_at():
    # Putting a verdict on a farmer's work that the data cannot support is
    # worse than saying nothing.
    a = assess_application(input_type="Urea")
    assert a.quality == "unknown"
    assert a.effective_fraction == 1.0
    assert any("Logging how you applied it" in n for n in a.next_time)


def test_non_nitrogen_applications_are_skipped():
    a = assess_application(input_type="Glyphosate", method="broadcast")
    assert a.quality == "unknown"
    assert "only assessed for nitrogen" in a.summary


# --- Volatilisation ----------------------------------------------------------

def test_surface_urea_on_dry_soil_is_flagged_as_lost_to_the_air():
    a = assess_application(
        input_type="Urea", method="broadcast", rain_mm_48h=1.0,
    )
    assert a.quality != "good"
    assert a.effective_fraction == pytest.approx(1 - VOLATILISATION_LOSS)
    assert any("to the air" in r for r in a.at_risk)
    assert any("Band it" in n for n in a.next_time)


def test_incorporated_urea_on_dry_soil_is_not_penalised():
    # Working it in is what prevents the loss, regardless of rain.
    a = assess_application(
        input_type="Urea", method="incorporated", rain_mm_48h=1.0,
    )
    assert a.effective_fraction == 1.0
    assert any("into the soil" in w for w in a.went_well)


def test_banded_placement_counts_as_going_into_the_soil():
    a = assess_application(input_type="Urea", method="banded", rain_mm_48h=0.0)
    assert a.quality == "good"


def test_the_incorporated_flag_rescues_a_broadcast_application():
    a = assess_application(
        input_type="Urea", method="broadcast", incorporated=True, rain_mm_48h=0.0,
    )
    assert a.effective_fraction == 1.0


def test_non_urea_nitrogen_broadcast_dry_is_not_charged_volatilisation():
    # AN does not volatilise the way urea does.
    a = assess_application(
        input_type="Ammonium Nitrate", method="broadcast", rain_mm_48h=1.0,
    )
    assert a.effective_fraction == 1.0


def test_surface_urea_with_no_rainfall_record_is_flagged_without_a_penalty():
    a = assess_application(input_type="Urea", method="broadcast")
    assert a.effective_fraction == 1.0
    assert any("cannot tell" in r for r in a.at_risk)


# --- Leaching ----------------------------------------------------------------

def test_heavy_rain_on_sand_is_charged_as_leaching():
    a = assess_application(
        input_type="AN", method="banded",
        rain_mm_48h=RAIN_TOO_MUCH_MM + 20, soil_texture="sandy loam",
    )
    assert a.effective_fraction == pytest.approx(1 - LEACHING_LOSS)
    assert any("past the roots" in r for r in a.at_risk)
    assert any("split the nitrogen" in n for n in a.next_time)


def test_the_same_rain_on_clay_is_not_charged():
    a = assess_application(
        input_type="AN", method="banded",
        rain_mm_48h=RAIN_TOO_MUCH_MM + 20, soil_texture="heavy clay",
    )
    assert a.effective_fraction == 1.0


def test_moderate_rain_is_reported_as_ideal():
    a = assess_application(
        input_type="AN", method="broadcast", rain_mm_48h=15.0, soil_texture="sandy loam",
    )
    assert a.quality == "good"
    assert any("into the root zone" in w for w in a.went_well)


def test_the_worst_case_compounds_both_losses():
    # Surface urea, dry at first then a downpour on sand.
    a = assess_application(
        input_type="Urea", method="broadcast",
        rain_mm_48h=1.0, soil_texture="sand",
    )
    # Volatilisation applies; the rain was too little to also leach.
    assert a.effective_fraction < 1.0
    assert a.quality in ("reduced", "poor")


def test_quality_bands_follow_the_effective_fraction():
    good = assess_application(input_type="AN", method="banded", rain_mm_48h=15.0)
    reduced = assess_application(input_type="Urea", method="broadcast", rain_mm_48h=1.0)
    assert good.quality == "good"
    assert reduced.quality in ("reduced", "poor")
    assert good.effective_fraction > reduced.effective_fraction


# --- Tone --------------------------------------------------------------------

def test_every_shortfall_comes_with_something_to_do_next_time():
    # A farmer who feels marked stops logging, and then there is no data at all.
    for a in [
        assess_application(input_type="Urea", method="broadcast", rain_mm_48h=1.0),
        assess_application(input_type="AN", method="banded",
                           rain_mm_48h=80.0, soil_texture="sand"),
    ]:
        assert a.at_risk
        assert a.next_time, f"{a.quality} assessment gave no next step"


# --- Season roll-up ----------------------------------------------------------

def test_season_summary_averages_only_assessable_applications():
    # Averaging an unknown in as 1.0 would quietly reward recording nothing.
    assessments = [
        assess_application(input_type="AN", method="banded", rain_mm_48h=15.0),
        assess_application(input_type="Urea", method="broadcast", rain_mm_48h=1.0),
        assess_application(input_type="Urea"),   # unknown
    ]
    out = summarise_season_execution(assessments)
    assert out["applications_assessed"] == 2


def test_a_season_with_nothing_recorded_says_what_would_fix_it():
    out = summarise_season_execution([assess_application(input_type="Urea")])
    assert out["applications_assessed"] == 0
    assert out["average_effective_fraction"] is None
    assert "Logging how each one went on" in out["summary"]


def test_a_well_executed_season_is_told_so():
    out = summarise_season_execution([
        assess_application(input_type="AN", method="banded", rain_mm_48h=15.0),
    ])
    assert out["average_effective_fraction"] == 1.0
    assert "went on well" in out["summary"]


def test_a_poorly_executed_season_quantifies_the_waste_in_money_terms():
    out = summarise_season_execution([
        assess_application(input_type="Urea", method="broadcast", rain_mm_48h=1.0),
    ])
    assert "fertiliser you paid for" in out["summary"]


def test_assessment_serialises_for_the_api():
    d = assess_application(
        input_type="Urea", method="broadcast", rain_mm_48h=1.0
    ).to_dict()
    assert set(d) >= {"quality", "effective_fraction", "went_well", "at_risk",
                      "next_time", "summary"}
