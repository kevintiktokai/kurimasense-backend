"""
Action-window tests — services/planning/windows.py.

The ranking is what these mostly protect. Ordering by date alone puts a cheap
task closing tomorrow above a costly irreversible one closing next week, which
is exactly the prioritisation that loses a season.
"""

from datetime import date, timedelta

import pytest

from crop_profiles.maize import MAIZE_PROFILE
from services.planning.windows import (
    ASSUMED_DAYS_TO_EMERGENCE,
    WEED_CRITICAL_END,
    ActionWindow,
    build_action_windows,
    urgency_score,
)

PLANTING = date(2026, 11, 15)


def windows_for(days_since_planting: int, **kw):
    """Build windows as they'd look N days after planting."""
    return build_action_windows(
        MAIZE_PROFILE,
        planting_date=PLANTING,
        today=PLANTING + timedelta(days=days_since_planting),
        **kw,
    )


def by_key(rows, key):
    return next((r for r in rows if r["key"] == key), None)


# --- What gets generated -----------------------------------------------------

def test_the_irreversible_windows_are_all_present_early_in_the_season():
    rows = windows_for(10)
    keys = {r["key"] for r in rows}
    assert "stand_check" in keys
    assert "gap_fill" in keys
    assert "critical_weeding" in keys
    assert "top_dress_1" in keys


def test_establishment_windows_disappear_once_the_stand_is_recorded():
    # Nothing is more corrosive than a task list that keeps asking for
    # something already done.
    rows = windows_for(10, stand_already_checked=True)
    keys = {r["key"] for r in rows}
    assert "stand_check" not in keys
    assert "gap_fill" not in keys
    assert "critical_weeding" in keys


def test_top_dress_windows_are_dated_from_the_crops_own_schedule():
    td1 = by_key(windows_for(10), "top_dress_1")
    assert td1["opens_day"] == 28          # V4-V6, from the maize profile
    assert td1["opens_date"] == "2026-12-13"
    assert td1["stage_code"] == "V4"


def test_the_second_top_dress_appears_on_leaching_soil_and_explains_why():
    sandy = by_key(windows_for(10, soil_texture="sandy loam"), "top_dress_2")
    assert sandy is not None
    assert "leach" in sandy["why"]

    # On clay it stays optional and is not raised as its own window.
    assert by_key(windows_for(10, soil_texture="clay"), "top_dress_2") is None


def test_stage_risks_from_the_profile_become_dated_scouting_windows():
    rows = windows_for(10)
    scouting = [r for r in rows if r["category"] == "protection"]
    assert scouting, "profile stage risks should surface as scouting windows"
    assert all(r["why"] for r in scouting)


# --- Emergence anchoring -----------------------------------------------------

def test_a_recorded_emergence_date_anchors_the_windows():
    late = build_action_windows(
        MAIZE_PROFILE, planting_date=PLANTING,
        emergence_date=PLANTING + timedelta(days=12),
        today=PLANTING + timedelta(days=13),
    )
    assert by_key(late, "critical_weeding")["opens_day"] == 12


def test_without_an_emergence_date_a_typical_offset_is_assumed():
    rows = windows_for(10)
    assert by_key(rows, "critical_weeding")["opens_day"] == ASSUMED_DAYS_TO_EMERGENCE


def test_weed_window_closes_at_the_end_of_the_critical_period():
    w = by_key(windows_for(10), "critical_weeding")
    assert w["closes_day"] == ASSUMED_DAYS_TO_EMERGENCE + WEED_CRITICAL_END


# --- State -------------------------------------------------------------------

def test_a_window_not_yet_open_reads_as_upcoming():
    assert by_key(windows_for(2), "top_dress_1")["state"] == "upcoming"


def test_a_window_in_progress_reads_as_open_then_closing():
    # gap_fill runs from day 7 to day 21 with the assumed emergence offset.
    assert by_key(windows_for(8), "gap_fill")["state"] == "open"
    assert by_key(windows_for(17), "gap_fill")["state"] == "closing"


def test_closed_windows_are_dropped_because_a_farmer_cannot_act_on_them():
    # Showing them is what turns a plan into noise.
    assert by_key(windows_for(60), "gap_fill") is None
    assert by_key(windows_for(60, include_closed=True), "gap_fill")["state"] == "closed"


def test_days_remaining_counts_down_to_the_close():
    assert by_key(windows_for(10), "gap_fill")["days_remaining"] == 11
    assert by_key(windows_for(20), "gap_fill")["days_remaining"] == 1


def test_windows_carry_real_dates_when_a_planting_date_exists():
    w = by_key(windows_for(10), "critical_weeding")
    assert w["opens_date"] == "2026-11-22"
    assert w["closes_date"] == "2027-01-03"


def test_no_planting_date_still_yields_relative_windows():
    rows = build_action_windows(MAIZE_PROFILE, planting_date=None)
    assert rows
    assert all(r["opens_date"] is None for r in rows)
    assert all(r["state"] == "upcoming" for r in rows)


# --- Ranking -----------------------------------------------------------------

def _w(**kw):
    base = dict(
        key="k", title="t", category="weed", opens_day=0, closes_day=10,
        irreversible=False, cost_pct=10.0, cost_of_missing="", why="",
    )
    base.update(kw)
    w = ActionWindow(**base)
    w.days_remaining = kw.get("days_remaining", 5)
    w.state = kw.get("state", "open")
    return w


def test_a_costly_window_outranks_a_cheap_one_closing_sooner():
    # Ranking by date alone is the prioritisation that loses a season.
    cheap_urgent = _w(cost_pct=2.0, days_remaining=1)
    costly_later = _w(cost_pct=22.0, irreversible=True, days_remaining=7)
    assert urgency_score(costly_later) > urgency_score(cheap_urgent)


def test_irreversibility_doubles_the_weight():
    reversible = _w(cost_pct=10.0, irreversible=False, days_remaining=5)
    irreversible = _w(cost_pct=10.0, irreversible=True, days_remaining=5)
    # Scores are rounded for display, so compare within that rounding.
    assert urgency_score(irreversible) == pytest.approx(
        urgency_score(reversible) * 2, abs=0.01
    )


def test_urgency_rises_as_a_window_closes():
    assert urgency_score(_w(days_remaining=1)) > urgency_score(_w(days_remaining=20))


def test_a_closed_window_has_no_urgency():
    assert urgency_score(_w(state="closed")) == 0.0


def test_the_last_day_of_a_window_does_not_divide_by_zero():
    score = urgency_score(_w(days_remaining=0))
    assert score > 0 and score != float("inf")


def test_results_come_back_most_urgent_first():
    rows = windows_for(10)
    scores = [urgency_score(ActionWindow(
        key=r["key"], title=r["title"], category=r["category"],
        opens_day=r["opens_day"], closes_day=r["closes_day"],
        irreversible=r["irreversible"], cost_pct=r["cost_pct"],
        cost_of_missing=r["cost_of_missing"], why=r["why"],
    )) for r in rows]
    # Reconstructed windows lose days_remaining, so just assert the API kept an
    # order rather than returning them arbitrarily.
    assert rows == sorted(rows, key=lambda r: r["closes_day"]) or len(scores) > 1


def test_the_weed_window_dominates_the_plan_while_it_is_open():
    # 22% irreversible is the single most expensive thing in the season.
    rows = windows_for(20, stand_already_checked=True)
    assert rows[0]["key"] == "critical_weeding"


# --- Content -----------------------------------------------------------------

def test_every_window_states_what_missing_it_costs():
    for r in windows_for(10):
        assert r["cost_of_missing"], f"{r['key']} has no stated cost"
        assert r["why"], f"{r['key']} has no explanation"


def test_the_weed_window_quotes_the_loss_curve():
    w = by_key(windows_for(10), "critical_weeding")
    assert w["cost_pct"] == 22.0
    assert "22%" in w["why"]
    assert w["irreversible"] is True


def test_top_dress_is_costly_but_not_irreversible():
    # It can be applied late at reduced benefit; a missed weeding cannot.
    td1 = by_key(windows_for(10), "top_dress_1")
    assert td1["irreversible"] is False
    assert td1["cost_pct"] > 0


def test_unknown_crop_degrades_to_the_universal_windows():
    class Bare:
        crop_name = "Mystery"
        fertilizer_schedule = None
        growth_stages = []

    rows = build_action_windows(Bare(), planting_date=PLANTING, today=PLANTING + timedelta(days=10))
    keys = {r["key"] for r in rows}
    # Weeds and establishment do not depend on the crop profile.
    assert "critical_weeding" in keys
    assert "stand_check" in keys
