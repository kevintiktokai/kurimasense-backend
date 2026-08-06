"""
Season retrospective tests — services/seasons/retrospective.py.

The honesty rule is what these mostly defend: nothing is attributed without
evidence, nothing sums to more than the actual gap, and whatever is left over is
reported as unexplained rather than quietly absorbed. A decomposition that
always adds to exactly 100% is one that has been fudged, and a farmer who spots
one fudged line discounts the whole thing.
"""

import pytest

from services.seasons.retrospective import (
    MIN_REPORTABLE_GAP_T_HA,
    build_retrospective,
)


def season(**kw):
    base = {
        "id": "s1",
        "crop_type": "Maize",
        "variety": "SC727",
        "yield_tonnes_per_ha": 4.2,
        "target_population_per_ha": 44000,
        "established_population_per_ha": 44000,
        "emergence_uniformity": "uniform",
    }
    base.update(kw)
    return base


def factor(retro, key):
    return next((f for f in retro.factors if f.key == key), None)


# --- Preconditions -----------------------------------------------------------

def test_no_harvest_means_no_retrospective():
    r = build_retrospective(season(yield_tonnes_per_ha=None), potential_yield_t_ha=6.5)
    assert r.gap_t_ha is None
    assert "nothing to compare" in r.headline
    assert any("Record your harvest" in n for n in r.notes)


def test_no_known_ceiling_reports_the_yield_without_inventing_a_benchmark():
    r = build_retrospective(season(), potential_yield_t_ha=None)
    assert r.gap_t_ha is None
    assert "4.2 t/ha" in r.headline
    assert any("cannot be broken down" in n for n in r.notes)


def test_hitting_potential_is_reported_as_success_not_a_gap():
    r = build_retrospective(season(yield_tonnes_per_ha=6.4), potential_yield_t_ha=6.5)
    assert r.factors == []
    assert "full potential" in r.headline


# --- Stand attribution -------------------------------------------------------

def test_a_thin_stand_is_named_with_its_measurement():
    r = build_retrospective(
        season(established_population_per_ha=31000), potential_yield_t_ha=6.5
    )
    f = factor(r, "thin_stand")
    assert f is not None
    assert f.tonnes_per_ha > 0
    assert "31,000" in f.evidence
    assert "44,000" in f.evidence
    assert f.controllable is True


def test_stand_loss_is_not_linear_in_population():
    # A 70% stand does not cost 30% of yield — surviving plants compensate.
    # Treating it as linear would push farmers into replants that lose money.
    r = build_retrospective(
        season(established_population_per_ha=30800), potential_yield_t_ha=6.5
    )
    linear_loss = 6.5 * 0.30
    assert factor(r, "thin_stand").tonnes_per_ha < linear_loss


def test_a_stand_within_compensation_range_is_not_blamed():
    r = build_retrospective(
        season(established_population_per_ha=43000), potential_yield_t_ha=6.5
    )
    assert factor(r, "thin_stand") is None


def test_stand_cannot_be_attributed_without_a_measurement():
    # This is the whole reason the Stand Check exists.
    r = build_retrospective(
        season(established_population_per_ha=None), potential_yield_t_ha=6.5
    )
    assert factor(r, "thin_stand") is None
    assert r.unexplained_t_ha == r.gap_t_ha


def test_no_target_means_no_stand_attribution():
    r = build_retrospective(
        season(target_population_per_ha=None, established_population_per_ha=31000),
        potential_yield_t_ha=6.5,
    )
    assert factor(r, "thin_stand") is None


# --- Emergence ---------------------------------------------------------------

def test_poor_emergence_is_charged_beyond_the_plant_count():
    r = build_retrospective(
        season(emergence_uniformity="poor"), potential_yield_t_ha=6.5
    )
    f = factor(r, "uneven_emergence")
    assert f is not None
    assert "shaded out" in f.next_season


def test_uniform_emergence_is_not_charged():
    r = build_retrospective(
        season(emergence_uniformity="uniform"), potential_yield_t_ha=6.5
    )
    assert factor(r, "uneven_emergence") is None


def test_poor_emergence_costs_more_than_moderate():
    poor = build_retrospective(season(emergence_uniformity="poor"), potential_yield_t_ha=6.5)
    moderate = build_retrospective(season(emergence_uniformity="moderate"), potential_yield_t_ha=6.5)
    assert factor(poor, "uneven_emergence").tonnes_per_ha > \
        factor(moderate, "uneven_emergence").tonnes_per_ha


def test_unrecorded_emergence_is_not_guessed_at():
    r = build_retrospective(season(emergence_uniformity=None), potential_yield_t_ha=6.5)
    assert factor(r, "uneven_emergence") is None


# --- Timing ------------------------------------------------------------------

def test_late_nitrogen_is_charged_by_how_late_it_was():
    early = build_retrospective(season(), potential_yield_t_ha=6.5, late_topdress_days=14)
    late = build_retrospective(season(), potential_yield_t_ha=6.5, late_topdress_days=28)
    assert factor(late, "late_topdress").tonnes_per_ha > \
        factor(early, "late_topdress").tonnes_per_ha


def test_nitrogen_applied_on_time_is_not_charged():
    r = build_retrospective(season(), potential_yield_t_ha=6.5, late_topdress_days=3)
    assert factor(r, "late_topdress") is None


def test_late_nitrogen_penalty_is_capped():
    # Beyond a point the crop has set its yield components; more nitrogen
    # cannot buy them back, and neither should the penalty keep growing.
    very_late = build_retrospective(season(), potential_yield_t_ha=6.5, late_topdress_days=120)
    assert factor(very_late, "late_topdress").tonnes_per_ha <= round(6.5 * 0.12, 2)


def test_unknown_timing_is_not_attributed():
    r = build_retrospective(season(), potential_yield_t_ha=6.5, late_topdress_days=None)
    assert factor(r, "late_topdress") is None


# --- The honesty rule --------------------------------------------------------

def test_whatever_is_not_evidenced_is_reported_as_unexplained():
    # An honest "we can't account for this" beats a tidy full breakdown.
    r = build_retrospective(season(), potential_yield_t_ha=6.5)
    assert r.gap_t_ha == pytest.approx(2.3)
    assert r.unexplained_t_ha == pytest.approx(2.3)
    assert any("not explained" in n for n in r.notes)


def test_attribution_never_exceeds_the_actual_gap():
    # Every factor maxed out against a small gap.
    r = build_retrospective(
        season(
            yield_tonnes_per_ha=6.0,
            established_population_per_ha=15000,
            emergence_uniformity="poor",
        ),
        potential_yield_t_ha=6.5,
        late_topdress_days=60,
    )
    attributed = sum(f.tonnes_per_ha for f in r.factors)
    assert attributed <= r.gap_t_ha + 0.01
    assert r.unexplained_t_ha >= 0
    assert any("scaled back" in n for n in r.notes)


def test_unexplained_is_never_negative():
    r = build_retrospective(
        season(yield_tonnes_per_ha=6.3, established_population_per_ha=10000,
               emergence_uniformity="poor"),
        potential_yield_t_ha=6.5,
    )
    assert r.unexplained_t_ha >= 0


def test_factors_are_ordered_by_what_cost_most():
    r = build_retrospective(
        season(established_population_per_ha=28000, emergence_uniformity="moderate"),
        potential_yield_t_ha=6.5,
        late_topdress_days=10,
    )
    costs = [f.tonnes_per_ha for f in r.factors]
    assert costs == sorted(costs, reverse=True)


def test_a_season_with_no_measurements_says_what_would_fix_that():
    r = build_retrospective(
        {"id": "s1", "crop_type": "Maize", "yield_tonnes_per_ha": 4.2},
        potential_yield_t_ha=6.5,
    )
    assert r.factors == []
    assert any("Recording establishment" in n for n in r.notes)


def test_trivial_gaps_are_not_dressed_up_as_findings():
    r = build_retrospective(
        season(yield_tonnes_per_ha=6.5 - MIN_REPORTABLE_GAP_T_HA / 2),
        potential_yield_t_ha=6.5,
    )
    assert r.factors == []


# --- Output ------------------------------------------------------------------

def test_every_factor_carries_evidence_and_an_action():
    r = build_retrospective(
        season(established_population_per_ha=31000, emergence_uniformity="poor"),
        potential_yield_t_ha=6.5, late_topdress_days=21,
    )
    assert r.factors
    for f in r.factors:
        assert f.evidence, f"{f.key} has no evidence"
        assert f.next_season, f"{f.key} has no action for next season"


def test_headline_states_both_numbers_and_the_gap():
    r = build_retrospective(season(), potential_yield_t_ha=6.5)
    assert "4.2" in r.headline and "6.5" in r.headline and "2.3" in r.headline


def test_retrospective_serialises_for_the_api():
    d = build_retrospective(
        season(established_population_per_ha=31000), potential_yield_t_ha=6.5
    ).to_dict()
    assert d["gap_t_ha"] == pytest.approx(2.3)
    assert d["factors"][0]["controllable"] is True
    assert "unexplained_t_ha" in d
