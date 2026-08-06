"""
Field report assembly.

The centre of gravity here is the stand-check gap: the one absence the document
states rather than passes over in silence, because it changes how every zone
finding below it should be read.
"""

from datetime import date

import pytest

from services.documents.field_report import (
    FieldReport,
    StandCheck,
    ZoneFinding,
    build_field_report,
    zone_findings,
)


def _zone(label="Northeast one", severity="problem", causes=(), summary="Behind"):
    return {
        "label": label,
        "severity": severity,
        "summary": summary,
        "causes": list(causes),
        "action": "Walk it",
    }


def _report(**kw):
    base = dict(
        field_name="Home Field",
        coverage_start=date(2025, 11, 1),
        coverage_end=date(2026, 5, 31),
    )
    base.update(kw)
    return build_field_report(**base)


# ── The stand-check gap ───────────────────────────────────────────────────────


def test_a_missing_stand_check_is_stated_not_passed_over():
    # The finding this whole body of work started from. Sections otherwise
    # render only when they have content; this absence is the exception.
    r = _report()
    assert r.stand_check_gap is not None
    assert any("thin healthy stand" in q for q in r.qualifications)


def test_the_gap_explains_why_it_matters_rather_than_just_noting_it():
    # "No stand check recorded" tells a reader nothing they can act on. The
    # point is that it makes every zone finding below ambiguous.
    gap = _report().stand_check_gap
    assert "cannot tell" in gap
    assert "next season" in gap


def test_a_recorded_stand_check_removes_the_gap():
    r = _report(stand_check=StandCheck(date(2025, 12, 8), 44000.0, 41000.0))
    assert r.stand_check_gap is None
    assert not any("thin healthy stand" in q for q in r.qualifications)


def test_achieved_share_is_computed_from_target_and_established():
    check = StandCheck(date(2025, 12, 8), 44000.0, 33000.0)
    assert check.achieved_share == pytest.approx(0.75)


@pytest.mark.parametrize(
    "target,established",
    [(None, 41000.0), (44000.0, None), (0.0, 41000.0)],
)
def test_achieved_share_declines_rather_than_dividing_by_a_gap(target, established):
    # A target of zero is data entry gone wrong, not a field with no plants.
    assert StandCheck(date(2025, 12, 8), target, established).achieved_share is None


def test_a_half_recorded_stand_check_is_qualified():
    # Present but unusable. Silently showing nothing would look like the check
    # was never done, which is a different conversation with the farmer.
    r = _report(stand_check=StandCheck(date(2025, 12, 8), None, 41000.0))
    assert any("cannot be scored" in q for q in r.qualifications)


# ── Zones ─────────────────────────────────────────────────────────────────────


def test_healthy_zones_are_omitted():
    # Twelve zones of which ten say "ok" buries the two that matter, and the
    # farmer has already walked the field.
    r = _report(zones=[_zone("A", "ok"), _zone("B", "problem")])
    assert [z.label for z in r.reportable_zones] == ["B"]


def test_problems_sort_above_watches():
    r = _report(zones=[_zone("A", "watch"), _zone("B", "problem")])
    assert [z.severity for z in r.reportable_zones] == ["problem", "watch"]


def test_unknown_zones_are_not_reported_as_findings():
    # 'unknown' means the engine could not assess it. Listing it as a finding
    # would turn an absence of assessment into an assessment.
    r = _report(zones=[_zone("A", "unknown")])
    assert r.reportable_zones == ()


def test_a_zone_with_no_corroborated_cause_is_flagged_as_unexplained():
    # The zone engine names a cause only when something supports it. A weak zone
    # with no cause is a problem with no explanation, not an absence of problem.
    r = _report(zones=[_zone("A", "problem", causes=())])
    assert len(r.unexplained_zones) == 1
    assert any("nothing in the record to explain" in q for q in r.qualifications)


def test_an_explained_zone_is_not_flagged():
    r = _report(zones=[_zone("A", "problem", causes=("Shallow soil",))])
    assert r.unexplained_zones == ()


def test_unexplained_qualification_is_grammatical_in_the_plural():
    r = _report(zones=[_zone("A", "problem"), _zone("B", "problem")])
    note = next(q for q in r.qualifications if "explain" in q)
    assert "2 zones are behind" in note and "They are" in note


def test_zone_findings_accepts_diagnosis_objects_as_well_as_dicts():
    class FakeDiagnosis:
        def to_dict(self):
            return _zone("From object", "watch", causes=("Waterlogging",))

    findings = zone_findings([FakeDiagnosis(), _zone("From dict")])
    assert [f.label for f in findings] == ["From object", "From dict"]
    assert findings[0].causes == ("Waterlogging",)


def test_zone_findings_survives_missing_keys():
    # Route data has been through JSON and a schema change or two.
    findings = zone_findings([{"severity": "problem"}])
    assert findings[0].label == "Zone"
    assert findings[0].causes == ()


# ── Whether to issue at all ───────────────────────────────────────────────────


def test_a_report_with_nothing_in_it_is_not_worth_issuing():
    # The failure this guards: a document carrying a verification line and no
    # findings, which reads as a clean bill of health for a field nobody looked
    # at.
    assert not _report().has_content


def test_any_one_section_makes_it_worth_issuing():
    assert _report(zones=[_zone()]).has_content
    assert _report(execution_notes=["Urea broadcast on dry soil"]).has_content
    assert _report(stand_check=StandCheck(date(2025, 12, 8), 44000.0, 41000.0)).has_content


def test_zones_that_are_all_healthy_do_not_by_themselves_justify_a_report():
    # Nothing to say is nothing to send. `has_content` reads reportable zones,
    # not raw ones.
    assert not _report(zones=[_zone("A", "ok"), _zone("B", "ok")]).has_content


# ── Identity ──────────────────────────────────────────────────────────────────


def test_optional_identity_fields_stay_absent_rather_than_becoming_blanks():
    r = _report()
    assert r.grower_name is None and r.district is None and r.variety is None


def test_the_report_carries_its_coverage_period():
    r = _report()
    assert r.coverage_start == date(2025, 11, 1)
    assert r.coverage_end == date(2026, 5, 31)


def test_a_field_report_is_immutable():
    # Assembled once, rendered once. A mutable view model invites a template
    # that adjusts a figure on its way to the page.
    r = _report()
    with pytest.raises(Exception):
        r.field_name = "Something else"  # type: ignore[misc]


def test_zone_finding_is_immutable():
    z = ZoneFinding(label="A", severity="problem", summary="")
    with pytest.raises(Exception):
        z.severity = "ok"  # type: ignore[misc]


def test_field_report_type_is_exported_for_the_renderer():
    assert isinstance(_report(), FieldReport)
