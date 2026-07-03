"""
Terrain & climate provider (Open-Meteo)
=======================================
Open-Meteo is already KurimaSense's weather backend (``climate_service.py``), so
reusing it for terrain/climate context adds no new vendor, key, or licence
surface. Verified July 2026:

  * The **archive API** returns ``elevation`` (m) with every response — a free,
    reliable elevation source (the dedicated elevation endpoint was unreliable
    behind the egress proxy, so we read elevation from the archive response we
    already need for rainfall).
  * **Long-term rainfall**: a multi-year daily precipitation sum from the archive
    yields a mean-annual-rainfall figure, which we also use to classify the field
    into Zimbabwe's Natural Regions (the agro-ecological zones the advisor already
    reasons about).

Slope is not directly available from Open-Meteo; it is derived downstream from a
small elevation sample when a polygon is supplied (see ``derive.py``). Here we
emit elevation, mean annual rainfall, and the derived climate zone.
"""

from __future__ import annotations

import os
from datetime import date
from typing import List, Optional

import httpx

from ..models import SoilAttribute, RefreshPolicy
from .base import SoilProvider


_ARCHIVE = os.getenv("OPENMETEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")
_TIMEOUT = float(os.getenv("SOIL_TERRAIN_TIMEOUT", "25"))


def classify_zimbabwe_natural_region(mean_annual_rainfall_mm: Optional[float]) -> Optional[str]:
    """Map mean annual rainfall to Zimbabwe's Natural Region (agro-ecological zone).

    Boundaries follow the standard Vincent & Thomas classification the advisor's
    system prompt already references (NR I >1000mm … NR V <450mm). Rainfall is the
    primary determinant, so this is a faithful first-order zone estimate.
    """
    if mean_annual_rainfall_mm is None:
        return None
    r = mean_annual_rainfall_mm
    if r >= 1000:
        return "NR I (Specialised & diversified, >1000mm)"
    if r >= 750:
        return "NR II (Intensive farming, 750-1000mm)"
    if r >= 650:
        return "NR III (Semi-intensive, 650-800mm)"
    if r >= 450:
        return "NR IV (Semi-extensive, 450-650mm)"
    return "NR V (Extensive/ranching, <450mm)"


class TerrainClimateProvider(SoilProvider):
    name = "Open-Meteo"
    priority = 5

    def __init__(self, years: int = 5):
        # Multi-year window for a stable rainfall normal without over-fetching.
        self.years = max(1, years)

    async def fetch(self, lat: float, lon: float) -> List[SoilAttribute]:
        out: List[SoilAttribute] = []
        try:
            end = date.today().replace(month=1, day=1)  # whole-year windows only
            start = end.replace(year=end.year - self.years)
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start.isoformat(),
                "end_date": (end.replace(year=end.year - 0)).isoformat(),
                "daily": "precipitation_sum",
                "timezone": "auto",
            }
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(_ARCHIVE, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            print(f"[Terrain/Open-Meteo] fetch failed: {type(e).__name__}: {e}")
            return out

        # Elevation — comes free with the archive response.
        elev = data.get("elevation")
        if isinstance(elev, (int, float)):
            out.append(SoilAttribute(
                key="elevation",
                value=round(float(elev), 1),
                unit="m",
                source=self.name,
                confidence=0.9,
                refresh_policy=RefreshPolicy.STATIC.value,
                detail="Open-Meteo archive DEM",
            ))

        # Mean annual rainfall from the multi-year daily precipitation series.
        daily = (data.get("daily") or {}).get("precipitation_sum") or []
        rain_vals = [v for v in daily if isinstance(v, (int, float))]
        mean_annual = None
        if rain_vals:
            total = sum(rain_vals)
            days = len(rain_vals)
            mean_annual = round(total / days * 365.25, 0)
            out.append(SoilAttribute(
                key="historical_rainfall",
                value=mean_annual,
                unit="mm/year",
                source=self.name,
                confidence=0.8,
                refresh_policy=RefreshPolicy.ANNUAL.value,
                detail=f"{self.years}-year mean from Open-Meteo archive",
            ))

        zone = classify_zimbabwe_natural_region(mean_annual)
        if zone:
            out.append(SoilAttribute(
                key="climate_zone",
                value=zone,
                source=self.name,
                confidence=0.7,
                refresh_policy=RefreshPolicy.ANNUAL.value,
                detail="Derived from mean annual rainfall (Vincent & Thomas NR scheme)",
                derived=True,
            ))

        return out
