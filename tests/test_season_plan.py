"""
Season plan assembly.

The only one of the four documents taken into the field. Two things carry the
weight: the persona split, which decides *which* instructions appear, and the
committed/conditional split, which decides what reads as an order.
"""

from dataclasses import replace
from datetime import date

import pytest

from services.documents.season_plan import (
    PlanStep,
    build_season_plan,
    normalise_persona,
    stage_label,
    steps_from_programme,
    steps_from_windows,
    uses_equipment,
)


def _plan(**kw):
    base = dict(
        field_name="Home Field",
        crop="maize",
        coverage_start=date(2025, 10, 1),
        coverage_end=date(2026, 6, 30),
        planned_planting_date=date(2025, 11, 20),
    )
    base.update(kw)
    return build_season_plan(**base)


def _step(key="s", on=None, optional=False, conditional=None, label="Step"):
    return PlanStep(
        key=key, label=label, detail="", when_text="",
        on_date=on, optional=optional, conditional_on=conditional,
    )


# ── Persona ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("persona", ["farmer", "agronomist"])
def test_commercial_personas_get_equipment_advice(persona):
    assert uses_equipment(persona)
    assert _plan(persona=persona).equipment_tips


@pytest.mark.parametrize("persona", ["smallholder", "hobbyist"])
def test_hand_planting_personas_get_none_of_it(persona):
    # Padding the page with machinery advice they cannot use is exactly what the
    # persona split exists to stop.
    assert not uses_equipment(persona)
    assert _plan(persona=persona).equipment_tips == ()
    assert _plan(persona=persona).hand_planting_tips


def test_the_two_tip_sets_are_mutually_exclusive():
    for persona in ("farmer", "smallholder", "agronomist", "hobbyist"):
        plan = _plan(persona=persona)
        assert not (plan.equipment_tips and plan.hand_planting_tips), persona


@pytest.mark.parametrize("unknown", [None, "", "   ", "beekeeper"])
def test_an_unknown_persona_falls_back_to_smallholder_not_commercial(unknown):
    # Getting it wrong this way gives someone plain language they did not need.
    # The other way tells a person with a hoe to calibrate a planter.
    assert normalise_persona(unknown) == "smallholder"
    assert _plan(persona=unknown).equipment_tips == ()


def test_persona_matching_is_case_insensitive():
    assert normalise_persona("Farmer") == "farmer"
    assert uses_equipment("  AGRONOMIST ")


def test_stage_codes_go_to_readers_who_want_them():
    assert stage_label("V6", "when it is knee-high", "agronomist") == "V6"
    assert stage_label("V6", "when it is knee-high", "smallholder") == "when it is knee-high"


def test_stage_label_falls_back_rather_than_rendering_empty():
    assert stage_label("V6", None, "smallholder") == "V6"
    assert stage_label(None, "when it is knee-high", "agronomist") == "when it is knee-high"
    assert stage_label(None, None, "farmer") == ""


# ── Committed vs conditional ──────────────────────────────────────────────────


def test_a_plain_step_is_committed():
    assert _step().is_committed


@pytest.mark.parametrize(
    "kwargs", [{"optional": True}, {"conditional": "if the rains hold"}]
)
def test_optional_and_conditional_steps_are_not_committed(kwargs):
    # A plan that presents every line as an order gets followed past the point
    # where it stopped applying — fertiliser spread on a crop that cannot use it.
    assert not _step(**kwargs).is_committed


def test_the_two_lists_partition_the_steps():
    plan = replace(_plan(), steps=(
        _step("a", date(2025, 11, 20)),
        _step("b", date(2025, 12, 5), optional=True),
        _step("c", date(2026, 1, 5), conditional="if the rains hold"),
    ))
    assert [s.key for s in plan.committed_steps] == ["a"]
    assert [s.key for s in plan.conditional_steps] == ["b", "c"]


def test_conditional_steps_are_qualified():
    plan = _plan()
    plan = replace(plan, steps=(_step("a", optional=True),))
    assert any("conditional" in q for q in plan.qualifications)


# ── Ordering ──────────────────────────────────────────────────────────────────


def test_steps_run_in_date_order_not_by_topic():
    # A farmer reading in November wants planting; in January the second
    # top-dress. Organised by subject they have to hunt.
    plan = _plan()
    plan = replace(plan, steps=(
        _step("late", date(2026, 1, 20)),
        _step("early", date(2025, 11, 20)),
    ))
    assert [s.key for s in plan.dated_steps] == ["early", "late"]


def test_undated_steps_sort_last_rather_than_being_dropped():
    # Hiding a step because the calendar is incomplete quietly shortens the plan.
    plan = _plan()
    plan = replace(plan, steps=(
        _step("undated"), _step("dated", date(2026, 1, 20)),
    ))
    assert [s.key for s in plan.dated_steps] == ["dated", "undated"]
    assert [s.key for s in plan.undated_steps] == ["undated"]


def test_undated_steps_are_qualified_when_a_planting_date_exists():
    plan = _plan()
    plan = replace(plan, steps=(_step("undated"),))
    assert any("could not be dated" in q for q in plan.qualifications)


def test_no_planting_date_is_qualified_as_the_reason_nothing_is_dated():
    # And says what to do about it — the plan moves as soon as one is set.
    plan = _plan(planned_planting_date=None)
    note = next(q for q in plan.qualifications if "No planting date" in q)
    assert "moves with it" in note


def test_undated_steps_are_not_double_reported_when_there_is_no_planting_date():
    # Without a date nothing can be dated; saying so twice is noise.
    plan = _plan(planned_planting_date=None)
    plan = replace(plan, steps=(_step("a"), _step("b")))
    assert sum("could not be dated" in q for q in plan.qualifications) == 0


# ── Adapting the engines ──────────────────────────────────────────────────────


def test_a_fertiliser_programme_flattens_into_steps():
    programme = {
        "steps": [
            {"key": "basal", "label": "Basal", "product": "Compound D",
             "rate_text": "300 kg/ha", "timing_text": "At planting",
             "scheduled_date": "2025-11-20", "optional": False},
            {"key": "top_dress_2", "label": "Second top-dress", "product": "AN",
             "rate_text": "150 kg/ha", "timing_text": "V8-V10",
             "scheduled_date": None, "optional": True},
        ]
    }
    steps = steps_from_programme(programme)
    assert [s.key for s in steps] == ["basal", "top_dress_2"]
    assert steps[0].on_date == date(2025, 11, 20)
    assert steps[0].detail == "Compound D · 300 kg/ha"
    assert steps[1].on_date is None and not steps[1].is_committed


def test_no_programme_yields_no_steps_rather_than_raising():
    assert steps_from_programme(None) == ()


def test_a_malformed_date_from_the_engine_becomes_undated_not_a_crash():
    steps = steps_from_programme({"steps": [{"key": "x", "scheduled_date": "soon"}]})
    assert steps[0].on_date is None


def test_windows_flatten_into_steps():
    windows = [{"key": "weeding", "label": "Critical weed period",
                "why": "Weeds now cost yield you cannot get back",
                "window_text": "Days 14-42", "closes_on": "2026-01-01"}]
    steps = steps_from_windows(windows)
    assert steps[0].on_date == date(2026, 1, 1)
    assert "cannot get back" in steps[0].detail


def test_windows_accept_objects_as_well_as_dicts():
    class FakeWindow:
        def to_dict(self):
            return {"key": "w", "label": "W", "closes_on": "2026-01-01"}

    assert steps_from_windows([FakeWindow()])[0].key == "w"


def test_both_engines_contribute_to_one_chronological_list():
    plan = _plan(
        fertiliser={"steps": [{"key": "basal", "scheduled_date": "2025-11-20"}]},
        windows=[{"key": "weeding", "closes_on": "2026-01-01"}],
    )
    assert [s.key for s in plan.dated_steps] == ["basal", "weeding"]


def test_engine_warnings_reach_the_qualifications():
    plan = _plan(warnings=["Sandy soil — split the nitrogen"])
    assert "Sandy soil — split the nitrogen" in plan.qualifications
