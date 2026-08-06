"""
TIMB grower number normalisation.

The interesting property here is what this module *doesn't* do: it does not
validate the format. Several tests below exist to pin that down, because the
tempting change — adding a regex from a handful of real examples — silently
drops the growers whose numbers look unusual, and traceability that quietly
excludes people is worse than none.
"""

import pytest

from services.documents.grower_number import (
    GrowerNumberError,
    MAX_LENGTH,
    comparison_key,
    normalise_grower_number,
)


def test_absent_stays_absent():
    # A grower with no TIMB number is a normal state, not an error — not every
    # grower in the system is a registered tobacco grower.
    assert normalise_grower_number(None) is None


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_blank_normalises_to_none_not_empty_string(blank):
    # An empty string in the column would be indistinguishable from a real
    # number in a NOT NULL check and would print as a blank cell in a pack.
    assert normalise_grower_number(blank) is None


def test_case_is_folded():
    # Read off a card and typed by different people at different offices.
    assert normalise_grower_number("m12345a") == "M12345A"


def test_surrounding_whitespace_is_trimmed():
    assert normalise_grower_number("  M12345  ") == "M12345"


def test_internal_whitespace_is_collapsed_not_removed():
    # Collapsed, because a double space is a typo; not removed, because the
    # space may be part of how the number is actually printed.
    assert normalise_grower_number("M 12345") == "M 12345"
    assert normalise_grower_number("M    12345") == "M 12345"


def test_absurdly_long_input_is_rejected():
    with pytest.raises(GrowerNumberError, match="not a registration number"):
        normalise_grower_number("X" * (MAX_LENGTH + 1))


def test_length_limit_is_inclusive():
    assert normalise_grower_number("X" * MAX_LENGTH) == "X" * MAX_LENGTH


@pytest.mark.parametrize(
    "unusual",
    [
        "M12345",          # letter prefix
        "12345678",        # bare digits
        "M-12345/A",       # separators
        "ZW/M/12345",      # a scheme we have not seen
        "0001",            # leading zeros, short
    ],
)
def test_unusual_shapes_are_accepted_because_the_format_is_not_documented(unusual):
    # This is the load-bearing test of the module. Every one of these would be
    # rejected by a plausible regex, and we cannot verify TIMB's real format
    # from here. Storing an odd number costs nothing; rejecting a valid grower
    # drops them out of the traceability the pack claims to provide.
    assert normalise_grower_number(unusual) is not None


# ── Comparison ────────────────────────────────────────────────────────────────


def test_separators_are_ignored_when_comparing():
    # The same grower entered on two systems. A pack that lists them as two
    # growers is worse than one that lists neither.
    assert comparison_key("M-12345") == comparison_key("M12345")
    assert comparison_key("M 12345") == comparison_key("m12345")
    assert comparison_key("ZW/M/12345") == comparison_key("ZWM12345")


def test_comparison_key_does_not_conflate_different_numbers():
    assert comparison_key("M12345") != comparison_key("M12346")


def test_comparison_key_of_absent_is_none():
    assert comparison_key(None) is None
    assert comparison_key("  ") is None


def test_a_value_of_only_separators_compares_as_absent():
    # "---" is not a grower number; it must not become the empty-string key that
    # every other separator-only entry would also match.
    assert comparison_key("---") is None


def test_display_value_keeps_what_was_entered():
    # comparison_key strips separators; the stored/displayed value must not.
    assert normalise_grower_number("M-12345") == "M-12345"
