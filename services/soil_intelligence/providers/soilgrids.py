"""
ISRIC SoilGrids provider
=========================
SoilGrids (https://soilgrids.org, https://rest.isric.org) is ISRIC's global,
250 m-resolution digital soil map produced by machine-learning over ~240k
profiles. It is the de-facto open standard for global soil property data.

Why SoilGrids is the primary provider (verified July 2026 against the live API):
  * **Free, keyless, stable v2.0 REST API** with a documented, versioned contract.
  * **Global coverage including Zimbabwe & Southern Africa.** Verified pH 6.1–6.4
    over Zimbabwean farmland; nulls occur only on urban/water-masked pixels
    (e.g. central Harare), which we handle by sampling nearby offset points.
  * **Per-attribute uncertainty** ships in the response — a natural, honest
    confidence signal rather than a guess.
  * **CC-BY 4.0 licence** — production-safe with attribution.
  * **Multi-year model vintages** — data is effectively static between releases,
    so a stored profile can be reused for years (see RefreshPolicy.MULTI_YEAR).

Two endpoints are used:
  * ``/properties/query`` — pH, sand/silt/clay, SOC, nitrogen, CEC, bulk density,
    and volumetric water content at field capacity (wv0033) and wilting point
    (wv1500), each with mean + uncertainty at standard depth bands.
  * ``/classification/query`` — WRB reference soil group with class probabilities.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..models import SoilAttribute, RefreshPolicy
from .base import SoilProvider


_BASE = os.getenv("SOILGRIDS_BASE_URL", "https://rest.isric.org/soilgrids/v2.0")
_TIMEOUT = float(os.getenv("SOILGRIDS_TIMEOUT", "25"))

# Depth bands we sample. Topsoil (0-5, 5-15) drives agronomy; 15-30 supports the
# rooting-zone average. SoilGrids returns g/kg or scaled ints that we convert via
# the response's own ``d_factor``.
_DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]

# Properties to request and how each maps into the canonical vocabulary.
# key -> (soilgrids_property, canonical_key, unit, converter)
# The converter receives the *already d_factor-scaled* value (target units) and
# returns the canonical value.
_PROPERTIES: List[Tuple[str, str, str, Any]] = [
    ("phh2o", "ph", "", lambda v: round(v, 2)),
    ("sand", "sand_pct", "%", lambda v: round(v, 1)),
    ("silt", "silt_pct", "%", lambda v: round(v, 1)),
    ("clay", "clay_pct", "%", lambda v: round(v, 1)),
    ("soc", "organic_carbon", "g/kg", lambda v: round(v, 2)),
    ("nitrogen", "nitrogen", "g/kg", lambda v: round(v, 2)),
    ("cec", "cec", "cmol(+)/kg", lambda v: round(v, 1)),
    ("bdod", "bulk_density", "kg/dm3", lambda v: round(v, 2)),
    ("wv0033", "field_capacity", "%", lambda v: round(v, 1)),
    ("wv1500", "wilting_point", "%", lambda v: round(v, 1)),
]

# Small offsets (~1–3 km) to retry when the exact centroid falls on a masked
# (urban/water) pixel and returns nulls.
_FALLBACK_OFFSETS = [(0.0, 0.0), (0.02, 0.02), (-0.02, 0.02), (0.02, -0.02), (-0.02, -0.02)]


class SoilGridsProvider(SoilProvider):
    name = "SoilGrids"
    priority = 10

    async def fetch(self, lat: float, lon: float) -> List[SoilAttribute]:
        attrs: List[SoilAttribute] = []
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                props = await self._fetch_properties(client, lat, lon)
                attrs.extend(props)
                classification = await self._fetch_classification(client, lat, lon)
                if classification is not None:
                    attrs.append(classification)
        except Exception as e:  # never raise from a provider
            print(f"[SoilGrids] fetch failed: {type(e).__name__}: {e}")
        return attrs

    # ------------------------------------------------------------------
    async def _fetch_properties(
        self, client: httpx.AsyncClient, lat: float, lon: float
    ) -> List[SoilAttribute]:
        params = [("lon", lon), ("lat", lat), ("value", "mean"), ("value", "uncertainty")]
        for prop, *_ in _PROPERTIES:
            params.append(("property", prop))
        for d in _DEPTHS:
            params.append(("depth", d))

        data: Optional[Dict[str, Any]] = None
        # Retry with small offsets if the centroid is on a masked pixel.
        for dlat, dlon in _FALLBACK_OFFSETS:
            q = [("lon", lon + dlon), ("lat", lat + dlat)] + params[2:]
            try:
                resp = await client.get(f"{_BASE}/properties/query", params=q)
                resp.raise_for_status()
                candidate = resp.json()
            except Exception as e:
                print(f"[SoilGrids] properties query error: {e}")
                continue
            if self._has_any_value(candidate):
                data = candidate
                break
        if data is None:
            return []

        return self._parse_properties(data)

    @staticmethod
    def _has_any_value(data: Dict[str, Any]) -> bool:
        for layer in (data.get("properties", {}) or {}).get("layers", []) or []:
            for dep in layer.get("depths", []) or []:
                if (dep.get("values") or {}).get("mean") is not None:
                    return True
        return False

    def _parse_properties(self, data: Dict[str, Any]) -> List[SoilAttribute]:
        prop_map = {p[0]: p for p in _PROPERTIES}
        layers = (data.get("properties", {}) or {}).get("layers", []) or []
        out: List[SoilAttribute] = []
        for layer in layers:
            sg_name = layer.get("name")
            spec = prop_map.get(sg_name)
            if not spec:
                continue
            _sg, canonical_key, unit, convert = spec
            d_factor = ((layer.get("unit_measure") or {}).get("d_factor")) or 1

            # Depth-average the means & uncertainties across the sampled bands
            # (topsoil-weighted by simply averaging the shallow bands we request).
            means: List[float] = []
            uncs: List[float] = []
            for dep in layer.get("depths", []) or []:
                vals = dep.get("values") or {}
                m = vals.get("mean")
                if m is not None:
                    means.append(m / d_factor)
                u = vals.get("uncertainty")
                if u is not None:
                    uncs.append(u)
            if not means:
                continue
            avg = sum(means) / len(means)
            try:
                value = convert(avg)
            except Exception:
                value = round(avg, 2)

            confidence = self._uncertainty_to_confidence(uncs)
            out.append(SoilAttribute(
                key=canonical_key,
                value=value,
                unit=unit or None,
                source=self.name,
                confidence=confidence,
                refresh_policy=RefreshPolicy.MULTI_YEAR.value,
                detail=f"depth-averaged over {', '.join(_DEPTHS)}; SoilGrids 250m",
            ))
        return out

    @staticmethod
    def _uncertainty_to_confidence(uncertainties: List[float]) -> Optional[float]:
        """Map SoilGrids' uncertainty (ratio of the 90% PI width to the median,
        ×10) to a 0–1 confidence. Lower spread → higher confidence. Values are
        heuristic but monotonic and honest; absent uncertainty → moderate."""
        if not uncertainties:
            return 0.6
        avg_unc = sum(uncertainties) / len(uncertainties)
        # avg_unc is ~ (PI width / median) * 10. Typical range ~3 (tight, e.g. pH)
        # to ~40+ (diffuse, e.g. clay/N/CEC over heterogeneous terrain).
        # Map: <=3 -> 0.85, >=25 -> 0.25 (floor at "low", not "very low"), linear.
        if avg_unc <= 3:
            return 0.85
        if avg_unc >= 25:
            return 0.25
        return round(0.85 - (avg_unc - 3) * (0.60 / 22), 2)

    # ------------------------------------------------------------------
    async def _fetch_classification(
        self, client: httpx.AsyncClient, lat: float, lon: float
    ) -> Optional[SoilAttribute]:
        try:
            resp = await client.get(
                f"{_BASE}/classification/query",
                params={"lon": lon, "lat": lat, "number_classes": 3},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[SoilGrids] classification query error: {e}")
            return None

        name = data.get("wrb_class_name")
        if not name:
            return None
        # Top-class probability → confidence.
        prob = None
        probs = data.get("wrb_class_probability") or []
        if probs and isinstance(probs[0], (list, tuple)) and len(probs[0]) >= 2:
            prob = probs[0][1]
        confidence = round(prob / 100, 2) if isinstance(prob, (int, float)) else 0.5
        detail = None
        if probs:
            detail = "WRB probabilities: " + ", ".join(
                f"{p[0]} {p[1]}%" for p in probs[:3] if isinstance(p, (list, tuple))
            )
        return SoilAttribute(
            key="soil_classification",
            value=name,
            source=self.name,
            confidence=confidence,
            refresh_policy=RefreshPolicy.MULTI_YEAR.value,
            detail=detail,
        )
