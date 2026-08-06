"""
Document identity — the mark, the verification line, and the issue number.

Pure. Unit-tested in ``tests/test_documents_identity.py``.

This module exists because of one sentence in the strategy:

    Every artefact that leaves a client's building carries a discreet
    KurimaSense mark and a single line: verified by KurimaSense, with the
    coverage period and hectare count.

That line is the entire commercial mechanism. A contractor forwards an evidence
pack to a leaf buyer; the buyer reads a claim about hectares and a period, and
the only thing that makes it a claim rather than a decoration is that it can be
brought back to a specific document that was issued on a specific day covering
specific ground.

So the line is generated, never typed, and it is generated from the same values
the document body was built from.

.. warning::

   The verification line asserts coverage. It must therefore never be produced
   from a hectare figure or a date range that the document did not actually
   report on — :func:`verification_line` refuses to render rather than round,
   estimate, or fill a gap. A document that overstates its own coverage is worse
   than no document, because it is the artefact a buyer relies on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone

#: How the mark reads. Lowercase "verified by" deliberately: the playbook asks
#: for discreet, and a shouted claim on someone else's paperwork reads as
#: marketing, which is the thing that gets a document thrown away.
MARK: str = "KurimaSense"

#: Prefixes are per document kind so that an issue number is legible on sight —
#: a contractor with a folder of these can tell an evidence pack from a field
#: report without opening either.
KIND_PREFIXES: dict[str, str] = {
    "evidence_pack": "EP",
    "portfolio_report": "PR",
    "field_report": "FR",
    "season_plan": "SP",
}


class CoverageError(ValueError):
    """Raised when a document cannot honestly state what it covers."""


@dataclass(frozen=True)
class DocumentIdentity:
    """Everything printed in the page furniture, resolved once per render."""

    kind: str
    issue_number: str
    issued_at: datetime
    subject: str
    """Who the document is about — client, grower or field name."""
    coverage_start: date | None
    coverage_end: date | None
    hectares: float | None

    @property
    def verification_line(self) -> str:
        return verification_line(
            self.coverage_start, self.coverage_end, self.hectares
        )


def issue_number(
    kind: str, sequence: int, issued_at: datetime | None = None
) -> str:
    """
    A human-quotable document number: ``EP-2026-000143``.

    Deliberately **not** a UUID. This number gets read down a phone line by an
    agronomist standing in a field, and written on the top of a printout by
    someone in a leaf buyer's compliance office. A UUID cannot survive either.

    The year is the issue year, not the season year: this identifies the piece of
    paper, and the paper's coverage period is stated separately on it. Two
    documents about the same season issued in different years are two documents.
    """
    prefix = KIND_PREFIXES.get(kind)
    if prefix is None:
        raise ValueError(
            f"unknown document kind {kind!r}; "
            f"known kinds: {', '.join(sorted(KIND_PREFIXES))}"
        )
    if sequence < 1:
        raise ValueError(f"sequence must be positive, got {sequence}")

    stamp = issued_at or datetime.now(timezone.utc)
    return f"{prefix}-{stamp.year}-{sequence:06d}"


_ISSUE_RE = re.compile(r"^(?P<prefix>[A-Z]{2})-(?P<year>\d{4})-(?P<seq>\d{6})$")


def parse_issue_number(value: str) -> tuple[str, int, int]:
    """
    Read an issue number back to ``(kind, year, sequence)``.

    The inverse of :func:`issue_number`, and the reason the format is fixed
    width: someone will paste one of these into a support conversation, and it
    has to be resolvable without a lookup table.
    """
    match = _ISSUE_RE.match(value.strip().upper())
    if not match:
        raise ValueError(f"not a KurimaSense issue number: {value!r}")

    prefix = match.group("prefix")
    for kind, known in KIND_PREFIXES.items():
        if known == prefix:
            return kind, int(match.group("year")), int(match.group("seq"))
    raise ValueError(f"unknown document prefix {prefix!r} in {value!r}")


def verification_line(
    coverage_start: date | None,
    coverage_end: date | None,
    hectares: float | None,
) -> str:
    """
    The single line the playbook asks for, or an explicit refusal.

    Three things have to be true before this reads as verification rather than a
    logo: the period must be real, the period must run forwards, and the hectare
    figure must be one the document actually covered. Missing any of them,
    :exc:`CoverageError` is raised — the caller's job is then to render the
    document *without* a verification line, not to invent one.

    That is the whole point. A pack that says "verified over 214 ha" when 40 of
    those hectares were never observed is the single artefact most likely to end
    the company, because it is the one a buyer acts on.
    """
    if coverage_start is None or coverage_end is None:
        raise CoverageError(
            "no coverage period — a verification line cannot state a period "
            "the document does not cover"
        )
    if coverage_end < coverage_start:
        raise CoverageError(
            f"coverage period runs backwards: {coverage_start} to {coverage_end}"
        )
    if hectares is None:
        raise CoverageError(
            "no hectare figure — a verification line cannot state an area the "
            "document did not measure"
        )
    if hectares <= 0:
        raise CoverageError(f"hectares must be positive, got {hectares}")

    period = f"{_fmt(coverage_start)} to {_fmt(coverage_end)}"
    return f"Verified by {MARK} · {period} · {format_hectares(hectares)}"


def format_hectares(hectares: float) -> str:
    """
    Hectares at a precision the measurement actually supports.

    Satellite-derived boundaries are not accurate to the square metre, and a
    figure printed as ``214.37 ha`` invites a buyer to check it against a
    cadastral record and find it wrong. Below 10 ha one decimal; above, whole
    hectares — the resolution the underlying imagery justifies.
    """
    if hectares < 10:
        return f"{hectares:.1f} ha"
    return f"{round(hectares):,} ha"


def _fmt(value: date) -> str:
    """``6 August 2026`` — unambiguous across the UK, US and Zimbabwe at once."""
    return f"{value.day} {value.strftime('%B %Y')}"
