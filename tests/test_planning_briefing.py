"""
The chat and the planner give the same numbers.

Ask the season planner how to space maize and it computes from
``services.planning.establishment``. Ask the chat and it improvised, because
``ai_brain`` knew about ``crop_profiles`` and nothing about
``services.planning``. Two surfaces, two answers, and no way for a farmer to
tell which one to plant by.

That is exactly what this repo's shared-helper convention exists to prevent, so
the chat now renders the planner's own functions rather than describing them.
These tests hold that: the briefing must quote what the plan computes, decline
where the plan declines, and never manufacture the parts the plan expresses as
a range.
"""

from datetime import date

from services.planning.briefing import (
    establishment_briefing,
    fertiliser_briefing,
    planning_briefing,
)
from services.planning.establishment import build_establishment_plan


def test_the_briefing_quotes_the_plan_rather_than_restating_it():
    # The whole point. Every number here must be the planner's number, so the
    # test derives them from the plan instead of hardcoding a second copy —
    # hardcoding would recreate the divergence this module removes.
    plan = build_establishment_plan("Maize", natural_region="IIa", area_hectares=2.0)
    text = establishment_briefing("Maize", natural_region="IIa", area_hectares=2.0)

    assert text is not None
    assert f"{plan.target_population_per_ha:,}" in text
    assert f"{plan.row_spacing_cm:g}" in text
    assert f"{plan.in_row_spacing_cm:g}" in text
    assert f"{plan.seed_rate_kg_ha:g}" in text


def test_an_unsupported_crop_declines_rather_than_inventing_a_table():
    # The rule that matters most on this surface: a chat will state a fabricated
    # spacing with total confidence, and a farmer will plant by it.
    assert establishment_briefing("Dragonfruit") is None
    assert planning_briefing("Dragonfruit") is None


def test_no_crop_at_all_is_not_an_answer():
    assert planning_briefing(None) is None
    assert planning_briefing("") is None


def test_a_depth_range_is_rendered_as_a_range():
    # planting_depth_cm is a (low, high) pair because that is what the agronomy
    # says. Quoting one end as "the" depth would invent a precision the source
    # does not have — and the first draft of this module crashed on exactly
    # that assumption.
    text = establishment_briefing("Maize", natural_region="IIa")
    assert text is not None
    plan = build_establishment_plan("Maize", natural_region="IIa")
    low, high = plan.planting_depth_cm
    assert f"{low:g}–{high:g}" in text


def test_the_fertiliser_programme_reaches_the_chat():
    # This one silently returned None in the first draft: the call passed a crop
    # name where the planner passes a profile object, and a defensive
    # `except TypeError` swallowed it. The chat simply never mentioned
    # fertiliser, and nothing failed.
    text = fertiliser_briefing("Maize", area_hectares=2.0)
    assert text is not None, "the fertiliser programme is missing from the chat context"
    assert "Fertiliser programme" in text
    assert "Basal" in text or "basal" in text


def test_the_fertiliser_briefing_is_trimmed_but_says_so():
    # A chat answer is not the place for the full season, but silently dropping
    # steps would leave a farmer thinking the programme is shorter than it is.
    text = fertiliser_briefing("Maize", area_hectares=2.0)
    assert text is not None
    if "further step" in text:
        assert "planning screen" in text


def test_a_planted_field_gets_no_pre_plant_framing():
    planted = planning_briefing(
        "Maize", natural_region="IIa", planting_date=date(2026, 11, 20), is_planted=True
    )
    assert planted is not None
    assert "not yet planted" not in planted


def test_an_unplanted_field_is_told_what_it_actually_is():
    # The case from the production log: "Demo 2", planting_date=None, a blank
    # yield card and no indication the app has anything to say. For that field
    # the establishment plan IS the answer, and the model must not wander into
    # stage or yield talk that does not exist yet.
    unplanted = planning_briefing("Maize", natural_region="IIa", is_planted=False)
    assert unplanted is not None
    assert "not yet planted" in unplanted
    assert "yield projection" in unplanted


def test_the_briefing_carries_the_field_check_a_farmer_can_perform():
    # The most useful line in the plan and the chat could not see it: a pace
    # count anyone can do standing in the row, without a tape measure.
    text = establishment_briefing("Maize", natural_region="IIa")
    assert text is not None
    assert "Field check:" in text


def test_the_chat_context_builder_actually_calls_this():
    # Wiring guard. The module can be perfect and still unreached — which is
    # the state it was in before, and nothing would have failed.
    import pathlib

    brain = (pathlib.Path(__file__).resolve().parent.parent / "ai_brain.py").read_text()
    assert "planning_briefing" in brain
    assert "from services.planning.briefing import" in brain


def test_a_transplanted_crop_is_not_given_a_seed_rate_of_zero():
    # Tobacco is transplanted, and the profiles express that as seed_rate 0 and
    # depth 0. Rendered literally that produced
    #
    #     - Planting depth: 0 cm, 1 seed(s) per station
    #     - Seed rate: 0 kg/ha
    #
    # for the crop most of this product's farmers actually grow — not a fact,
    # a broken-looking calculation, and the same mistake as a card that renders
    # empty instead of rendering nothing.
    text = establishment_briefing("Tobacco", natural_region="IIa", area_hectares=2.0)
    assert text is not None
    # Precise, not substring: "0 cm" also matches inside a legitimate
    # "120 cm" row spacing, which is how the first draft of this test failed.
    assert "Seed rate:" not in text
    assert "Planting depth:" not in text
    assert "seedlings per hectare" in text


def test_a_direct_seeded_crop_still_gets_its_seed_rate():
    # The counterpart: suppressing zeros must not suppress real numbers.
    text = establishment_briefing("Maize", natural_region="IIa", area_hectares=2.0)
    assert text is not None
    assert "Seed rate:" in text
    assert "Planting depth:" in text


def test_the_chat_is_given_the_natural_region_and_the_area():
    # Not cosmetic. build_establishment_plan targets a plant population per
    # natural region, so with natural_region=None a Region IIa field got
    #
    #     planning screen:  50,000 plants/ha, 22.2 cm in-row
    #     chat:             44,000 plants/ha, 25.3 cm in-row
    #
    # for the same field and crop — two spacings, no way for a farmer to tell
    # which to plant by, and nothing failing anywhere. That is precisely the
    # divergence this module was written to close, present in the code that
    # closes it. Area does the same to barn sizing: the screen says "3 × rocket
    # barn", the chat says nothing at all.
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent
    brain = (root / "ai_brain.py").read_text()
    call = brain[brain.index("briefing = planning_briefing("):]
    call = call[: call.index(")")]
    assert "natural_region=field_context.natural_region" in call
    assert "area_hectares=field_context.area_hectares" in call

    # ...and the context has to actually carry them, or the call passes None.
    assert "area_hectares: Optional[float] = None" in brain
    assert "natural_region: Optional[str] = None" in brain
    deps = (root / "deps.py").read_text()
    assert "f.size_hectares, f.natural_region" in deps, "the query must select them"
    assert "context.natural_region = row.get(\"natural_region\")" in deps


def test_the_region_actually_changes_the_answer():
    # Guard on the guard. If populations ever stop varying by region the test
    # above becomes decoration, and the next person deletes the plumbing it
    # protects because nothing appears to depend on it.
    iia = build_establishment_plan("Maize", natural_region="IIa")
    unknown = build_establishment_plan("Maize", natural_region=None)
    assert iia.target_population_per_ha != unknown.target_population_per_ha
