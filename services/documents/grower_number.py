"""
TIMB grower numbers — normalisation, not validation.

Pure. Unit-tested in ``tests/test_grower_number.py``.

A Season Evidence Pack is only evidence if a buyer can reconcile it against
TIMB's own register. The join key for that is the grower's TIMB registration
number, so it has to be stored, and stored in a form that matches when compared.

.. warning::

   **This module deliberately does not validate the format.** TIMB's number
   format is not documented in anything reachable from here, and a regex written
   from a handful of examples would reject valid growers — which, in a system
   whose whole claim is traceability, means quietly dropping the growers whose
   numbers look unusual. The failure is silent and lands on the people least
   able to argue with it.

   So: normalise for comparison, reject only what cannot be an identifier at all
   (empty, or absurdly long), and store what the user typed. If someone obtains
   the real format from TIMB, tighten :func:`normalise_grower_number` then — and
   backfill-check the existing rows rather than rejecting on write.
"""

from __future__ import annotations

import re

#: Long enough for any plausible registration number plus a prefix, short enough
#: that a pasted paragraph is caught. Not a format claim.
MAX_LENGTH = 32

_COLLAPSE = re.compile(r"[\s ]+")

#: Separators people type into reference numbers. Removed for comparison only —
#: "M 12345/A" and "M12345/A" are the same grower, and a pack that lists them as
#: two is worse than one that lists neither.
_SEPARATORS = re.compile(r"[\s\-/.]")


class GrowerNumberError(ValueError):
    """Raised when a value cannot be a grower number at all."""


def normalise_grower_number(value: str | None) -> str | None:
    """
    Tidy a grower number for storage: trimmed, whitespace collapsed, uppercased.

    Returns ``None`` for absent or blank input — a grower without a TIMB number
    is a normal state (not every grower is a registered tobacco grower), and it
    must be distinguishable from one whose number is an empty string.

    Case is folded because these are read off a card and typed by different
    people; the character sequence is otherwise left alone.
    """
    if value is None:
        return None

    text = _COLLAPSE.sub(" ", value).strip()
    if not text:
        return None
    if len(text) > MAX_LENGTH:
        raise GrowerNumberError(
            f"grower number is {len(text)} characters; "
            f"more than {MAX_LENGTH} is not a registration number"
        )
    return text.upper()


def comparison_key(value: str | None) -> str | None:
    """
    The form to compare two grower numbers by.

    Strips separators as well as case, so a number written ``M-12345`` on one
    system and ``M12345`` on another resolves to the same grower. Used for
    matching and duplicate detection — never for display, which shows what the
    user actually entered.
    """
    normalised = normalise_grower_number(value)
    if normalised is None:
        return None
    key = _SEPARATORS.sub("", normalised)
    return key or None
