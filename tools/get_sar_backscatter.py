"""
Sentinel-1 SAR backscatter fetch (Sprint 4, Slice 3 — closes data-gap G2).

Radar penetrates cloud, so VV/VH backscatter gives a canopy-structure signal
even when optical NDVI is fully cloud-blocked — the wet-season floor. Mirrors the
proven Sentinel-2 path in tools/get_crop_health.py: same CDSE OAuth + Statistics
API, same credentials (SATELLITE_API_CLIENT_ID / SATELLITE_API_CLIENT_SECRET),
read server-side only. Returns a plain dict; never raises to the caller.

Output: {"status": "ok", "data": {sar_vv_db, sar_vh_db, last_pass_date}} or
{"status": "error", "error_message": ...}.
"""

import math
import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

# Reuse the shared CDSE helpers (same account, same endpoints) — single source of
# truth for auth, URLs, bbox and float coercion.
from tools.get_crop_health import (
    REQUEST_TIMEOUT_SECONDS,
    RETRY_ATTEMPTS,
    _build_bbox,
    _get_access_token,
    _isoformat_z,
    _stats_url,
    _to_float,
)


def _error(message):
    return {"status": "error", "error_message": message}


# Sentinel-1 GRD evalscript: linear VV/VH backscatter → decibels. Pixels with no
# valid backscatter (<=0) are floored to -30 dB (a conventional radar noise floor)
# and excluded from the mean via dataMask.
_S1_EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["VV", "VH", "dataMask"] }],
    output: [
      { id: "vv", bands: 1, sampleType: "FLOAT32" },
      { id: "vh", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 }
    ]
  };
}
function toDb(linear) { return 10 * Math.log(linear) / Math.LN10; }
function evaluatePixel(s) {
  return {
    vv: [s.VV > 0 ? toDb(s.VV) : -30],
    vh: [s.VH > 0 ? toDb(s.VH) : -30],
    dataMask: [s.dataMask]
  };
}
""".strip()


def _build_s1_stats_request(bbox, start_date, end_date):
    return {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [
                {
                    "type": "sentinel-1-grd",
                    "dataFilter": {
                        "timeRange": {"from": start_date, "to": end_date},
                        "acquisitionMode": "IW",
                        "polarization": "DV",  # dual VV+VH
                    },
                    "processing": {
                        "orthorectify": True,
                        "backCoeff": "GAMMA0_TERRAIN",
                    },
                }
            ],
        },
        "aggregation": {
            "timeRange": {"from": start_date, "to": end_date},
            "aggregationInterval": {"of": "P1D"},
            "evalscript": _S1_EVALSCRIPT,
        },
    }


def _fetch_stats(token, payload):
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
                f"Sentinel-1 statistics error {response.status_code}: {response.text}"
            )
        return response.json()
    raise RuntimeError(f"Sentinel-1 statistics request failed: {last_error}")


def _band_mean(outputs, output_id):
    stats = outputs.get(output_id, {}).get("bands", {}).get("B0", {}).get("stats", {})
    return _to_float(stats.get("mean"))


def _parse_s1_stats(stats):
    intervals = stats.get("data", [])
    vv_means, vh_means = [], []
    last_pass = None
    for interval in intervals:
        outputs = interval.get("outputs", {})
        vv = _band_mean(outputs, "vv")
        vh = _band_mean(outputs, "vh")
        if vv is not None:
            vv_means.append(vv)
            last_pass = interval.get("interval", {}).get("to")
        if vh is not None:
            vh_means.append(vh)

    if not vv_means and not vh_means:
        raise RuntimeError("Sentinel-1 statistics returned no backscatter values")

    return {
        "sar_vv_db": round(sum(vv_means) / len(vv_means), 3) if vv_means else None,
        "sar_vh_db": round(sum(vh_means) / len(vh_means), 3) if vh_means else None,
        "last_pass_date": last_pass.split("T")[0] if last_pass else None,
        "source": "sentinel-1-grd",
    }


def run(lat, lon, lookback_days: int = 14):
    """Fetch mean Sentinel-1 VV/VH backscatter (dB) over the last `lookback_days`
    for the field around (lat, lon). Best-effort — returns an error dict rather
    than raising so the caller can persist optical data even when SAR is absent."""
    load_dotenv()
    client_id = os.getenv("SATELLITE_API_CLIENT_ID")
    client_secret = os.getenv("SATELLITE_API_CLIENT_SECRET")
    if not client_id or not client_secret or "your_" in client_id:
        return _error("Sentinel Hub credentials missing or placeholder")

    try:
        token = _get_access_token(client_id, client_secret)
        if not token:
            raise RuntimeError("Sentinel Hub access token missing in response")

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)
        bbox = _build_bbox(lat, lon)
        payload = _build_s1_stats_request(
            bbox, _isoformat_z(start_date), _isoformat_z(end_date)
        )
        stats = _fetch_stats(token, payload)
        data = _parse_s1_stats(stats)
        data["fetched_at"] = datetime.now(timezone.utc).isoformat()
        return {"status": "ok", "data": data}
    except Exception as exc:
        return _error(str(exc))
