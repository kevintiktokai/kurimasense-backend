"""
Season retrospective — where the yield gap went. Pure, no I/O.

Answers the question a farmer actually wants at the end of a season: *"I got
4.2 t/ha and the variety says 6.5. Where did the other 2.3 go?"*

This is the artefact most likely to make a farmer renew, and it is only possible
now that establishment is measured — you cannot attribute a gap to a thin stand
you never counted.

The honesty rule
----------------
**Nothing is attributed without evidence.** Yield attribution is genuinely
uncertain: weather, soil variability, pest pressure and management all interact,
and a decomposition that adds up to exactly 100% is a decomposition that has
been fudged. So this module:

* attributes a shortfall **only** to factors it has a measurement for;
* caps each factor at what the evidence supports;
* reports whatever is left over as **unexplained**, explicitly and without
  apology.

An honest "0.8 t/ha we can't account for" is worth more than a tidy full
breakdown a farmer will disbelieve the moment one line looks wrong — and the
research is explicit that farmers discount advice they cannot interrogate.

.. warning::
   The attribution coefficients are compiled from extension research and are
   pending agronomist sign-off before farmer-facing release.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence

# Below this fraction of target, a stand is thin enough to be worth naming as a
# cause. Above it, plant-to-plant compensation absorbs the difference.
STAND_ATTRIBUTION_THRESHOLD = 0.95

# Uneven emergence costs beyond the plant count: late plants are shaded out by
# earlier neighbours and often end up barren. Extension data puts a three-week
# emergence spread at 20%+ on its own.
EMERGENCE_PENALTY = {"poor": 0.15, "moderate": 0.07, "uniform": 0.0}

# A gap smaller than this is noise, not a finding worth reporting.
MIN_REPORTABLE_GAP_T_HA = 0.15


@dataclass
class GapFactor:
    """One evidenced contributor to the yield gap."""
    key: str
    label: str
    tonnes_per_ha: float
    evidence: str
    controllable: bool
    next_season: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "tonnes_per_ha": self.tonnes_per_ha,
            "evidence": self.evidence,
            "controllable": self.controllable,
            "next_season": self.next_season,
        }


@dataclass
class Retrospective:
    season_id: str
    crop_type: Optional[str]
    variety: Optional[str]
    actual_yield_t_ha: Optional[float]
    potential_yield_t_ha: Optional[float]
    gap_t_ha: Optional[float]
    factors: List[GapFactor] = dc_field(default_factory=list)
    unexplained_t_ha: Optional[float] = None
    headline: str = ""
    notes: List[str] = dc_field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "season_id": self.season_id,
            "crop_type": self.crop_type,
            "variety": self.variety,
            "actual_yield_t_ha": self.actual_yield_t_ha,
            "potential_yield_t_ha": self.potential_yield_t_ha,
            "gap_t_ha": self.gap_t_ha,
            "factors": [f.to_dict() for f in self.factors],
            "unexplained_t_ha": self.unexplained_t_ha,
            "headline": self.headline,
            "notes": self.notes,
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


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def _stand_factor(season: Dict[str, Any], potential: float) -> Optional[GapFactor]:
    """Yield lost to a stand that never reached its target population."""
    target = season.get("target_population_per_ha")
    established = season.get("established_population_per_ha")
    if not target or not established:
        return None

    achieved = established / target
    if achieved >= STAND_ATTRIBUTION_THRESHOLD:
        return None

    # Non-linear, matching the Stand Check's compensation curve: a 70% stand
    # does not cost 30% of yield, because surviving plants compensate. Treating
    # it as linear would overstate the loss and push farmers toward replants
    # that cost more than they recover.
    shortfall = 1 - achieved
    loss_fraction = shortfall * 0.55
    tonnes = round(potential * loss_fraction, 2)
    if tonnes < MIN_REPORTABLE_GAP_T_HA:
        return None

    return GapFactor(
        key="thin_stand",
        label="Thin stand at establishment",
        tonnes_per_ha=tonnes,
        evidence=(
            f"You established {established:,} plants/ha against a "
            f"{target:,} target — {achieved * 100:.0f}% of plan."
        ),
        controllable=True,
        next_season=(
            "Check seed rate, planting depth and soil moisture at planting. "
            "Run the Stand Check within two weeks of emergence so a thin stand "
            "can still be gap-filled."
        ),
    )


def _emergence_factor(season: Dict[str, Any], potential: float) -> Optional[GapFactor]:
    """Yield lost to uneven emergence, over and above the plant count."""
    uniformity = (season.get("emergence_uniformity") or "").strip().lower()
    penalty = EMERGENCE_PENALTY.get(uniformity, 0.0)
    if penalty <= 0:
        return None

    tonnes = round(potential * penalty, 2)
    if tonnes < MIN_REPORTABLE_GAP_T_HA:
        return None

    return GapFactor(
        key="uneven_emergence",
        label="Uneven emergence",
        tonnes_per_ha=tonnes,
        evidence=f"Emergence was recorded as {uniformity}.",
        controllable=True,
        next_season=(
            "Uniform depth and soil moisture at planting are what buy even "
            "emergence. Plants that come up a week late are shaded out by their "
            "neighbours and often carry no head at all."
        ),
    )


def _late_topdress_factor(
    season: Dict[str, Any],
    potential: float,
    late_topdress_days: Optional[int],
) -> Optional[GapFactor]:
    """Yield lost to nitrogen that arrived after the crop needed it."""
    if late_topdress_days is None or late_topdress_days <= 7:
        return None

    # Roughly 1% of potential per week late, capped — beyond a month the crop
    # has set its yield components and more nitrogen cannot buy them back.
    weeks_late = late_topdress_days / 7.0
    loss_fraction = min(0.12, weeks_late * 0.02)
    tonnes = round(potential * loss_fraction, 2)
    if tonnes < MIN_REPORTABLE_GAP_T_HA:
        return None

    return GapFactor(
        key="late_topdress",
        label="Late top-dressing",
        tonnes_per_ha=tonnes,
        evidence=f"Nitrogen went on about {late_topdress_days} days after the window opened.",
        controllable=True,
        next_season=(
            "Nitrogen demand peaks during rapid vegetative growth. Applied after "
            "that, the crop has already set fewer sites to fill, and the "
            "fertiliser cannot buy them back."
        ),
    )


def build_retrospective(
    season: Dict[str, Any],
    *,
    potential_yield_t_ha: Optional[float] = None,
    late_topdress_days: Optional[int] = None,
) -> Retrospective:
    """Decompose a finished season's yield gap into evidenced factors.

    ``potential_yield_t_ha`` is the realistic ceiling for this variety in this
    environment — the comparison basis. Without it no gap can be computed, and
    the retrospective says so rather than inventing a benchmark.
    """
    actual = _as_float(season.get("yield_tonnes_per_ha"))
    potential = _as_float(potential_yield_t_ha)

    retro = Retrospective(
        season_id=str(season.get("id") or ""),
        crop_type=season.get("crop_type"),
        variety=season.get("variety"),
        actual_yield_t_ha=actual,
        potential_yield_t_ha=potential,
        gap_t_ha=None,
    )

    if actual is None:
        retro.headline = "No harvest was recorded for this season, so there is nothing to compare."
        retro.notes.append("Record your harvest to unlock the retrospective.")
        return retro

    if potential is None:
        retro.headline = f"You harvested {actual} t/ha."
        retro.notes.append(
            "No realistic ceiling is known for this variety and environment, so "
            "the shortfall cannot be broken down."
        )
        return retro

    gap = round(potential - actual, 2)
    retro.gap_t_ha = gap

    if gap <= MIN_REPORTABLE_GAP_T_HA:
        retro.headline = (
            f"You harvested {actual} t/ha against a {potential} t/ha ceiling — "
            f"essentially the full potential of this crop."
        )
        retro.notes.append(
            "Whatever you did this season, it is worth repeating. The record of "
            "how you managed it is kept with the season."
        )
        return retro

    for factor in (
        _stand_factor(season, potential),
        _emergence_factor(season, potential),
        _late_topdress_factor(season, potential, late_topdress_days),
    ):
        if factor:
            retro.factors.append(factor)

    # Never claim more than the gap itself. If the evidenced factors exceed it,
    # the coefficients are overstating rather than the farmer having done worse
    # than they did — scale back rather than report a negative remainder.
    attributed = round(sum(f.tonnes_per_ha for f in retro.factors), 2)
    if attributed > gap and attributed > 0:
        scale = gap / attributed
        for f in retro.factors:
            f.tonnes_per_ha = round(f.tonnes_per_ha * scale, 2)
        attributed = round(sum(f.tonnes_per_ha for f in retro.factors), 2)
        retro.notes.append(
            "The measured causes add up to more than the actual shortfall, so "
            "each has been scaled back proportionally."
        )

    retro.factors.sort(key=lambda f: f.tonnes_per_ha, reverse=True)
    retro.unexplained_t_ha = round(max(0.0, gap - attributed), 2)

    retro.headline = (
        f"You harvested {actual} t/ha against a realistic {potential} t/ha — "
        f"a gap of {gap} t/ha."
    )

    if retro.unexplained_t_ha >= MIN_REPORTABLE_GAP_T_HA:
        retro.notes.append(
            f"{retro.unexplained_t_ha} t/ha of the gap is not explained by anything "
            f"we measured. Weather, soil variation and pest pressure all play a "
            f"part, and pretending otherwise would make the rest of this less "
            f"trustworthy."
        )
    if not retro.factors:
        retro.notes.append(
            "None of the shortfall traces to something we measured this season. "
            "Recording establishment and input timing next season is what makes "
            "this breakdown useful."
        )

    return retro


# ---------------------------------------------------------------------------
# Deriving input timing from what was actually logged
# ---------------------------------------------------------------------------

# Input types that carry nitrogen. Matched loosely because farmers type these
# freely ("AN", "ammonium nitrate", "urea top dress").
_NITROGEN_KEYWORDS = (
    "an", "ammonium nitrate", "urea", "top dress", "topdress", "top-dress",
    "nitrogen", "uan", "can",
)

# Basal compounds are not top-dressing, and matching them would report the
# top-dress as impossibly early.
_BASAL_KEYWORDS = ("compound", "basal", "dap", "map", "npk")


def _looks_like_nitrogen(input_type: Optional[str]) -> bool:
    if not input_type:
        return False
    t = str(input_type).strip().lower()
    if any(b in t for b in _BASAL_KEYWORDS):
        return False
    # Bare "an" must match as a whole word, or it fires on every word with
    # those letters in it ("manure", "planting").
    tokens = {tok.strip(" .,-") for tok in t.replace("-", " ").split()}
    if "an" in tokens or "can" in tokens:
        return True
    return any(k in t for k in _NITROGEN_KEYWORDS if k not in ("an", "can"))


def derive_topdress_delay(
    inputs: Sequence[Dict[str, Any]],
    planting_date: Any,
    expected_day: int,
) -> Optional[int]:
    """How many days after the window opened the first nitrogen actually went on.

    Returns ``None`` when nothing identifiable was logged — which is the right
    answer, not zero. Reading "no record" as "applied on time" would quietly
    credit farmers for work there is no evidence of, and the whole retrospective
    depends on not doing that.

    Negative delays (applied early) clamp to 0: early nitrogen is a different
    conversation, not a yield penalty to charge here.
    """
    planted = _as_date(planting_date)
    if not planted:
        return None

    days: List[int] = []
    for row in inputs or []:
        if not _looks_like_nitrogen(row.get("input_type")):
            continue
        applied = _as_date(row.get("input_date"))
        if not applied:
            continue
        dap = (applied - planted).days
        if dap < 0:
            continue
        days.append(dap)

    if not days:
        return None
    return max(0, min(days) - expected_day)
