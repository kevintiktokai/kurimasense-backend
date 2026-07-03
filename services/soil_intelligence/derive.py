"""
Derived soil attributes
========================
Providers supply *primary* measurements (sand/silt/clay, SOC, water content at
field capacity & wilting point, elevation…). This module computes the
*agronomically useful* attributes that follow deterministically from those
primaries, so the AI advisor and downstream analytics get texture class, plant-
available water, drainage, erosion risk, organic matter, and rooting depth for
free — no extra API calls, fully explainable, and locally testable.

Every derived attribute is tagged ``derived=True`` and sourced as
``"KurimaSense (derived)"`` with a confidence propagated from its inputs, so the
provenance chain stays honest.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import SoilAttribute, SoilProfile, RefreshPolicy


_DERIVED_SOURCE = "KurimaSense (derived)"


def usda_texture_class(sand: float, silt: float, clay: float) -> str:
    """USDA soil texture triangle classification from sand/silt/clay percentages.

    Standard textural triangle boundaries. Inputs are normalised to sum to 100 so
    small rounding gaps from depth-averaging don't misclassify.
    """
    total = sand + silt + clay
    if total <= 0:
        return "unknown"
    sand = sand * 100.0 / total
    silt = silt * 100.0 / total
    clay = clay * 100.0 / total

    if clay >= 40:
        if sand >= 45:
            return "sandy clay"
        if silt >= 40:
            return "silty clay"
        return "clay"
    if clay >= 27:
        if sand >= 45:
            return "sandy clay loam"
        if silt >= 28:
            return "clay loam"
        return "clay loam"
    if clay >= 20:
        if sand >= 45:
            return "sandy clay loam"
    # clay < 27 region
    if silt >= 80 and clay < 12:
        return "silt"
    if silt >= 50:
        if clay >= 12:
            return "silty clay loam" if clay >= 27 else "silt loam"
        return "silt loam"
    if sand >= 85 and clay <= 10:
        return "sand"
    if sand >= 70 and clay <= 15:
        return "loamy sand"
    if sand >= 43 and clay < 20:
        return "sandy loam"
    return "loam"


def _drainage_from_texture(texture: str, clay: float) -> str:
    t = texture.lower()
    if "sand" in t and "clay" not in t:
        return "well to excessively drained"
    if clay >= 40 or t in ("clay", "silty clay"):
        return "poorly drained"
    if "clay" in t:
        return "moderately drained"
    return "well drained"


def _erosion_risk(slope_deg: Optional[float], texture: str, sand: float) -> str:
    """Erosion risk from slope + erodibility (silt/fine sand fractions erode most)."""
    s = slope_deg if slope_deg is not None else 0.0
    erodible = "silt" in texture.lower() or (60 <= sand <= 85)
    if s >= 12:
        return "high"
    if s >= 6:
        return "high" if erodible else "moderate"
    if s >= 3:
        return "moderate" if erodible else "low"
    return "low"


def _terrain_descriptor(slope_deg: Optional[float]) -> Optional[str]:
    if slope_deg is None:
        return None
    s = slope_deg
    if s < 2:
        return "flat to gently undulating"
    if s < 5:
        return "gently sloping"
    if s < 10:
        return "moderately sloping"
    if s < 18:
        return "strongly sloping"
    return "steep"


def _min_confidence(profile: SoilProfile, keys: List[str]) -> Optional[float]:
    confs = [
        profile.attributes[k].confidence
        for k in keys
        if k in profile.attributes and profile.attributes[k].confidence is not None
    ]
    return min(confs) if confs else None


def enrich_with_derived(profile: SoilProfile, slope_deg: Optional[float] = None) -> SoilProfile:
    """Compute and attach all derivable attributes onto ``profile`` in place.

    Idempotent: derived attributes are recomputed from current primaries each
    call, so re-running after a refresh keeps them consistent. Never overwrites a
    higher-priority primary value (e.g. a texture_class from a lab test).
    """
    def primary(key: str) -> Optional[float]:
        a = profile.attributes.get(key)
        if a is None or a.value is None:
            return None
        try:
            return float(a.value)
        except (TypeError, ValueError):
            return None

    def add(attr: SoilAttribute, *, only_if_absent: bool = False) -> None:
        existing = profile.attributes.get(attr.key)
        if only_if_absent and existing is not None and not existing.derived:
            return  # keep authoritative primary
        profile.set(attr)

    sand = primary("sand_pct")
    silt = primary("silt_pct")
    clay = primary("clay_pct")

    # --- Texture class + drainage + erosion (need sand/silt/clay) ---
    texture_class: Optional[str] = None
    if sand is not None and silt is not None and clay is not None:
        texture_class = usda_texture_class(sand, silt, clay)
        conf = _min_confidence(profile, ["sand_pct", "silt_pct", "clay_pct"])
        add(SoilAttribute(
            key="texture_class", value=texture_class, source=_DERIVED_SOURCE,
            confidence=conf, refresh_policy=RefreshPolicy.MULTI_YEAR.value,
            detail="USDA texture triangle from sand/silt/clay", derived=True,
        ), only_if_absent=True)

        add(SoilAttribute(
            key="drainage", value=_drainage_from_texture(texture_class, clay),
            source=_DERIVED_SOURCE, confidence=conf,
            refresh_policy=RefreshPolicy.MULTI_YEAR.value,
            detail="Inferred from texture class", derived=True,
        ), only_if_absent=True)

        add(SoilAttribute(
            key="erosion_risk", value=_erosion_risk(slope_deg, texture_class, sand),
            source=_DERIVED_SOURCE, confidence=conf,
            refresh_policy=RefreshPolicy.MULTI_YEAR.value,
            detail="Inferred from slope + texture erodibility", derived=True,
        ), only_if_absent=True)

    # --- Organic matter from SOC (Van Bemmelen factor 1.724) ---
    soc = primary("organic_carbon")  # g/kg
    if soc is not None:
        om_pct = round(soc / 10.0 * 1.724, 2)  # g/kg -> % then ×1.724
        add(SoilAttribute(
            key="organic_matter", value=om_pct, unit="%", source=_DERIVED_SOURCE,
            confidence=_min_confidence(profile, ["organic_carbon"]),
            refresh_policy=RefreshPolicy.MULTI_YEAR.value,
            detail="SOC × 1.724 (Van Bemmelen)", derived=True,
        ), only_if_absent=True)

    # --- Available water & water-holding capacity from FC & WP ---
    fc = primary("field_capacity")   # vol %
    wp = primary("wilting_point")    # vol %
    if fc is not None and wp is not None:
        awc_vol = round(fc - wp, 1)  # volumetric % available water
        conf = _min_confidence(profile, ["field_capacity", "wilting_point"])
        add(SoilAttribute(
            key="available_water", value=max(awc_vol, 0.0), unit="%",
            source=_DERIVED_SOURCE, confidence=conf,
            refresh_policy=RefreshPolicy.MULTI_YEAR.value,
            detail="Field capacity minus wilting point (volumetric)", derived=True,
        ), only_if_absent=True)
        # mm of plant-available water per metre of soil = vol% × 10.
        whc_mm_per_m = round(max(awc_vol, 0.0) * 10.0, 0)
        add(SoilAttribute(
            key="water_holding_capacity", value=whc_mm_per_m, unit="mm/m",
            source=_DERIVED_SOURCE, confidence=conf,
            refresh_policy=RefreshPolicy.MULTI_YEAR.value,
            detail="Available water × 10 (mm per metre rooting depth)", derived=True,
        ), only_if_absent=True)

    # --- Effective rooting depth: texture-informed default (cm) ---
    if texture_class and "root_depth" not in profile.attributes:
        t = texture_class.lower()
        if "clay" in t:
            depth = 90
        elif "sand" in t:
            depth = 120
        else:
            depth = 100
        add(SoilAttribute(
            key="root_depth", value=depth, unit="cm", source=_DERIVED_SOURCE,
            confidence=0.4, refresh_policy=RefreshPolicy.MULTI_YEAR.value,
            detail="Texture-based estimate; refine with a soil pit", derived=True,
        ), only_if_absent=True)

    # --- Terrain descriptor from slope ---
    if slope_deg is not None:
        add(SoilAttribute(
            key="slope", value=round(slope_deg, 1), unit="degrees",
            source=_DERIVED_SOURCE, confidence=0.5,
            refresh_policy=RefreshPolicy.STATIC.value,
            detail="Estimated from elevation sampling", derived=True,
        ), only_if_absent=True)
        desc = _terrain_descriptor(slope_deg)
        if desc:
            add(SoilAttribute(
                key="terrain", value=desc, source=_DERIVED_SOURCE, confidence=0.5,
                refresh_policy=RefreshPolicy.STATIC.value,
                detail="Slope descriptor", derived=True,
            ), only_if_absent=True)

    return profile
