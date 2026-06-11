import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


REQUEST_TIMEOUT_SECONDS = 60
RETRY_ATTEMPTS = 3
CACHE_TTL_SECONDS = 21600

# Satellite backend: defaults to the free Copernicus Data Space Ecosystem (CDSE),
# which exposes the same Sentinel Hub APIs (OAuth + Statistics) at no cost and
# needs no paid plan. Override via env to point at commercial Sentinel Hub
# (https://services.sentinel-hub.com/oauth/token + /api/v1/statistics) if ever
# subscribed. Read at call time so a .env loaded in run()/scripts takes effect.
DEFAULT_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
)
DEFAULT_STATS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"


def _token_url():
    return os.getenv("SATELLITE_TOKEN_URL", DEFAULT_TOKEN_URL)


def _stats_url():
    return os.getenv("SATELLITE_STATS_URL", DEFAULT_STATS_URL)


def _error(message):
    return {"status": "error", "error_message": message}


def _to_float(value):
    """Coerce a Statistics API stat to a finite float, else None.

    CDSE returns the JSON string "NaN" (not null) for the mean of intervals
    with no valid pixels (fully clouded/masked days), so a plain None-check
    is not enough."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


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


def _get_access_token(client_id, client_secret):
    url = _token_url()
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post(url, data=payload, timeout=20)
    if response.status_code != 200:
        raise RuntimeError(f"Sentinel Hub auth error {response.status_code}: {response.text}")
    return response.json().get("access_token")


def _build_bbox(lat, lon, delta=0.002):
    return [lon - delta, lat - delta, lon + delta, lat + delta]


def _isoformat_z(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _build_stats_request(bbox, start_date, end_date):
    evalscript = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B04", "B08", "dataMask"] }],
    output: [
      { id: "ndvi", bands: 1, sampleType: "FLOAT32" },
      { id: "evi", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 }
    ]
  };
}

function evaluatePixel(sample) {
  let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
  let evi = 2.5 * (sample.B08 - sample.B04) /
    (sample.B08 + 6 * sample.B04 - 7.5 * sample.B02 + 1);
  return { ndvi: [ndvi], evi: [evi], dataMask: [sample.dataMask] };
}
""".strip()

    return {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {"from": start_date, "to": end_date},
                        "maxCloudCoverage": 80,
                    },
                }
            ],
        },
        "aggregation": {
            "timeRange": {"from": start_date, "to": end_date},
            "aggregationInterval": {"of": "P1D"},
            "evalscript": evalscript,
        },
    }


def _fetch_ndvi_stats(token, payload):
    url = _stats_url()
    headers = {"Authorization": f"Bearer {token}"}
    last_error = None
    for _ in range(RETRY_ATTEMPTS):
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS
            )
        except requests.RequestException as exc:
            last_error = exc
            continue
        if response.status_code != 200:
            raise RuntimeError(
                f"Sentinel Hub statistics error {response.status_code}: {response.text}"
            )
        return response.json()

    raise RuntimeError(f"Sentinel Hub statistics request failed: {last_error}")


def _parse_stats(stats):
    intervals = stats.get("data", [])
    ndvi_means = []
    evi_means = []
    mask_means = []
    last_pass = None

    for interval in intervals:
        outputs = interval.get("outputs", {})
        ndvi_stats = (
            outputs.get("ndvi", {})
            .get("bands", {})
            .get("B0", {})
            .get("stats", {})
        )
        evi_stats = (
            outputs.get("evi", {})
            .get("bands", {})
            .get("B0", {})
            .get("stats", {})
        )
        mask_stats = (
            outputs.get("dataMask", {})
            .get("bands", {})
            .get("B0", {})
            .get("stats", {})
        )
        mean_ndvi = _to_float(ndvi_stats.get("mean"))
        mean_evi = _to_float(evi_stats.get("mean"))
        mean_mask = _to_float(mask_stats.get("mean"))
        if mean_ndvi is not None:
            ndvi_means.append(mean_ndvi)
        if mean_evi is not None:
            evi_means.append(mean_evi)
        if mean_mask is not None:
            mask_means.append(mean_mask)

        if mean_ndvi is not None:
            last_pass = interval.get("interval", {}).get("to")

    if not ndvi_means:
        raise RuntimeError("Sentinel Hub statistics returned no NDVI values")

    ndvi_mean = sum(ndvi_means) / len(ndvi_means)
    evi_mean = sum(evi_means) / len(evi_means) if evi_means else None
    data_mask_mean = sum(mask_means) / len(mask_means) if mask_means else None
    cloud_cover_pct = None
    if data_mask_mean is not None:
        cloud_cover_pct = round(max(0.0, 1 - data_mask_mean) * 100, 2)

    last_pass_date = None
    if last_pass:
        last_pass_date = last_pass.split("T")[0]

    return {
        "ndvi_mean": round(ndvi_mean, 4),
        "evi_mean": round(evi_mean, 4) if evi_mean is not None else None,
        "cloud_cover_pct": cloud_cover_pct,
        "last_pass_date": last_pass_date,
        "source": "sentinel_hub",
    }


def _calculate_anomaly(current_mean, baseline_mean):
    if current_mean is None or baseline_mean is None:
        return None
    return round(current_mean - baseline_mean, 4)


def run(lat, lon):
    """Run Sentinel Hub crop health analysis. Returns the result dict directly."""
    load_dotenv()
    client_id = os.getenv("SATELLITE_API_CLIENT_ID")
    client_secret = os.getenv("SATELLITE_API_CLIENT_SECRET")
    if not client_id or not client_secret or "your_" in client_id:
        return _error("Sentinel Hub credentials missing or placeholder")

    try:
        cached = _read_cache(lat, lon)
        if cached:
            return {"status": "ok", "data": cached}
        token = _get_access_token(client_id, client_secret)
        if not token:
            raise RuntimeError("Sentinel Hub access token missing in response")

        end_date = datetime.now(timezone.utc)
        recent_start = end_date - timedelta(days=10)
        baseline_end = end_date - timedelta(days=30)
        baseline_start = baseline_end - timedelta(days=60)

        bbox = _build_bbox(lat, lon)
        recent_request = _build_stats_request(
            bbox, _isoformat_z(recent_start), _isoformat_z(end_date)
        )
        baseline_request = _build_stats_request(
            bbox, _isoformat_z(baseline_start), _isoformat_z(baseline_end)
        )

        recent_stats = _fetch_ndvi_stats(token, recent_request)
        baseline_stats = _fetch_ndvi_stats(token, baseline_request)
        recent_data = _parse_stats(recent_stats)
        baseline_data = _parse_stats(baseline_stats)

        data = {
            **recent_data,
            "ndvi_anomaly": _calculate_anomaly(
                recent_data.get("ndvi_mean"), baseline_data.get("ndvi_mean")
            ),
            "evi_anomaly": _calculate_anomaly(
                recent_data.get("evi_mean"), baseline_data.get("evi_mean")
            ),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "baseline_window": {
                "from": baseline_start.date().isoformat(),
                "to": baseline_end.date().isoformat(),
            },
        }

        _write_cache(lat, lon, data)
        return {"status": "ok", "data": data}
    except Exception as exc:
        return _error(str(exc))


def main():
    try:
        seed = _load_seed()
        lat, lon = _extract_location(seed)
    except Exception as exc:
        sys.stdout.write(json.dumps(_error(str(exc))))
        return
    result = run(lat, lon)
    sys.stdout.write(json.dumps(result, indent=2))


def _cache_path(lat, lon):
    tmp_dir = Path.cwd() / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    key = f"satellite_{lat:.4f}_{lon:.4f}.json"
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


if __name__ == "__main__":
    main()
