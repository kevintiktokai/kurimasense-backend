"""
Field State Aggregator — the canonical "state of this field" service
====================================================================
``build_field_state(field_id, requester_id)`` returns a complete
:class:`FieldState` composed from every existing subsystem (yield model,
KurimaScore math, climate, agronomic engine, proactive intelligence, and direct
DB reads). After this lands, two screens reading this response reach *identical*
conclusions about a field — contradictions become impossible by construction.

Design notes
------------
* **Heavy imports are lazy.** ``yield_model`` / ``climate_service`` /
  ``proactive_intelligence`` pull in optional deps (openai, tiktoken). They are
  imported *inside* :func:`build_field_state` so this module — and the pure
  :func:`assemble_field_state` used by the unit tests — imports cleanly without them.
* **Pure core.** :func:`assemble_field_state` takes already-fetched primitives and
  returns a ``FieldState``. It does no I/O, so it is fully unit-testable.
* **Graceful degradation.** Every upstream source is best-effort; a failure yields
  ``None`` + a completeness/stale flag, never a 500.
* **Security boundary.** Access is resolved by looking the field up by id first;
  an ownership mismatch is a 403, a genuinely missing field is a 404.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    FieldState, FieldInfo, SeasonInfo, KurimaScore, KurimaScoreComponents,
    Indices, CurrentIndices, TrendPoint, YieldProjection, ConfidenceFactors,
    Weather, CurrentWeather, TodayWeather, ForecastDay, WaterBalance,
    GrowingDegreeDays, PlanItem, Alert, ScoutingObservation, DataCompleteness, Meta,
)
from . import classifiers, generic_crop_math


# ---------------------------------------------------------------------------
# Access-control errors (mapped to HTTP status in the route)
# ---------------------------------------------------------------------------
class FieldNotFound(Exception):
    """Field id does not exist at all -> 404."""


class FieldAccessDenied(Exception):
    """Field exists but belongs to another tenant -> 403 (not 404)."""


_TRANSPLANTED_CROPS = {"tomato", "cabbage", "onion", "potato", "pepper", "eggplant", "lettuce", "tobacco"}
_TOBACCO_CROPS = {"tobacco", "flue-cured tobacco", "flue cured tobacco", "tobacco_flue_cured"}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
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


def _iso(value: Any) -> Optional[str]:
    d = _as_date(value)
    return d.isoformat() if d else None


def _maturity_days(crop_type: Optional[str], variety_days: Optional[int]) -> int:
    """Best-effort days-to-maturity from variety record, else crop profile, else 120."""
    if variety_days:
        try:
            return int(variety_days)
        except (TypeError, ValueError):
            pass
    try:
        from crop_profiles import get_crop_profile_or_generic
        profile = get_crop_profile_or_generic(crop_type or "")
        stages = getattr(profile, "growth_stages", None)
        if stages:
            return int(max(s.day_range[1] for s in stages))
    except Exception:
        pass
    return 120


# ---------------------------------------------------------------------------
# Scoring: choose tobacco math (crop == tobacco & variety known) or generic
# ---------------------------------------------------------------------------
def _normalise_tobacco_output(raw: dict, confidence_band: str, confidence_pct: int) -> dict:
    comp = raw.get("component_breakdown", {}) or {}
    return {
        "score": int(raw.get("score", 0)),
        "label": raw.get("label", "Adequate"),
        "color": raw.get("color", "#FBC02D"),
        "components": {
            "satellite": comp.get("satellite"),
            "management": comp.get("management"),
            "environmental": comp.get("environmental"),
        },
        "primary_driver": raw.get("primary_driver"),
        "likely_cause": raw.get("likely_cause"),
        "recommended_action": raw.get("recommended_action"),
        "yield_implication": raw.get("yield_implication"),
        "confidence_band": confidence_band,
        "confidence_pct": confidence_pct,
        "stage": raw.get("stage"),
    }


def compute_score(
    *,
    crop_type: Optional[str],
    variety_code: Optional[str],
    phase: str,
    indices_history: List[dict],
    transplant_or_plant_date: Optional[date],
    current_date: date,
    natural_region: Optional[str],
    management_component: Optional[float],
    environmental_component: Optional[float],
    confidence_band: str,
    confidence_pct: int,
    current_ndvi: Optional[float],
) -> dict:
    """
    Return the normalised KurimaScore dict. Uses the dedicated flue-cured tobacco
    model when the crop is tobacco *and* the variety resolves in its database;
    otherwise the crop-agnostic generic model. Any failure falls back to generic.
    """
    is_tobacco = (crop_type or "").strip().lower() in _TOBACCO_CROPS
    if is_tobacco and variety_code and transplant_or_plant_date:
        try:
            from crop_profiles.tobacco_flue_cured import tobacco_math as tm
            tm.get_variety(variety_code)  # raises UnknownVarietyError if not present
            # tobacco math expects upper-case index keys
            hist = [
                {k.upper(): v for k, v in obs.items()}
                for obs in (indices_history or [])
                if isinstance(obs, dict)
            ]
            stage = tm.detect_stage(variety_code, transplant_or_plant_date, current_date)
            sat = tm.compute_satellite_component(hist, stage, variety_code, natural_region or "II")
            mgt = management_component if management_component is not None else 0.55
            env = environmental_component if environmental_component is not None else 0.55
            raw = tm.compute_kurima_score(
                sat, mgt, env, stage,
                confidence_band=confidence_band,
                indices_trend=tm._indices_trend(hist),
                as_of_date=current_date.isoformat(),
            )
            return _normalise_tobacco_output(raw, confidence_band, confidence_pct)
        except Exception:
            pass  # fall through to generic

    return generic_crop_math.compute_generic_kurima_score(
        crop_type, phase, indices_history,
        management_component=management_component,
        environmental_component=environmental_component,
        confidence_band=confidence_band,
        confidence_pct=confidence_pct,
        current_ndvi=current_ndvi,
    )


# ---------------------------------------------------------------------------
# Component estimators (management / environmental / confidence) from sparse data
# ---------------------------------------------------------------------------
def _management_component(has_input_records: bool, has_planting_date: bool) -> float:
    c = 0.60
    c += 0.10 if has_input_records else -0.05
    c += 0.0 if has_planting_date else -0.10
    return max(0.0, min(1.0, c))


def _environmental_component(balance_status: Optional[str], urgency: str) -> float:
    base = {
        "surplus": 0.80, "balanced": 0.65, "deficit": 0.45, None: 0.55,
    }.get(balance_status, 0.55)
    if balance_status == "deficit" and urgency == "high":
        base = 0.30
    return max(0.0, min(1.0, base))


def _state_confidence(
    has_recent_satellite_pass: bool,
    has_variety_in_database: bool,
    has_planting_date: bool,
    has_input_records: bool,
) -> tuple[str, int]:
    frac = 0.50
    frac += 0.20 if has_recent_satellite_pass else -0.10
    frac += 0.15 if has_variety_in_database else 0.0
    frac += 0.10 if has_planting_date else -0.05
    frac += 0.05 if has_input_records else 0.0
    return classifiers.confidence_from_fraction(frac)


# ---------------------------------------------------------------------------
# Pure assembly (unit-testable, no I/O)
# ---------------------------------------------------------------------------
def assemble_field_state(
    *,
    field_row: Dict[str, Any],
    requester_id: Optional[str],
    daily_logs: List[Dict[str, Any]],
    variety_days_to_maturity: Optional[int] = None,
    variety_in_database: bool = False,
    input_record_count: int = 0,
    yield_raw: Optional[Dict[str, Any]] = None,
    weather_raw: Optional[Dict[str, Any]] = None,
    agri_raw: Optional[Dict[str, Any]] = None,
    gdd_raw: Optional[Dict[str, Any]] = None,
    plan_rows: Optional[List[Dict[str, Any]]] = None,
    alerts_raw: Optional[List[Dict[str, Any]]] = None,
    scouting_rows: Optional[List[Dict[str, Any]]] = None,
    now: Optional[datetime] = None,
    enforce_owner: bool = True,
) -> FieldState:
    """
    Build a :class:`FieldState` from already-fetched primitives.

    ``field_row`` must include at least ``id`` and ``user_id``. With
    ``enforce_owner=True`` (the default, used by direct callers/tests) this raises
    :class:`FieldAccessDenied` if ``requester_id`` does not match the field's
    ``user_id`` — a legacy backstop. The real pipeline (:func:`build_field_state`)
    passes ``enforce_owner=False`` because :func:`resolve_access` has already
    enforced tenant access (so institutional officers, whose user_id differs from
    the field's, are correctly allowed).
    """
    started = time.time()
    now = now or datetime.utcnow()
    today = now.date()

    owner = field_row.get("user_id")
    if enforce_owner and requester_id is not None and owner is not None and str(owner) != str(requester_id):
        raise FieldAccessDenied(field_row.get("id"))

    crop_type = field_row.get("crop_type") or field_row.get("crop")
    variety_code = field_row.get("variety")
    natural_region = field_row.get("natural_region")
    polygon = field_row.get("polygon_coordinates")
    area_ha = field_row.get("size_hectares") or field_row.get("area_ha")
    try:
        area_ha = float(area_ha) if area_ha is not None else None
    except (TypeError, ValueError):
        area_ha = None

    # --- season -----------------------------------------------------------
    is_transplanted = bool(field_row.get("is_transplanted")) or (crop_type or "").strip().lower() in _TRANSPLANTED_CROPS
    planting_date = _as_date(field_row.get("planting_date"))
    transplant_date = _as_date(field_row.get("transplant_date"))
    anchor_date = transplant_date if (is_transplanted and transplant_date) else planting_date

    maturity = _maturity_days(crop_type, variety_days_to_maturity)
    days_since = (today - anchor_date).days if anchor_date else None
    phase = generic_crop_math.detect_phase(days_since, maturity)
    expected_harvest = (anchor_date + timedelta(days=maturity)) if anchor_date else None
    days_to_harvest = (expected_harvest - today).days if expected_harvest else None
    season_progress = (
        int(round(100 * max(0, min(days_since, maturity)) / maturity))
        if (days_since is not None and maturity) else None
    )

    # --- indices (latest pass + trend) -----------------------------------
    logs = sorted(
        [l for l in (daily_logs or []) if isinstance(l, dict)],
        key=lambda r: str(r.get("log_date") or r.get("date") or ""),
    )
    latest = logs[-1] if logs else {}
    latest_date = _as_date(latest.get("log_date") or latest.get("date"))
    days_since_pass = (today - latest_date).days if latest_date else None
    current_ndvi = _num(latest.get("ndvi"))
    cloud_pct = _num(latest.get("cloud_cover") or latest.get("cloud_pct"))
    obs_quality = classifiers.observation_quality(days_since_pass, cloud_pct)
    has_recent_pass = obs_quality in ("good", "fair")

    ndvi_cls = classifiers.classify_ndvi(crop_type, phase, current_ndvi)
    # indices_history for scoring uses lowercase keys
    indices_history = [
        {"ndvi": _num(l.get("ndvi")), "evi": _num(l.get("evi")),
         "date": _iso(l.get("log_date") or l.get("date"))}
        for l in logs
    ]

    current_indices = CurrentIndices(
        as_of_date=_iso(latest_date),
        ndvi=current_ndvi,
        evi=_num(latest.get("evi")),
        ndre=None, ndmi=None, savi=None, sar_vv_db=None,  # not stored today (audit G2)
        observation_quality=obs_quality,
        cloud_pct=cloud_pct,
        ndvi_label=ndvi_cls["label"],
        ndvi_color=ndvi_cls["color"],
        ndvi_expected_low=ndvi_cls["expected_low"],
        ndvi_expected_high=ndvi_cls["expected_high"],
    )

    # --- water balance / soil moisture -----------------------------------
    wb_raw = (agri_raw or {}).get("water_balance", {}) if agri_raw else {}
    weekly_rain = _num(wb_raw.get("weekly_precipitation"))
    weekly_et = _num(wb_raw.get("weekly_et"))
    balance_mm = _num(wb_raw.get("balance"))
    if balance_mm is None and weekly_rain is not None and weekly_et is not None:
        balance_mm = round(weekly_rain - weekly_et, 1)
    wb_status, irrigate, urgency = classifiers.classify_water_balance(balance_mm)
    soil_moisture_pct = _num(latest.get("soil_moisture"))
    if soil_moisture_pct is None and agri_raw:
        soil_moisture_pct = _num((agri_raw.get("soil_moisture") or {}).get("shallow_pct"))
    soil_label = classifiers.classify_soil_moisture(crop_type, soil_moisture_pct)

    water_balance = WaterBalance(
        weekly_rainfall_mm=weekly_rain,
        weekly_et_mm=weekly_et,
        balance_mm=balance_mm,
        balance_status=wb_status,
        soil_moisture_pct=soil_moisture_pct,
        soil_moisture_label=soil_label,
        irrigation_recommended=irrigate,
        urgency=urgency,
    )

    # --- completeness + confidence ---------------------------------------
    completeness_pct, missing = classifiers.compute_completeness(
        has_variety_in_database=variety_in_database,
        has_recent_satellite_pass=has_recent_pass,
        has_input_records=input_record_count > 0,
        has_planting_date=anchor_date is not None,
        has_field_polygon=bool(polygon),
    )
    conf_band, conf_pct = _state_confidence(
        has_recent_pass, variety_in_database, anchor_date is not None, input_record_count > 0
    )

    # --- KurimaScore (the single source of health truth) ------------------
    mgmt_c = _management_component(input_record_count > 0, anchor_date is not None)
    env_c = _environmental_component(wb_status, urgency)
    score = compute_score(
        crop_type=crop_type, variety_code=variety_code, phase=phase,
        indices_history=indices_history, transplant_or_plant_date=anchor_date,
        current_date=today, natural_region=natural_region,
        management_component=mgmt_c, environmental_component=env_c,
        confidence_band=conf_band, confidence_pct=conf_pct, current_ndvi=current_ndvi,
    )
    kurima_score = KurimaScore(
        score=score["score"], label=score["label"], color=score["color"],
        components=KurimaScoreComponents(**(score.get("components") or {})),
        primary_driver=score.get("primary_driver"),
        likely_cause=score.get("likely_cause"),
        recommended_action=score.get("recommended_action"),
        yield_implication=score.get("yield_implication"),
        confidence_band=conf_band, confidence_pct=conf_pct,
    )

    # --- trend_30d (KurimaScore 0-100 over time, NOT raw NDVI) ------------
    trend: List[TrendPoint] = []
    for l in logs[-30:]:
        v = _num(l.get("ndvi"))
        pt_score = generic_crop_math.compute_generic_kurima_score(
            crop_type, phase, [{"ndvi": v}],
        )["score"] if v is not None else None
        trend.append(TrendPoint(
            date=_iso(l.get("log_date") or l.get("date")) or "",
            ndvi=v, kurima_score=pt_score,
        ))

    indices = Indices(current=current_indices, trend_30d=trend)

    # --- yield projection (banded confidence) ----------------------------
    yield_projection = _build_yield(yield_raw, area_ha)

    # --- weather ----------------------------------------------------------
    weather = _build_weather(weather_raw)

    # --- GDD --------------------------------------------------------------
    gdd = _build_gdd(gdd_raw)

    # --- plan items (contextualised against current alerts) --------------
    alerts = _build_alerts(alerts_raw, kurima_score, ndvi_cls, current_ndvi, water_balance, latest_date)
    plan_items = _build_plan_items(plan_rows, alerts)

    # --- scouting ---------------------------------------------------------
    scouting = [
        ScoutingObservation(
            id=str(s.get("id")), date=_iso(s.get("date")),
            type=s.get("type"), notes=s.get("notes"),
        )
        for s in (scouting_rows or []) if isinstance(s, dict)
    ]

    # --- data completeness ------------------------------------------------
    data_completeness = DataCompleteness(
        has_variety_in_database=variety_in_database,
        has_recent_satellite_pass=has_recent_pass,
        has_input_records=input_record_count > 0,
        has_planting_date=anchor_date is not None,
        has_field_polygon=bool(polygon),
        overall_completeness_pct=completeness_pct,
        missing_for_full_confidence=missing,
    )

    # --- meta -------------------------------------------------------------
    stale_warnings: List[str] = []
    if obs_quality == "stale":
        stale_warnings.append(
            f"Latest satellite pass is {days_since_pass} days old — indices may not reflect current conditions."
            if days_since_pass is not None else "No satellite pass on record."
        )
    if obs_quality == "none":
        stale_warnings.append("No satellite observations available for this field yet.")
    meta = Meta(
        generated_at=now.isoformat() + "Z",
        computation_time_ms=int(round((time.time() - started) * 1000)),
        stale_data_warnings=stale_warnings,
        as_of_satellite_pass=_iso(latest_date),
        next_satellite_pass_estimate=_iso(latest_date + timedelta(days=5)) if latest_date else None,
    )

    field_info = FieldInfo(
        id=str(field_row.get("id")),
        name=field_row.get("name") or "Unnamed field",
        crop_type=crop_type,
        variety_code=variety_code,
        area_ha=area_ha,
        natural_region=natural_region,
        polygon_coordinates=polygon if isinstance(polygon, list) else None,
        # Prefer the real tenant_id (Workstream 3); fall back to owner user_id for
        # rows not yet backfilled / direct-test field rows.
        tenant_id=field_row.get("tenant_id") or (str(owner) if owner is not None else None),
    )

    season = SeasonInfo(
        planted_date=_iso(anchor_date),
        days_since_planted=days_since,
        expected_harvest_date=_iso(expected_harvest),
        days_to_harvest=days_to_harvest,
        current_stage=score.get("stage") or phase,
        season_progress_pct=season_progress,
        season_phase=phase,
    )

    return FieldState(
        field=field_info,
        season=season,
        kurima_score=kurima_score,
        indices=indices,
        yield_projection=yield_projection,
        weather=weather,
        water_balance=water_balance,
        growing_degree_days=gdd,
        active_plan_items=plan_items,
        alerts=alerts,
        scouting_observations=scouting,
        data_completeness=data_completeness,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------
def _num(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


_NEG_FACTOR_HINTS = ("not in", "no ", "missing", "unavailable", "below", "without", "estimate", "lack")


def _build_yield(yield_raw: Optional[Dict[str, Any]], area_ha: Optional[float]) -> YieldProjection:
    if not yield_raw:
        return YieldProjection()
    projected = _num(yield_raw.get("projected_yield") or yield_raw.get("projected_tonnes_per_ha"))
    potential = _num(yield_raw.get("yield_potential") or yield_raw.get("potential_tonnes_per_ha"))
    gap = None
    if projected is not None and potential and potential > 0:
        gap = int(round(max(0.0, min(1.0, 1 - projected / potential)) * 100))
    band, pct = classifiers.confidence_from_fraction(_num(yield_raw.get("confidence_score")))
    factors = yield_raw.get("confidence_factors") or []
    positive, negative = [], []
    for f in factors:
        fl = str(f).lower()
        (negative if any(h in fl for h in _NEG_FACTOR_HINTS) else positive).append(str(f))
    bands = yield_raw.get("confidence_bands") or {}
    return YieldProjection(
        projected_tonnes_per_ha=projected,
        potential_tonnes_per_ha=potential,
        yield_gap_pct=gap,
        confidence_band=band,
        confidence_pct=pct,
        confidence_factors=ConfidenceFactors(positive=positive, negative=negative),
        confidence_interval_low=_num(bands.get("low")),
        confidence_interval_high=_num(bands.get("high")),
    )


def _build_weather(weather_raw: Optional[Dict[str, Any]]) -> Weather:
    if not weather_raw:
        return Weather()
    cur = weather_raw.get("current", {}) or {}
    current = CurrentWeather(
        temperature_c=_num(cur.get("temperature")),
        humidity_pct=_num(cur.get("humidity")),
        wind_kmh=_num(cur.get("wind_speed")),
        uv_index=_num(cur.get("uv_index")),
        condition=cur.get("weather_description") or cur.get("condition"),
        as_of=cur.get("time") or cur.get("as_of"),
    )
    daily = weather_raw.get("daily") or weather_raw.get("next_5_days") or []
    today = TodayWeather()
    forecast: List[ForecastDay] = []
    if daily:
        d0 = daily[0]
        today = TodayWeather(high=_num(d0.get("temp_max") or d0.get("high")),
                             low=_num(d0.get("temp_min") or d0.get("low")),
                             icon=d0.get("icon") or d0.get("weather_description"))
        for d in daily[1:6]:
            day_label = d.get("day")
            if not day_label and d.get("date"):
                dt = _as_date(d.get("date"))
                day_label = dt.strftime("%a") if dt else ""
            forecast.append(ForecastDay(
                day=day_label or "",
                high=_num(d.get("temp_max") or d.get("high")),
                low=_num(d.get("temp_min") or d.get("low")),
                icon=d.get("icon") or d.get("weather_description"),
            ))
    return Weather(current=current, today=today, next_5_days=forecast)


def _build_gdd(gdd_raw: Optional[Dict[str, Any]]) -> GrowingDegreeDays:
    if not gdd_raw:
        return GrowingDegreeDays()
    pct = gdd_raw.get("progress_percent")
    return GrowingDegreeDays(
        accumulated_gdd=_num(gdd_raw.get("total_gdd")),
        remaining_gdd=_num(gdd_raw.get("remaining_gdd")),
        progress_to_maturity_pct=int(round(pct)) if pct is not None else None,
        estimated_maturity_days=gdd_raw.get("days_to_maturity"),
        current_phase=gdd_raw.get("status"),
    )


_SEVERITY_MAP = {"info": "low", "warning": "medium", "critical": "high", "low": "low", "medium": "medium", "high": "high"}


def _build_alerts(
    alerts_raw: Optional[List[Dict[str, Any]]],
    kurima_score: KurimaScore,
    ndvi_cls: dict,
    current_ndvi: Optional[float],
    water_balance: WaterBalance,
    latest_date: Optional[date],
) -> List[Alert]:
    """Normalise upstream alerts and add derived alerts so the score and alerts
    can never disagree (contradiction resolution)."""
    alerts: List[Alert] = []

    # 1. Derived: canopy materially below stage expectation -> always an alert.
    if current_ndvi is not None and ndvi_cls.get("expected_low") is not None:
        if current_ndvi < ndvi_cls["expected_low"] * 0.85:
            alerts.append(Alert(
                severity="high" if kurima_score.score < 40 else "medium",
                category="canopy_stress",
                headline="Canopy below stage expectation",
                detail=(
                    f"NDVI {current_ndvi:.2f} is below the expected "
                    f"{ndvi_cls['expected_low']:.2f}-{ndvi_cls['expected_high']:.2f} band for this stage. "
                    f"KurimaScore is {kurima_score.score} ({kurima_score.label})."
                ),
                first_detected=latest_date.isoformat() if latest_date else None,
                recommended_action=kurima_score.recommended_action or "Scout the field to identify the stressor.",
            ))

    # 2. Derived: water deficit.
    if water_balance.irrigation_recommended and water_balance.urgency in ("medium", "high"):
        alerts.append(Alert(
            severity="high" if water_balance.urgency == "high" else "medium",
            category="water_stress",
            headline="Water deficit detected",
            detail=(
                f"Weekly water balance is {water_balance.balance_mm} mm "
                f"({water_balance.balance_status}); soil moisture {water_balance.soil_moisture_pct}% "
                f"({water_balance.soil_moisture_label})."
            ),
            recommended_action="Irrigation recommended within 48 hours where possible.",
        ))

    # 3. Upstream proactive-intelligence alerts.
    for a in (alerts_raw or []):
        if not isinstance(a, dict):
            continue
        sev = _SEVERITY_MAP.get(str(a.get("severity", "")).lower(), "medium")
        actions = a.get("recommended_actions") or a.get("recommended_action")
        if isinstance(actions, list):
            actions = "; ".join(actions)
        alerts.append(Alert(
            severity=sev,
            category=a.get("type") or a.get("category"),
            headline=a.get("title") or a.get("headline") or "Alert",
            detail=a.get("message") or a.get("detail"),
            first_detected=_iso(a.get("created_at") or a.get("first_detected")),
            recommended_action=actions,
        ))
    return alerts


def _build_plan_items(plan_rows: Optional[List[Dict[str, Any]]], alerts: List[Alert]) -> List[PlanItem]:
    """Map tasks to plan items, flagging any whose action conflicts with a
    current high-severity alert (e.g. 'apply foliar feed' during a water deficit)."""
    high_water_stress = any(a.severity == "high" and a.category in ("water_stress", "canopy_stress") for a in alerts)
    items: List[PlanItem] = []
    for t in (plan_rows or []):
        if not isinstance(t, dict):
            continue
        title = t.get("title") or t.get("activity") or "Task"
        ai_rec = bool(t.get("is_ai_generated") or t.get("ai_recommended"))
        contextualised = True
        notes = t.get("notes")
        # Conflict heuristic: feeding/spraying actions during high water stress.
        action_text = f"{title} {t.get('description', '')}".lower()
        if high_water_stress and any(k in action_text for k in ("foliar", "feed", "fertil", "top-dress", "topdress", "spray")):
            contextualised = False
            notes = (notes + " " if notes else "") + "Review this against current conditions — a high-severity water/canopy alert is active for this field."
        items.append(PlanItem(
            id=str(t.get("id")),
            date=_iso(t.get("task_date") or t.get("date")),
            category=t.get("activity_type") or t.get("category"),
            title=title,
            description=t.get("description"),
            status="completed" if t.get("completed") else (t.get("status") or "pending"),
            ai_recommended=ai_rec,
            contextualized_to_current_conditions=contextualised,
            notes=notes,
        ))
    return items


# ---------------------------------------------------------------------------
# I/O orchestration (lazy imports; best-effort everywhere)
# ---------------------------------------------------------------------------
def resolve_access(
    field_id: str,
    requester_id: str,
    tenant_ids: Optional[List[str]] = None,
    is_admin: bool = False,
) -> Dict[str, Any]:
    """
    Look the field up by id *without* a tenant filter, then enforce access.
    Raises FieldNotFound (404) if absent, FieldAccessDenied (403) otherwise.

    Access is granted if any of: admin; the field's ``tenant_id`` is in the
    caller's ``tenant_ids`` (the tenant model, Workstream 3); or — legacy
    fallback — the field's ``user_id`` equals ``requester_id`` (keeps consumers
    working even if tenant context is unavailable). Returns the field row dict.
    """
    from database import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    if not conn:
        raise FieldNotFound(field_id)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, user_id, tenant_id::text AS tenant_id, grower_id::text AS grower_id,
                   name, crop_type, variety, planting_date, transplant_date,
                   is_transplanted, size_hectares, polygon_coordinates,
                   fertilizer_history, health_score
            FROM fields WHERE id = %s::uuid
            """,
            (field_id,),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not row:
        raise FieldNotFound(field_id)

    field_tenant = row.get("tenant_id")
    allowed_tenants = {str(t) for t in (tenant_ids or [])}
    allowed = (
        is_admin
        or (field_tenant is not None and str(field_tenant) in allowed_tenants)
        or (row.get("user_id") is not None and str(row.get("user_id")) == str(requester_id))
    )
    if not allowed:
        raise FieldAccessDenied(field_id)
    return dict(row)


async def build_field_state(
    field_id: str,
    requester_id: str,
    tenant_ids: Optional[List[str]] = None,
    is_admin: bool = False,
) -> FieldState:
    """
    Full pipeline: resolve access, gather data from every subsystem (best-effort),
    and assemble the canonical FieldState. Target < 300ms for a single field.
    """
    field_row = resolve_access(field_id, requester_id, tenant_ids=tenant_ids, is_admin=is_admin)
    crop_type = field_row.get("crop_type")
    variety_code = field_row.get("variety")

    # --- DB reads (sync, fast) -------------------------------------------
    daily_logs = _fetch_daily_logs(field_id)
    input_count = _fetch_input_count(field_id)
    plan_rows = _fetch_plan_items(field_id, requester_id)
    scouting_rows = _fetch_scouting(field_id)

    # variety in tobacco DB?
    variety_in_db, variety_days = _resolve_variety(crop_type, variety_code)

    # --- coordinates ------------------------------------------------------
    lat, lon = _centroid(field_row.get("polygon_coordinates"))

    # --- climate (async, best-effort) ------------------------------------
    weather_raw = agri_raw = gdd_raw = None
    try:
        import climate_service
        cur = await climate_service.get_current_weather(lat, lon)
        fc = await climate_service.get_daily_forecast(lat, lon, days=6)
        weather_raw = {"current": cur, "daily": (fc or {}).get("daily", [])}
    except Exception:
        pass
    try:
        import climate_service
        agri_raw = await climate_service.get_agricultural_metrics(lat, lon)
    except Exception:
        pass
    try:
        import climate_service
        anchor = field_row.get("transplant_date") or field_row.get("planting_date")
        gdd_raw = await climate_service.calculate_gdd(
            lat, lon, start_date=_iso(anchor), crop_type=crop_type, variety=variety_code,
        )
    except Exception:
        pass

    # --- yield (sync, best-effort) ---------------------------------------
    yield_raw = _fetch_yield(field_row, daily_logs)

    # --- snapshot projection (fire-and-forget, own connection) -----------
    try:
        from services.calibration.snapshot import snapshot_projection
        snapshot_projection(field_row, yield_raw, daily_logs)
    except Exception:
        pass

    # --- alerts (async, best-effort) -------------------------------------
    alerts_raw = await _fetch_alerts(field_row, weather_raw)

    return assemble_field_state(
        field_row=field_row,
        requester_id=requester_id,
        daily_logs=daily_logs,
        variety_days_to_maturity=variety_days,
        variety_in_database=variety_in_db,
        input_record_count=input_count,
        yield_raw=yield_raw,
        weather_raw=weather_raw,
        agri_raw=agri_raw,
        gdd_raw=gdd_raw,
        plan_rows=plan_rows,
        alerts_raw=alerts_raw,
        scouting_rows=scouting_rows,
        # resolve_access already enforced tenant access; don't re-check by user_id
        # (institutional officers legitimately differ from the field's user_id).
        enforce_owner=False,
    )


# ---- DB fetch helpers (best-effort) ---------------------------------------
def _q(sql: str, params: tuple) -> List[Dict[str, Any]]:
    try:
        from database import get_db_connection
        from psycopg2.extras import RealDictCursor
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            cur.close()
            return rows
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        return []


def _fetch_daily_logs(field_id: str) -> List[Dict[str, Any]]:
    return _q(
        """
        SELECT log_date, ndvi, evi, soil_moisture, cloud_cover
        FROM daily_logs WHERE field_id = %s::uuid
        ORDER BY log_date ASC LIMIT 90
        """,
        (field_id,),
    )


def _fetch_input_count(field_id: str) -> int:
    rows = _q("SELECT COUNT(*) AS n FROM field_inputs WHERE field_id = %s::uuid", (field_id,))
    return int(rows[0]["n"]) if rows else 0


def _fetch_plan_items(field_id: str, user_id: str) -> List[Dict[str, Any]]:
    return _q(
        """
        SELECT id, title, description, activity_type, task_date, completed, is_ai_generated
        FROM farm_tasks
        WHERE field_id = %s::uuid AND user_id = %s AND completed = FALSE
        ORDER BY task_date ASC LIMIT 25
        """,
        (field_id, str(user_id)),
    )


def _fetch_scouting(field_id: str) -> List[Dict[str, Any]]:
    # Scouting is localStorage-only today (audit G4); return [] until a table exists.
    return []


def _resolve_variety(crop_type: Optional[str], variety_code: Optional[str]) -> tuple[bool, Optional[int]]:
    if not variety_code:
        return False, None
    if (crop_type or "").strip().lower() in _TOBACCO_CROPS:
        try:
            from crop_profiles.tobacco_flue_cured import tobacco_math as tm
            rec = tm.get_variety(variety_code)
            return True, rec.get("days_to_maturity_max")
        except Exception:
            return False, None
    # Non-tobacco: check crop_varieties table.
    rows = _q(
        "SELECT days_to_maturity FROM crop_varieties WHERE LOWER(variety_name) = LOWER(%s) LIMIT 1",
        (variety_code,),
    )
    if rows:
        return True, rows[0].get("days_to_maturity")
    return False, None


def _centroid(polygon: Any) -> tuple[float, float]:
    default = (-17.82, 31.05)
    if isinstance(polygon, list) and polygon:
        try:
            lats = [p["lat"] for p in polygon]
            lons = [p["lon"] for p in polygon]
            return sum(lats) / len(lats), sum(lons) / len(lons)
        except Exception:
            return default
    return default


def _fetch_yield(field_row: Dict[str, Any], daily_logs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    try:
        from yield_model import generate_yield_projection
        planting = _as_date(field_row.get("planting_date"))
        if not planting:
            return None
        ndvi_history = [float(l["ndvi"]) for l in daily_logs if l.get("ndvi") is not None]
        proj = generate_yield_projection(
            field_id=str(field_row.get("id")),
            crop=field_row.get("crop_type") or "Maize",
            variety=field_row.get("variety"),
            planting_date=planting,
            area_ha=float(field_row.get("size_hectares") or 0) or 1.0,
            fertilizer_history=field_row.get("fertilizer_history"),
            ndvi_history=ndvi_history or None,
            transplant_date=_as_date(field_row.get("transplant_date")),
            is_transplanted=bool(field_row.get("is_transplanted")),
        )
        return {
            "projected_yield": getattr(proj, "projected_yield", None),
            "yield_potential": getattr(proj, "yield_potential", None),
            "confidence_bands": getattr(proj, "confidence_bands", None),
            "confidence_score": getattr(proj, "confidence_score", None),
            "confidence_factors": getattr(proj, "confidence_factors", None),
        }
    except Exception:
        return None


async def _fetch_alerts(field_row: Dict[str, Any], weather_raw: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        from proactive_intelligence import generate_proactive_alerts
        planting = _as_date(field_row.get("planting_date"))
        if not planting:
            return []
        result = await generate_proactive_alerts(
            field_id=str(field_row.get("id")),
            field_name=field_row.get("name") or "Field",
            crop_type=field_row.get("crop_type") or "Maize",
            variety_name=field_row.get("variety") or "Generic",
            planting_date=planting,
            weather_data=(weather_raw or {}).get("current"),
            transplant_date=_as_date(field_row.get("transplant_date")),
            is_transplanted=bool(field_row.get("is_transplanted")),
        )
        return (result or {}).get("alerts", [])
    except Exception:
        return []
