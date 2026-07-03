"""
Soil Intelligence — data model
==============================
The canonical, provider-agnostic representation of everything KurimaSense knows
about the soil and terrain beneath a field.

Design goals
------------
* **Provider-agnostic.** A :class:`SoilProfile` is assembled from one *or many*
  providers (see ``providers/``). Nothing here knows about SoilGrids, Open-Meteo,
  a future national dataset, or a user-uploaded lab test. Each contributed value
  is a :class:`SoilAttribute` that carries its *own* provenance, so a profile can
  freely mix sources attribute-by-attribute.
* **Every value is self-describing.** An attribute records not just the number but
  its unit, the source it came from, a 0–1 confidence, when it was acquired, and
  the refresh policy that governs when it should be re-fetched. This is what lets
  the AI advisor say "pH 5.4 (SoilGrids, moderate confidence)" and lets the
  lifecycle layer avoid needless external calls.
* **Serialisable.** ``to_dict`` / ``from_dict`` round-trip through the JSONB
  column in ``soil_profiles`` with no bespoke encoder.

This module is dependency-free (stdlib only) so it imports cleanly in unit tests
without pulling the provider HTTP stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RefreshPolicy(str, Enum):
    """How often an attribute should be re-fetched from its source.

    Soil physical/chemical properties are effectively static on human timescales,
    so the default is deliberately long. Terrain never changes. Climate normals
    drift slowly; live-ish series (historical rainfall aggregates) refresh more
    often. A user-supplied lab test is authoritative and never auto-refreshed.
    """
    STATIC = "static"                # never auto-refresh (terrain, lab tests)
    SEASONAL = "seasonal"            # ~ every 180 days
    ANNUAL = "annual"               # ~ every 365 days
    MULTI_YEAR = "multi_year"       # ~ every 3 years (SoilGrids model vintages)

    def ttl(self) -> Optional[timedelta]:
        return {
            RefreshPolicy.STATIC: None,
            RefreshPolicy.SEASONAL: timedelta(days=180),
            RefreshPolicy.ANNUAL: timedelta(days=365),
            RefreshPolicy.MULTI_YEAR: timedelta(days=365 * 3),
        }[self]


# Confidence bands used across providers so the AI layer can speak in words.
def confidence_label(value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if value >= 0.75:
        return "high"
    if value >= 0.5:
        return "moderate"
    if value >= 0.25:
        return "low"
    return "very low"


@dataclass
class SoilAttribute:
    """A single measured or modelled soil/terrain attribute with full provenance.

    ``value`` may be any JSON-serialisable scalar (float/int/str). ``key`` is the
    canonical attribute name (e.g. ``"ph"``, ``"clay_pct"``, ``"texture_class"``);
    the full canonical set is enumerated in :data:`CANONICAL_ATTRIBUTES`.
    """
    key: str
    value: Any
    unit: Optional[str] = None
    source: str = "unknown"
    confidence: Optional[float] = None
    acquired_at: str = field(default_factory=_utcnow_iso)
    refresh_policy: str = RefreshPolicy.MULTI_YEAR.value
    # Optional free-form provenance (depth band sampled, model vintage, method…).
    detail: Optional[str] = None
    # True when derived locally from other attributes rather than fetched.
    derived: bool = False

    def is_stale(self, *, now: Optional[datetime] = None) -> bool:
        """True if this attribute is past its refresh TTL."""
        try:
            policy = RefreshPolicy(self.refresh_policy)
        except ValueError:
            policy = RefreshPolicy.MULTI_YEAR
        ttl = policy.ttl()
        if ttl is None:
            return False
        now = now or datetime.now(timezone.utc)
        try:
            acquired = datetime.fromisoformat(self.acquired_at)
            if acquired.tzinfo is None:
                acquired = acquired.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return True
        return (now - acquired) > ttl

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SoilAttribute":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# The canonical attribute vocabulary. Providers emit a subset; the merger unions
# them. Keeping this list explicit (rather than free-form) means the AI prompt and
# the frontend can rely on stable keys, and new providers slot into existing keys.
CANONICAL_ATTRIBUTES: Dict[str, str] = {
    # Classification & texture
    "soil_classification": "WRB reference soil group",
    "texture_class": "USDA texture class (derived from sand/silt/clay)",
    "sand_pct": "Sand fraction (%)",
    "silt_pct": "Silt fraction (%)",
    "clay_pct": "Clay fraction (%)",
    # Chemistry
    "ph": "Soil pH (H2O)",
    "organic_carbon": "Soil organic carbon (g/kg)",
    "organic_matter": "Soil organic matter (%) — derived from SOC",
    "nitrogen": "Total nitrogen (g/kg)",
    "cec": "Cation exchange capacity (cmol(+)/kg)",
    # Physical
    "bulk_density": "Bulk density (kg/dm3)",
    "water_holding_capacity": "Plant-available water capacity (mm/m) — derived",
    "available_water": "Volumetric available water (%) — derived",
    "field_capacity": "Volumetric water at field capacity (%)",
    "wilting_point": "Volumetric water at wilting point (%)",
    "root_depth": "Estimated effective rooting depth (cm)",
    "drainage": "Drainage class (derived from texture)",
    "erosion_risk": "Erosion risk class (derived from slope + texture)",
    # Terrain
    "elevation": "Elevation above sea level (m)",
    "slope": "Terrain slope (degrees)",
    "terrain": "Terrain descriptor (derived from slope)",
    # Climate context
    "climate_zone": "Zimbabwe Natural Region / agro-ecological zone",
    "historical_rainfall": "Mean annual rainfall (mm) — long-term",
}


@dataclass
class SoilProfile:
    """A persistent soil intelligence profile for one field.

    Holds the merged attribute set (keyed by canonical name) plus book-keeping:
    which providers contributed, when the profile was last built, and the
    coordinates it was sampled at. This is what gets stored in ``soil_profiles``
    and injected into the AI advisor.
    """
    field_id: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    attributes: Dict[str, SoilAttribute] = field(default_factory=dict)
    # provider name -> status string ("ok" | "partial" | "error:<reason>" | "empty")
    provider_status: Dict[str, str] = field(default_factory=dict)
    built_at: str = field(default_factory=_utcnow_iso)
    schema_version: int = 1

    # ------------------------------------------------------------------
    def get(self, key: str) -> Optional[SoilAttribute]:
        return self.attributes.get(key)

    def value(self, key: str, default: Any = None) -> Any:
        a = self.attributes.get(key)
        return a.value if a is not None else default

    def set(self, attr: SoilAttribute) -> None:
        self.attributes[attr.key] = attr

    def is_empty(self) -> bool:
        return not self.attributes

    def needs_refresh(self, *, now: Optional[datetime] = None) -> bool:
        """True if any non-derived attribute is stale (drives the lifecycle)."""
        return any(
            a.is_stale(now=now) for a in self.attributes.values() if not a.derived
        )

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "lat": self.lat,
            "lon": self.lon,
            "built_at": self.built_at,
            "schema_version": self.schema_version,
            "provider_status": self.provider_status,
            "attributes": {k: a.to_dict() for k, a in self.attributes.items()},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SoilProfile":
        attrs = {
            k: SoilAttribute.from_dict(v)
            for k, v in (d.get("attributes") or {}).items()
        }
        return cls(
            field_id=d.get("field_id"),
            lat=d.get("lat"),
            lon=d.get("lon"),
            attributes=attrs,
            provider_status=d.get("provider_status") or {},
            built_at=d.get("built_at") or _utcnow_iso(),
            schema_version=d.get("schema_version") or 1,
        )

    def to_ai_summary(self) -> str:
        """Render a compact, human-readable block for the AI advisor prompt.

        Groups attributes logically and states source + confidence so the model
        can reason about how much to trust each figure — and, crucially, so it
        never re-asks the farmer for soil facts KurimaSense already holds.
        """
        if self.is_empty():
            return ""

        def line(key: str, label: str, fmt=lambda v: v) -> Optional[str]:
            a = self.attributes.get(key)
            if a is None or a.value is None:
                return None
            try:
                shown = fmt(a.value)
            except Exception:
                shown = a.value
            unit = f" {a.unit}" if a.unit else ""
            conf = confidence_label(a.confidence)
            src = a.source
            return f"- {label}: {shown}{unit} (source: {src}, confidence: {conf})"

        groups: List[tuple[str, List[Optional[str]]]] = [
            ("Classification & texture", [
                line("soil_classification", "Soil type"),
                line("texture_class", "Texture"),
                line("sand_pct", "Sand"),
                line("silt_pct", "Silt"),
                line("clay_pct", "Clay"),
            ]),
            ("Chemistry", [
                line("ph", "pH (H2O)"),
                line("organic_carbon", "Organic carbon"),
                line("organic_matter", "Organic matter"),
                line("nitrogen", "Total nitrogen"),
                line("cec", "CEC"),
            ]),
            ("Physical & water", [
                line("bulk_density", "Bulk density"),
                line("water_holding_capacity", "Plant-available water capacity"),
                line("available_water", "Available water"),
                line("root_depth", "Effective rooting depth"),
                line("drainage", "Drainage"),
                line("erosion_risk", "Erosion risk"),
            ]),
            ("Terrain & climate", [
                line("elevation", "Elevation"),
                line("slope", "Slope"),
                line("terrain", "Terrain"),
                line("climate_zone", "Agro-ecological zone"),
                line("historical_rainfall", "Mean annual rainfall"),
            ]),
        ]

        out: List[str] = ["**Soil Intelligence Profile** (persisted for this field):"]
        for title, lines in groups:
            present = [l for l in lines if l]
            if present:
                out.append(f"_{title}_")
                out.extend(present)
        return "\n".join(out)
