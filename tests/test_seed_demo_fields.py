"""
Tests for the demo field seeder (MVP PR 1).

Exercises the pure generation logic (no DB). DB-dependent paths (insert, --clear,
consumer-tenant refusal) are integration concerns; the CLI-arg refusal is covered
via subprocess.
"""

import math
import os
import random
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import seed_demo_fields as seed  # noqa: E402


def _poly_area_ha(poly):
    """Approximate polygon area in hectares via planar projection + shoelace."""
    lat0 = sum(p["lat"] for p in poly) / len(poly)
    lon0 = sum(p["lon"] for p in poly) / len(poly)
    pts = [
        ((p["lon"] - lon0) * 111320.0 * math.cos(math.radians(lat0)),
         (p["lat"] - lat0) * 111320.0)
        for p in poly
    ]
    area_m2 = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        area_m2 += x1 * y2 - x2 * y1
    return abs(area_m2) / 2.0 / 10_000.0


# ---------------------------------------------------------------------------
# 1. Field generation
# ---------------------------------------------------------------------------
def test_generates_requested_number_of_fields():
    plan = seed.build_seed_plan(random.Random(7), 40)
    assert len(plan["fields"]) == 40


def test_crop_mix_proportions_within_tolerance():
    # Large sample → weighting converges to the configured proportions (±10%).
    plan = seed.build_seed_plan(random.Random(3), 1000)
    crops = [f["crop_type"] for f in plan["fields"]]
    n = len(crops)
    tobacco = sum(1 for c in crops if c == "tobacco_flue_cured") / n
    assert 0.70 <= tobacco <= 0.90, tobacco  # target 0.80
    maize = sum(1 for c in crops if c == "maize") / n
    assert 0.05 <= maize <= 0.15, maize       # target 0.10


def test_all_fields_have_valid_zimbabwe_polygons():
    plan = seed.build_seed_plan(random.Random(11), 40)
    for f in plan["fields"]:
        poly = f["polygon"]
        assert len(poly) == 4
        for p in poly:
            assert -23.0 <= p["lat"] <= -15.0, p   # Zimbabwe latitude band
            assert 25.0 <= p["lon"] <= 34.0, p     # Zimbabwe longitude band


def test_district_distribution_covers_all_districts():
    plan = seed.build_seed_plan(random.Random(5), 40)
    districts = {f["district"] for f in plan["fields"]}
    assert districts == set(seed.DISTRICTS.keys())


def test_natural_region_assigned_per_district():
    plan = seed.build_seed_plan(random.Random(5), 40)
    for f in plan["fields"]:
        assert f["natural_region"] == seed.NATURAL_REGION_BY_DISTRICT[f["district"]]


# ---------------------------------------------------------------------------
# 2. Grower-field linking
# ---------------------------------------------------------------------------
def test_grower_field_linking():
    plan = seed.build_seed_plan(random.Random(9), 40)
    n_growers = len(plan["growers"])
    # every field references a valid grower
    for f in plan["fields"]:
        assert 0 <= f["grower_index"] < n_growers
    # no orphan growers: each grower has >= 1 field
    used = {f["grower_index"] for f in plan["fields"]}
    assert used == set(range(n_growers))
    # some growers have multiple fields
    from collections import Counter
    counts = Counter(f["grower_index"] for f in plan["fields"])
    assert max(counts.values()) >= 2
    assert all(1 <= c <= 3 for c in counts.values())
    # realistic grower count for 40 fields
    assert 20 <= n_growers <= 38


def test_grower_names_unique_and_have_demo_marker():
    plan = seed.build_seed_plan(random.Random(2), 40)
    names = [g["name"] for g in plan["growers"]]
    assert len(names) == len(set(names))  # unique
    assert all(g["notes"] == seed.DEMO_GROWER_NOTE for g in plan["growers"])
    assert all(f["name"].startswith(seed.DEMO_PREFIX) for f in plan["fields"])


# ---------------------------------------------------------------------------
# 3. Polygon size sanity
# ---------------------------------------------------------------------------
def test_polygon_area_matches_size():
    rng = random.Random(1)
    poly4 = seed.make_polygon(rng, -17.3, 31.0, 4.0)
    assert abs(_poly_area_ha(poly4) - 4.0) / 4.0 <= 0.20  # within ±20%


def test_larger_field_has_larger_polygon():
    rng = random.Random(1)
    small = _poly_area_ha(seed.make_polygon(rng, -17.3, 31.0, 1.5))
    big = _poly_area_ha(seed.make_polygon(rng, -17.3, 31.0, 6.0))
    assert big > small


def test_tobacco_fields_are_transplanted():
    plan = seed.build_seed_plan(random.Random(4), 40)
    for f in plan["fields"]:
        if f["crop_type"] == "tobacco_flue_cured":
            assert f["is_transplanted"] is True
            assert f["transplant_date"] == f["planting_date"]
        else:
            assert f["is_transplanted"] is False


# ---------------------------------------------------------------------------
# 5. Tenant scope — CLI refuses without --tenant-id
# ---------------------------------------------------------------------------
def test_cli_requires_tenant_id():
    script = os.path.join(os.path.dirname(__file__), "..", "scripts", "seed_demo_fields.py")
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    assert result.returncode != 0
    assert "tenant-id" in (result.stderr + result.stdout).lower()
