"""
KurimaSense Agronomic Decision Engine
=======================================
Provides deterministic, science-based agronomic recommendations
without requiring an LLM call. These fast-path decisions supplement
the AI Brain with instant, reliable advice.

Features:
  - Planting window advisor (crop × region × date)
  - Fertilizer schedule generator (crop × stage × soil)
  - IPM decision support (disease risk × pest stage × weather)
  - Irrigation scheduling (Kc × ET₀ × rainfall)
  - Harvest readiness checker
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from crop_profiles import (
    CropProfile,
    get_crop_profile,
    get_current_stage_for_crop,
    get_diseases_for_conditions,
    get_pests_for_stage,
)


# ---------------------------------------------------------------------------
# Planting Window Advisor
# ---------------------------------------------------------------------------

def check_planting_window(
    crop_name: str,
    region: str = "",
    check_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Determine if the given date falls within the optimal planting window
    for the crop in the specified natural region.

    Returns {status, recommendation, window, scientific_basis}.
    """
    profile = get_crop_profile(crop_name)
    if not profile:
        return {
            "status": "unknown",
            "recommendation": f"No planting data for '{crop_name}'.",
        }

    check_date = check_date or date.today()
    month_day = (check_date.month, check_date.day)

    # Find matching window
    best_window = None
    for window in profile.planting_windows:
        if region and region.lower() not in window.region.lower():
            continue
        best_window = window
        break

    if not best_window and profile.planting_windows:
        best_window = profile.planting_windows[0]

    if not best_window:
        return {"status": "unknown", "recommendation": "No planting window data available."}

    def _parse_month_day(s: str) -> Tuple[int, int]:
        """Parse 'November 15' → (11, 15)."""
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
        }
        parts = s.strip().lower().split()
        return (months.get(parts[0], 1), int(parts[1]) if len(parts) > 1 else 1)

    opt_start = _parse_month_day(best_window.optimal_start)
    opt_end = _parse_month_day(best_window.optimal_end)
    acc_start = _parse_month_day(best_window.acceptable_start)
    acc_end = _parse_month_day(best_window.acceptable_end)

    if opt_start <= month_day <= opt_end:
        status = "optimal"
        rec = (f"✅ This is the OPTIMAL planting window for {crop_name} in {best_window.region}. "
               f"Plant now for best results.")
    elif acc_start <= month_day <= acc_end:
        status = "acceptable"
        rec = (f"🟡 You are within the acceptable window but outside the optimal period. "
               f"Consider short-season varieties to reduce risk.")
    elif month_day < acc_start:
        status = "too_early"
        days_until = (date(check_date.year, acc_start[0], acc_start[1]) - check_date).days
        rec = (f"⏳ Too early for {crop_name}. Optimal window opens {best_window.optimal_start} "
               f"(~{days_until} days away). Use this time for land preparation and liming.")
    else:
        status = "too_late"
        rec = (f"⚠️ The planting window for {crop_name} has passed. Consider: "
               f"(1) short-season variety if within 2 weeks of window close, "
               f"(2) switch to a more appropriate crop, or "
               f"(3) plan for next season.")

    return {
        "status": status,
        "recommendation": rec,
        "window": {
            "region": best_window.region,
            "optimal": f"{best_window.optimal_start} – {best_window.optimal_end}",
            "acceptable": f"{best_window.acceptable_start} – {best_window.acceptable_end}",
        },
        "notes": best_window.notes,
    }


# ---------------------------------------------------------------------------
# Fertilizer Recommendation Engine
# ---------------------------------------------------------------------------

def get_fertilizer_recommendation(
    crop_name: str,
    days_since_planting: int,
    soil_ph: Optional[float] = None,
    natural_region: str = "II",
) -> Dict[str, Any]:
    """
    Generate a specific fertilizer recommendation based on crop, stage, and soil.
    Returns actionable advice with products, rates, and scientific justification.
    """
    profile = get_crop_profile(crop_name)
    if not profile:
        return {"recommendation": f"No fertilizer data for '{crop_name}'."}

    stage = get_current_stage_for_crop(crop_name, days_since_planting)
    fert = profile.fertilizer_schedule
    result: Dict[str, Any] = {
        "crop": crop_name,
        "growth_stage": stage.stage_name if stage else "Unknown",
        "day": days_since_planting,
        "recommendations": [],
        "warnings": [],
    }

    # Liming check (always relevant)
    if soil_ph is not None and soil_ph < profile.critical_ph_low:
        lime_rec = fert.liming or {}
        result["warnings"].append({
            "type": "soil_acidity",
            "severity": "critical",
            "message": (
                f"⚠️ CRITICAL: Soil pH {soil_ph} is below {profile.critical_ph_low}. "
                f"Aluminium toxicity is inhibiting root growth and locking up Phosphorus. "
                f"Apply {lime_rec.get('rate', '2-3 t/ha lime')} immediately."
            ),
            "product": lime_rec.get("product", "Agricultural lime"),
            "rate": lime_rec.get("rate", "2-3 t/ha"),
            "scientific_basis": lime_rec.get("scientific_basis",
                                              "pH correction eliminates Al toxicity and releases P."),
        })

    if not stage:
        result["recommendations"].append({
            "phase": "General",
            "advice": "Unable to determine growth stage. Review planting date.",
        })
        return result

    # Determine which fertilizer phase we're in
    code = stage.stage_code.lower()

    # Basal phase
    if any(k in code for k in ["ve", "transplant", "germination"]):
        b = fert.basal
        result["recommendations"].append({
            "phase": "Basal (At Planting)",
            "product": b.get("product"),
            "rate": b.get("rate"),
            "timing": b.get("timing"),
            "scientific_basis": b.get("scientific_basis"),
            "nutrients": b.get("nutrients_supplied"),
        })

    # Top-dress window
    elif any(k in code for k in ["v4", "v1-v6", "rapid", "v4-v6"]):
        td = fert.top_dress_1
        result["recommendations"].append({
            "phase": "Top-Dress 1",
            "product": td.get("product"),
            "rate": td.get("rate"),
            "timing": td.get("timing"),
            "application": td.get("application", ""),
            "scientific_basis": td.get("scientific_basis"),
        })

    # Late vegetative (second top-dress for high-potential)
    elif any(k in code for k in ["v7", "v7-v10"]):
        if fert.top_dress_2:
            td2 = fert.top_dress_2
            result["recommendations"].append({
                "phase": "Top-Dress 2 (High-Potential Only)",
                "product": td2.get("product"),
                "rate": td2.get("rate"),
                "timing": td2.get("timing"),
                "scientific_basis": td2.get("scientific_basis"),
            })
        else:
            result["recommendations"].append({
                "phase": "Monitoring",
                "advice": "No additional fertiliser needed at this stage. Focus on crop protection.",
            })

    # Reproductive / grain fill
    else:
        result["recommendations"].append({
            "phase": "Post Top-Dress",
            "advice": (
                "Major fertiliser applications are complete. Focus on: "
                "crop protection, adequate moisture, and monitoring for nutrient deficiency symptoms."
            ),
        })

    # Foliar if available and stage-appropriate
    if fert.foliar and days_since_planting < 50:
        result["recommendations"].append({
            "phase": "Foliar (if deficiency symptoms observed)",
            "product": fert.foliar.get("product"),
            "rate": fert.foliar.get("rate"),
            "timing": fert.foliar.get("timing"),
            "scientific_basis": fert.foliar.get("scientific_basis"),
        })

    return result


# ---------------------------------------------------------------------------
# IPM Decision Support
# ---------------------------------------------------------------------------

def get_ipm_recommendations(
    crop_name: str,
    days_since_planting: int,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Integrated Pest Management recommendations based on current conditions.
    """
    stage = get_current_stage_for_crop(crop_name, days_since_planting)
    stage_code = stage.stage_code if stage else ""

    diseases = get_diseases_for_conditions(crop_name, temperature, humidity, stage_code)
    pests = get_pests_for_stage(crop_name, stage_code)

    scouting_plan = []
    spray_recommendations = []
    cultural_actions = []

    for d in diseases:
        if d["risk_level"] == "high":
            spray_recommendations.append({
                "target": d["disease"],
                "urgency": "high",
                "product": d["recommended_actions"][0] if d["recommended_actions"] else "Consult extension officer",
                "justification": "; ".join(d["reasons"]),
            })
        scouting_plan.append({
            "target": d["disease"],
            "look_for": d["scouting_tip"],
            "risk": d["risk_level"],
        })

    for p in pests:
        scouting_plan.append({
            "target": p["pest"],
            "look_for": ", ".join(p["damage_to_look_for"]),
            "protocol": p["scouting_protocol"],
            "threshold": p["economic_threshold"],
        })

    if stage:
        for act in stage.key_activities:
            if any(kw in act.lower() for kw in ["scout", "weed", "rotate", "remove"]):
                cultural_actions.append(act)

    return {
        "crop": crop_name,
        "stage": stage.stage_name if stage else "Unknown",
        "day": days_since_planting,
        "scouting_plan": scouting_plan,
        "spray_recommendations": spray_recommendations,
        "cultural_actions": cultural_actions,
        "summary": (
            f"{'🔴 HIGH RISK' if any(d['risk_level'] == 'high' for d in diseases) else '🟡 Monitor closely' if diseases else '🟢 Low risk'}: "
            f"{len(diseases)} disease risk(s), {len(pests)} pest(s) to watch at {stage.stage_name if stage else 'current stage'}."
        ),
    }


# ---------------------------------------------------------------------------
# Irrigation Scheduler
# ---------------------------------------------------------------------------

def get_irrigation_advice(
    crop_name: str,
    days_since_planting: int,
    recent_rainfall_mm: float = 0.0,
    et0_mm_per_day: float = 5.0,
) -> Dict[str, Any]:
    """
    Simple crop-coefficient-based irrigation scheduling.
    ETc = Kc × ET₀
    Deficit = ETc - Rainfall
    """
    stage = get_current_stage_for_crop(crop_name, days_since_planting)
    if not stage:
        return {"advice": "Unable to determine stage for irrigation scheduling."}

    kc = stage.water_kc
    etc_daily = kc * et0_mm_per_day
    etc_weekly = etc_daily * 7
    deficit = max(0, etc_weekly - recent_rainfall_mm)

    if deficit <= 5:
        status = "adequate"
        advice = "Rainfall is meeting crop water demand. No irrigation needed this week."
    elif deficit <= 15:
        status = "monitor"
        advice = (f"Slight water deficit of ~{deficit:.0f}mm. Monitor soil moisture. "
                  f"If no rain expected in 3 days, irrigate {deficit:.0f}mm.")
    else:
        status = "irrigate"
        advice = (f"Water deficit of {deficit:.0f}mm. Irrigate {deficit:.0f}mm within 2 days. "
                  f"At {stage.stage_name}, water stress causes: {', '.join(stage.risks[:2]) if stage.risks else 'reduced yield'}.")

    return {
        "crop": crop_name,
        "stage": stage.stage_name,
        "kc": kc,
        "et0": et0_mm_per_day,
        "etc_daily_mm": round(etc_daily, 1),
        "etc_weekly_mm": round(etc_weekly, 1),
        "recent_rainfall_mm": recent_rainfall_mm,
        "deficit_mm": round(deficit, 1),
        "status": status,
        "advice": advice,
        "critical_note": stage.scientific_notes[:200] if "water" in stage.scientific_notes.lower() else "",
    }


# ---------------------------------------------------------------------------
# Harvest Readiness
# ---------------------------------------------------------------------------

def check_harvest_readiness(
    crop_name: str,
    days_since_planting: int,
    variety_maturity_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Determine harvest readiness and provide post-harvest guidance.
    """
    profile = get_crop_profile(crop_name)
    if not profile:
        return {"status": "unknown", "advice": f"No harvest data for '{crop_name}'."}

    # Use variety maturity if known, otherwise use last stage end
    if variety_maturity_days:
        target = variety_maturity_days
    elif profile.growth_stages:
        target = profile.growth_stages[-1].day_range[1]
    else:
        target = 120

    days_to_harvest = max(0, target - days_since_planting)
    progress = min(100, round((days_since_planting / target) * 100))

    if days_to_harvest == 0:
        status = "ready"
        urgency = "critical"
        advice = (f"🌾 HARVEST NOW. {profile.crop_name} has reached maturity at day {days_since_planting}. "
                  f"{profile.harvest_moisture}")
    elif days_to_harvest <= 7:
        status = "imminent"
        urgency = "high"
        advice = (f"Harvest in ~{days_to_harvest} days. Prepare logistics: "
                  f"storage, transport, drying facility. {profile.harvest_moisture}")
    elif days_to_harvest <= 21:
        status = "approaching"
        urgency = "medium"
        advice = (f"~{days_to_harvest} days to harvest. Begin planning. "
                  f"Check storage readiness. {profile.post_harvest_notes[:150]}")
    else:
        status = "growing"
        urgency = "low"
        advice = f"~{days_to_harvest} days to harvest. Continue crop management."

    return {
        "crop": crop_name,
        "days_since_planting": days_since_planting,
        "days_to_harvest": days_to_harvest,
        "progress_percent": progress,
        "status": status,
        "urgency": urgency,
        "advice": advice,
        "harvest_target": f"{profile.harvest_moisture}",
        "storage": f"{profile.storage_conditions}",
        "post_harvest": f"{profile.post_harvest_notes[:200]}",
    }
