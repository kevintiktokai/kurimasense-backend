"""
Tests for the Soil Intelligence subsystem.

Hermetic and deterministic: they exercise the pure model, merger, derivation, and
orchestration paths with *fake* in-memory providers, so they run with no network
and no database. The live SoilGrids/Open-Meteo providers are not exercised here
(that is covered by the manual smoke path); these tests lock down the logic that
turns raw provider output into a persisted, AI-ready profile.
"""

import asyncio
from datetime import datetime, timezone, timedelta

import pytest

from services.soil_intelligence.models import (
    SoilAttribute, SoilProfile, RefreshPolicy, confidence_label,
)
from services.soil_intelligence.merger import merge_attributes, build_profile
from services.soil_intelligence.derive import usda_texture_class, enrich_with_derived
from services.soil_intelligence.providers.base import SoilProvider
from services.soil_intelligence.providers.terrain import classify_zimbabwe_natural_region
from services.soil_intelligence.service import build_profile_from_coords, _soonest_refresh


# --------------------------------------------------------------------------- #
# Fake providers
# --------------------------------------------------------------------------- #
class _FakeProvider(SoilProvider):
    def __init__(self, name, priority, attrs):
        self.name = name
        self.priority = priority
        self._attrs = attrs

    async def fetch(self, lat, lon):
        return list(self._attrs)


class _BoomProvider(SoilProvider):
    name = "Boom"
    priority = 1

    async def fetch(self, lat, lon):
        raise RuntimeError("network exploded")


def _attr(key, value, source="A", conf=0.6, **kw):
    return SoilAttribute(key=key, value=value, source=source, confidence=conf, **kw)


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
def test_confidence_label_bands():
    assert confidence_label(0.9) == "high"
    assert confidence_label(0.6) == "moderate"
    assert confidence_label(0.3) == "low"
    assert confidence_label(0.1) == "very low"
    assert confidence_label(None) == "unknown"


def test_attribute_staleness():
    old = SoilAttribute(
        key="ph", value=5.5, refresh_policy=RefreshPolicy.ANNUAL.value,
        acquired_at=(datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),
    )
    fresh = SoilAttribute(
        key="ph", value=5.5, refresh_policy=RefreshPolicy.ANNUAL.value,
        acquired_at=datetime.now(timezone.utc).isoformat(),
    )
    static = SoilAttribute(
        key="elevation", value=1200, refresh_policy=RefreshPolicy.STATIC.value,
        acquired_at=(datetime.now(timezone.utc) - timedelta(days=9999)).isoformat(),
    )
    assert old.is_stale() is True
    assert fresh.is_stale() is False
    assert static.is_stale() is False  # static never goes stale


def test_profile_roundtrip_and_needs_refresh():
    p = SoilProfile(field_id="f1", lat=-18.0, lon=31.0)
    p.set(_attr("ph", 5.6, conf=0.8))
    p.set(SoilAttribute(
        key="clay_pct", value=22, refresh_policy=RefreshPolicy.MULTI_YEAR.value,
        acquired_at=(datetime.now(timezone.utc) - timedelta(days=5000)).isoformat(),
    ))
    restored = SoilProfile.from_dict(p.to_dict())
    assert restored.field_id == "f1"
    assert restored.value("ph") == 5.6
    assert restored.needs_refresh() is True  # the stale clay attribute triggers it


def test_ai_summary_includes_provenance():
    p = SoilProfile(field_id="f1")
    p.set(_attr("ph", 5.4, source="SoilGrids", conf=0.85))
    summary = p.to_ai_summary()
    assert "Soil Intelligence Profile" in summary
    assert "pH" in summary
    assert "SoilGrids" in summary
    assert "high" in summary  # confidence label


def test_empty_profile_summary_is_blank():
    assert SoilProfile().to_ai_summary() == ""


# --------------------------------------------------------------------------- #
# Merger — priority then confidence
# --------------------------------------------------------------------------- #
def test_merge_priority_wins_over_confidence():
    lowpri_high_conf = _FakeProvider("Model", 5, [_attr("ph", 6.0, "Model", 0.9)])
    hipri_low_conf = _FakeProvider("Lab", 100, [_attr("ph", 5.2, "Lab", 0.4)])
    merged = merge_attributes([
        (lowpri_high_conf, lowpri_high_conf._attrs),
        (hipri_low_conf, hipri_low_conf._attrs),
    ])
    assert merged["ph"].value == 5.2  # lab (higher priority) wins despite lower conf


def test_merge_confidence_breaks_tie_within_same_priority():
    a = _FakeProvider("A", 10, [_attr("clay_pct", 20, "A", 0.5)])
    b = _FakeProvider("B", 10, [_attr("clay_pct", 25, "B", 0.8)])
    merged = merge_attributes([(a, a._attrs), (b, b._attrs)])
    assert merged["clay_pct"].value == 25  # higher confidence wins the tie


def test_merge_skips_none_values():
    a = _FakeProvider("A", 10, [_attr("ph", None, "A", 0.9)])
    merged = merge_attributes([(a, a._attrs)])
    assert "ph" not in merged


def test_build_profile_records_provider_status():
    ok = _FakeProvider("OK", 10, [_attr("ph", 5.5, "OK")])
    empty = _FakeProvider("Empty", 10, [])
    profile = build_profile("f1", -18.0, 31.0, [(ok, ok._attrs), (empty, empty._attrs)])
    assert profile.provider_status["OK"] == "ok"
    assert profile.provider_status["Empty"] == "error"


# --------------------------------------------------------------------------- #
# Derivation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sand,silt,clay,expected", [
    (90, 5, 5, "sand"),
    (60, 17, 23, "sandy clay loam"),
    (20, 65, 15, "silt loam"),
    (20, 20, 60, "clay"),
    (40, 40, 20, "loam"),
])
def test_usda_texture_class(sand, silt, clay, expected):
    assert usda_texture_class(sand, silt, clay) == expected


def test_texture_class_normalises_off_100_sums():
    # Depth-averaging can yield sums != 100; classifier must still work.
    assert usda_texture_class(45, 9, 12) != "unknown"


def test_enrich_derives_full_agronomic_set():
    p = SoilProfile(field_id="f1")
    p.set(_attr("sand_pct", 59, conf=0.6))
    p.set(_attr("silt_pct", 18, conf=0.3))
    p.set(_attr("clay_pct", 23, conf=0.3))
    p.set(_attr("organic_carbon", 14.0, conf=0.4))     # g/kg
    p.set(_attr("field_capacity", 28.0, conf=0.5))     # vol %
    p.set(_attr("wilting_point", 14.0, conf=0.5))      # vol %
    enrich_with_derived(p, slope_deg=4.0)

    assert p.value("texture_class") == "sandy clay loam"
    assert p.value("drainage") is not None
    assert p.value("erosion_risk") is not None
    # organic matter = SOC(g/kg)/10 * 1.724 = 1.4 * 1.724
    assert p.value("organic_matter") == pytest.approx(2.41, abs=0.05)
    # available water = FC - WP = 14 vol%
    assert p.value("available_water") == pytest.approx(14.0, abs=0.1)
    # water-holding capacity = 14 * 10 = 140 mm/m
    assert p.value("water_holding_capacity") == pytest.approx(140.0, abs=1)
    assert p.value("root_depth") is not None
    assert p.value("terrain") is not None
    assert p.get("texture_class").derived is True


def test_enrich_does_not_override_authoritative_primary():
    p = SoilProfile(field_id="f1")
    p.set(_attr("sand_pct", 59))
    p.set(_attr("silt_pct", 18))
    p.set(_attr("clay_pct", 23))
    # A non-derived, authoritative texture (e.g. from a lab test) must survive.
    p.set(SoilAttribute(key="texture_class", value="loam", source="Lab", derived=False))
    enrich_with_derived(p)
    assert p.value("texture_class") == "loam"


# --------------------------------------------------------------------------- #
# Climate zone
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("rain,zone_prefix", [
    (1200, "NR I"),
    (850, "NR II"),
    (700, "NR III"),
    (500, "NR IV"),
    (300, "NR V"),
    (None, None),
])
def test_zimbabwe_natural_region(rain, zone_prefix):
    z = classify_zimbabwe_natural_region(rain)
    if zone_prefix is None:
        assert z is None
    else:
        assert z.startswith(zone_prefix)


# --------------------------------------------------------------------------- #
# Orchestration (async, fake providers, no DB)
# --------------------------------------------------------------------------- #
def test_build_profile_from_coords_merges_and_derives():
    soil = _FakeProvider("SoilGrids", 10, [
        _attr("sand_pct", 59, "SoilGrids"), _attr("silt_pct", 18, "SoilGrids"),
        _attr("clay_pct", 23, "SoilGrids"), _attr("ph", 5.7, "SoilGrids", 0.85),
    ])
    terrain = _FakeProvider("Open-Meteo", 5, [
        _attr("elevation", 1667, "Open-Meteo", 0.9, unit="m"),
        _attr("historical_rainfall", 834, "Open-Meteo", 0.8),
    ])
    profile = asyncio.run(build_profile_from_coords(
        "f1", -18.19, 31.55, providers=[soil, terrain]))
    assert profile.value("ph") == 5.7
    assert profile.value("elevation") == 1667
    assert profile.value("texture_class") == "sandy clay loam"  # derived
    assert profile.provider_status["SoilGrids"] == "ok"
    assert profile.provider_status["Open-Meteo"] == "ok"


def test_orchestrator_survives_a_failing_provider():
    good = _FakeProvider("Good", 10, [_attr("ph", 6.0, "Good")])
    profile = asyncio.run(build_profile_from_coords(
        "f1", -18.0, 31.0, providers=[good, _BoomProvider()]))
    assert profile.value("ph") == 6.0  # good provider's data still lands
    assert profile.provider_status["Boom"] == "error"


def test_soonest_refresh_ignores_derived_and_static():
    p = SoilProfile(field_id="f1")
    p.set(SoilAttribute(key="ph", value=5.5, refresh_policy=RefreshPolicy.MULTI_YEAR.value))
    p.set(SoilAttribute(key="elevation", value=1200, refresh_policy=RefreshPolicy.STATIC.value))
    p.set(SoilAttribute(key="texture_class", value="loam", derived=True,
                        refresh_policy=RefreshPolicy.MULTI_YEAR.value))
    due = _soonest_refresh(p)
    assert due is not None  # driven by the multi-year ph attribute
    assert due > datetime.now(timezone.utc)
