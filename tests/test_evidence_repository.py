"""
Gathering evidence for a pack.

The SQL needs a database; the grouping and the theme mapping do not, and they
are where the mistakes would be invisible. The load-bearing one is `land_use`:
nothing in this database evidences it, and the pack must say so rather than
infer it from having a boundary.
"""

import pytest

from services.documents.evidence_repository import (
    EVIDENCEABLE_THEMES,
    _themes_for,
    group_rows,
)


def _row(**kw):
    base = dict(
        field_id="f-1", field_name="Home Field", hectares=12.4, crop="Tobacco",
        grower_id="g-1", grower_name="Tariro", timb_grower_number="M12345",
        observed=True, has_soil=True, has_protection=True, has_practice=True,
    )
    base.update(kw)
    return base


# ── Themes ────────────────────────────────────────────────────────────────────


def test_land_use_is_never_evidenced():
    # The load-bearing assertion of this module. Nothing here evidences land use
    # and deforestation, and it is the theme a leaf buyer opens the pack for.
    # Inferring it from a boundary would turn "we have a polygon" into "we
    # checked for deforestation" — the most dangerous line in the document.
    assert "land_use" not in _themes_for(_row())
    assert "land_use" not in EVIDENCEABLE_THEMES


def test_a_fully_evidenced_field_carries_the_three_themes_we_can_source():
    assert _themes_for(_row()) == EVIDENCEABLE_THEMES


def test_each_flag_maps_to_exactly_one_theme():
    assert _themes_for(_row(has_protection=False, has_practice=False)) == {"soil"}
    assert _themes_for(_row(has_soil=False, has_practice=False)) == {"crop_protection"}
    assert _themes_for(_row(has_soil=False, has_protection=False)) == {
        "good_agricultural_practice"
    }


def test_a_field_with_no_evidence_carries_no_themes():
    assert _themes_for(
        _row(has_soil=False, has_protection=False, has_practice=False)
    ) == frozenset()


# ── Grouping ──────────────────────────────────────────────────────────────────


def test_one_grower_with_two_fields_is_one_grower():
    growers = group_rows([
        _row(field_id="f-1", field_name="A"),
        _row(field_id="f-2", field_name="B"),
    ])
    assert len(growers) == 1
    assert [f.field_name for f in growers[0].fields] == ["A", "B"]


def test_two_growers_stay_separate():
    growers = group_rows([
        _row(grower_id="g-1", grower_name="Tariro"),
        _row(grower_id="g-2", grower_name="Nyasha", field_id="f-2"),
    ])
    assert {g.grower_name for g in growers} == {"Tariro", "Nyasha"}


def test_fields_with_no_grower_are_kept_and_named():
    # Dropping them would make the pack's hectare figure disagree with the
    # portfolio report's for reasons no reader could see. Naming the bucket
    # makes the gap itself visible.
    growers = group_rows([_row(grower_id=None, grower_name=None, timb_grower_number=None)])
    assert len(growers) == 1
    assert growers[0].grower_name == "Not assigned to a grower"
    assert growers[0].timb_grower_number is None


def test_an_unassigned_bucket_is_never_treated_as_traceable():
    # It has no TIMB number by construction, so it must not inflate the pack's
    # traceable count.
    growers = group_rows([_row(grower_id=None, grower_name=None, timb_grower_number="M1")])
    assert not growers[0].is_traceable


def test_unassigned_fields_do_not_merge_into_a_real_grower():
    growers = group_rows([
        _row(grower_id="g-1", field_id="f-1"),
        _row(grower_id=None, grower_name=None, field_id="f-2"),
    ])
    assert len(growers) == 2


def test_the_observed_flag_survives_grouping():
    # It decides covered hectares, which the verification line states.
    growers = group_rows([
        _row(field_id="f-1", observed=True),
        _row(field_id="f-2", observed=False),
    ])
    assert growers[0].covered_hectares == pytest.approx(12.4)
    assert growers[0].total_hectares == pytest.approx(24.8)


def test_a_null_area_does_not_break_grouping():
    growers = group_rows([_row(hectares=None)])
    assert growers[0].covered_hectares == 0


def test_a_non_numeric_area_is_treated_as_absent_rather_than_raising():
    # Route data has been through a driver and a schema change or two.
    growers = group_rows([_row(hectares="not a number")])
    assert growers[0].fields[0].hectares is None


def test_missing_names_fall_back_rather_than_rendering_blank():
    growers = group_rows([_row(field_name=None)])
    assert growers[0].fields[0].field_name == "Field"


def test_no_rows_yields_no_growers():
    # The route turns this into a 422 — a pack covering nothing would still
    # carry a mark.
    assert group_rows([]) == ()
