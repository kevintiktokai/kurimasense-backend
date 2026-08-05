"""
Fertiliser programme planning — pure, no I/O.

Turns the ``FertilizerSchedule`` already carried by every ``CropProfile`` into a
**calendared, quantified programme** anchored to a planting date: what to apply,
when (as a real date, not "V4-V6"), how much for *this* field's area, and why.

Why this module exists
----------------------
Every crop profile has carried ``basal`` / ``top_dress_1`` / ``top_dress_2`` /
``foliar`` / ``liming`` with rates, timings and scientific basis since the
knowledge base was written, and **no screen has ever rendered any of it**. The
knowledge was not missing; the surface was.

Prices are deliberately out of scope — farmers enter their own costs against
their own supplier quotes. This module answers *what, when and how much*.

Soil-aware adjustments
----------------------
Two adjustments carry real money and are applied here rather than left to prose:

* **Split nitrogen on sandy soils.** Zimbabwean sandy loams leach 29-40 kg N/ha
  from the top 40 cm within two weeks under heavy rain. A single large top-dress
  on sand is partly a donation to the water table, so the programme splits it
  and says so.
* **Lime before phosphorus.** Below the crop's ``critical_ph_low``, applied P is
  locked up in Al/Fe phosphates — basal P spent on an acid soil is largely
  wasted. Liming has a 3-6 month lead time, so it must surface at *planning*
  time, which is the whole point of a pre-plant brief.

.. warning::
   Rates come from the crop profiles and are pending agronomist sign-off for
   farmer-facing release.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Soil textures that leach nitrogen fast enough to warrant splitting.
_LEACHING_TEXTURES = ("sand", "sandy", "loamy sand", "sandy loam", "kaolinitic")

# "(28-42 days after planting)" / "28-42 DAP" / "day 28-42"
_DAY_RANGE_RE = re.compile(
    r"(\d+)\s*[-–]\s*(\d+)\s*(?:days?|DAP|day)", re.IGNORECASE
)
# A leading stage code such as "V4-V6", "R1", "VT".
_STAGE_RE = re.compile(r"\b([VR]\d{1,2}|VT|VE)\b")
# "200-300 kg/ha", "1-3 t/ha", and — as the profiles actually write them — a
# product name wedged between the unit and the /ha: "150-200 kg AN/ha",
# "2 kg ZnSO4/ha". The optional product token is what makes this survive real
# profile prose rather than only the tidy cases.
_RATE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*"
    r"(kg|t|L|mL)\s*(?:[A-Za-z][A-Za-z0-9()\.]*\s*)?/\s*ha",
    re.IGNORECASE,
)


@dataclass
class FertiliserStep:
    """One application in the programme."""
    key: str                      # 'liming' | 'basal' | 'top_dress_1' | ...
    label: str
    product: str
    rate_text: str
    rate_low: Optional[float]
    rate_high: Optional[float]
    rate_unit: Optional[str]
    amount_low: Optional[float]   # for the field's whole area
    amount_high: Optional[float]
    timing_text: str
    days_after_planting: Optional[int]
    scheduled_date: Optional[str]
    stage_code: Optional[str]
    application: Optional[str]
    why: str
    optional: bool = False
    conditional_on: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "product": self.product,
            "rate_text": self.rate_text,
            "rate_low": self.rate_low,
            "rate_high": self.rate_high,
            "rate_unit": self.rate_unit,
            "amount_low": self.amount_low,
            "amount_high": self.amount_high,
            "timing_text": self.timing_text,
            "days_after_planting": self.days_after_planting,
            "scheduled_date": self.scheduled_date,
            "stage_code": self.stage_code,
            "application": self.application,
            "why": self.why,
            "optional": self.optional,
            "conditional_on": self.conditional_on,
        }


@dataclass
class FertiliserProgramme:
    crop: str
    area_hectares: Optional[float]
    planting_date: Optional[str]
    steps: List[FertiliserStep] = dc_field(default_factory=list)
    adjustments: List[str] = dc_field(default_factory=list)
    warnings: List[str] = dc_field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crop": self.crop,
            "area_hectares": self.area_hectares,
            "planting_date": self.planting_date,
            "steps": [s.to_dict() for s in self.steps],
            "adjustments": self.adjustments,
            "warnings": self.warnings,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Parsing helpers — the profiles store human prose, so parse defensively and
# always keep the original text alongside anything extracted from it.
# ---------------------------------------------------------------------------
def parse_rate(rate_text: Optional[str]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """``"200-300 kg/ha"`` → ``(200.0, 300.0, "kg")``. Unparseable → all None."""
    if not rate_text:
        return (None, None, None)
    m = _RATE_RE.search(str(rate_text))
    if not m:
        return (None, None, None)
    low = float(m.group(1))
    high = float(m.group(2)) if m.group(2) else low
    return (low, high, m.group(3).lower())


def parse_days_after_planting(timing_text: Optional[str]) -> Optional[int]:
    """Earliest day-after-planting mentioned in a timing string, if any.

    Returns the *start* of a range — the programme schedules the opening of the
    window, not its midpoint, because the cost of being early is far lower than
    the cost of being late.
    """
    if not timing_text:
        return None
    m = _DAY_RANGE_RE.search(str(timing_text))
    if m:
        return int(m.group(1))
    solo = re.search(r"(\d+)\s*(?:days?|DAP)\s*(?:after planting)?", str(timing_text), re.IGNORECASE)
    return int(solo.group(1)) if solo else None


def parse_stage_code(timing_text: Optional[str]) -> Optional[str]:
    if not timing_text:
        return None
    m = _STAGE_RE.search(str(timing_text))
    return m.group(1) if m else None


def _split_stage_code(code: str) -> Optional[Tuple[str, Optional[int]]]:
    """``"V8"`` → ``("V", 8)``; ``"VT"`` → ``("VT", None)``."""
    m = re.fullmatch(r"([VR])(\d{1,2})", code.strip(), re.IGNORECASE)
    if m:
        return (m.group(1).upper(), int(m.group(2)))
    letters = code.strip().upper()
    return (letters, None) if letters else None


def _stage_matches(target: str, profile_code: str) -> bool:
    """Does ``target`` (e.g. "V8") fall inside a profile stage code?

    Profile stage codes are *ranges* — "V7-V10", "V1-V3", "R2-R4" — so a plain
    substring test silently misses: "V8" is not a substring of "V7-V10". That
    miss left the second top-dress undated, which is exactly the application
    that matters most on leaching soils.
    """
    t = _split_stage_code(target)
    if not t:
        return False
    t_letter, t_num = t

    bounds = re.split(r"\s*[-–]\s*", profile_code.strip())
    parsed = [_split_stage_code(b) for b in bounds if b]
    parsed = [p for p in parsed if p]
    if not parsed:
        return False

    # Non-numeric codes ("VT", "VE") only match exactly.
    if t_num is None or any(p[1] is None for p in parsed):
        return any(t_letter == p[0] for p in parsed)

    if any(p[0] != t_letter for p in parsed):
        return False
    nums = [p[1] for p in parsed]
    return min(nums) <= t_num <= max(nums)


def _days_from_growth_stages(profile: Any, stage_code: Optional[str]) -> Optional[int]:
    """Fall back to the profile's ``growth_stages`` to date a stage code."""
    if not stage_code:
        return None
    for stage in getattr(profile, "growth_stages", None) or []:
        code = getattr(stage, "stage_code", "") or ""
        if code and _stage_matches(stage_code, code):
            try:
                return int(stage.day_range[0])
            except (AttributeError, TypeError, ValueError, IndexError):
                return None
    return None


def _is_leaching_soil(soil_texture: Optional[str]) -> bool:
    if not soil_texture:
        return False
    t = str(soil_texture).strip().lower()
    return any(k in t for k in _LEACHING_TEXTURES)


def _build_step(
    key: str,
    label: str,
    spec: Optional[Dict[str, Any]],
    *,
    profile: Any,
    planting: Optional[date],
    area_ha: Optional[float],
    optional: bool = False,
    conditional_on: Optional[str] = None,
    days_override: Optional[int] = None,
) -> Optional[FertiliserStep]:
    if not spec:
        return None

    rate_text = str(spec.get("rate", "") or "")
    low, high, unit = parse_rate(rate_text)
    timing_text = str(spec.get("timing", "") or "")

    stage_code = parse_stage_code(timing_text)
    days = days_override
    if days is None:
        days = parse_days_after_planting(timing_text)
    if days is None:
        days = _days_from_growth_stages(profile, stage_code)

    scheduled = None
    if planting and days is not None:
        scheduled = (planting + timedelta(days=days)).isoformat()

    amount_low = round(low * area_ha, 1) if (low is not None and area_ha) else None
    amount_high = round(high * area_ha, 1) if (high is not None and area_ha) else None

    return FertiliserStep(
        key=key,
        label=label,
        product=str(spec.get("product", "") or ""),
        rate_text=rate_text,
        rate_low=low,
        rate_high=high,
        rate_unit=unit,
        amount_low=amount_low,
        amount_high=amount_high,
        timing_text=timing_text,
        days_after_planting=days,
        scheduled_date=scheduled,
        stage_code=stage_code,
        application=spec.get("application"),
        why=str(spec.get("scientific_basis", "") or ""),
        optional=optional,
        conditional_on=conditional_on,
    )


# ---------------------------------------------------------------------------
# The programme
# ---------------------------------------------------------------------------
def build_fertiliser_programme(
    profile: Any,
    *,
    planting_date: Optional[date] = None,
    area_hectares: Optional[float] = None,
    soil_ph: Optional[float] = None,
    soil_texture: Optional[str] = None,
    irrigated: bool = False,
    target_yield_t_ha: Optional[float] = None,
) -> FertiliserProgramme:
    """Render a crop profile's fertiliser schedule as a dated, quantified plan.

    ``profile`` is a ``CropProfile`` (duck-typed so tests can pass a stub).
    """
    schedule = getattr(profile, "fertilizer_schedule", None)
    crop = getattr(profile, "crop_name", "") or ""
    programme = FertiliserProgramme(
        crop=crop,
        area_hectares=area_hectares,
        planting_date=planting_date.isoformat() if planting_date else None,
        notes=str(getattr(schedule, "notes", "") or "") if schedule else "",
    )
    if schedule is None:
        programme.warnings.append(f"No fertiliser schedule is defined for {crop or 'this crop'}.")
        return programme

    # --- Lime: first in the list because it has the longest lead time --------
    critical_ph = getattr(profile, "critical_ph_low", None)
    liming = getattr(schedule, "liming", None)
    needs_lime = (
        soil_ph is not None and critical_ph is not None and soil_ph < float(critical_ph)
    )
    if liming:
        step = _build_step(
            "liming", "Lime", liming,
            profile=profile, planting=planting_date, area_ha=area_hectares,
            optional=not needs_lime,
            conditional_on=None if needs_lime else "soil test showing pH below target",
            # Lime wants 3-6 months of lead time; schedule it 120 days BEFORE planting.
            days_override=-120,
        )
        if step:
            if needs_lime:
                step.why = (
                    f"Your soil pH of {soil_ph} is below {critical_ph}, where aluminium "
                    f"becomes toxic to roots and applied phosphorus is locked up in "
                    f"Al/Fe phosphates. Liming first is what makes the basal fertiliser "
                    f"worth buying. " + step.why
                ).strip()
                programme.adjustments.append(
                    f"Lime raised to a required step — soil pH {soil_ph} is below the "
                    f"{critical_ph} threshold for {crop or 'this crop'}."
                )
            programme.steps.append(step)

    # --- Basal ---------------------------------------------------------------
    basal = _build_step(
        "basal", "Basal (at planting)", getattr(schedule, "basal", None),
        profile=profile, planting=planting_date, area_ha=area_hectares,
        days_override=0,
    )
    if basal:
        programme.steps.append(basal)
        if needs_lime:
            programme.warnings.append(
                "Basal phosphorus applied to soil this acid will be largely locked "
                "up. Lime first if the calendar allows it."
            )

    # --- Top dressing --------------------------------------------------------
    leaching = _is_leaching_soil(soil_texture)
    td1 = _build_step(
        "top_dress_1", "First top-dress", getattr(schedule, "top_dress_1", None),
        profile=profile, planting=planting_date, area_ha=area_hectares,
    )
    if td1:
        if leaching:
            td1.why = (
                "On sandy soil nitrogen leaches fast — Zimbabwean sandy loams lose "
                "29-40 kg N/ha from the root zone within two weeks of heavy rain. "
                "Splitting the nitrogen keeps it available to the crop instead of "
                "sending it past the roots. " + td1.why
            ).strip()
        programme.steps.append(td1)

    td2_spec = getattr(schedule, "top_dress_2", None)
    # The profiles mark the second top-dress as optional/high-potential-only. On
    # leaching soils it stops being optional: it is how a split is achieved.
    td2_optional = not (leaching or irrigated or (target_yield_t_ha or 0) >= 8)
    td2 = _build_step(
        "top_dress_2", "Second top-dress", td2_spec,
        profile=profile, planting=planting_date, area_ha=area_hectares,
        optional=td2_optional,
        conditional_on="high-potential or irrigated fields" if td2_optional else None,
    )
    if td2:
        if leaching and td2_optional is False:
            programme.adjustments.append(
                "Second top-dress promoted from optional to recommended: your soil "
                "texture leaches nitrogen, so a split application is the difference "
                "between feeding the crop and feeding the water table."
            )
        programme.steps.append(td2)

    # --- Foliar --------------------------------------------------------------
    foliar = _build_step(
        "foliar", "Foliar feed", getattr(schedule, "foliar", None),
        profile=profile, planting=planting_date, area_ha=area_hectares,
        optional=True, conditional_on="only if deficiency symptoms appear",
    )
    if foliar:
        programme.steps.append(foliar)

    # Order by date where known; undated steps sink to the bottom.
    programme.steps.sort(
        key=lambda s: (s.days_after_planting is None, s.days_after_planting or 0)
    )

    if area_hectares is None:
        programme.warnings.append(
            "Field area is unknown, so only per-hectare rates are shown."
        )
    if planting_date is None:
        programme.warnings.append(
            "No planting date set, so steps are shown as days after planting "
            "rather than calendar dates."
        )

    return programme
