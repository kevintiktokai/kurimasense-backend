"""
Climate Intelligence Service for KurimaSense
Integrates with Open-Meteo API for agricultural weather data
"""
import httpx
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import asyncio
from database import get_db_connection
from crop_constants import CROP_BASE_TEMPS as _CANONICAL_BASE_TEMPS, TRANSPLANTED_CROPS as _CANONICAL_TRANSPLANTED

# Open-Meteo API base URLs
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# Default location (Zimbabwe - Harare area)
DEFAULT_LAT = -17.82
DEFAULT_LON = 31.05

_http: Optional[httpx.AsyncClient] = None

# ---------------------------------------------------------------------------
# Module-local TTL cache for upstream Open-Meteo responses
#
# Keyed on (cache-namespace, lat rounded to 2dp, lon rounded to 2dp, *extras).
# 2dp ≈ 1.1 km, finer than Open-Meteo's grid resolution but coarse enough
# to deliver a high cache hit rate across users in the same area.
#
# A single client makes O(N) Open-Meteo calls per page visit (current,
# forecast, agricultural, alerts, spray-window, historical, gdd).  The
# cluster cache turns repeat visits within the TTL into near-zero-latency
# hits; cross-user calls in the same village also hit the same entry.
#
# TTLs are chosen so we re-fetch when source data actually changes:
#   current      ->  5 min  (Open-Meteo updates hourly anyway)
#   hourly       -> 10 min
#   daily        -> 10 min
#   agricultural -> 30 min  (soil temp/moisture move slowly)
#   alerts       -> 15 min  (derived from forecast)
#   spray        -> 15 min
#   historical   -> 24 hour (year-ago data does not change)
#   gdd          -> 60 min  (cumulative; one new day per request)
# ---------------------------------------------------------------------------
_cluster_cache: Dict[str, Tuple[float, Any]] = {}
_weather_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}  # legacy
_WEATHER_TTL = 60 * 5

CLIMATE_TTLS = {
    "current": 60 * 5,
    "hourly": 60 * 10,
    "daily": 60 * 10,
    "agricultural": 60 * 30,
    "alerts": 60 * 15,
    "spray": 60 * 15,
    "historical": 60 * 60 * 24,
    "gdd": 60 * 60,
    "full": 60 * 5,
}


def _get_http() -> httpx.AsyncClient:
    global _http
    if _http is None:
        _http = httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=10.0))
    return _http


def _cache_key(lat: float, lon: float, *extras: Any) -> str:
    """2-decimal rounded geo key plus optional extra discriminators."""
    base = f"{round(lat, 2)}:{round(lon, 2)}"
    if extras:
        base += ":" + ":".join("" if e is None else str(e) for e in extras)
    return base


def _cluster_get(namespace: str, key: str, ttl: int) -> Optional[Any]:
    entry = _cluster_cache.get(f"{namespace}:{key}")
    if not entry:
        return None
    ts, data = entry
    if time.time() - ts > ttl:
        _cluster_cache.pop(f"{namespace}:{key}", None)
        return None
    return data


def _cluster_set(namespace: str, key: str, data: Any) -> None:
    _cluster_cache[f"{namespace}:{key}"] = (time.time(), data)
    # Soft cap to avoid unbounded growth on cache key explosion.
    if len(_cluster_cache) > 5000:
        items = sorted(_cluster_cache.items(), key=lambda kv: kv[1][0])
        for k, _ in items[:1250]:
            _cluster_cache.pop(k, None)


def cluster_cache_stats() -> Dict[str, int]:
    return {"size": len(_cluster_cache)}


def _join_params(params: Dict[str, Any]) -> Dict[str, str]:
    """Convert list params to comma-separated strings for Open-Meteo API compatibility."""
    out = {}
    for k, v in params.items():
        if isinstance(v, list):
            out[k] = ",".join(str(x) for x in v)
        else:
            out[k] = v
    return out


async def get_current_weather(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> Dict[str, Any]:
    """
    Get current weather conditions for a location.
    Returns: temperature, humidity, wind speed/direction, precipitation, UV index, weather code
    """
    key = _cache_key(lat, lon)
    now = time.time()
    cached = _weather_cache.get(key)
    if cached and (now - cached[0]) < _WEATHER_TTL:
        return cached[1]

    params = _join_params({
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "uv_index",
            "cloud_cover",
            "pressure_msl"
        ],
        "timezone": "auto"
    })

    client = _get_http()
    response = await client.get(FORECAST_URL, params=params)
    response.raise_for_status()
    data = response.json()

    current = data.get("current", {})

    result = {
        "temperature": current.get("temperature_2m"),
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation": current.get("precipitation"),
        "weather_code": current.get("weather_code"),
        "weather_description": get_weather_description(current.get("weather_code", 0)),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_direction": current.get("wind_direction_10m"),
        "wind_direction_text": get_wind_direction_text(current.get("wind_direction_10m", 0)),
        "uv_index": current.get("uv_index"),
        "uv_level": get_uv_level(current.get("uv_index", 0)),
        "cloud_cover": current.get("cloud_cover"),
        "pressure": current.get("pressure_msl"),
        "time": current.get("time"),
        "timezone": data.get("timezone"),
        "location": {"lat": lat, "lon": lon}
    }
    _weather_cache[key] = (now, result)
    return result


async def get_hourly_forecast(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON, hours: int = 48) -> Dict[str, Any]:
    """
    Get hourly forecast for next N hours (max 168 = 7 days).
    """
    cache_key = _cache_key(lat, lon, hours)
    cached = _cluster_get("hourly", cache_key, CLIMATE_TTLS["hourly"])
    if cached is not None:
        return cached

    params = _join_params({
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "uv_index"
        ],
        "forecast_hours": min(hours, 168),
        "timezone": "auto"
    })

    client = _get_http()
    response = await client.get(FORECAST_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    
    forecast = []
    for i, time in enumerate(times[:hours]):
        forecast.append({
            "time": time,
            "temperature": hourly.get("temperature_2m", [])[i] if i < len(hourly.get("temperature_2m", [])) else None,
            "humidity": hourly.get("relative_humidity_2m", [])[i] if i < len(hourly.get("relative_humidity_2m", [])) else None,
            "precipitation_probability": hourly.get("precipitation_probability", [])[i] if i < len(hourly.get("precipitation_probability", [])) else None,
            "precipitation": hourly.get("precipitation", [])[i] if i < len(hourly.get("precipitation", [])) else None,
            "weather_code": hourly.get("weather_code", [])[i] if i < len(hourly.get("weather_code", [])) else None,
            "wind_speed": hourly.get("wind_speed_10m", [])[i] if i < len(hourly.get("wind_speed_10m", [])) else None,
            "uv_index": hourly.get("uv_index", [])[i] if i < len(hourly.get("uv_index", [])) else None,
        })
    
    result = {
        "location": {"lat": lat, "lon": lon},
        "timezone": data.get("timezone"),
        "hourly": forecast
    }
    _cluster_set("hourly", cache_key, result)
    return result


async def get_daily_forecast(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON, days: int = 7) -> Dict[str, Any]:
    """
    Get daily forecast for next N days (max 16).
    """
    cache_key = _cache_key(lat, lon, days)
    cached = _cluster_get("daily", cache_key, CLIMATE_TTLS["daily"])
    if cached is not None:
        return cached

    params = _join_params({
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "weather_code",
            "sunrise",
            "sunset",
            "uv_index_max",
            "wind_speed_10m_max",
            "et0_fao_evapotranspiration"
        ],
        "forecast_days": min(days, 16),
        "timezone": "auto"
    })

    client = _get_http()
    response = await client.get(FORECAST_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    daily = data.get("daily", {})
    times = daily.get("time", [])
    
    forecast = []
    for i, date in enumerate(times[:days]):
        weather_code = daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0
        forecast.append({
            "date": date,
            "temp_max": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
            "temp_min": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
            "feels_like_max": daily.get("apparent_temperature_max", [])[i] if i < len(daily.get("apparent_temperature_max", [])) else None,
            "feels_like_min": daily.get("apparent_temperature_min", [])[i] if i < len(daily.get("apparent_temperature_min", [])) else None,
            "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else None,
            "precipitation_probability": daily.get("precipitation_probability_max", [])[i] if i < len(daily.get("precipitation_probability_max", [])) else None,
            "weather_code": weather_code,
            "weather_description": get_weather_description(weather_code),
            "weather_icon": get_weather_icon(weather_code),
            "sunrise": daily.get("sunrise", [])[i] if i < len(daily.get("sunrise", [])) else None,
            "sunset": daily.get("sunset", [])[i] if i < len(daily.get("sunset", [])) else None,
            "uv_index_max": daily.get("uv_index_max", [])[i] if i < len(daily.get("uv_index_max", [])) else None,
            "wind_speed_max": daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
            "evapotranspiration": daily.get("et0_fao_evapotranspiration", [])[i] if i < len(daily.get("et0_fao_evapotranspiration", [])) else None,
        })
    
    result = {
        "location": {"lat": lat, "lon": lon},
        "timezone": data.get("timezone"),
        "daily": forecast
    }
    _cluster_set("daily", cache_key, result)
    return result


async def get_agricultural_metrics(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> Dict[str, Any]:
    """
    Get agricultural-specific metrics: soil moisture, soil temperature, evapotranspiration.
    """
    cache_key = _cache_key(lat, lon)
    cached = _cluster_get("agricultural", cache_key, CLIMATE_TTLS["agricultural"])
    if cached is not None:
        return cached

    params = _join_params({
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "soil_temperature_0cm",
            "soil_temperature_6cm",
            "soil_temperature_18cm",
            "soil_moisture_0_to_1cm",
            "soil_moisture_1_to_3cm",
            "soil_moisture_3_to_9cm",
            "et0_fao_evapotranspiration"
        ],
        "daily": [
            "et0_fao_evapotranspiration",
            "precipitation_sum"
        ],
        "forecast_days": 7,
        "timezone": "auto"
    })

    client = _get_http()
    response = await client.get(FORECAST_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    hourly = data.get("hourly", {})
    daily = data.get("daily", {})
    
    # Get current values (first/latest hourly reading)
    current_soil_temp_surface = hourly.get("soil_temperature_0cm", [None])[0]
    current_soil_temp_6cm = hourly.get("soil_temperature_6cm", [None])[0]
    current_soil_temp_18cm = hourly.get("soil_temperature_18cm", [None])[0]
    current_soil_moisture_surface = hourly.get("soil_moisture_0_to_1cm", [None])[0]
    current_soil_moisture_shallow = hourly.get("soil_moisture_1_to_3cm", [None])[0]
    current_soil_moisture_deep = hourly.get("soil_moisture_3_to_9cm", [None])[0]
    
    # Calculate averages and totals
    et_values = [v for v in daily.get("et0_fao_evapotranspiration", []) if v is not None]
    precip_values = [v for v in daily.get("precipitation_sum", []) if v is not None]
    
    avg_daily_et = sum(et_values) / len(et_values) if et_values else 0
    total_weekly_precip = sum(precip_values)
    total_weekly_et = sum(et_values)
    
    # Water balance indicator
    water_balance = total_weekly_precip - total_weekly_et
    water_status = "surplus" if water_balance > 10 else "balanced" if water_balance > -10 else "deficit"
    
    # Convert soil moisture from m³/m³ to percentage (roughly)
    soil_moisture_pct = round((current_soil_moisture_shallow or 0) * 100, 1) if current_soil_moisture_shallow else None
    
    result = {
        "location": {"lat": lat, "lon": lon},
        "soil_temperature": {
            "surface": current_soil_temp_surface,
            "depth_6cm": current_soil_temp_6cm,
            "depth_18cm": current_soil_temp_18cm,
            "unit": "°C"
        },
        "soil_moisture": {
            "surface_pct": round((current_soil_moisture_surface or 0) * 100, 1) if current_soil_moisture_surface else None,
            "shallow_pct": soil_moisture_pct,
            "deep_pct": round((current_soil_moisture_deep or 0) * 100, 1) if current_soil_moisture_deep else None,
            "status": get_moisture_status(soil_moisture_pct)
        },
        "evapotranspiration": {
            "today": et_values[0] if et_values else None,
            "avg_daily": round(avg_daily_et, 2),
            "weekly_total": round(total_weekly_et, 2),
            "unit": "mm"
        },
        "water_balance": {
            "weekly_precipitation": round(total_weekly_precip, 2),
            "weekly_et": round(total_weekly_et, 2),
            "balance": round(water_balance, 2),
            "status": water_status,
            "irrigation_recommendation": get_irrigation_recommendation(water_balance, soil_moisture_pct)
        }
    }
    _cluster_set("agricultural", cache_key, result)
    return result


async def calculate_gdd(
    lat: float = DEFAULT_LAT, 
    lon: float = DEFAULT_LON, 
    base_temp: float = 10.0,
    start_date: Optional[str] = None,
    crop_gdd_requirement: float = 2800,
    variety: Optional[str] = None,
    transplant_date: Optional[str] = None,
    is_transplanted: bool = False,
    crop_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate Growing Degree Days (GDD) from a start date to present.
    Uses historical weather data for past dates.
    
    GDD = max(0, (T_max + T_min) / 2 - T_base)
    
    Args:
        base_temp: Crop-specific base temperature (default 10°C for maize)
        start_date: Planting/seeding date in YYYY-MM-DD format (defaults to 90 days ago)
        crop_gdd_requirement: Total GDD needed for maturity (maize ~2700-2900)
        variety: Variety name for specific GDD lookup
        transplant_date: Date seedlings were transplanted (for transplanted crops)
        is_transplanted: Whether this is a transplanted crop
        crop_type: Type of crop (used to determine if transplanted)
    
    Note: For transplanted crops (Cabbage, Tomato, Onion, Potato), GDD is calculated
    from transplant_date, not planting_date. The nursery period (4-6 weeks) is not
    counted towards field GDD accumulation.
    """
    # Cache GDD results — they only change with the next day's weather.
    # Key includes everything that materially affects the result so two
    # different fields with the same params share the cache.
    today_bucket = datetime.now().strftime("%Y-%m-%d")
    gdd_cache_key = _cache_key(
        lat, lon,
        round(base_temp, 1), start_date or "auto",
        crop_gdd_requirement, variety or "", transplant_date or "",
        is_transplanted, crop_type or "", today_bucket,
    )
    _gdd_cached = _cluster_get("gdd", gdd_cache_key, CLIMATE_TTLS["gdd"])
    if _gdd_cached is not None:
        return _gdd_cached

    # Transplanted crops - use transplant_date instead of planting_date
    use_transplant_date = is_transplanted or (crop_type and crop_type in _CANONICAL_TRANSPLANTED)

    # Determine effective start date for GDD calculation
    effective_start_date = start_date
    if use_transplant_date and transplant_date:
        effective_start_date = transplant_date
        print(f"📅 Using transplant_date ({transplant_date}) for GDD calculation (transplanted crop)")
    
    if effective_start_date is None:
        effective_start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # Crop base temps — from crop_constants (single source of truth)
    # _CANONICAL_BASE_TEMPS uses lowercase keys; build Title-case lookup for backward compat
    CROP_BASE_TEMPS = {k.title(): v for k, v in _CANONICAL_BASE_TEMPS.items()}
    
    # Use crop-specific base temp if available
    if crop_type and crop_type in CROP_BASE_TEMPS:
        base_temp = CROP_BASE_TEMPS[crop_type]
    
    # [NEW] Lookup variety-specific GDD if provided
    if variety:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT days_to_maturity, crop_name FROM crop_varieties WHERE variety_name ILIKE %s", (variety,))
                row = cursor.fetchone()
                if row and row['days_to_maturity']:
                    # Heuristic: GDD ~= Days * factor (varies by crop)
                    # Maize: ~18 GDD/day (tropical summer)
                    # Vegetables: ~14-16 GDD/day (shorter cycle)
                    crop_name = row.get('crop_name', '')
                    if crop_name in ['Tomato', 'Cabbage', 'Onion', 'Potato']:
                        # Vegetables typically accumulate fewer GDD per day
                        crop_gdd_requirement = row['days_to_maturity'] * 15.0
                    else:
                        crop_gdd_requirement = row['days_to_maturity'] * 18.0
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Failed to lookup variety GDD: {e}")

    end_date = datetime.now().strftime("%Y-%m-%d")
    
    params = _join_params({
        "latitude": lat,
        "longitude": lon,
        "start_date": effective_start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "timezone": "auto"
    })

    client = _get_http()
    response = await client.get(HISTORICAL_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    t_max_list = daily.get("temperature_2m_max", [])
    t_min_list = daily.get("temperature_2m_min", [])
    
    total_gdd = 0
    daily_gdd = []
    
    for i, date in enumerate(dates):
        if i < len(t_max_list) and i < len(t_min_list):
            t_max = t_max_list[i]
            t_min = t_min_list[i]
            if t_max is not None and t_min is not None:
                avg_temp = (t_max + t_min) / 2
                gdd = max(0, avg_temp - base_temp)
                total_gdd += gdd
                daily_gdd.append({"date": date, "gdd": round(gdd, 1), "cumulative": round(total_gdd, 1)})
    
    # Calculate progress and estimated maturity
    progress_pct = min(100, (total_gdd / crop_gdd_requirement) * 100)
    remaining_gdd = max(0, crop_gdd_requirement - total_gdd)
    
    # Estimate days to maturity based on recent average GDD accumulation
    recent_daily_avg = total_gdd / max(1, len(daily_gdd))
    days_to_maturity = int(remaining_gdd / recent_daily_avg) if recent_daily_avg > 0 else None
    estimated_maturity_date = None
    if days_to_maturity:
        estimated_maturity_date = (datetime.now() + timedelta(days=days_to_maturity)).strftime("%Y-%m-%d")
    
    gdd_result = {
        "location": {"lat": lat, "lon": lon},
        "base_temperature": base_temp,
        "start_date": effective_start_date,
        "original_planting_date": start_date if use_transplant_date else None,
        "is_transplanted": use_transplant_date,
        "end_date": end_date,
        "total_gdd": round(total_gdd, 1),
        "crop_requirement": crop_gdd_requirement,
        "progress_percent": round(progress_pct, 1),
        "remaining_gdd": round(remaining_gdd, 1),
        "daily_avg_gdd": round(recent_daily_avg, 1),
        "days_to_maturity": days_to_maturity,
        "estimated_maturity_date": estimated_maturity_date,
        "daily_breakdown": daily_gdd[-14:],
        "status": get_gdd_status(progress_pct),
        "tracking_from": "transplant_date" if use_transplant_date else "planting_date",
    }
    _cluster_set("gdd", gdd_cache_key, gdd_result)
    return gdd_result


async def get_weather_alerts(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> Dict[str, Any]:
    """
    Generate weather alerts based on forecast conditions.
    Checks for: frost risk, heat stress, high winds, heavy rain, drought conditions.
    Uses AI-backed professional agronomist recommendations.
    """
    cache_key = _cache_key(lat, lon)
    cached = _cluster_get("alerts", cache_key, CLIMATE_TTLS["alerts"])
    if cached is not None:
        return cached

    # Concurrent under-the-hood fetch — both functions are themselves
    # cached now, so back-to-back calls re-use in-memory data.
    forecast, hourly = await asyncio.gather(
        get_daily_forecast(lat, lon, days=7),
        get_hourly_forecast(lat, lon, hours=72),
    )
    
    alerts = []
    
    for day in forecast.get("daily", []):
        date = day.get("date")
        temp_min = day.get("temp_min")
        temp_max = day.get("temp_max")
        wind_max = day.get("wind_speed_max")
        precip = day.get("precipitation")
        uv_max = day.get("uv_index_max")
        
        # Frost Alert (temp <= 2°C)
        if temp_min is not None and temp_min <= 2:
            severity = "high" if temp_min <= 0 else "medium"
            alerts.append({
                "type": "frost",
                "severity": severity,
                "date": date,
                "title": "🥶 Frost Risk Alert",
                "message": f"Temperature expected to drop to {temp_min}°C. Protect sensitive crops immediately.",
                "ai_powered": True,
                "recommendations": [
                    "Apply 20-30mm irrigation before sunset - water releases heat as it freezes, protecting root zones",
                    "Cover young seedlings with white frost cloth or dry grass mulch for 2-3°C protection",
                    "Delay planting new crops until frost risk passes - check 7-day forecast",
                    "Harvest any mature crops susceptible to frost damage within 24 hours"
                ]
            })
        
        # Heat Stress Alert (temp >= 35°C)
        if temp_max is not None and temp_max >= 35:
            severity = "high" if temp_max >= 40 else "medium"
            alerts.append({
                "type": "heat",
                "severity": severity,
                "date": date,
                "title": "🌡️ Heat Stress Warning",
                "message": f"High temperatures of {temp_max}°C expected. Crops and workers at risk.",
                "ai_powered": True,
                "recommendations": [
                    "Increase irrigation frequency to early morning (5-7am) and late afternoon (5-7pm)",
                    "Apply 5-10cm organic mulch around plants to reduce soil temperature by 5-8°C",
                    "Postpone transplanting and field work until evening hours when temps drop",
                    "Monitor for heat stress signs: leaf rolling in maize, wilting, premature flowering"
                ]
            })
        
        # High Wind Alert (wind >= 40 km/h)
        if wind_max is not None and wind_max >= 40:
            severity = "high" if wind_max >= 60 else "medium"
            alerts.append({
                "type": "wind",
                "severity": severity,
                "date": date,
                "title": "💨 High Wind Advisory",
                "message": f"Wind speeds up to {wind_max} km/h expected. Spray operations prohibited.",
                "ai_powered": True,
                "recommendations": [
                    "Postpone all spray operations - chemicals will drift and reduce efficacy by 50%+",
                    "Stake tall crops (maize, sunflower, sorghum) and secure greenhouse covers immediately",
                    "Delay irrigation to prevent water wastage from evaporation and spray drift",
                    "Check field drainage - strong winds often precede incoming rain systems"
                ]
            })
        
        # Heavy Rain Alert (precipitation >= 30mm)
        if precip is not None and precip >= 30:
            severity = "high" if precip >= 50 else "medium"
            alerts.append({
                "type": "rain",
                "severity": severity,
                "date": date,
                "title": "🌧️ Heavy Rain Expected",
                "message": f"Expect {precip}mm of rainfall. Prepare for waterlogging risk.",
                "ai_powered": True,
                "recommendations": [
                    "Check and clear field drainage channels before heavy rain arrives",
                    "Delay all fertilizer and pesticide applications - risk of runoff and pollution",
                    "Harvest any mature crops to prevent post-harvest losses from waterlogging",
                    "Scout for fungal diseases (anthracnose, downy mildew) 3-5 days after rain"
                ]
            })
        
        # Extreme UV Alert (UV >= 8)
        if uv_max is not None and uv_max >= 8:
            severity = "high" if uv_max >= 11 else "medium"
            alerts.append({
                "type": "uv",
                "severity": severity,
                "date": date,
                "title": "☀️ High UV Warning",
                "message": f"UV index reaching {uv_max}. Worker sun protection essential.",
                "ai_powered": True,
                "recommendations": [
                    "Schedule field work for early morning (before 10am) or late afternoon (after 4pm)",
                    "Provide shade structures and regular water breaks for all field workers",
                    "Apply sunscreen (SPF 30+) and wear wide-brimmed hats during outdoor work",
                    "Consider UV-reflective mulching to protect sensitive seedlings and transplants"
                ]
            })
    
    # Sort by severity (high first) then by date
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda x: (severity_order.get(x["severity"], 2), x["date"]))
    
    result = {
        "location": {"lat": lat, "lon": lon},
        "generated_at": datetime.now().isoformat(),
        "alert_count": len(alerts),
        "has_critical": any(a["severity"] == "high" for a in alerts),
        "alerts": alerts[:10]  # Limit to top 10 alerts
    }
    _cluster_set("alerts", cache_key, result)
    return result


async def get_spray_window(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON, hours: int = 72) -> Dict[str, Any]:
    """
    Calculate optimal spray windows based on weather conditions.

    Ideal conditions:
    - Wind speed: 3-10 km/h (too low = poor coverage, too high = drift)
    - No rain in next 6 hours
    - Temperature: 15-28°C
    - Humidity: 40-80%
    """
    cache_key = _cache_key(lat, lon, hours)
    cached = _cluster_get("spray", cache_key, CLIMATE_TTLS["spray"])
    if cached is not None:
        return cached

    hourly_data = await get_hourly_forecast(lat, lon, hours=hours)
    hourly = hourly_data.get("hourly", [])
    
    windows = []
    current_window = None
    
    for i, hour in enumerate(hourly):
        time = hour.get("time")
        temp = hour.get("temperature")
        wind = hour.get("wind_speed")
        precip_prob = hour.get("precipitation_probability", 0)
        humidity = hour.get("humidity")
        
        # Check if next 6 hours have rain
        future_precip = [
            hourly[j].get("precipitation_probability", 0) 
            for j in range(i, min(i + 6, len(hourly)))
        ]
        rain_coming = any((p or 0) > 50 for p in future_precip)
        
        # Evaluate conditions
        is_ideal = (
            wind is not None and 3 <= wind <= 10 and
            temp is not None and 15 <= temp <= 28 and
            (humidity is None or 40 <= humidity <= 80) and
            (precip_prob or 0) < 30 and
            not rain_coming
        )
        
        is_acceptable = (
            wind is not None and wind <= 15 and
            temp is not None and 10 <= temp <= 32 and
            (precip_prob or 0) < 50 and
            not rain_coming
        ) if not is_ideal else False
        
        status = "ideal" if is_ideal else ("acceptable" if is_acceptable else "avoid")
        
        windows.append({
            "time": time,
            "status": status,
            "temperature": temp,
            "wind_speed": wind,
            "precipitation_probability": precip_prob,
            "humidity": humidity,
            "reasons": get_spray_reasons(temp, wind, precip_prob, humidity, rain_coming)
        })
    
    # Group into spray windows
    ideal_windows = []
    current_start = None
    
    for i, w in enumerate(windows):
        if w["status"] == "ideal":
            if current_start is None:
                current_start = w["time"]
        else:
            if current_start is not None:
                ideal_windows.append({
                    "start": current_start,
                    "end": windows[i-1]["time"],
                    "status": "ideal"
                })
                current_start = None
    
    if current_start is not None:
        ideal_windows.append({
            "start": current_start,
            "end": windows[-1]["time"],
            "status": "ideal"
        })
    
    result = {
        "location": {"lat": lat, "lon": lon},
        "generated_at": datetime.now().isoformat(),
        "ideal_conditions": {
            "wind_speed": "3-10 km/h",
            "temperature": "15-28°C",
            "humidity": "40-80%",
            "precipitation_probability": "<30%"
        },
        "ideal_windows": ideal_windows[:5],
        "hourly_breakdown": windows
    }
    _cluster_set("spray", cache_key, result)
    return result


async def get_historical_comparison(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> Dict[str, Any]:
    """
    Compare current conditions with historical averages for the same period.
    Uses data from 1 year ago for comparison (more relevant for year-over-year performance).
    """
    # 24-hour TTL — year-ago data does not change.  Bucket by date so a
    # midnight rollover invalidates yesterday's entry.
    cache_key = _cache_key(lat, lon, datetime.now().strftime("%Y-%m-%d"))
    cached = _cluster_get("historical", cache_key, CLIMATE_TTLS["historical"])
    if cached is not None:
        return cached

    current = await get_current_weather(lat, lon)
    daily = await get_daily_forecast(lat, lon, days=7)
    
    # Get historical data for same week, 1 year ago
    today = datetime.now()
    historical_start = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    historical_end = (today - timedelta(days=365) + timedelta(days=7)).strftime("%Y-%m-%d")
    
    params = _join_params({
        "latitude": lat,
        "longitude": lon,
        "start_date": historical_start,
        "end_date": historical_end,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum"
        ],
        "timezone": "auto"
    })

    try:
        client = _get_http()
        response = await client.get(HISTORICAL_URL, params=params)
        response.raise_for_status()
        historical_data = response.json()
        
        hist_daily = historical_data.get("daily", {})
        hist_temps_max = [t for t in hist_daily.get("temperature_2m_max", []) if t is not None]
        hist_temps_min = [t for t in hist_daily.get("temperature_2m_min", []) if t is not None]
        hist_precip = [p for p in hist_daily.get("precipitation_sum", []) if p is not None]
        
        hist_avg_max = sum(hist_temps_max) / len(hist_temps_max) if hist_temps_max else None
        hist_avg_min = sum(hist_temps_min) / len(hist_temps_min) if hist_temps_min else None
        hist_avg_precip = sum(hist_precip) / len(hist_precip) if hist_precip else None
        
    except Exception:
        hist_avg_max = None
        hist_avg_min = None
        hist_avg_precip = None
    
    # Current week averages
    current_temps_max = [d.get("temp_max") for d in daily.get("daily", []) if d.get("temp_max") is not None]
    current_temps_min = [d.get("temp_min") for d in daily.get("daily", []) if d.get("temp_min") is not None]
    current_precip = [d.get("precipitation") for d in daily.get("daily", []) if d.get("precipitation") is not None]
    
    current_avg_max = sum(current_temps_max) / len(current_temps_max) if current_temps_max else None
    current_avg_min = sum(current_temps_min) / len(current_temps_min) if current_temps_min else None
    current_avg_precip = sum(current_precip) / len(current_precip) if current_precip else None
    
    # Calculate deviations
    temp_deviation = None
    precip_deviation = None
    
    if current_avg_max and hist_avg_max:
        temp_deviation = round(current_avg_max - hist_avg_max, 1)
    
    if current_avg_precip is not None and hist_avg_precip is not None and hist_avg_precip > 0:
        precip_deviation = round(((current_avg_precip - hist_avg_precip) / hist_avg_precip) * 100, 1)
    
    result = {
        "location": {"lat": lat, "lon": lon},
        "comparison_period": f"Same week, 1 year ago ({historical_start})",
        "current": {
            "temperature": current.get("temperature"),
            "avg_temp_max": round(current_avg_max, 1) if current_avg_max else None,
            "avg_temp_min": round(current_avg_min, 1) if current_avg_min else None,
            "avg_daily_precip": round(current_avg_precip, 1) if current_avg_precip is not None else None
        },
        "historical": {
            "avg_temp_max": round(hist_avg_max, 1) if hist_avg_max else None,
            "avg_temp_min": round(hist_avg_min, 1) if hist_avg_min else None,
            "avg_daily_precip": round(hist_avg_precip, 1) if hist_avg_precip is not None else None
        },
        "deviation": {
            "temperature": temp_deviation,
            "temperature_text": get_temp_deviation_text(temp_deviation),
            "precipitation": precip_deviation,
            "precipitation_text": get_precip_deviation_text(precip_deviation)
        }
    }
    _cluster_set("historical", cache_key, result)
    return result


# ==================== HELPER FUNCTIONS ====================

def get_weather_description(code: int) -> str:
    """Convert WMO weather code to human-readable description."""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return descriptions.get(code, "Unknown")


def get_weather_icon(code: int) -> str:
    """Get emoji icon for weather code."""
    if code == 0:
        return "☀️"
    elif code in [1, 2]:
        return "🌤️"
    elif code == 3:
        return "☁️"
    elif code in [45, 48]:
        return "🌫️"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "🌧️"
    elif code in [66, 67]:
        return "🌨️"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "❄️"
    elif code in [95, 96, 99]:
        return "⛈️"
    return "🌡️"


def get_wind_direction_text(degrees: float) -> str:
    """Convert wind direction degrees to compass direction."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]


def get_uv_level(uv_index: float) -> str:
    """Get UV exposure level description."""
    if uv_index < 3:
        return "Low"
    elif uv_index < 6:
        return "Moderate"
    elif uv_index < 8:
        return "High"
    elif uv_index < 11:
        return "Very High"
    return "Extreme"


def get_moisture_status(moisture_pct: Optional[float]) -> str:
    """Get soil moisture status."""
    if moisture_pct is None:
        return "Unknown"
    if moisture_pct < 20:
        return "Very Dry"
    elif moisture_pct < 35:
        return "Dry"
    elif moisture_pct < 55:
        return "Adequate"
    elif moisture_pct < 75:
        return "Moist"
    return "Saturated"


def get_irrigation_recommendation(water_balance: float, soil_moisture: Optional[float]) -> str:
    """Generate irrigation recommendation based on water balance and soil moisture."""
    if water_balance < -20 or (soil_moisture and soil_moisture < 25):
        return "Irrigation strongly recommended. Significant water deficit detected."
    elif water_balance < -10 or (soil_moisture and soil_moisture < 35):
        return "Consider irrigation within the next few days."
    elif water_balance > 20 or (soil_moisture and soil_moisture > 70):
        return "No irrigation needed. Soil moisture is adequate."
    return "Monitor conditions. Irrigation may be needed soon."


def get_gdd_status(progress_pct: float) -> str:
    """Get crop growth stage based on GDD progress."""
    if progress_pct < 20:
        return "Early vegetative"
    elif progress_pct < 40:
        return "Mid vegetative"
    elif progress_pct < 60:
        return "Late vegetative / Early reproductive"
    elif progress_pct < 80:
        return "Reproductive / Grain fill"
    elif progress_pct < 95:
        return "Maturation"
    return "Harvest ready"


def get_spray_reasons(temp: Optional[float], wind: Optional[float], precip_prob: Optional[float], humidity: Optional[float], rain_coming: bool) -> List[str]:
    """Get list of reasons for spray window status."""
    reasons = []
    
    if wind is not None:
        if wind < 3:
            reasons.append("Wind too low - poor spray distribution")
        elif wind > 15:
            reasons.append("Wind too high - spray drift risk")
        elif wind > 10:
            reasons.append("Wind slightly elevated")
    
    if temp is not None:
        if temp < 10:
            reasons.append("Temperature too low for effective uptake")
        elif temp > 32:
            reasons.append("Temperature too high - rapid evaporation")
        elif temp < 15 or temp > 28:
            reasons.append("Temperature outside ideal range")
    
    if precip_prob is not None and precip_prob > 30:
        reasons.append(f"Rain probability: {precip_prob}%")
    
    if rain_coming:
        reasons.append("Rain expected within 6 hours - spray may wash off")
    
    if humidity is not None:
        if humidity < 40:
            reasons.append("Low humidity - increased evaporation")
        elif humidity > 80:
            reasons.append("High humidity - slower drying")
    
    if not reasons:
        reasons.append("Conditions optimal for spraying")
    
    return reasons


def get_temp_deviation_text(deviation: Optional[float]) -> str:
    """Get description of temperature deviation from historical."""
    if deviation is None:
        return "Historical data unavailable"
    if deviation > 3:
        return f"Significantly warmer (+{deviation}°C)"
    elif deviation > 1:
        return f"Slightly warmer (+{deviation}°C)"
    elif deviation < -3:
        return f"Significantly cooler ({deviation}°C)"
    elif deviation < -1:
        return f"Slightly cooler ({deviation}°C)"
    return "Near historical average"


def get_precip_deviation_text(deviation: Optional[float]) -> str:
    """Get description of precipitation deviation from historical."""
    if deviation is None:
        return "Historical data unavailable"
    if deviation > 50:
        return f"Much wetter than normal (+{deviation}%)"
    elif deviation > 20:
        return f"Wetter than normal (+{deviation}%)"
    elif deviation < -50:
        return f"Much drier than normal ({deviation}%)"
    elif deviation < -20:
        return f"Drier than normal ({deviation}%)"
    return "Near normal precipitation"


# ==================== COMBINED CLIMATE DATA ====================

async def get_full_climate_data(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> Dict[str, Any]:
    """
    Get comprehensive climate data in a single call for the dashboard.

    The frontend should prefer this endpoint (mapped to /climate/full) over
    the six individual ones — it returns the same payload but in one HTTP
    round-trip and one logical fan-out.

    Each underlying function is independently cached.  Within the 5-minute
    "full" TTL we serve the entire bundle from this top-level cache so we
    don't even pay for the asyncio.gather scheduling overhead.
    """
    cache_key = _cache_key(lat, lon)
    cached = _cluster_get("full", cache_key, CLIMATE_TTLS["full"])
    if cached is not None:
        return cached

    current, hourly, daily, agricultural, alerts, historical = await asyncio.gather(
        get_current_weather(lat, lon),
        get_hourly_forecast(lat, lon, hours=48),
        get_daily_forecast(lat, lon, days=7),
        get_agricultural_metrics(lat, lon),
        get_weather_alerts(lat, lon),
        get_historical_comparison(lat, lon),
        return_exceptions=True
    )

    def safe_result(result, default=None):
        return result if not isinstance(result, Exception) else default

    result = {
        "current": safe_result(current, {}),
        "hourly": safe_result(hourly, {"hourly": []}),
        "daily": safe_result(daily, {"daily": []}),
        "agricultural": safe_result(agricultural, {}),
        "alerts": safe_result(alerts, {"alerts": []}),
        "historical": safe_result(historical, {}),
        "generated_at": datetime.now().isoformat()
    }
    _cluster_set("full", cache_key, result)
    return result


# ==================== AI-POWERED AGRONOMIST RECOMMENDATIONS ====================

async def generate_ai_recommendations(
    alert_type: str,
    alert_data: Dict[str, Any],
    agricultural_context: Optional[Dict[str, Any]] = None,
    crop_type: str = "maize"
) -> List[str]:
    """
    Generate AI-powered agronomist recommendations for weather alerts.
    Uses OpenAI to provide contextual, professional advice.
    
    Args:
        alert_type: Type of alert (frost, heat, wind, rain, uv)
        alert_data: Alert details including severity, temperatures, etc.
        agricultural_context: Optional soil moisture, GDD, water balance data
        crop_type: Primary crop being grown
    
    Returns:
        List of AI-generated recommendations
    """
    import os
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or "your_" in api_key or "placeholder" in api_key:
            # Fallback to static recommendations if no API key
            return get_static_recommendations(alert_type, alert_data)
        
        client = OpenAI(api_key=api_key)
        
        # Build context for the AI
        context = f"""You are a professional agronomist for the KurimaSense platform.
Generate 3-4 specific, actionable recommendations for a farmer facing {alert_type} weather conditions.

Weather Alert Details:
- Type: {alert_type}
- Severity: {alert_data.get('severity', 'medium')}
- Message: {alert_data.get('message', '')}
- Date: {alert_data.get('date', 'upcoming')}

Agricultural Context:
- Primary Crop: {crop_type}
"""
        if agricultural_context:
            if agricultural_context.get('water_balance'):
                wb = agricultural_context['water_balance']
                context += f"- Water Balance: {wb.get('balance', 0):.1f}mm ({wb.get('status', 'unknown')})\n"
            if agricultural_context.get('soil_moisture'):
                sm = agricultural_context['soil_moisture']
                context += f"- Soil Moisture: {sm.get('shallow_pct', 0):.0f}% ({sm.get('status', 'unknown')})\n"
            if agricultural_context.get('growing_degree_days'):
                gdd = agricultural_context['growing_degree_days']
                context += f"- Growth Stage: {gdd.get('status', 'unknown')} ({gdd.get('progress_percent', 0):.0f}% to maturity)\n"

        context += """
Requirements:
1. Be specific and actionable (include timing, quantities where appropriate)
2. Consider the local African farming context
3. Prioritize low-cost, practical solutions
4. Include both immediate actions and preventive measures
5. Keep each recommendation under 25 words

Return ONLY a JSON array of 3-4 recommendation strings, nothing else."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": context}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=300,
            timeout=10
        )
        
        content = response.choices[0].message.content
        if content:
            import json
            try:
                parsed = json.loads(content)
                # Handle various JSON formats the AI might return
                if isinstance(parsed, list):
                    return parsed[:4]
                elif isinstance(parsed, dict):
                    # Look for common keys
                    for key in ['recommendations', 'advice', 'suggestions', 'actions']:
                        if key in parsed and isinstance(parsed[key], list):
                            return parsed[key][:4]
            except json.JSONDecodeError:
                pass
        
        return get_static_recommendations(alert_type, alert_data)
        
    except Exception as e:
        print(f"AI Recommendation Error: {e}")
        return get_static_recommendations(alert_type, alert_data)


def get_static_recommendations(alert_type: str, alert_data: Dict[str, Any]) -> List[str]:
    """
    Fallback static recommendations when AI is unavailable.
    These are professional agronomist-quality recommendations.
    """
    recommendations_db = {
        "frost": [
            "Apply 20-30mm irrigation before sunset - water releases heat as it freezes, protecting roots",
            "Cover young seedlings with white frost cloth or dry grass mulch for 2-3°C protection",
            "Delay planting new crops until frost risk passes - check 7-day forecast",
            "Harvest any mature crops susceptible to frost damage within 24 hours"
        ],
        "heat": [
            "Increase irrigation frequency to early morning and late afternoon (avoid midday evaporation)",
            "Apply 5-10cm organic mulch around plants to reduce soil temperature by 5-8°C",
            "Postpone any transplanting or field work until evening hours",
            "Monitor for signs of heat stress: leaf rolling, wilting, premature flowering"
        ],
        "wind": [
            "Postpone all spray operations - chemicals will drift and reduce efficacy by 50%+",
            "Stake tall crops (maize, sunflower) and secure greenhouse covers immediately",
            "Delay irrigation to prevent water wastage from evaporation and drift",
            "Check field drainage - strong winds often precede rain systems"
        ],
        "rain": [
            "Check and clear field drainage channels before heavy rain arrives",
            "Delay all fertilizer and pesticide applications - risk of runoff and pollution",
            "Harvest any mature crops to prevent post-harvest losses from waterlogging",
            "Scout for fungal diseases 3-5 days after rain - early intervention is critical"
        ],
        "uv": [
            "Schedule field work for early morning (before 10am) or late afternoon (after 4pm)",
            "Provide shade structures and regular water breaks for all field workers",
            "Apply sunscreen (SPF 30+) and wear wide-brimmed hats during outdoor work",
            "Consider UV-reflective mulching to protect sensitive crop varieties"
        ]
    }
    
    return recommendations_db.get(alert_type, [
        "Monitor conditions closely and prepare for changing weather",
        "Check crop health status and document any stress symptoms",
        "Consult local extension services for region-specific guidance"
    ])
