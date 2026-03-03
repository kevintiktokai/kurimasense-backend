import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


REQUEST_TIMEOUT_SECONDS = 20
RETRY_ATTEMPTS = 3
CACHE_TTL_SECONDS = 1800


def _error(message):
    return {"status": "error", "error_message": message}


def _load_seed():
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input received on stdin")
    return json.loads(raw)


def _extract_location(seed):
    location = seed.get("location") or {}
    if "lat" not in location or "lon" not in location:
        raise ValueError("Seed.location must include lat and lon")
    return location["lat"], location["lon"]


def fetch_weather(lat, lon, api_key):
    cached = _read_cache(lat, lon)
    if cached:
        return cached

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }
    last_error = None
    for _ in range(RETRY_ATTEMPTS):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            last_error = exc
            continue
        if response.status_code != 200:
            raise RuntimeError(
                f"OpenWeatherMap error {response.status_code}: {response.text}"
            )
        payload = response.json()
        break
    else:
        raise RuntimeError(f"OpenWeatherMap request failed: {last_error}")
    items = payload.get("list", [])
    if not items:
        raise RuntimeError("OpenWeatherMap response missing forecast data")

    current = items[0]
    pops = [entry.get("pop", 0.0) for entry in items[:8]]
    precip_avg = sum(pops) / len(pops) if pops else 0.0
    weather_desc = current.get("weather", [{}])[0].get("description")

    data = {
        "current_temp": current.get("main", {}).get("temp"),
        "precip_chance_24h": round(precip_avg, 3),
        "humidity": current.get("main", {}).get("humidity"),
        "forecast_summary": weather_desc,
        "source": "openweathermap",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_cache(lat, lon, data)
    return data


def _cache_path(lat, lon):
    tmp_dir = Path.cwd() / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    key = f"weather_{lat:.4f}_{lon:.4f}.json"
    return tmp_dir / key


def _read_cache(lat, lon):
    path = _cache_path(lat, lon)
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    fetched_at = cached.get("fetched_at")
    if not fetched_at:
        return None
    try:
        ts = datetime.fromisoformat(fetched_at)
    except ValueError:
        return None
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    if age > CACHE_TTL_SECONDS:
        return None
    return cached


def _write_cache(lat, lon, data):
    path = _cache_path(lat, lon)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    load_dotenv()
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key or "your_" in api_key:
        sys.stdout.write(json.dumps(_error("WEATHER_API_KEY missing or placeholder")))
        return

    try:
        seed = _load_seed()
        lat, lon = _extract_location(seed)
        data = fetch_weather(lat, lon, api_key)
        sys.stdout.write(json.dumps({"status": "ok", "data": data}, indent=2))
    except Exception as exc:
        sys.stdout.write(json.dumps(_error(str(exc))))


if __name__ == "__main__":
    main()
