"""
Flue-curing: the barn schedule, barn sizing, and the crops it must not answer for.

A tobacco season is won or lost in the barn. A grower can execute a flawless
crop and destroy it in three days of bad curing, and until this module existed
every screen and the chat went quiet at exactly that point.

The tests that matter most here are the negative ones. A chat asked "how do I
cure this" will answer, confidently, whatever it has — so the module has to
decline for burley (air-cured), for maize, and for anything it does not know,
rather than reaching for the nearest schedule it holds.
"""

import math

import pytest

from services.planning.briefing import curing_briefing, planning_briefing
from services.planning.curing import (
    BARN_TYPES,
    CONDITIONING_MOISTURE_PCT,
    CURING_STAGES,
    MAX_BARNS,
    OVERSIZE_FACTOR,
    barn_options_for_area,
    build_curing_plan,
    fuel_required_kg,
    is_flue_cured,
    stage_by_key,
    total_cure_days,
)


# ---------------------------------------------------------------------------
# What the module will and will not speak about
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "crop",
    ["Tobacco", "tobacco", "flue-cured tobacco", "Virginia", "TOBACCO_FLUE_CURED"],
)
def test_flue_cured_tobacco_is_recognised_however_it_is_written(crop):
    assert is_flue_cured(crop) is True


#: The names that actually discriminate. A crop is stored however the farmer
#: typed it, and every one of these leads with "tobacco" — so the obvious test,
#: ``crop.lower().startswith("tobacco")``, says yes to all of them.
BURLEY_AS_A_FARMER_WOULD_TYPE_IT = [
    "Tobacco (Burley)",
    "tobacco_burley",
    "Tobacco - Burley",
    "Tobacco, air-cured",
    "Tobacco dark fire-cured",
]


@pytest.mark.parametrize(
    "crop",
    BURLEY_AS_A_FARMER_WOULD_TYPE_IT
    + ["Burley tobacco", "burley", "Oriental tobacco", "air-cured tobacco"],
)
def test_air_cured_tobacco_is_refused(crop):
    # The bug this list exists for. `crop.lower().startswith("tobacco")` reads
    # as obviously correct, passes review, and hands a burley grower a ramp to
    # 70 °C that destroys the crop. Burley is air-cured; it never sees a flue.
    assert is_flue_cured(crop) is False, f"{crop!r} is not flue-cured"
    assert build_curing_plan(crop) is None
    assert curing_briefing(crop) is None


def test_the_guard_can_see_the_bug_it_was_written_for():
    # Without this, the burley test above is reassuring rather than useful. The
    # first draft of it used "Burley tobacco" and "burley" — neither of which
    # starts with "tobacco", so both passed against the broken implementation
    # and the test proved nothing.
    def the_obvious_wrong_version(crop: str) -> bool:
        return crop.strip().lower().startswith("tobacco")

    assert all(
        the_obvious_wrong_version(c) for c in BURLEY_AS_A_FARMER_WOULD_TYPE_IT
    ), "these fixtures no longer distinguish the correct implementation from the broken one"


@pytest.mark.parametrize("crop", ["Maize", "Soyabean", "Groundnut", "", None])
def test_a_crop_that_never_sees_a_barn_gets_nothing(crop):
    assert is_flue_cured(crop) is False
    assert build_curing_plan(crop) is None
    assert curing_briefing(crop) is None


# ---------------------------------------------------------------------------
# The schedule itself
# ---------------------------------------------------------------------------
def test_the_stages_are_in_the_order_the_barn_runs_them():
    keys = [s.key for s in CURING_STAGES]
    assert keys == ["colouring", "lamina_drying", "midrib_drying"]


def test_temperature_climbs_monotonically_through_the_cure():
    # The shape of the ramp is the agronomy. A schedule that steps backwards
    # would still render as a tidy table, which is why this is asserted rather
    # than eyeballed.
    lows = [s.temperature_c[0] for s in CURING_STAGES]
    assert lows == sorted(lows)
    for stage in CURING_STAGES:
        low, high = stage.temperature_c
        assert low < high, f"{stage.key} has an inverted temperature range"


def test_every_stage_range_is_low_then_high():
    for stage in CURING_STAGES:
        low, high = stage.duration_days
        assert 0 < low <= high, f"{stage.key} has a nonsensical duration"


def test_colouring_is_the_only_stage_that_names_a_humidity_target():
    # Holding ~85% through colouring is the counter-intuitive instruction in the
    # whole cure — it is why the leaf does not simply dry green — and the source
    # gives a figure only for that stage. Inventing one for the others would be
    # inventing agronomy.
    with_humidity = [s.key for s in CURING_STAGES if s.relative_humidity_pct is not None]
    assert with_humidity == ["colouring"]
    assert stage_by_key("colouring").relative_humidity_pct == 85.0


def test_the_whole_cure_lands_where_the_source_says_it_does():
    low, high = total_cure_days()
    assert (low, high) == (7.0, 10.0)


def test_conditioning_adds_moisture_back_rather_than_taking_it_out():
    low, high = CONDITIONING_MOISTURE_PCT
    assert 0 < low < high


def test_stage_by_key_declines_on_an_unknown_stage():
    assert stage_by_key("smoking") is None


# ---------------------------------------------------------------------------
# Barn sizing
# ---------------------------------------------------------------------------
def test_a_smallholder_is_offered_barns_a_smallholder_could_build():
    options = barn_options_for_area(0.5)
    assert options, "half a hectare of tobacco has to be curable somehow"
    keys = [o.barn.key for o in options]
    assert "plastic" in keys
    # The point of OVERSIZE_FACTOR: an estate-scale tunnel system is not an
    # option for half a hectare, however efficient its fuel figure is.
    assert "tunnel" not in keys


def test_a_mid_sized_grower_is_told_to_build_several_barns_not_to_buy_a_bigger_one():
    # The bug this replaced: an earlier draft returned only barns whose single
    # unit exceeded the area, so 5 ha matched nothing but the 120 ha continuous
    # tunnel system. What a 5 ha grower actually does is build four barns.
    options = barn_options_for_area(5.0)
    assert options
    assert any(o.count > 1 for o in options)
    assert all(o.covers_hectares >= 5.0 for o in options)
    assert "tunnel" not in [o.barn.key for o in options]


def test_barn_counts_cover_the_area_and_never_fall_short():
    for hectares in (0.3, 0.6, 1.0, 2.5, 4.0, 8.0):
        for option in barn_options_for_area(hectares):
            assert option.count == math.ceil(hectares / option.barn.hectares[0])
            assert option.covers_hectares >= hectares


def test_sizing_uses_the_typical_rating_not_the_top_of_tolerance():
    # A barn run at its stated maximum becomes the bottleneck at peak reaping,
    # and leaf that waits does not wait in good condition. The rocket barn is
    # published as 0.7 ± 0.2 ha; 0.85 ha must need two, not one.
    rocket = next(b for b in BARN_TYPES if b.key == "rocket")
    assert rocket.hectares == (0.7, 0.2)
    option = next(o for o in barn_options_for_area(0.85) if o.barn.key == "rocket")
    assert option.count == 2


def test_an_area_needing_an_absurd_number_of_barns_is_dropped_not_reported():
    # 30 ha would be 50 plastic barns. That is not advice, and printing the
    # number would imply someone had thought about it.
    options = barn_options_for_area(30.0)
    assert all(o.count <= MAX_BARNS for o in options)
    assert "plastic" not in [o.barn.key for o in options]


def test_no_area_yields_no_barn_advice_rather_than_a_default():
    assert barn_options_for_area(None) == []
    assert barn_options_for_area(0) == []
    assert barn_options_for_area(-3) == []
    plan = build_curing_plan("Tobacco")
    assert plan is not None
    assert plan.barn_options == ()


def test_the_oversize_rule_is_the_one_that_drops_the_tunnel():
    # Guard on the constant, so tuning it stays a deliberate act.
    tunnel = next(b for b in BARN_TYPES if b.key == "tunnel")
    assert tunnel.hectares[0] > 1.0 * OVERSIZE_FACTOR


# ---------------------------------------------------------------------------
# Fuel — the number a grower actually budgets against
# ---------------------------------------------------------------------------
def test_fuel_is_quoted_only_for_barns_with_a_published_figure():
    # The conventional up-draught has no efficiency figure in the source.
    # Borrowing the down-draught's number would be inventing the one thing a
    # grower plans their wood or coal purchase against.
    up = next(b for b in BARN_TYPES if b.key == "conventional_up")
    assert up.fuel_kg_per_kg_cured is None
    assert fuel_required_kg(up, 2000) is None

    plastic = next(b for b in BARN_TYPES if b.key == "plastic")
    assert fuel_required_kg(plastic, 2000) == pytest.approx(9000.0)


def test_fuel_declines_on_a_meaningless_quantity():
    plastic = next(b for b in BARN_TYPES if b.key == "plastic")
    assert fuel_required_kg(plastic, 0) is None
    assert fuel_required_kg(plastic, -1) is None
    assert fuel_required_kg(plastic, None) is None


def test_every_barn_that_quotes_a_fuel_rate_names_the_fuel():
    # "4.5 kg per kg cured" is unusable without knowing whether that is wood or
    # coal — they are not interchangeable and one of them is a land decision.
    for barn in BARN_TYPES:
        if barn.fuel_kg_per_kg_cured is not None:
            assert barn.fuel, f"{barn.key} quotes a rate with no fuel named"


# ---------------------------------------------------------------------------
# Serialisation — the planning screen reads this
# ---------------------------------------------------------------------------
def test_the_plan_serialises_to_something_a_screen_can_render():
    plan = build_curing_plan("Tobacco", area_hectares=2.0)
    assert plan is not None
    data = plan.to_dict()

    assert data["crop"] == "Tobacco"
    assert data["total_days"] == [7.0, 10.0]
    assert data["conditioning_moisture_pct"] == [12.0, 15.0]
    assert len(data["stages"]) == 3
    assert data["stages"][0]["key"] == "colouring"
    assert data["stages"][0]["relative_humidity_pct"] == 85.0
    assert data["barn_options"]
    assert data["barn_options"][0]["count"] >= 1
    assert data["warnings"], "the pending-sign-off caveat must survive to the screen"


def test_the_serialised_plan_is_json_safe():
    import json

    json.dumps(build_curing_plan("Tobacco", area_hectares=1.5).to_dict())


# ---------------------------------------------------------------------------
# The chat surface — same functions, so the same numbers
# ---------------------------------------------------------------------------
def test_the_briefing_quotes_the_plan_rather_than_restating_it():
    # Same rule as the establishment briefing: derive from the source so a
    # divergence cannot hide in a second hardcoded copy.
    text = curing_briefing("Tobacco", area_hectares=2.0)
    assert text is not None
    for stage in CURING_STAGES:
        low, high = stage.temperature_c
        assert f"{low:g}–{high:g} °C" in text
    low, high = total_cure_days()
    assert f"{low:g}–{high:g} days" in text


def test_the_briefing_tells_the_farmer_to_condition_the_leaf():
    # The step that is easiest to skip and most expensive to skip: dry leaf off
    # the sticks shatters, and the grade goes with it.
    text = curing_briefing("Tobacco")
    assert text is not None
    assert "Conditioning" in text
    assert "12–15%" in text


def test_the_briefing_carries_the_reason_colouring_is_held_humid():
    # The counter-intuitive instruction. A farmer who does not know *why* will
    # rationally turn the heat up, and set green into the whole barn.
    text = curing_briefing("Tobacco")
    assert text is not None
    assert "85%" in text
    assert "green" in text.lower()


def test_the_briefing_does_not_pick_a_barn_for_the_grower():
    # Fuel availability decides this, not efficiency, and we do not know what
    # the grower can get hold of.
    text = curing_briefing("Tobacco", area_hectares=2.0)
    assert text is not None
    assert "fuel the grower can" in text


def test_curing_reaches_a_tobacco_field_through_the_planning_briefing():
    # Wiring guard. The module can be perfect and unreached — which is exactly
    # the state postharvest sat in, with nothing failing.
    text = planning_briefing("Tobacco", natural_region="IIa", area_hectares=2.0)
    assert text is not None
    assert "Flue-curing" in text


def test_curing_does_not_leak_into_a_maize_briefing():
    text = planning_briefing("Maize", natural_region="IIa", area_hectares=2.0)
    assert text is not None
    assert "Flue-curing" not in text
    assert "barn" not in text.lower()


def test_curing_is_available_before_planting_not_only_after_harvest():
    # Deliberate. A grower decides how many barns to build, and cuts or buys the
    # wood to fire them, months before the first leaf is ready. By reaping time
    # the decision has already been made, so withholding this until harvest
    # would deliver it after it was useful.
    text = planning_briefing("Tobacco", natural_region="IIa", area_hectares=2.0,
                             is_planted=False)
    assert text is not None
    assert "Flue-curing" in text
    assert "not yet planted" in text


def test_the_route_serves_this():
    # Second wiring guard, for the planning screen rather than the chat.
    import pathlib

    routes = (
        pathlib.Path(__file__).resolve().parent.parent / "season_lifecycle_routes.py"
    ).read_text()
    assert "build_curing_plan" in routes
    assert "/fields/{field_id}/curing" in routes


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
def test_the_source_and_the_pending_review_warning_stay_attached():
    # Every farmer-facing constant in this package carries a `.. warning::`
    # until an agronomist signs it off, and this one also has to say where the
    # numbers came from — the answer is Kutsaga, not TIMB, and someone will
    # eventually need to know that.
    from services.planning import curing

    doc = curing.__doc__ or ""
    assert ".. warning::" in doc
    assert "kutsaga" in doc.lower()
