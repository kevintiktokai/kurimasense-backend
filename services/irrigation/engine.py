"""
Pure irrigation decision core — no I/O, deterministic, unit-tested.

FAO-56 style daily root-zone water balance:

    TAW  = AWC (mm/m) × root depth (m)          total available water
    RAW  = p × TAW                              readily available (stress trigger)
    Dr,t = clamp(Dr,t-1 + ETc,t − Pe,t − I,t, 0, TAW)   depletion bookkeeping

Recommend irrigation when depletion reaches RAW, *net of what the forecast is
about to deliver* — the engine will explicitly say "delay, rain is coming"
rather than telling a farmer to pump water ahead of a storm.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple

from .models import (
    DEFAULT_IRRIGATION_METHOD,
    EFFECTIVE_RAIN_FACTOR,
    IRRIGATION_METHOD_RATES_MM_PER_HOUR,
    DayWeather,
    IrrigationInputs,
    IrrigationRecommendation,
)

_FALLBACK_ET0 = 5.0  # mm/day — reasonable subtropical default when data is missing


def _effective_rain(precip: Optional[float]) -> float:
    return max(0.0, (precip or 0.0)) * EFFECTIVE_RAIN_FACTOR


def _expected_forecast_rain(forecast: List[DayWeather], days: int) -> Tuple[float, float]:
    """Probability-weighted effective rain over the next N days + max probability."""
    total, max_prob = 0.0, 0.0
    for day in forecast[:days]:
        prob = day.precip_probability
        weight = min(1.0, (prob / 100.0)) if prob is not None else 0.6
        total += _effective_rain(day.precip) * weight
        if prob is not None:
            max_prob = max(max_prob, prob)
    return total, max_prob


def _simulate_depletion(inputs: IrrigationInputs, taw: float, raw: float) -> Tuple[float, bool, float, float]:
    """Walk the past series; returns (depletion_mm, state_anchored, rain_past_7d,
    et0_coverage). state_anchored is True when a full-refill event (heavy rain
    or recorded irrigation) pinned the balance to a known point, which raises
    confidence in the estimate."""
    depletion = 0.5 * raw  # unknown starting point — mid-trigger, self-corrects
    anchored = False
    irrigated = set(inputs.irrigation_dates or [])
    rain_7d = 0.0
    et0_present = 0
    past = inputs.past or []
    for i, day in enumerate(past):
        et0 = day.et0 if day.et0 is not None else _FALLBACK_ET0
        if day.et0 is not None:
            et0_present += 1
        etc = inputs.kc * et0
        depletion = depletion + etc - _effective_rain(day.precip)
        if day.date in irrigated:
            depletion = 0.0  # planner-recorded irrigation: assume refill to FC
            anchored = True
        depletion = min(max(depletion, 0.0), taw)
        if depletion == 0.0:
            anchored = True
        if i >= len(past) - 7:
            rain_7d += day.precip or 0.0
    coverage = (et0_present / len(past)) if past else 0.0
    return depletion, anchored, rain_7d, coverage


def _confidence(inputs: IrrigationInputs, anchored: bool, et0_coverage: float,
                has_forecast_probs: bool) -> Tuple[float, str]:
    score = 0.55
    if inputs.awc_source == "soil_profile":
        score += 0.15
    if et0_coverage >= 0.7:
        score += 0.10
    if has_forecast_probs:
        score += 0.05
    if anchored:
        score += 0.10
    else:
        score -= 0.10
    if inputs.measured_soil_moisture_depletion_mm is not None:
        score = max(score, 0.85)  # a probe reading trumps the model
    score = min(max(score, 0.2), 0.95)
    label = "high" if score >= 0.75 else ("medium" if score >= 0.5 else "low")
    return score, label


def recommend(inputs: IrrigationInputs, today: Optional[date] = None) -> IrrigationRecommendation:
    today = today or date.today()
    taw = max(inputs.awc_mm_per_m * inputs.root_depth_m, 10.0)
    raw = taw * inputs.depletion_fraction

    depletion, anchored, rain_7d, et0_coverage = _simulate_depletion(inputs, taw, raw)
    if inputs.measured_soil_moisture_depletion_mm is not None:
        depletion = min(max(inputs.measured_soil_moisture_depletion_mm, 0.0), taw)
        anchored = True

    forecast = inputs.forecast or []
    has_probs = any(d.precip_probability is not None for d in forecast)
    expected_rain_3d, max_prob_3d = _expected_forecast_rain(forecast, 3)
    expected_rain_2d, max_prob_2d = _expected_forecast_rain(forecast, 2)

    et0_next = [d.et0 for d in forecast[:3] if d.et0 is not None]
    et0_now = sum(et0_next) / len(et0_next) if et0_next else _FALLBACK_ET0
    etc_daily = inputs.kc * et0_now

    # ── reasoning chain (always present, action-independent parts first) ────
    reasoning: List[str] = [
        f"{inputs.crop} is at the {inputs.stage_name} stage (day {inputs.days_since_planting}); "
        f"crop coefficient Kc = {inputs.kc:.2f}.",
        f"Current crop water use ≈ {etc_daily:.1f} mm/day (reference ET₀ {et0_now:.1f} mm × Kc).",
        f"Estimated root-zone depletion: {depletion:.0f} mm of {taw:.0f} mm total available water "
        f"(irrigation trigger at {raw:.0f} mm).",
        f"Rainfall in the last 7 days: {rain_7d:.0f} mm.",
        f"Forecast: ~{expected_rain_3d:.0f} mm of effective rain expected in the next 3 days "
        f"(max rain chance {max_prob_3d:.0f}%)."
        if forecast else "No rainfall forecast available — decision based on the recent balance only.",
    ]
    if inputs.awc_source == "soil_profile":
        reasoning.append(
            f"Soil water capacity {inputs.awc_mm_per_m:.0f} mm/m from this field's soil profile.")
    else:
        reasoning.append(
            f"Soil water capacity assumed at {inputs.awc_mm_per_m:.0f} mm/m (typical loam) — "
            "a Soil Intelligence profile for this field will sharpen this.")
    if inputs.irrigation_dates:
        reasoning.append(
            f"Last recorded irrigation: {max(inputs.irrigation_dates)} (from your planner).")

    method = inputs.method or DEFAULT_IRRIGATION_METHOD
    rate = IRRIGATION_METHOD_RATES_MM_PER_HOUR.get(method,
                                                   IRRIGATION_METHOD_RATES_MM_PER_HOUR[DEFAULT_IRRIGATION_METHOD])

    # ── decision ────────────────────────────────────────────────────────────
    action: str
    headline: str
    recommended = 0.0
    next_review: Optional[date] = None

    days_to_trigger = ((raw - depletion) / etc_daily) if etc_daily > 0 else 99.0

    if depletion >= raw:
        # Delay only when near-certain rain within 2 days would pull the root
        # zone back below the stress trigger — brief stress at the boundary
        # beats pumping water ahead of a storm.
        if (depletion - expected_rain_2d) < raw and max_prob_2d >= 60:
            action = "delay_rain_expected"
            headline = (f"Hold off — forecast rain (~{expected_rain_2d:.0f} mm within 2 days) "
                        f"should pull the {depletion:.0f} mm deficit back below the stress trigger.")
            reasoning.append("Irrigating ahead of near-certain rain wastes water and risks "
                             "waterlogging; re-check after the rain passes.")
            next_review = today + timedelta(days=2)
        else:
            action = "irrigate_now"
            recommended = max(depletion - expected_rain_3d, min(10.0, depletion))
            recommended = min(recommended, taw)
            headline = (f"Irrigate today: apply ~{recommended:.0f} mm to refill the root zone.")
            reasoning.append(
                f"Depletion has reached the stress trigger; net of expected rain, "
                f"~{recommended:.0f} mm restores the root zone without deep-percolation losses.")
            next_review = today + timedelta(days=max(1, int(raw / etc_daily)) if etc_daily > 0 else 3)
    elif days_to_trigger <= 2.0:
        gap_at_trigger = depletion + 2 * etc_daily
        if expected_rain_3d >= (gap_at_trigger - raw) + raw * 0.3 and max_prob_3d >= 60:
            action = "delay_rain_expected"
            headline = (f"Rain expected before stress sets in (~{expected_rain_3d:.0f} mm in 3 days) — "
                        "delay irrigation and re-check.")
            next_review = today + timedelta(days=2)
        else:
            action = "irrigate_soon"
            recommended = max(min(gap_at_trigger - expected_rain_3d, taw), 0.0)
            headline = (f"Irrigate within 2 days: the root zone will hit its stress trigger "
                        f"in ~{max(days_to_trigger, 0.5):.0f} day(s); plan ~{recommended:.0f} mm.")
            next_review = today + timedelta(days=1)
    elif depletion <= 0.3 * raw:
        action = "not_needed"
        headline = "No irrigation needed — the root zone is well supplied."
        next_review = today + timedelta(days=max(2, int(days_to_trigger * 0.6)))
    else:
        action = "monitor"
        headline = (f"No irrigation yet — about {days_to_trigger:.0f} day(s) of soil water remain. "
                    "Monitor and re-check.")
        next_review = today + timedelta(days=max(1, int(days_to_trigger * 0.5)))

    duration_minutes: Optional[int] = None
    if recommended > 0 and rate > 0:
        duration_minutes = int(round(recommended / rate * 60))
        reasoning.append(
            f"With {method.replace('_', ' ')} irrigation (~{rate:.0f} mm/h), "
            f"{recommended:.0f} mm takes about {duration_minutes} minutes.")

    confidence, label = _confidence(inputs, anchored, et0_coverage, has_probs)

    sources = ["open-meteo:et0+rain"]
    sources.append("soil_intelligence" if inputs.awc_source == "soil_profile" else "soil:default")
    sources.append(f"crop_profiles:{inputs.crop.lower()}")
    if inputs.irrigation_dates:
        sources.append("planner:irrigation_log")
    if inputs.measured_soil_moisture_depletion_mm is not None:
        sources.append("soil_moisture_sensor")

    return IrrigationRecommendation(
        field_id=inputs.field_id,
        field_name=inputs.field_name,
        crop=inputs.crop,
        stage=inputs.stage_name,
        action=action,
        headline=headline,
        reasoning=reasoning,
        water_deficit_mm=depletion,
        raw_trigger_mm=raw,
        taw_mm=taw,
        recommended_mm=recommended,
        duration_minutes=duration_minutes,
        method=method,
        expected_rain_mm_3d=expected_rain_3d,
        etc_mm_per_day=etc_daily,
        confidence=confidence,
        confidence_label=label,
        next_review_date=next_review.isoformat() if next_review else None,
        valid_until=(today + timedelta(days=1)).isoformat(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        data_sources=sources,
    )
