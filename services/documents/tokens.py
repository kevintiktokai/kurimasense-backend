"""
Brand tokens for generated documents.

A document produced here leaves the client's building. The playbook is explicit
about what that means:

    Every artefact that leaves a client's building carries a discreet
    KurimaSense mark and a single line: verified by KurimaSense, with the
    coverage period and hectare count.

Once it has been forwarded to a leaf buyer or a bank it cannot be re-rendered or
corrected, so consistency has to be structural rather than a matter of whoever
writes the next template remembering the hex codes. Everything visual in
``services/documents`` reads from here and nothing hardcodes a colour or a size.

**Mirrors the app, deliberately.** The values below are the same ones in
``kurima-sense/app/globals.css`` (``--ee-primary``, ``--ee-text``, ``--ee-muted``
and friends). A document and a screen have to look like the same product; if
these two drift, the document stops corroborating the app.

**Print is not screen**, though, so this is a mirror and not a copy:

* The app's neumorphic shadows (``--shadow-neu``) are absent. They render as
  grey mud on paper and as nothing at all through a fax-quality scan, which is
  how some of these documents will actually be read. Documents get flat rules,
  hairlines and tints instead.
* Sizes are in **points against a baseline grid**, not rem against a viewport.
  A4 does not resize.
* Tints are derived from the brand hues rather than picked, so a table zebra
  stripe and a callout background are provably the same family.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# ── Palette ───────────────────────────────────────────────────────────────────
#
# Mirrored from the app's `:root` custom properties. Names match the CSS
# variable they came from so a drift is greppable in both repos.

PRIMARY: Final = "#0fb885"  # --ee-primary   brand green, used as signal not wash
TEXT: Final = "#2D3A30"  # --ee-text      body copy
MUTED: Final = "#8B9D8F"  # --ee-muted     labels, captions, secondary rows
BG: Final = "#F4F1ED"     # --ee-bg        warm paper tone
SURFACE: Final = "#FFFFFF"  # --ee-surface
SUN: Final = "#E8A365"    # --ee-sun       warning / attention
WATER: Final = "#5C9EAD"  # --ee-water     water, irrigation
LOAM: Final = "#0E1A14"   # --ee-loam      institutional dark, cover pages
CLAY: Final = "#C8A98A"   # --ee-clay      warm neutral

#: Nothing on a KurimaSense document is pure black. Rules and hairlines are the
#: text colour at low opacity, flattened against paper — black rules read as
#: cheap, and against the warm background they read as a printer artefact.
RULE: Final = "#D8D5CF"
HAIRLINE: Final = "#E6E3DE"

#: Reserved for genuine problems — a missed window, an unexplained shortfall.
#: Not used for "below target", which is information rather than an alarm.
ALERT: Final = "#B4483C"


def tint(hex_colour: str, strength: float, *, on: str = SURFACE) -> str:
    """
    A brand hue mixed down towards the paper it sits on.

    ``strength`` is how much of the hue survives: ``1.0`` is the hue itself,
    ``0.0`` is the background. Table stripes, callout panels and chart fills all
    come from here so they are demonstrably the same family as the ink, which is
    what stops a document looking like several documents.

    Mixing towards ``on`` rather than towards white matters: these documents sit
    on a warm paper tone, and a hue mixed with pure white on a warm ground reads
    as a slightly cold patch.
    """
    if not 0.0 <= strength <= 1.0:
        raise ValueError(f"strength must be in [0, 1], got {strength}")

    fg = _parse_hex(hex_colour)
    bg = _parse_hex(on)
    mixed = tuple(
        round(f * strength + b * (1.0 - strength)) for f, b in zip(fg, bg)
    )
    return "#{:02X}{:02X}{:02X}".format(*mixed)


def _parse_hex(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    if len(text) != 6:
        raise ValueError(f"not a hex colour: {value!r}")
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError as exc:  # pragma: no cover - message clarity only
        raise ValueError(f"not a hex colour: {value!r}") from exc


# ── Typography ────────────────────────────────────────────────────────────────
#
# The app's faces, bundled as files in `fonts/` rather than linked, because a
# document must render identically on a server with no network and no fonts
# installed. Both are SIL OFL 1.1; the licences ship beside them.

FONT_HEADING: Final = "Fraunces"
FONT_BODY: Final = "Hanken Grotesk"

#: Fallbacks that exist on essentially any Linux host. If the bundled files ever
#: fail to load the document degrades to something readable rather than to
#: whatever the renderer picks, which on a bare container is a font with no
#: bold weight.
FONT_HEADING_FALLBACK: Final = "DejaVu Serif, Georgia, serif"
FONT_BODY_FALLBACK: Final = "DejaVu Sans, Helvetica, sans-serif"


@dataclass(frozen=True)
class TypeStep:
    """One step of the document type scale. Points, because the page is fixed."""

    size_pt: float
    leading_pt: float
    weight: int
    tracking_em: float = 0.0


#: A scale in points on a 4 pt baseline grid. Screen `rem` steps do not survive
#: the trip to A4 — a 14 px body becomes uncomfortably small at print density,
#: and a screen h1 becomes a poster. These are set for the page.
#:
#: Body is 9.5 pt: smaller than a book, because these documents are dense tables
#: read at a desk, and larger than the 8 pt that agricultural paperwork usually
#: defaults to, because a lot of them are read as a scan or a phone photo.
SCALE: Final[dict[str, TypeStep]] = {
    "display": TypeStep(size_pt=30.0, leading_pt=34.0, weight=600, tracking_em=-0.015),
    "title": TypeStep(size_pt=20.0, leading_pt=24.0, weight=600, tracking_em=-0.01),
    "section": TypeStep(size_pt=13.0, leading_pt=16.0, weight=600),
    "subsection": TypeStep(size_pt=10.5, leading_pt=14.0, weight=600),
    "body": TypeStep(size_pt=9.5, leading_pt=14.0, weight=400),
    "table": TypeStep(size_pt=8.5, leading_pt=12.0, weight=400),
    "label": TypeStep(size_pt=7.5, leading_pt=10.0, weight=600, tracking_em=0.06),
    "caption": TypeStep(size_pt=7.5, leading_pt=10.0, weight=400),
    "footer": TypeStep(size_pt=7.0, leading_pt=9.0, weight=400),
}

#: The grid everything vertical is a multiple of.
BASELINE_PT: Final = 4.0


def space(units: float) -> str:
    """
    Vertical space as a multiple of the baseline, formatted for CSS.

    Templates say ``space(4)`` rather than ``16pt`` so that changing the grid
    changes the whole document rather than the places someone remembered.
    """
    value = units * BASELINE_PT
    return f"{value:g}pt"


# ── Page ──────────────────────────────────────────────────────────────────────

#: A4, not Letter. These documents are filed in Harare, Lilongwe and London.
PAGE_SIZE: Final = "A4"

#: Generous outer margins, a deeper foot. The footer carries the verification
#: line and the document ID on every page — that furniture needs room, and it
#: needs to survive a hole-punch and a staple in a contractor's file.
MARGIN_TOP: Final = "18mm"
MARGIN_BOTTOM: Final = "20mm"
MARGIN_SIDE: Final = "16mm"
