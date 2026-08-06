"""
Zone-level diagnosis — why a part of a field is behind, not just that it is.
Pure computation, no I/O.

Why this exists
---------------
Today a zone gets a number. "The North-East is at 0.42" tells a farmer where to
walk but nothing about what they will find when they get there, and nothing
about whether it is worth fixing. That is the difference between a map and
advice.

The inputs to say more already exist and were never combined:

* per-zone NDVI from ``field_section_analysis``;
* scouting observations carrying **lat/lon**, which can be attributed to the
  zone they fall in;
* the field's soil profile — texture, drainage, slope, erosion risk — from
  ``services.soil_intelligence``.

The restraint
-------------
A zone being below average is not a diagnosis, it is an observation. Half of
any field is below its own average by definition. So this module:

* only flags a zone when it is **meaningfully** behind the field, not merely
  below the mean;
* names a cause only where something corroborates it — a scouting pin inside
  that zone, or a soil/terrain property that explains it;
* otherwise says plainly that the cause is unknown and the zone is worth
  walking.

Naming a cause we cannot evidence would be worse than staying quiet: a farmer
who walks to a zone expecting waterlogging and finds armyworm stops trusting
the map.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional, Sequence, Tuple

# A zone must be this far below the field mean, in NDVI, before it is called
# out. Below this, the difference is inside the noise of cloud, sampling and
# ordinary within-field variation.
MATERIAL_NDVI_GAP = 0.08

# And this far below to be treated as a problem rather than a soft spot.
SEVERE_NDVI_GAP = 0.18

# Soil/terrain properties that plausibly explain a persistently weak patch.
_TERRAIN_EXPLANATIONS = {
    "steep": "the ground here is steeper, so water runs off rather than soaking in",
    "moderate_slope": "this part of the field slopes, which sheds water and topsoil",
    "high": "erosion risk is high here, so topsoil and nutrients move downhill",
}


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
def point_in_ring(lat: float, lon: float, ring: Sequence[Dict[str, float]]) -> bool:
    """Ray-casting point-in-polygon on an open ring of ``{lat, lon}``.

    Used to attribute a scouting pin to the zone it was dropped in. Getting this
    wrong puts a farmer's own observation on the wrong part of their field,
    which is worse than not showing it at all.
    """
    pts = [p for p in (ring or []) if isinstance(p, dict) and "lat" in p and "lon" in p]
    if len(pts) < 3:
        return False

    inside = False
    n = len(pts)
    for i in range(n):
        j = (i - 1) % n
        yi, xi = pts[i]["lat"], pts[i]["lon"]
        yj, xj = pts[j]["lat"], pts[j]["lon"]
        # Half-open edge test (yi > lat) != (yj > lat): counting a vertex from
        # one side only, so a point level with a vertex is not counted twice.
        if (yi > lat) != (yj > lat):
            x_cross = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x_cross:
                inside = not inside
    return inside


def attribute_observations(
    zones: Sequence[Dict[str, Any]],
    observations: Sequence[Dict[str, Any]],
) -> Dict[int, List[Dict[str, Any]]]:
    """Group observations by the zone index whose polygon contains them.

    Observations with no coordinates, or falling outside every zone, are
    dropped rather than assigned to the nearest — a pin placed outside the
    mapped boundary is not evidence about any zone inside it.
    """
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for obs in observations or []:
        lat, lon = obs.get("lat"), obs.get("lon")
        if lat is None or lon is None:
            continue
        try:
            lat_f, lon_f = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        for zone in zones:
            if point_in_ring(lat_f, lon_f, zone.get("polygon") or []):
                grouped.setdefault(int(zone.get("index", -1)), []).append(obs)
                break
    return grouped


# ---------------------------------------------------------------------------
# Diagnosis
# ---------------------------------------------------------------------------
@dataclass
class ZoneDiagnosis:
    index: int
    label: str
    ndvi: Optional[float]
    gap_vs_field: Optional[float]      # positive = behind the field mean
    severity: str                      # 'ok' | 'watch' | 'problem' | 'unknown'
    summary: str
    causes: List[str] = dc_field(default_factory=list)
    observation_count: int = 0
    action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "label": self.label,
            "ndvi": self.ndvi,
            "gap_vs_field": self.gap_vs_field,
            "severity": self.severity,
            "summary": self.summary,
            "causes": self.causes,
            "observation_count": self.observation_count,
            "action": self.action,
        }


def field_mean_ndvi(zones: Sequence[Dict[str, Any]]) -> Optional[float]:
    """Area-weighted mean NDVI across analysed zones, or None if none are."""
    total_weight = 0.0
    total = 0.0
    for z in zones or []:
        ndvi = z.get("ndvi")
        if ndvi is None:
            continue
        try:
            value = float(ndvi)
        except (TypeError, ValueError):
            continue
        weight = float(z.get("area_share") or 0) or 1.0
        total += value * weight
        total_weight += weight
    return round(total / total_weight, 4) if total_weight else None


def _observation_causes(observations: Sequence[Dict[str, Any]]) -> List[str]:
    """Turn a zone's own scouting pins into named, corroborated causes."""
    causes: List[str] = []
    by_category: Dict[str, int] = {}
    for obs in observations:
        cat = (obs.get("category") or "general").strip().lower()
        by_category[cat] = by_category.get(cat, 0) + 1

    readable = {
        "pest": "pest damage",
        "disease": "disease",
        "weed": "weed pressure",
        "water": "a water problem",
        "nutrient": "a nutrient problem",
        "general": "something noted on a scouting walk",
    }
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        label = readable.get(cat, cat)
        causes.append(
            f"You logged {label} here"
            + (f" ({count} times)" if count > 1 else "")
            + "."
        )
    return causes


def _soil_causes(soil: Optional[Dict[str, Any]]) -> List[str]:
    """Field-level soil/terrain facts that could explain a weak patch.

    Field-level, not per-zone: the soil profile is sampled at the field
    centroid, so these are offered as *possible* explanations rather than
    stated as fact about this specific zone.
    """
    if not soil:
        return []
    causes: List[str] = []

    terrain = str(soil.get("terrain") or "").strip().lower()
    if terrain in _TERRAIN_EXPLANATIONS:
        causes.append(f"Possible: {_TERRAIN_EXPLANATIONS[terrain]}.")

    erosion = str(soil.get("erosion_risk") or "").strip().lower()
    if erosion in _TERRAIN_EXPLANATIONS and erosion == "high":
        causes.append(f"Possible: {_TERRAIN_EXPLANATIONS[erosion]}.")

    drainage = str(soil.get("drainage") or "").strip().lower()
    if "poor" in drainage:
        causes.append(
            "Possible: this field drains poorly, so low-lying parts stay wet "
            "after rain."
        )
    elif "excessive" in drainage or "rapid" in drainage:
        causes.append(
            "Possible: this field drains fast, so the lighter patches dry out "
            "first between rains."
        )
    return causes


def diagnose_zones(
    zones: Sequence[Dict[str, Any]],
    *,
    observations: Optional[Sequence[Dict[str, Any]]] = None,
    soil: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Explain each zone relative to its own field, worst first.

    Comparison is always **within** the field. An absolute NDVI threshold would
    call every zone of a young crop a problem and every zone of a mature one
    healthy, which is a calendar reading rather than a diagnosis.
    """
    mean = field_mean_ndvi(zones)
    grouped = attribute_observations(zones, observations or [])
    soil_causes = _soil_causes(soil)

    results: List[ZoneDiagnosis] = []
    for zone in zones or []:
        index = int(zone.get("index", -1))
        label = str(zone.get("label") or f"Zone {index + 1}")
        raw = zone.get("ndvi")
        zone_obs = grouped.get(index, [])

        try:
            ndvi = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            ndvi = None

        if ndvi is None or mean is None:
            results.append(ZoneDiagnosis(
                index=index, label=label, ndvi=None, gap_vs_field=None,
                severity="unknown",
                summary=f"{label} has not been analysed yet.",
                observation_count=len(zone_obs),
                action="Run a zone scan to see how this part of the field is doing.",
            ))
            continue

        gap = round(mean - ndvi, 4)

        if gap < MATERIAL_NDVI_GAP:
            # Half of any field is below its own average — that is arithmetic,
            # not a finding.
            severity = "ok"
            summary = f"{label} is in line with the rest of the field."
            action = ""
            causes: List[str] = []
        else:
            severity = "problem" if gap >= SEVERE_NDVI_GAP else "watch"
            summary = (
                f"{label} is at {ndvi:.2f} against a field average of {mean:.2f} — "
                f"noticeably behind."
            )
            causes = _observation_causes(zone_obs) + soil_causes
            if causes:
                action = f"Walk {label} and check what you logged there."
            else:
                # Naming a cause we cannot evidence is worse than admitting we
                # do not know: a farmer who walks expecting waterlogging and
                # finds armyworm stops trusting the map.
                causes = [
                    "Nothing recorded here explains it yet — this zone is worth "
                    "walking before deciding what to do."
                ]
                action = f"Scout {label} and log what you find."

        results.append(ZoneDiagnosis(
            index=index, label=label, ndvi=round(ndvi, 4), gap_vs_field=gap,
            severity=severity, summary=summary, causes=causes,
            observation_count=len(zone_obs), action=action,
        ))

    # Worst first: the point of the view is where to go, not a tour of the field.
    results.sort(key=lambda d: (d.gap_vs_field is None, -(d.gap_vs_field or 0)))
    return [d.to_dict() for d in results]
