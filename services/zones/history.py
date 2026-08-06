"""
Zone history across seasons — telling a soil problem apart from a bad year.
Pure computation, no I/O.

Why this exists
---------------
*"The North-East is stressed"* and *"the North-East has been the weakest part of
this field for three seasons running"* are different statements with different
price tags. The first is this week's weather or this season's management. The
second is a property of the ground — drainage, a compaction pan, shallower soil
— and it justifies spending money: a soil test, drainage work, variable-rate
input, or simply farming that corner differently.

Nothing in the product could distinguish them, because zone analysis had no
season attribution. It does now, so the comparison is finally possible.

The comparability constraint
----------------------------
**Zones are only comparable across seasons when the grid matches.** Zone 3 of a
2x2 is the south-west quarter; zone 3 of a 4x4 is somewhere in the north-west.
Comparing them by index would silently compare different pieces of ground and
report a trend that does not exist — the worst kind of bug here, because the
output looks plausible and a farmer might dig a drain because of it.

So seasons are grouped by grid size and only the largest comparable group is
analysed, with the skipped seasons reported rather than dropped silently.

The same caution applies to boundary edits, which the caller must handle:
history sampled from a different field shape is not this field's history.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional, Sequence

# How far below its field's mean a zone must sit, in a given season, to count
# as "behind" for that season. Matches the diagnosis threshold so one screen
# cannot call a zone weak while the other calls it fine.
BEHIND_THRESHOLD = 0.08

# A pattern needs at least this many comparable seasons before it is a pattern
# rather than a coincidence.
MIN_SEASONS_FOR_PATTERN = 2

# Fraction of comparable seasons a zone must be behind in to be called
# persistent. Two out of three is a pattern; one out of three is a bad year.
PERSISTENT_FRACTION = 0.66


@dataclass
class ZoneSeasonPoint:
    season_id: str
    season_label: Optional[str]
    ndvi: Optional[float]
    field_mean: Optional[float]
    gap: Optional[float]
    behind: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "season_id": self.season_id,
            "season_label": self.season_label,
            "ndvi": self.ndvi,
            "field_mean": self.field_mean,
            "gap": self.gap,
            "behind": self.behind,
        }


@dataclass
class ZoneTrack:
    index: int
    label: str
    seasons_compared: int
    seasons_behind: int
    verdict: str            # 'persistent' | 'occasional' | 'consistent' | 'insufficient'
    summary: str
    action: str
    points: List[ZoneSeasonPoint] = dc_field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "label": self.label,
            "seasons_compared": self.seasons_compared,
            "seasons_behind": self.seasons_behind,
            "verdict": self.verdict,
            "summary": self.summary,
            "action": self.action,
            "points": [p.to_dict() for p in self.points],
        }


def _mean(values: Sequence[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def comparable_batches(
    batches: Sequence[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split batches into the largest grid-consistent group, and the rest.

    Returns ``(comparable, skipped)``. Grouping by grid size is not a nicety:
    zone 3 of a 2x2 and zone 3 of a 4x4 are different pieces of ground, and
    comparing them would invent a trend.
    """
    by_grid: Dict[int, List[Dict[str, Any]]] = {}
    for b in batches or []:
        try:
            grid = int(b.get("grid_size"))
        except (TypeError, ValueError):
            continue
        by_grid.setdefault(grid, []).append(b)

    if not by_grid:
        return ([], list(batches or []))

    # Prefer the grid with the most seasons; break ties toward the finer grid,
    # which localises a problem more usefully.
    best_grid = max(by_grid, key=lambda g: (len(by_grid[g]), g))
    comparable = by_grid.pop(best_grid)
    skipped = [b for group in by_grid.values() for b in group]
    return (comparable, skipped)


def build_zone_history(
    batches: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Track each zone's standing within its own field, season over season.

    ``batches`` is one entry per season::

        {"season_id", "season_label", "grid_size",
         "zones": [{"index", "label", "ndvi"}, ...]}

    Each season's zones are judged against **that season's** field mean, never
    against an absolute NDVI or against another season's values. A dry year
    lowers every zone; what matters is whether the same corner keeps ending up
    at the bottom of its own field.
    """
    comparable, skipped = comparable_batches(batches)

    notes: List[str] = []
    if skipped:
        notes.append(
            f"{len(skipped)} season(s) were analysed with a different zone grid "
            f"and are not comparable — zone 3 of a 2×2 is not the same ground as "
            f"zone 3 of a 4×4."
        )

    if len(comparable) < MIN_SEASONS_FOR_PATTERN:
        return {
            "seasons_compared": len(comparable),
            "zones": [],
            "notes": notes + [
                "At least two seasons analysed on the same zone grid are needed "
                "before a pattern can be told apart from a bad year."
            ],
        }

    # Oldest first, so a farmer reads left to right through time.
    ordered = sorted(comparable, key=lambda b: str(b.get("season_label") or ""))

    tracks: Dict[int, ZoneTrack] = {}
    for batch in ordered:
        zones = batch.get("zones") or []
        field_mean = _mean([
            z.get("ndvi") for z in zones if z.get("ndvi") is not None
        ])

        for z in zones:
            index = int(z.get("index", -1))
            label = str(z.get("label") or f"Zone {index + 1}")
            raw = z.get("ndvi")
            try:
                ndvi = float(raw) if raw is not None else None
            except (TypeError, ValueError):
                ndvi = None

            gap = (
                round(field_mean - ndvi, 4)
                if (ndvi is not None and field_mean is not None) else None
            )
            behind = gap is not None and gap >= BEHIND_THRESHOLD

            track = tracks.setdefault(index, ZoneTrack(
                index=index, label=label, seasons_compared=0, seasons_behind=0,
                verdict="insufficient", summary="", action="",
            ))
            # Keep the most recent label — zone names are generated, and a
            # rename should not fragment the track.
            track.label = label
            track.points.append(ZoneSeasonPoint(
                season_id=str(batch.get("season_id") or ""),
                season_label=batch.get("season_label"),
                ndvi=round(ndvi, 4) if ndvi is not None else None,
                field_mean=field_mean,
                gap=gap,
                behind=behind,
            ))
            if ndvi is not None:
                track.seasons_compared += 1
                if behind:
                    track.seasons_behind += 1

    for track in tracks.values():
        if track.seasons_compared < MIN_SEASONS_FOR_PATTERN:
            track.verdict = "insufficient"
            track.summary = f"{track.label} has too few analysed seasons to judge."
            track.action = ""
            continue

        fraction = track.seasons_behind / track.seasons_compared
        if track.seasons_behind == 0:
            track.verdict = "consistent"
            track.summary = f"{track.label} has kept up with the field every season."
            track.action = ""
        elif fraction >= PERSISTENT_FRACTION:
            track.verdict = "persistent"
            track.summary = (
                f"{track.label} has been behind the rest of the field in "
                f"{track.seasons_behind} of {track.seasons_compared} seasons."
            )
            track.action = (
                "A patch that underperforms season after season is usually the "
                "ground, not the year — drainage, compaction or shallower soil. "
                "This is worth a soil test or digging an inspection pit before "
                "spending another season's inputs on it."
            )
        else:
            track.verdict = "occasional"
            track.summary = (
                f"{track.label} was behind in {track.seasons_behind} of "
                f"{track.seasons_compared} seasons, but not consistently."
            )
            track.action = (
                "One weak season in an otherwise normal patch is usually weather "
                "or something that happened that year, not the soil. Worth noting, "
                "not worth digging up."
            )

    # Worst first: most seasons behind, then the largest average gap.
    ordered_tracks = sorted(
        tracks.values(),
        key=lambda t: (
            -(t.seasons_behind / t.seasons_compared) if t.seasons_compared else 0,
            -(_mean([p.gap for p in t.points if p.gap is not None]) or 0),
        ),
    )

    persistent = [t for t in ordered_tracks if t.verdict == "persistent"]
    if persistent:
        notes.append(
            f"{len(persistent)} zone(s) have underperformed across seasons. Those "
            f"are the parts of this field where fixing the ground would pay back "
            f"every year, not just this one."
        )

    return {
        "seasons_compared": len(ordered),
        "zones": [t.to_dict() for t in ordered_tracks],
        "notes": notes,
    }
