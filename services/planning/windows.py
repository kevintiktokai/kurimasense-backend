"""
Action windows — the operations that close, and what missing them costs.

Pure computation, no I/O.

Why this exists
---------------
The plan is currently a flat list of tasks, all rendered the same. But several
of the costliest mistakes in a season are **time-boxed and irreversible**, and
the research is specific about the numbers:

* **Weed competition.** The critical period runs roughly 4-6 weeks after
  emergence, and competition inside it causes *irreversible* loss. Iowa State
  puts the slope at weeds 4" → 2% loss, 6" → 6%, 12" → **22%**. Weeding a week
  late is not "a late task", it is a permanent deduction that grows nonlinearly.
* **Nitrogen leaching.** Zimbabwean sandy loams lose **29-40 kg N/ha** from the
  top 40 cm within two weeks under heavy rain, so top-dress timing relative to
  rain decides whether the fertiliser feeds the crop or the water table.
* **Establishment.** Assessed in a ~2-week window after emergence or not at all;
  after that the season's ceiling is unknown and unrecoverable.

A farmer with forty things to do does not need a longer list. They need to know
which three are irreversible this week. That is what this module computes.

Design
------
Windows are derived from the crop profile's ``growth_stages`` and
``fertilizer_schedule`` where possible, so every crop in the knowledge base gets
them, with research-backed constants filling the gaps the profiles do not model
(the critical weed period is not a growth stage).

Ranking is by **cost per remaining day**, not by date: a cheap task closing
tomorrow should not outrank a costly one closing next week.

.. warning::
   The yield-cost percentages are compiled from extension research and are
   pending agronomist sign-off before farmer-facing release.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

# Emergence is roughly a week after planting for most field crops. Used only
# where a season has no recorded emergence date.
ASSUMED_DAYS_TO_EMERGENCE = 7

# Critical period of weed competition, in days after emergence. Competition
# inside this window causes irreversible loss; outside it the crop's canopy
# suppresses weeds well enough that late weeding is cosmetic.
WEED_CRITICAL_START = 0
WEED_CRITICAL_END = 42

# Establishment can only be assessed while replacements could still catch up.
STAND_CHECK_WINDOW_DAYS = 21
GAP_FILL_WINDOW_DAYS = 14


@dataclass
class ActionWindow:
    """One time-boxed operation, with the cost of missing it."""
    key: str
    title: str
    category: str            # establishment | weed | nutrition | protection
    opens_day: int           # days after planting
    closes_day: int
    irreversible: bool
    cost_pct: Optional[float]        # yield loss if missed, percent
    cost_of_missing: str             # farmer-facing phrasing
    why: str
    stage_code: Optional[str] = None
    opens_date: Optional[str] = None
    closes_date: Optional[str] = None
    days_remaining: Optional[int] = None
    state: str = "upcoming"          # upcoming | open | closing | closed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "category": self.category,
            "opens_day": self.opens_day,
            "closes_day": self.closes_day,
            "irreversible": self.irreversible,
            "cost_pct": self.cost_pct,
            "cost_of_missing": self.cost_of_missing,
            "why": self.why,
            "stage_code": self.stage_code,
            "opens_date": self.opens_date,
            "closes_date": self.closes_date,
            "days_remaining": self.days_remaining,
            "state": self.state,
        }


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


# ---------------------------------------------------------------------------
# Window construction
# ---------------------------------------------------------------------------
def _establishment_windows(emergence_offset: int, already_checked: bool) -> List[ActionWindow]:
    if already_checked:
        return []
    return [
        ActionWindow(
            key="stand_check",
            title="Count your stand",
            category="establishment",
            opens_day=emergence_offset,
            closes_day=emergence_offset + STAND_CHECK_WINDOW_DAYS,
            irreversible=True,
            cost_pct=None,
            cost_of_missing="This season's ceiling stays unknown",
            why=(
                "Plant population sets the ceiling for the whole season and cannot "
                "be measured once the canopy closes. Without it, a thin stand and a "
                "stressed one look identical from satellite — and they need opposite "
                "actions."
            ),
        ),
        ActionWindow(
            key="gap_fill",
            title="Gap-fill thin patches",
            category="establishment",
            opens_day=emergence_offset,
            closes_day=emergence_offset + GAP_FILL_WINDOW_DAYS,
            irreversible=True,
            cost_pct=5.0,
            cost_of_missing="Gaps stay for the season",
            why=(
                "A replacement planted within about two weeks of emergence can still "
                "catch up. After that it is shaded out by its neighbours and often "
                "ends up barren, so it adds cost without adding yield."
            ),
        ),
    ]


def _weed_window(emergence_offset: int) -> ActionWindow:
    return ActionWindow(
        key="critical_weeding",
        title="Keep the crop weed-free",
        category="weed",
        opens_day=emergence_offset + WEED_CRITICAL_START,
        closes_day=emergence_offset + WEED_CRITICAL_END,
        irreversible=True,
        cost_pct=22.0,
        cost_of_missing="Up to 22% of yield, permanently",
        why=(
            "This is the critical period of weed competition. Yield lost to weeds "
            "now is never recovered, even if the field is cleaned later, and the "
            "loss grows fast: weeds at 4 inches cost about 2%, at 6 inches about "
            "6%, at 12 inches about 22%."
        ),
    )


def _nutrition_windows(profile: Any, leaching_soil: bool) -> List[ActionWindow]:
    """Top-dress windows, dated from the crop's own fertiliser schedule."""
    from .fertiliser import build_fertiliser_programme

    programme = build_fertiliser_programme(profile)
    windows: List[ActionWindow] = []

    for step in programme.steps:
        if step.key not in ("top_dress_1", "top_dress_2"):
            continue
        if step.days_after_planting is None:
            continue
        if step.optional and step.key == "top_dress_2" and not leaching_soil:
            continue

        first = step.key == "top_dress_1"
        why = (
            "Nitrogen demand peaks during rapid vegetative growth and ear-size "
            "determination. Applied late, the crop has already set fewer sites to "
            "fill."
            if first else
            "The second split carries the crop through grain fill."
        )
        if leaching_soil:
            why += (
                " On sandy soil this is also a timing decision against the rain: "
                "29-40 kg N/ha can leach past the roots within two weeks of heavy "
                "rainfall, so applying just before steady rain feeds the crop and "
                "applying just before a downpour feeds the water table."
            )

        windows.append(
            ActionWindow(
                key=step.key,
                title=f"{'First' if first else 'Second'} top-dress",
                category="nutrition",
                opens_day=step.days_after_planting,
                # Two weeks of usefulness after the window opens; past that the
                # growth it would have fed has already happened.
                closes_day=step.days_after_planting + 14,
                irreversible=False,
                cost_pct=12.0 if first else 6.0,
                cost_of_missing=(
                    "Yield potential the crop cannot make up later"
                    if first else "Reduced grain fill"
                ),
                why=why,
                stage_code=step.stage_code,
            )
        )
    return windows


def _stage_risk_windows(profile: Any) -> List[ActionWindow]:
    """Scouting windows for stages the profile flags as risky.

    The crop profiles already record per-stage ``risks`` and ``key_activities``;
    this turns the riskiest ones into dated scouting prompts instead of prose
    nobody reads.
    """
    windows: List[ActionWindow] = []
    for stage in getattr(profile, "growth_stages", None) or []:
        risks = getattr(stage, "risks", None) or []
        if not risks:
            continue
        try:
            start, end = int(stage.day_range[0]), int(stage.day_range[1])
        except (AttributeError, TypeError, ValueError, IndexError):
            continue
        windows.append(
            ActionWindow(
                key=f"scout_{getattr(stage, 'stage_code', '') or start}",
                title=f"Scout during {getattr(stage, 'stage_name', 'this stage')}",
                category="protection",
                opens_day=start,
                closes_day=end,
                irreversible=False,
                cost_pct=None,
                cost_of_missing="Problems caught late cost more to fix",
                why="; ".join(str(r) for r in risks[:2]),
                stage_code=getattr(stage, "stage_code", None),
            )
        )
    return windows


# ---------------------------------------------------------------------------
# Assembly and ranking
# ---------------------------------------------------------------------------
def _annotate(window: ActionWindow, planting: Optional[date], today: date) -> ActionWindow:
    """Attach real dates, days remaining, and the window's state."""
    days_since_planting = (today - planting).days if planting else None

    if planting:
        window.opens_date = (planting + timedelta(days=window.opens_day)).isoformat()
        window.closes_date = (planting + timedelta(days=window.closes_day)).isoformat()

    if days_since_planting is None:
        window.state = "upcoming"
        return window

    if days_since_planting < window.opens_day:
        window.state = "upcoming"
        window.days_remaining = window.closes_day - days_since_planting
    elif days_since_planting > window.closes_day:
        window.state = "closed"
        window.days_remaining = 0
    else:
        remaining = window.closes_day - days_since_planting
        window.days_remaining = remaining
        window.state = "closing" if remaining <= 7 else "open"
    return window


def urgency_score(window: ActionWindow) -> float:
    """Cost per remaining day — the ranking that matches how a farmer should act.

    Ranking by date alone puts a cheap task closing tomorrow above a costly one
    closing next week, which is exactly the prioritisation that loses yield.
    Irreversible windows carry a multiplier because a reversible miss can be
    made up and an irreversible one cannot.
    """
    if window.state == "closed":
        return 0.0
    cost = window.cost_pct if window.cost_pct is not None else 5.0
    if window.irreversible:
        cost *= 2.0
    remaining = window.days_remaining if window.days_remaining is not None else 30
    # +1 avoids a divide-by-zero on the last day and keeps the curve smooth.
    return round(cost / max(1, remaining + 1), 3)


def build_action_windows(
    profile: Any,
    *,
    planting_date: Any = None,
    emergence_date: Any = None,
    soil_texture: Optional[str] = None,
    stand_already_checked: bool = False,
    today: Optional[date] = None,
    include_closed: bool = False,
) -> List[Dict[str, Any]]:
    """Every action window for a season, ranked most-urgent first.

    Returns dicts ready for the API. Closed windows are dropped unless
    ``include_closed`` — a farmer cannot act on them, and showing them is what
    turns a plan into noise.
    """
    from .fertiliser import _is_leaching_soil

    planted = _as_date(planting_date)
    emerged = _as_date(emergence_date)
    now = today or date.today()

    # Prefer the real emergence date; fall back to a typical offset.
    if planted and emerged:
        emergence_offset = max(0, (emerged - planted).days)
    else:
        emergence_offset = ASSUMED_DAYS_TO_EMERGENCE

    leaching = _is_leaching_soil(soil_texture)

    windows: List[ActionWindow] = []
    windows.extend(_establishment_windows(emergence_offset, stand_already_checked))
    windows.append(_weed_window(emergence_offset))
    windows.extend(_nutrition_windows(profile, leaching))
    windows.extend(_stage_risk_windows(profile))

    annotated = [_annotate(w, planted, now) for w in windows]
    if not include_closed:
        annotated = [w for w in annotated if w.state != "closed"]

    annotated.sort(key=lambda w: (-urgency_score(w), w.closes_day))
    return [w.to_dict() for w in annotated]
