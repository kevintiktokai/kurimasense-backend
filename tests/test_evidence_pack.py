"""
Season Evidence Pack assembly.

Almost everything here tests a refusal to overstate. The pack is forwarded to a
leaf buyer and acted on; the playbook rates a data controversy as existential.
So the interesting assertions are about what the pack declines to count, what it
puts on the cover rather than burying, and what it orders unflatteringly.
"""

from datetime import date

from services.documents.evidence_pack import (
    THEME_ADEQUATE_SHARE,
    EvidencePack,
    FieldEvidence,
    GrowerEvidence,
    build_evidence_pack,
    build_theme_coverage,
)

ALL_THEMES = frozenset(
    {"land_use", "soil", "crop_protection", "good_agricultural_practice"}
)


def _field(name="F", ha=10.0, observed=True, themes=ALL_THEMES):
    return FieldEvidence(
        field_id=name.lower(),
        field_name=name,
        hectares=ha,
        crop="Tobacco",
        observed=observed,
        themes=themes,
    )


def _grower(name="Tariro", timb="M12345", fields=None):
    return GrowerEvidence(
        grower_id=name.lower(),
        grower_name=name,
        timb_grower_number=timb,
        fields=tuple(fields if fields is not None else [_field()]),
    )


def _pack(growers) -> EvidencePack:
    return build_evidence_pack(
        client_name="Servemox",
        coverage_start=date(2025, 11, 1),
        coverage_end=date(2026, 5, 31),
        growers=growers,
    )


# ── Traceability ──────────────────────────────────────────────────────────────


def test_a_grower_with_a_timb_number_is_traceable():
    assert _grower(timb="M12345").is_traceable


def test_a_grower_without_one_is_not():
    assert not _grower(timb=None).is_traceable


def test_a_blank_timb_number_does_not_count_as_traceable():
    # The failure this guards: an empty string in the column reading as present
    # and inflating the headline traceability figure.
    assert not _grower(timb="   ").is_traceable


def test_untraceable_growers_are_reported_not_hidden():
    pack = _pack([_grower("A", timb="M1"), _grower("B", timb=None)])
    assert pack.grower_count == 2
    assert len(pack.traceable_growers) == 1
    assert len(pack.untraceable_growers) == 1


def test_untraceable_growers_are_listed_first():
    # Deliberately unflattering. The gaps are what someone can fix before
    # sending; sorted alphabetically they end up on page four.
    pack = _pack([_grower("Anna", timb="M1"), _grower("Zvi", timb=None)])
    assert [g.grower_name for g in pack.growers] == ["Zvi", "Anna"]


def test_traceable_growers_are_ordered_alphabetically_among_themselves():
    pack = _pack([_grower("Zvi", timb="M2"), _grower("Anna", timb="M1")])
    assert [g.grower_name for g in pack.growers] == ["Anna", "Zvi"]


# ── Coverage hectares ─────────────────────────────────────────────────────────


def test_covered_hectares_counts_only_observed_ground():
    # The verification line is generated from this number. A field the satellite
    # never saw is not covered, whatever the contract says it is.
    pack = _pack([_grower(fields=[_field("A", 10), _field("B", 30, observed=False)])])
    assert pack.covered_hectares == 10
    assert pack.total_hectares == 40


def test_a_field_with_no_area_does_not_break_the_sum():
    pack = _pack([_grower(fields=[_field("A", None), _field("B", 12)])])
    assert pack.covered_hectares == 12


def test_unobserved_fields_are_enumerated():
    pack = _pack([_grower(fields=[_field("A"), _field("B", observed=False)])])
    assert [f.field_name for f in pack.unobserved_fields] == ["B"]


# ── Theme coverage ────────────────────────────────────────────────────────────


def test_a_theme_evidenced_everywhere_is_covered():
    themes = build_theme_coverage([_field(), _field()])
    assert all(t.status == "covered" for t in themes)


def test_a_theme_with_no_evidence_is_absent_not_omitted():
    # A buyer has to be able to tell "we checked and it's fine" from "we didn't
    # check". Omitting the theme makes those two look identical.
    themes = build_theme_coverage([_field(themes=frozenset())])
    assert {t.status for t in themes} == {"absent"}


def test_a_partly_evidenced_theme_is_partial():
    fields = [_field("A", themes=ALL_THEMES)] + [
        _field(f"F{i}", themes=frozenset()) for i in range(3)
    ]
    soil = next(t for t in build_theme_coverage(fields) if t.theme == "soil")
    assert soil.status == "partial"
    assert soil.fields_with_evidence == 1 and soil.fields_total == 4


def test_the_adequacy_threshold_is_inclusive():
    n = 10
    keep = round(THEME_ADEQUATE_SHARE * n)
    fields = [_field(f"y{i}", themes=ALL_THEMES) for i in range(keep)] + [
        _field(f"n{i}", themes=frozenset()) for i in range(n - keep)
    ]
    soil = next(t for t in build_theme_coverage(fields) if t.theme == "soil")
    assert soil.status == "covered"


def test_no_fields_is_not_applicable_rather_than_zero_percent():
    # No fields means the question was never asked. Reporting 0% would claim we
    # looked and found nothing.
    themes = build_theme_coverage([])
    assert {t.status for t in themes} == {"not_applicable"}
    assert all(t.share is None for t in themes)


def test_theme_coverage_counts_unobserved_fields_against_the_total():
    # Counting only observed fields would let a pack covering a tenth of the
    # ground report full coverage of every theme.
    fields = [_field("A", themes=ALL_THEMES), _field("B", observed=False, themes=frozenset())]
    soil = next(t for t in build_theme_coverage(fields) if t.theme == "soil")
    assert soil.fields_total == 2


def test_every_theme_has_a_readable_label():
    for theme in build_theme_coverage([_field()]):
        assert theme.label != theme.theme


# ── Duplicates ────────────────────────────────────────────────────────────────


def test_duplicate_timb_numbers_are_surfaced():
    pack = _pack([_grower("A", timb="M12345"), _grower("B", timb="M12345")])
    assert len(pack.duplicate_grower_numbers) == 1


def test_duplicates_are_detected_across_separator_differences():
    # Entered as M-12345 on one system and M12345 on another. A pack listing
    # them as two growers is worse than one listing neither.
    pack = _pack([_grower("A", timb="M-12345"), _grower("B", timb="m12345")])
    assert len(pack.duplicate_grower_numbers) == 1


def test_growers_without_numbers_are_not_treated_as_duplicates_of_each_other():
    pack = _pack([_grower("A", timb=None), _grower("B", timb=None)])
    assert pack.duplicate_grower_numbers == ()


# ── Qualifications ────────────────────────────────────────────────────────────


def test_a_complete_pack_carries_no_qualifications():
    pack = _pack([_grower("A", timb="M1"), _grower("B", timb="M2")])
    assert pack.qualifications == ()
    assert pack.is_complete


def test_missing_timb_numbers_are_qualified_on_the_cover():
    pack = _pack([_grower("A", timb="M1"), _grower("B", timb=None)])
    assert any("no TIMB number" in q for q in pack.qualifications)
    assert not pack.is_complete


def test_unobserved_ground_is_qualified_with_its_hectares():
    pack = _pack([_grower(fields=[_field("A", 10), _field("B", 30, observed=False)])])
    note = next(q for q in pack.qualifications if "not observed" in q)
    assert "30 ha" in note


def test_qualifications_are_grammatical_in_the_singular():
    # "1 fields were not observed" on a document going to a multinational reads
    # as software nobody proofread — and a reader who doubts the care taken over
    # the sentence doubts the care taken over the number.
    pack = _pack([
        _grower("A", timb=None, fields=[_field("F", 10, observed=False)]),
        _grower("B", timb="M2"),
    ])
    joined = " ".join(pack.qualifications)
    assert "1 field " in joined and "1 fields" not in joined
    assert "1 of 2 growers has" in joined


def test_qualifications_are_grammatical_in_the_plural():
    pack = _pack([
        _grower("A", timb=None, fields=[_field("F", 10, observed=False), _field("G", 5, observed=False)]),
        _grower("B", timb=None),
        _grower("C", timb="M3"),
    ])
    joined = " ".join(pack.qualifications)
    assert "2 fields" in joined and "were not observed" in joined
    assert "2 of 3 growers have" in joined


def test_a_partial_theme_is_qualified_with_its_counts():
    fields = [_field("A", themes=ALL_THEMES)] + [
        _field(f"F{i}", themes=frozenset()) for i in range(3)
    ]
    pack = _pack([_grower(fields=fields)])
    assert any("1 of 4 fields" in q for q in pack.qualifications)


def test_duplicates_are_qualified_as_needing_resolution_before_sending():
    pack = _pack([_grower("A", timb="M1"), _grower("B", timb="M1")])
    note = next(q for q in pack.qualifications if "before this pack is sent" in q)
    assert "1 TIMB number appears" in note


def test_a_pack_is_not_complete_merely_because_every_grower_is_traceable():
    # The trap: full traceability, but half the ground never looked at.
    pack = _pack([_grower("A", timb="M1", fields=[_field("F", 10, observed=False)])])
    assert not pack.is_complete


def test_an_empty_pack_is_not_reported_as_complete():
    # Zero growers, zero hectares, nothing observed. Every count is consistent
    # and the pack claims nothing — but "complete" would read as verified.
    pack = _pack([])
    assert not pack.is_complete
    assert pack.covered_hectares == 0
