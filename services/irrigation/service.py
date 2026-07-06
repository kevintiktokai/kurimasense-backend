"""
Irrigation service — wires the pure decision core (engine.py) to KurimaSense
data: fields, crop profiles, Soil Intelligence, the climate service, and the
planner.

Also owns the planner integration: ``ensure_planner_task`` materialises an
actionable recommendation as an AI-generated ``farm_tasks`` row (idempotent per
field per day), which is how recommendations "automatically appear as
intelligent planner tasks".
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from psycopg2.extras import RealDictCursor

import climate_service
from crop_profiles import get_current_stage_for_crop
from database import get_db_connection

from .engine import recommend
from .models import (
    DEFAULT_AWC_MM_PER_M,
    DEFAULT_IRRIGATION_METHOD,
    DEFAULT_MAX_ROOT_DEPTH_M,
    MAX_ROOT_DEPTH_BY_CROP_M,
    MIN_ROOT_DEPTH_M,
    DayWeather,
    IrrigationInputs,
    IrrigationRecommendation,
)

_DEFAULT_LOCATION = (-17.82, 31.05)  # Harare fallback, same as climate_service


def _centroid(polygon: Any) -> Tuple[float, float]:
    if isinstance(polygon, list) and polygon:
        try:
            lats = [p["lat"] for p in polygon]
            lons = [p["lon"] for p in polygon]
            return sum(lats) / len(lats), sum(lons) / len(lons)
        except Exception:
            pass
    return _DEFAULT_LOCATION


def _as_date(value: Any) -> Optional[date]:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value[:10]).date()
        except ValueError:
            return None
    return None


def _root_depth_m(crop: str, days_since_planting: int, season_length_days: int) -> float:
    """Two-point root growth model: MIN at emergence → crop max by mid-season."""
    max_depth = MAX_ROOT_DEPTH_BY_CROP_M.get((crop or "").strip().lower(), DEFAULT_MAX_ROOT_DEPTH_M)
    if season_length_days <= 0:
        return max_depth
    # Roots reach full depth around 60% of the season (flowering for annuals).
    progress = min(days_since_planting / (season_length_days * 0.6), 1.0)
    return round(MIN_ROOT_DEPTH_M + (max_depth - MIN_ROOT_DEPTH_M) * progress, 2)


def _soil_awc(field_id: str) -> Tuple[float, str]:
    """Plant-available water capacity (mm/m) from the Soil Intelligence profile,
    or the loam default when no profile exists yet."""
    try:
        from services.soil_intelligence.repository import load_profile
        profile = load_profile(field_id)
        if profile is not None:
            whc = profile.value("water_holding_capacity")
            if whc:
                return float(whc), "soil_profile"
    except Exception as e:
        print(f"[irrigation] soil profile lookup failed for {field_id}: {e}")
    return DEFAULT_AWC_MM_PER_M, "default"


def _recorded_irrigation_dates(field_id: str, days: int = 21) -> List[str]:
    """ISO dates with completed irrigation tasks in the planner (best signal we
    have for applied water until amount capture lands)."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT DISTINCT COALESCE(completed_at::date, task_date) AS d
            FROM farm_tasks
            WHERE field_id = %s::uuid AND activity_type = 'irrigation' AND completed = TRUE
              AND COALESCE(completed_at::date, task_date) > CURRENT_DATE - %s
            """,
            (field_id, days),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [r["d"].isoformat() for r in rows if r.get("d")]
    except Exception as e:
        print(f"[irrigation] irrigation history lookup failed: {e}")
        return []
    finally:
        conn.close()


async def recommendation_for_field_row(
    field_row: Dict[str, Any],
    method: Optional[str] = None,
) -> Optional[IrrigationRecommendation]:
    """Compute a recommendation from an already-loaded fields row
    (needs: id, name, crop_type, planting_date, polygon_coordinates).
    Returns None when the field can't be evaluated (no planting date/stage)."""
    planting = _as_date(field_row.get("planting_date"))
    crop = (field_row.get("crop_type") or field_row.get("crop") or "").strip()
    if not planting or not crop:
        return None
    days_since_planting = (date.today() - planting).days
    if days_since_planting < 0:
        return None

    stage = get_current_stage_for_crop(crop, days_since_planting)
    if stage is None:
        return None
    season_length = stage.day_range[1]
    try:
        from crop_profiles import get_crop_profile_or_generic
        profile = get_crop_profile_or_generic(crop)
        if profile.growth_stages:
            season_length = profile.growth_stages[-1].day_range[1]
    except Exception:
        pass

    field_id = str(field_row["id"])
    lat, lon = _centroid(field_row.get("polygon_coordinates"))
    series = await climate_service.get_water_balance_series(lat, lon, past_days=14, forecast_days=7)

    def to_days(rows: List[Dict[str, Any]]) -> List[DayWeather]:
        return [DayWeather(
            date=r.get("date"), et0=r.get("et0"), precip=r.get("precip"),
            precip_probability=r.get("precip_probability"),
            tmax=r.get("tmax"), tmin=r.get("tmin"),
        ) for r in (rows or [])]

    awc, awc_source = _soil_awc(field_id)
    inputs = IrrigationInputs(
        field_id=field_id,
        field_name=field_row.get("name") or "Field",
        crop=crop,
        stage_name=stage.stage_name,
        kc=float(stage.water_kc),
        days_since_planting=days_since_planting,
        awc_mm_per_m=awc,
        awc_source=awc_source,
        root_depth_m=_root_depth_m(crop, days_since_planting, season_length),
        past=to_days((series or {}).get("past")),
        forecast=to_days((series or {}).get("forecast")),
        irrigation_dates=_recorded_irrigation_dates(field_id),
        method=method or DEFAULT_IRRIGATION_METHOD,
    )
    return recommend(inputs)


def ensure_planner_task(field_row: Dict[str, Any], rec: IrrigationRecommendation) -> Optional[Dict[str, Any]]:
    """Materialise an actionable recommendation as an AI planner task —
    idempotent: one open AI irrigation task per field per day."""
    if rec.action not in ("irrigate_now", "irrigate_soon"):
        return None
    user_id = field_row.get("user_id")
    if not user_id:
        return None
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        task_date = date.today() if rec.action == "irrigate_now" else date.today() + timedelta(days=1)
        cursor.execute(
            """
            SELECT id FROM farm_tasks
            WHERE field_id = %s::uuid AND activity_type = 'irrigation'
              AND is_ai_generated = TRUE AND completed = FALSE
              AND task_date >= CURRENT_DATE
            LIMIT 1
            """,
            (rec.field_id,),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            return {"id": str(existing["id"]), "created": False}

        duration = f" (~{rec.duration_minutes} min)" if rec.duration_minutes else ""
        title = f"Irrigate {rec.field_name}: ~{rec.recommended_mm:.0f}mm{duration}"
        description = rec.headline + "\n" + "\n".join(f"• {r}" for r in rec.reasoning)
        cursor.execute(
            """
            INSERT INTO farm_tasks
                (user_id, field_id, title, description, activity_type, priority,
                 task_date, is_ai_generated)
            VALUES (%s, %s::uuid, %s, %s, 'irrigation', %s, %s, TRUE)
            RETURNING id
            """,
            (
                user_id, rec.field_id, title, description[:2000],
                "urgent" if rec.action == "irrigate_now" else "high",
                task_date,
            ),
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        return {"id": str(row["id"]), "created": True}
    except Exception as e:
        print(f"[irrigation] ensure_planner_task failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        conn.close()
