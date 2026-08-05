"""
Satellite history backfill planning — pure, no I/O.

The fetching itself lives in ``scripts/backfill_field_history.py``; this module
holds the decisions that are worth testing independently of the network:

* **Window chunking.** The Copernicus Statistics API will not return an
  arbitrarily long daily series in one response, so a multi-year request has to
  be split. Sentinel-2 imagery starts in 2015, so "as deep as needed" is real —
  a ten-year backfill is thirty-odd requests per field, and getting the chunk
  boundaries wrong silently drops or double-counts days.
* **Idempotency.** Re-running a backfill must add nothing. Existing dates are
  filtered out rather than upserted, so a re-run costs quota but never
  duplicates or overwrites an observation.
* **Season attribution.** Rows are tagged with the season that was running on
  the day they were captured, so backfilled history lands on the right season
  without a separate migration pass.

Pure by design: no DB, no network, fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# Days per Statistics API request. CDSE degrades on very long daily series, and
# a smaller window also means a failure costs less work to retry.
DEFAULT_WINDOW_DAYS = 180

# Sentinel-2A reached operational service in 2015; asking for imagery before
# then burns quota to receive nothing.
SENTINEL2_EPOCH = date(2015, 7, 1)


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


@dataclass(frozen=True)
class FetchWindow:
    """One Statistics API request's worth of time."""
    start: date
    end: date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    def as_iso(self) -> Tuple[str, str]:
        return (self.start.isoformat(), self.end.isoformat())


def plan_windows(
    start: Any,
    end: Any,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> List[FetchWindow]:
    """Split ``[start, end]`` into contiguous, non-overlapping fetch windows.

    Windows are returned **newest first**: if a backfill is interrupted or
    quota runs out, the farmer is left with the recent history that matters
    most rather than a decade of context and a missing current season.

    Clamped to the Sentinel-2 archive — requesting earlier costs quota and
    returns nothing.
    """
    s, e = _as_date(start), _as_date(end)
    if s is None or e is None or e < s:
        return []
    if window_days < 1:
        window_days = 1
    if s < SENTINEL2_EPOCH:
        s = SENTINEL2_EPOCH
    if e < s:
        return []

    windows: List[FetchWindow] = []
    cursor = s
    while cursor <= e:
        chunk_end = min(cursor + timedelta(days=window_days - 1), e)
        windows.append(FetchWindow(start=cursor, end=chunk_end))
        cursor = chunk_end + timedelta(days=1)

    windows.reverse()
    return windows


def plan_backfill_range(
    years: float,
    today: Optional[date] = None,
    earliest_season_planting: Any = None,
) -> Tuple[Optional[date], Optional[date]]:
    """Work out how far back to go.

    ``years`` is the requested depth. If the field has a recorded season older
    than that, the range is extended to cover it — a season the farmer told us
    about but that has no imagery would render as an empty line on the history
    chart, which reads as a bad season rather than an unobserved one.
    """
    end = today or date.today()
    start = end - timedelta(days=int(round(years * 365.25)))

    earliest = _as_date(earliest_season_planting)
    if earliest and earliest < start:
        start = earliest

    if start < SENTINEL2_EPOCH:
        start = SENTINEL2_EPOCH
    if start > end:
        return (None, None)
    return (start, end)


def select_new_rows(
    parsed: Iterable[Tuple[str, Optional[float], Optional[float], Optional[float]]],
    existing_dates: Sequence[str],
) -> List[Tuple[str, Optional[float], Optional[float], Optional[float]]]:
    """Drop days already stored, and any duplicate days within one response.

    Filtering rather than upserting is deliberate: a re-run must never overwrite
    an observation that ingestion already wrote, and must never create a second
    row for the same day.
    """
    have = set(existing_dates)
    out: List[Tuple[str, Optional[float], Optional[float], Optional[float]]] = []
    seen: set = set()
    for row in parsed:
        day = row[0]
        if not day or day in have or day in seen:
            continue
        seen.add(day)
        out.append(row)
    return out


def attribute_row_to_season(
    day: Any,
    seasons: Sequence[Dict[str, Any]],
) -> Optional[str]:
    """The id of the season running on ``day``, or None if none was.

    A day belongs to the season with the latest planting date at or before it.
    Backfilled rows predating every recorded season stay unattributed rather
    than being forced onto the oldest one.
    """
    d = _as_date(day)
    if not d:
        return None
    candidates = [
        (sid, planted)
        for sid, planted in (
            (str(s.get("id") or ""), _as_date(s.get("planting_date"))) for s in seasons
        )
        if sid and planted and planted <= d
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[1])[0]


def estimate_requests(windows_per_field: int, field_count: int) -> int:
    """Total Statistics API calls a run will make — the quota a run will cost.

    Surfaced before a run starts so a ten-year backfill across a large tenant
    is a deliberate choice rather than a surprise bill.
    """
    return max(0, windows_per_field) * max(0, field_count)
