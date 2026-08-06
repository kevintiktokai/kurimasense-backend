"""
Document identity: issue numbers and the verification line.

The verification line is the one string in this codebase that a leaf buyer or a
bank acts on directly, so most of what is tested here is what it *refuses* to
say.
"""

from datetime import date, datetime, timezone

import pytest

from services.documents.identity import (
    CoverageError,
    DocumentIdentity,
    format_hectares,
    issue_number,
    parse_issue_number,
    verification_line,
)


# ── Issue numbers ─────────────────────────────────────────────────────────────


def test_issue_number_is_quotable_down_a_phone_line():
    stamp = datetime(2026, 8, 6, tzinfo=timezone.utc)
    assert issue_number("evidence_pack", 143, stamp) == "EP-2026-000143"


def test_issue_number_prefix_identifies_the_kind_on_sight():
    stamp = datetime(2026, 8, 6, tzinfo=timezone.utc)
    prefixes = {
        issue_number(kind, 1, stamp).split("-")[0]
        for kind in ("evidence_pack", "portfolio_report", "field_report", "season_plan")
    }
    # Four kinds, four distinct prefixes — a folder of these is sortable by eye.
    assert len(prefixes) == 4


def test_unknown_kind_is_refused_rather_than_given_a_default_prefix():
    with pytest.raises(ValueError, match="unknown document kind"):
        issue_number("invoice", 1)


def test_sequence_must_be_positive():
    with pytest.raises(ValueError, match="sequence must be positive"):
        issue_number("evidence_pack", 0)


def test_issue_number_round_trips():
    stamp = datetime(2026, 8, 6, tzinfo=timezone.utc)
    value = issue_number("field_report", 7, stamp)
    assert parse_issue_number(value) == ("field_report", 2026, 7)


def test_issue_number_parses_case_insensitively():
    # Someone will type it back in lowercase from a phone note.
    assert parse_issue_number("ep-2026-000143")[0] == "evidence_pack"


@pytest.mark.parametrize("bad", ["EP-2026-143", "XX-2026-000143", "nonsense", ""])
def test_malformed_issue_numbers_are_rejected(bad):
    with pytest.raises(ValueError):
        parse_issue_number(bad)


# ── The verification line ─────────────────────────────────────────────────────


def test_verification_line_states_period_and_hectares():
    line = verification_line(date(2025, 11, 1), date(2026, 5, 31), 214.0)
    assert line == "Verified by KurimaSense · 1 November 2025 to 31 May 2026 · 214 ha"


def test_no_coverage_period_refuses_rather_than_omitting_it():
    # The failure this guards: a line reading "Verified by KurimaSense · 214 ha"
    # with no period, which asserts open-ended coverage.
    with pytest.raises(CoverageError, match="no coverage period"):
        verification_line(None, date(2026, 5, 31), 214.0)
    with pytest.raises(CoverageError, match="no coverage period"):
        verification_line(date(2025, 11, 1), None, 214.0)


def test_no_hectare_figure_refuses():
    with pytest.raises(CoverageError, match="no hectare figure"):
        verification_line(date(2025, 11, 1), date(2026, 5, 31), None)


def test_backwards_period_refuses_rather_than_silently_swapping():
    # Swapping them would produce a plausible line from a caller that has its
    # dates the wrong way round — and hide the bug that caused it.
    with pytest.raises(CoverageError, match="runs backwards"):
        verification_line(date(2026, 5, 31), date(2025, 11, 1), 214.0)


def test_zero_hectares_refuses():
    with pytest.raises(CoverageError):
        verification_line(date(2025, 11, 1), date(2026, 5, 31), 0.0)


def test_single_day_coverage_is_allowed():
    # Degenerate but honest: a document covering one observation date.
    line = verification_line(date(2026, 1, 5), date(2026, 1, 5), 12.0)
    assert "5 January 2026 to 5 January 2026" in line


def test_dates_are_unambiguous_across_locales():
    # 5/6/2026 means two different days in Harare and in New York. These
    # documents cross both, so the month is spelled.
    line = verification_line(date(2026, 6, 5), date(2026, 6, 5), 20.0)
    assert "5 June 2026" in line


# ── Hectare precision ─────────────────────────────────────────────────────────


def test_large_areas_are_not_printed_to_a_precision_imagery_cannot_support():
    # 214.37 ha invites a buyer to check it against a cadastral record and find
    # it wrong; satellite-derived boundaries do not justify two decimals.
    assert format_hectares(214.37) == "214 ha"


def test_small_areas_keep_a_decimal():
    # At 2 ha, rounding to whole hectares loses half the smallholder's field.
    assert format_hectares(2.4) == "2.4 ha"


def test_large_areas_are_thousands_separated():
    assert format_hectares(12450.0) == "12,450 ha"


# ── The identity object ───────────────────────────────────────────────────────


def test_identity_exposes_the_line_it_would_print():
    identity = DocumentIdentity(
        kind="evidence_pack",
        issue_number="EP-2026-000143",
        issued_at=datetime(2026, 8, 6, tzinfo=timezone.utc),
        subject="Servemox",
        coverage_start=date(2025, 11, 1),
        coverage_end=date(2026, 5, 31),
        hectares=214.0,
    )
    assert identity.verification_line.endswith("214 ha")


def test_identity_without_coverage_raises_rather_than_returning_a_partial_line():
    identity = DocumentIdentity(
        kind="field_report",
        issue_number="FR-2026-000001",
        issued_at=datetime(2026, 8, 6, tzinfo=timezone.utc),
        subject="Home Field",
        coverage_start=None,
        coverage_end=None,
        hectares=None,
    )
    with pytest.raises(CoverageError):
        _ = identity.verification_line
