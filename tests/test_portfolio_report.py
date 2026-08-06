"""
Portfolio report assembly.

Two things carry most of the weight: the separation between hectares *under
management* and hectares *observed*, and the anonymiser — which exists because
this document doubles as a sales demo and the playbook forbids showing
grower-level data without consent.
"""

from datetime import date

from services.documents.portfolio_report import (
    STALE_AFTER_DAYS,
    FieldRow,
    anonymise_rows,
    build_portfolio_report,
)


def _f(
    name="Home Field",
    ha=10.0,
    score=70,
    band="good",
    urgency="low",
    district="Mazowe",
    grower=("g1", "Tariro"),
    days=2,
):
    return FieldRow(
        field_id=name.lower().replace(" ", "-"),
        field_name=name,
        grower_id=grower[0] if grower else None,
        grower_name=grower[1] if grower else None,
        district=district,
        crop_type="Tobacco",
        hectares=ha,
        kurima_score=score,
        band=band,
        urgency=urgency,
        primary_concern=None,
        days_since_observation=days,
    )


def _report(fields, **kw):
    return build_portfolio_report(
        client_name="Servemox",
        coverage_start=date(2025, 11, 1),
        coverage_end=date(2026, 5, 31),
        fields=fields,
        **kw,
    )


# ── Observed vs under management ──────────────────────────────────────────────


def test_unscored_fields_count_as_unobserved():
    # A score is the evidence of observation; the aggregator returns None until
    # there is something to score.
    r = _report([_f("A", 10), _f("B", 30, score=None, band=None, urgency="awaiting_data")])
    assert r.hectares_under_management == 40
    assert r.hectares_observed == 10


def test_awaiting_data_is_not_an_attention_field():
    # It is not a field in trouble, it is a field we cannot see. Conflating the
    # two sends someone to drive to a field where nothing is wrong.
    r = _report([_f("B", 30, score=None, band=None, urgency="awaiting_data")])
    assert r.attention == ()
    assert len(r.unobserved_fields) == 1


def test_a_field_with_no_area_does_not_break_the_sums():
    r = _report([_f("A", None), _f("B", 12)])
    assert r.hectares_observed == 12


def test_grower_count_is_distinct():
    r = _report([_f("A", grower=("g1", "T")), _f("B", grower=("g1", "T")), _f("C", grower=("g2", "N"))])
    assert r.grower_count == 2


def test_fields_without_a_grower_are_not_counted_as_one():
    r = _report([_f("A", grower=None), _f("B", grower=None)])
    assert r.grower_count == 0


# ── Staleness ─────────────────────────────────────────────────────────────────


def test_an_old_observation_is_stale():
    r = _report([_f("A", days=STALE_AFTER_DAYS + 1)])
    assert len(r.stale_fields) == 1
    assert any("last observed more than" in q for q in r.qualifications)


def test_the_staleness_boundary_is_inclusive_of_the_threshold_day():
    r = _report([_f("A", days=STALE_AFTER_DAYS)])
    assert r.stale_fields == ()


def test_an_unobserved_field_is_not_also_reported_as_stale():
    # It would be counted twice in the qualifications, and "never seen" and
    # "seen a while ago" are different things a lender prices differently.
    r = _report([_f("A", score=None, band=None, urgency="awaiting_data", days=None)])
    assert r.stale_fields == ()
    assert len(r.unobserved_fields) == 1


# ── Scores and bands ──────────────────────────────────────────────────────────


def test_average_ignores_unscored_fields():
    r = _report([_f("A", score=80), _f("B", score=None, band=None, urgency="awaiting_data")])
    assert r.average_score == 80


def test_average_is_none_when_nothing_is_scored():
    # Not zero. Zero is a portfolio in crisis; None is a portfolio nobody has
    # looked at, and they call for opposite responses.
    r = _report([_f("A", score=None, band=None, urgency="awaiting_data")])
    assert r.average_score is None


def test_the_unweighted_average_is_disclosed():
    r = _report([_f("A", score=80)])
    assert any("unweighted by area" in q for q in r.qualifications)


def test_bands_omit_empty_ones_and_run_worst_first():
    r = _report([
        _f("A", band="critical", urgency="critical"),
        _f("B", band="good"),
        _f("C", band="good"),
    ])
    assert [b.band for b in r.bands] == ["critical", "good"]
    assert [b.fields for b in r.bands] == [1, 2]


def test_unscored_fields_get_no_band():
    # Inventing one would put a field nobody has looked at into a credit
    # assessment.
    r = _report([_f("A", score=None, band=None, urgency="awaiting_data")])
    assert r.bands == ()


# ── Districts ─────────────────────────────────────────────────────────────────


def test_districts_are_ordered_by_area():
    # A lender's first question is concentration: a portfolio in one district is
    # one weather event.
    r = _report([_f("A", 10, district="Mazowe"), _f("B", 50, district="Karoi")])
    assert [d.district for d in r.districts] == ["Karoi", "Mazowe"]


def test_a_missing_district_is_named_not_dropped():
    r = _report([_f("A", 10, district=None)])
    assert [d.district for d in r.districts] == ["Not recorded"]


def test_districts_report_how_much_of_themselves_is_observed():
    r = _report([
        _f("A", 10, district="Mazowe"),
        _f("B", 20, district="Mazowe", score=None, band=None, urgency="awaiting_data"),
    ])
    row = r.districts[0]
    assert row.fields == 2 and row.observed_fields == 1


# ── Attention list ────────────────────────────────────────────────────────────


def test_critical_sorts_above_high():
    r = _report([_f("A", urgency="high"), _f("B", urgency="critical")])
    assert [f.field_name for f in r.attention] == ["B", "A"]


def test_larger_fields_sort_first_within_an_urgency():
    # Two equally urgent fields are not equally expensive, and the reader is
    # deciding where to send a vehicle.
    r = _report([_f("A", 5, urgency="critical"), _f("B", 40, urgency="critical")])
    assert [f.field_name for f in r.attention] == ["B", "A"]


def test_healthy_fields_are_not_on_the_attention_list():
    r = _report([_f("A", urgency="low"), _f("B", urgency="medium")])
    assert r.attention == ()


# ── Anonymisation ─────────────────────────────────────────────────────────────


def test_anonymising_removes_grower_and_field_names():
    # The playbook: never publish grower-level data without written consent.
    # This document doubles as the demo shown in a prospect meeting.
    r = _report([_f("Home Field", grower=("g1", "Tariro Mhlanga"))], anonymise=True)
    names = {f.field_name for f in r.fields} | {f.grower_name for f in r.fields}
    assert "Home Field" not in names
    assert "Tariro Mhlanga" not in names


def test_anonymising_leaves_the_figures_alone():
    rows = [_f("A", 12.4, score=71)]
    plain, anon = _report(rows), _report(rows, anonymise=True)
    assert anon.hectares_observed == plain.hectares_observed
    assert anon.average_score == plain.average_score


def test_the_same_grower_gets_the_same_label_throughout():
    # "Grower C" must be the same grower on page 1 and page 4, or the document
    # is unreadable.
    r = _report(
        [_f("A", grower=("g1", "T")), _f("B", grower=("g2", "N")), _f("C", grower=("g1", "T"))],
        anonymise=True,
    )
    labels = [f.grower_name for f in r.fields]
    assert labels[0] == labels[2] != labels[1]


def test_labels_continue_past_twenty_six_growers():
    rows = [_f(f"F{i}", grower=(f"g{i}", f"N{i}")) for i in range(30)]
    labels = [f.grower_name for f in anonymise_rows(rows)]
    assert labels[25] == "Grower Z"
    assert labels[26] == "Grower AA"
    assert len(set(labels)) == 30


def test_the_client_name_is_replaced_too():
    # Anonymising the growers but leaving "Servemox" on the cover defeats it.
    r = _report([_f("A")], anonymise=True)
    assert r.client_name != "Servemox"


def test_the_document_says_it_has_been_anonymised():
    # A reader must never mistake labels for the real names of small growers.
    r = _report([_f("A")], anonymise=True)
    assert any("replaced with labels" in q for q in r.qualifications)


def test_a_normal_report_says_nothing_about_anonymisation():
    r = _report([_f("A")])
    assert not any("label" in q for q in r.qualifications)
    assert r.anonymised is False


def test_anonymising_keeps_the_districts_which_is_why_it_is_not_consent():
    # Deliberate: a lender needs the concentration picture, so districts stay.
    # It is also why anonymising is not permission — a contractor can often work
    # out whose book it is from the district mix alone. The module says so.
    r = _report([_f("A", district="Mazowe")], anonymise=True)
    assert r.fields[0].district == "Mazowe"


def test_fields_without_a_grower_stay_without_one_when_anonymised():
    # Inventing "Grower A" for a field with no grower would assert a
    # relationship that does not exist.
    r = _report([_f("A", grower=None)], anonymise=True)
    assert r.fields[0].grower_name is None
