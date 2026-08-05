"""
Season-over-season history — pure computation, no I/O.

Turns a field's seasons plus their satellite observations into **comparable**
curves and a plain-language read on whether this field is getting better or
worse.

Why days-after-planting, not calendar dates
-------------------------------------------
A maize crop planted on 15 November and one planted on 2 December are at
completely different growth stages on any given calendar day, so plotting them
against dates compares a six-leaf crop with a tasselling one and calls the
difference "performance". Re-indexing every season to **days after its own
planting date** is what makes the comparison mean anything — it lines the
seasons up by crop age, which is the only axis on which two seasons are the
same thing.

That re-indexing is also what surfaces the finding farmers actually act on:
*"you planted nine days earlier and hit peak canopy eleven days sooner"* is a
decision for next season. *"NDVI was 0.71 on 3 January"* is not.

Pure by design: no DB, no network, fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence

# Below this, a "peak" is noise rather than a canopy — bare soil sits around
# 0.15-0.2, so a season whose best observation is under this never established
# a canopy worth comparing.
MIN_MEANINGFUL_NDVI = 0.25

# A season with fewer observations than this can still be shown, but its peak
# is not trustworthy enough to drive a comparison (cloud can hide the real one).
MIN_OBS_FOR_CONFIDENT_PEAK = 5


def _as_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f == f else None  # NaN check


@dataclass
class HistoryPoint:
    """One observation, re-indexed to the age of the crop."""
    date: str
    days_after_planting: int
    ndvi: Optional[float]
    evi: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "days_after_planting": self.days_after_planting,
            "ndvi": self.ndvi,
            "evi": self.evi,
        }


@dataclass
class SeasonHistory:
    """One season's comparable curve plus the facts worth comparing."""
    season_id: str
    season_label: Optional[str]
    crop_type: Optional[str]
    variety: Optional[str]
    status: Optional[str]
    planting_date: Optional[str]
    points: List[HistoryPoint] = dc_field(default_factory=list)

    peak_ndvi: Optional[float] = None
    days_to_peak: Optional[int] = None
    mean_ndvi: Optional[float] = None
    observation_count: int = 0
    peak_is_confident: bool = False

    target_population_per_ha: Optional[int] = None
    established_population_per_ha: Optional[int] = None
    yield_tonnes_per_ha: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "season_id": self.season_id,
            "season_label": self.season_label,
            "crop_type": self.crop_type,
            "variety": self.variety,
            "status": self.status,
            "planting_date": self.planting_date,
            "points": [p.to_dict() for p in self.points],
            "peak_ndvi": self.peak_ndvi,
            "days_to_peak": self.days_to_peak,
            "mean_ndvi": self.mean_ndvi,
            "observation_count": self.observation_count,
            "peak_is_confident": self.peak_is_confident,
            "target_population_per_ha": self.target_population_per_ha,
            "established_population_per_ha": self.established_population_per_ha,
            "yield_tonnes_per_ha": self.yield_tonnes_per_ha,
        }


@dataclass
class FieldHistory:
    field_id: str
    seasons: List[SeasonHistory] = dc_field(default_factory=list)
    comparisons: List[str] = dc_field(default_factory=list)
    trend: str = "unknown"   # 'unknown' | 'improving' | 'stable' | 'declining'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "seasons": [s.to_dict() for s in self.seasons],
            "comparisons": self.comparisons,
            "trend": self.trend,
        }


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------
def align_observations(
    planting_date: Any,
    observations: Sequence[Dict[str, Any]],
) -> List[HistoryPoint]:
    """Re-index observations to days after planting, oldest first.

    Observations before the planting date are dropped: they belong to whatever
    was in the field previously, and including them would show a phantom canopy
    at "day -20" that never belonged to this crop.
    """
    planted = _as_date(planting_date)
    if not planted:
        return []

    points: List[HistoryPoint] = []
    for obs in observations:
        obs_date = _as_date(obs.get("log_date") or obs.get("date"))
        if not obs_date:
            continue
        dap = (obs_date - planted).days
        if dap < 0:
            continue
        points.append(
            HistoryPoint(
                date=obs_date.isoformat(),
                days_after_planting=dap,
                ndvi=_as_float(obs.get("ndvi")),
                evi=_as_float(obs.get("evi")),
            )
        )
    points.sort(key=lambda p: p.days_after_planting)
    return points


def summarise_season(
    season: Dict[str, Any],
    observations: Sequence[Dict[str, Any]],
) -> SeasonHistory:
    """Build one season's comparable curve and its headline facts."""
    points = align_observations(
        season.get("planting_date") or season.get("planned_planting_date"),
        observations,
    )

    hist = SeasonHistory(
        season_id=str(season.get("id") or ""),
        season_label=season.get("season_label"),
        crop_type=season.get("crop_type"),
        variety=season.get("variety"),
        status=season.get("status"),
        planting_date=(
            _as_date(season.get("planting_date")).isoformat()
            if _as_date(season.get("planting_date")) else None
        ),
        points=points,
        target_population_per_ha=season.get("target_population_per_ha"),
        established_population_per_ha=season.get("established_population_per_ha"),
        yield_tonnes_per_ha=_as_float(season.get("yield_tonnes_per_ha")),
    )

    ndvis = [(p.ndvi, p.days_after_planting) for p in points if p.ndvi is not None]
    hist.observation_count = len(ndvis)
    if ndvis:
        peak_value, peak_day = max(ndvis, key=lambda x: x[0])
        hist.mean_ndvi = round(sum(v for v, _ in ndvis) / len(ndvis), 3)
        if peak_value >= MIN_MEANINGFUL_NDVI:
            hist.peak_ndvi = round(peak_value, 3)
            hist.days_to_peak = peak_day
            hist.peak_is_confident = len(ndvis) >= MIN_OBS_FOR_CONFIDENT_PEAK
    return hist


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def _compare_pair(current: SeasonHistory, previous: SeasonHistory) -> List[str]:
    """Plain-language deltas between two seasons, only where they're meaningful."""
    lines: List[str] = []

    # Yield is the outcome that matters, so it leads when both are known.
    if current.yield_tonnes_per_ha is not None and previous.yield_tonnes_per_ha is not None:
        delta = round(current.yield_tonnes_per_ha - previous.yield_tonnes_per_ha, 2)
        if abs(delta) >= 0.1:
            direction = "more" if delta > 0 else "less"
            lines.append(
                f"{current.season_label or 'This season'} yielded {abs(delta)} t/ha "
                f"{direction} than {previous.season_label or 'the season before'}."
            )

    # Only compare canopy when both peaks are trustworthy — a cloud-thinned
    # season can look like a bad one when it was merely unobserved.
    if (
        current.peak_ndvi is not None and previous.peak_ndvi is not None
        and current.peak_is_confident and previous.peak_is_confident
    ):
        d = round(current.peak_ndvi - previous.peak_ndvi, 3)
        if abs(d) >= 0.05:
            lines.append(
                f"Peak canopy was {'stronger' if d > 0 else 'weaker'} "
                f"({current.peak_ndvi} vs {previous.peak_ndvi})."
            )
        if current.days_to_peak is not None and previous.days_to_peak is not None:
            dd = current.days_to_peak - previous.days_to_peak
            if abs(dd) >= 7:
                lines.append(
                    f"It reached that peak {abs(dd)} days "
                    f"{'earlier' if dd < 0 else 'later'} in the crop's life."
                )

    # Establishment is the lever the farmer controls, so name it explicitly
    # whenever both seasons measured it.
    if (
        current.established_population_per_ha is not None
        and previous.established_population_per_ha is not None
    ):
        d = current.established_population_per_ha - previous.established_population_per_ha
        if abs(d) >= 2000:
            lines.append(
                f"You established {abs(d):,} plants/ha "
                f"{'more' if d > 0 else 'fewer'} than last season."
            )
    return lines


def _trend(seasons: Sequence[SeasonHistory]) -> str:
    """Is this field improving across seasons, regardless of what was planted?

    Uses yield where enough seasons record it, else confident peak NDVI. Both
    are compared oldest-half against newest-half rather than first-vs-last, so
    one exceptional season doesn't set the verdict.
    """
    def _trend_from(values: List[float], threshold: float) -> Optional[str]:
        if len(values) < 2:
            return None
        mid = len(values) // 2
        older, newer = values[:mid] or values[:1], values[mid:]
        older_avg = sum(older) / len(older)
        newer_avg = sum(newer) / len(newer)
        delta = newer_avg - older_avg
        if abs(delta) < threshold:
            return "stable"
        return "improving" if delta > 0 else "declining"

    # Oldest first for the halves to mean what they say.
    ordered = list(reversed(list(seasons)))

    yields = [s.yield_tonnes_per_ha for s in ordered if s.yield_tonnes_per_ha is not None]
    verdict = _trend_from([y for y in yields], 0.3)
    if verdict:
        return verdict

    peaks = [s.peak_ndvi for s in ordered if s.peak_ndvi is not None and s.peak_is_confident]
    verdict = _trend_from([p for p in peaks], 0.05)
    return verdict or "unknown"


def group_observations_by_season(
    seasons: Sequence[Dict[str, Any]],
    observations: Sequence[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Attribute observations to seasons by date, newest-planting-first.

    An observation belongs to the season with the **latest planting date at or
    before** it. Deriving this from dates rather than trusting ``season_id``
    keeps history correct for rows that predate the backfill, for seasons
    created retrospectively, and for any row the activation path never touched —
    all cases where a stored ``season_id`` is absent rather than wrong.
    """
    dated = [
        (sid, planted)
        for sid, planted in (
            (str(s.get("id") or ""), _as_date(s.get("planting_date"))) for s in seasons
        )
        if sid and planted
    ]
    # Newest planting first, so the first match is the most recent season that
    # had already started when the observation was taken.
    dated.sort(key=lambda x: x[1], reverse=True)

    grouped: Dict[str, List[Dict[str, Any]]] = {sid: [] for sid, _ in dated}
    for obs in observations:
        obs_date = _as_date(obs.get("log_date") or obs.get("date"))
        if not obs_date:
            continue
        for sid, planted in dated:
            if obs_date >= planted:
                grouped[sid].append(obs)
                break
        # Observations older than every season belong to a season we have no
        # record of, and are simply dropped.
    return grouped


def build_field_history(
    field_id: str,
    seasons: Sequence[Dict[str, Any]],
    observations_by_season: Dict[str, List[Dict[str, Any]]],
) -> FieldHistory:
    """Assemble a field's season-over-season history, newest season first.

    ``observations_by_season`` maps season id → its daily_logs rows. Seasons
    with no planting date are skipped entirely: without one there is no crop
    age, so nothing can be aligned or compared.
    """
    histories: List[SeasonHistory] = []
    for season in seasons:
        if not _as_date(season.get("planting_date")):
            continue
        sid = str(season.get("id") or "")
        histories.append(summarise_season(season, observations_by_season.get(sid, [])))

    # Newest first — the season a farmer cares about most is the current one.
    histories.sort(key=lambda h: h.planting_date or "", reverse=True)

    history = FieldHistory(field_id=field_id, seasons=histories)
    if len(histories) >= 2:
        history.comparisons = _compare_pair(histories[0], histories[1])
    history.trend = _trend(histories)
    return history
