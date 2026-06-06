#!/usr/bin/env python3
"""
Demo data seeding for an institutional tenant (MVP PR 1)
=======================================================
ONE-SHOT, MANUAL demo tool. Seeds ~40 fields + their growers into an
institutional tenant using **fictional Zimbabwean grower names on REAL GPS
polygons** in real tobacco districts, so Sentinel-2 returns genuine satellite
data. Only names/labels are synthetic.

NOT a production tool and NOT exposed as an API endpoint. Safe to re-run:
demo rows are marked with a "DEMO_SEED: " prefix and only those are touched by
``--clear``.

Usage:
    python scripts/seed_demo_fields.py --tenant-id <uuid>
    python scripts/seed_demo_fields.py --tenant-id <uuid> --clear
    python scripts/seed_demo_fields.py --tenant-id <uuid> --num-fields 40

Generation logic (``build_seed_plan``) is pure/deterministic given an RNG so it
is unit-tested without a database.

Schema notes (findings):
  * the real fields column is ``size_hectares`` (the spec's ``area_hectares``);
  * ``fields`` has no ``natural_region`` column — this script adds it idempotently
    (``ALTER TABLE ... ADD COLUMN IF NOT EXISTS``) so demo fields can carry it;
  * there is no ``workers/backfill_ingestion.py`` — satellite backfill is queued
    to a file with run instructions (Option 2 in the spec).
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
import uuid
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NUM_FIELDS = 40
DEMO_PREFIX = "DEMO_SEED: "
DEMO_GROWER_NOTE = "DEMO_SEED: Demo grower seeded for institutional dashboard validation"

FIRST_NAMES = [
    "Tinashe", "Tafadzwa", "Tendai", "Chipo", "Tatenda", "Farai",
    "Munashe", "Rumbidzai", "Tongai", "Kudakwashe", "Tariro",
    "Simbarashe", "Rutendo", "Nyasha", "Tichaona", "Vimbai",
    "Tendekai", "Memory", "Tapiwa", "Cleopatra", "Wisdom", "Pride",
    "Blessing", "Anesu", "Rangarirai", "Tinaye", "Maita",
    "Privilege", "Ngonidzashe", "Shamiso",
]

LAST_NAMES = [
    "Moyo", "Ndlovu", "Sibanda", "Nkomo", "Chivasa", "Mukamuri",
    "Mutasa", "Chitando", "Chigumba", "Madondo", "Mushava", "Nhongo",
    "Gondo", "Magaya", "Chimene", "Madziwa", "Mhlanga", "Dube",
    "Nyathi", "Tshuma", "Chinyoka", "Mutsago", "Pasipanodya",
    "Marufu", "Chinyani", "Murwira", "Chiweshe", "Madhuyu",
    "Mapuranga", "Chirwa",
]

# district -> (center_lat, center_lon, spread_radius_deg)
DISTRICTS = {
    "Centenary":   (-16.7833, 31.1167, 0.18),
    "Mt Darwin":   (-16.7833, 31.5833, 0.20),
    "Bindura":     (-17.3019, 31.3306, 0.15),
    "Karoi":       (-16.8167, 29.6833, 0.20),
    "Chinhoyi":    (-17.3656, 30.1944, 0.15),
    "Murehwa":     (-17.6500, 31.7833, 0.15),
    "Marondera":   (-18.1853, 31.5519, 0.15),
    "Headlands":   (-18.3500, 32.0167, 0.15),
}

NATURAL_REGION_BY_DISTRICT = {
    "Centenary": "II", "Mt Darwin": "II", "Bindura": "II", "Karoi": "II",
    "Chinhoyi": "IIa", "Murehwa": "IIa", "Marondera": "IIa", "Headlands": "I",
}

# (crop_type, variety, days_to_maturity_target, weight)
CROP_MIX = [
    ("tobacco_flue_cured", "KRK26", 145, 0.30),
    ("tobacco_flue_cured", "K326", 150, 0.25),
    ("tobacco_flue_cured", "KRK22", 145, 0.15),
    ("tobacco_flue_cured", "T-66", 140, 0.10),
    ("maize",              "SC727", 145, 0.10),
    ("cotton",             "SZ9314", 165, 0.05),
    ("soybean",            "Storm", 135, 0.05),
]

FIELD_SIZES_HA = [
    (1.5, 0.20), (2.5, 0.25), (4.0, 0.25), (6.0, 0.15), (8.0, 0.10), (12.0, 0.05),
]

PLANTING_DATE_RANGE_DAYS = (60, 180)  # days before today

# fields per grower distribution (most have one)
FIELDS_PER_GROWER = [(1, 0.60), (2, 0.30), (3, 0.10)]

TOBACCO_CROPS = {"tobacco_flue_cured"}

_CROP_SHORT = {
    "tobacco_flue_cured": "Flue-Cured",
    "maize": "Maize",
    "cotton": "Cotton",
    "soybean": "Soybean",
}

_M_PER_DEG = 111320.0  # metres per degree latitude (≈ longitude at equator)


# ---------------------------------------------------------------------------
# Pure generation (unit-tested, no I/O)
# ---------------------------------------------------------------------------
def weighted_choice(rng: random.Random, items):
    """items: list of (value, weight). Returns a value."""
    total = sum(w for _, w in items)
    r = rng.uniform(0, total)
    upto = 0.0
    for value, w in items:
        upto += w
        if r <= upto:
            return value
    return items[-1][0]


def make_polygon(rng: random.Random, center_lat: float, center_lon: float, size_ha: float):
    """A roughly-square 4-vertex polygon of ~size_ha around (center_lat, center_lon)."""
    side_m = math.sqrt(size_ha * 10_000.0)  # area = ha * 10,000 m²
    half = side_m / 2.0
    lat_deg = half / _M_PER_DEG
    lon_deg = half / (_M_PER_DEG * math.cos(math.radians(center_lat)))
    # small per-axis jitter (±5%) so polygons aren't identical, area stays ~size_ha
    jlat = lat_deg * rng.uniform(0.95, 1.05)
    jlon = lon_deg * rng.uniform(0.95, 1.05)
    return [
        {"lat": round(center_lat + jlat, 6), "lon": round(center_lon - jlon, 6)},  # NW
        {"lat": round(center_lat + jlat, 6), "lon": round(center_lon + jlon, 6)},  # NE
        {"lat": round(center_lat - jlat, 6), "lon": round(center_lon + jlon, 6)},  # SE
        {"lat": round(center_lat - jlat, 6), "lon": round(center_lon - jlon, 6)},  # SW
    ]


def polygon_centroid(polygon):
    n = len(polygon)
    return {
        "lat": round(sum(p["lat"] for p in polygon) / n, 6),
        "lon": round(sum(p["lon"] for p in polygon) / n, 6),
    }


def build_seed_plan(rng: random.Random, num_fields: int = NUM_FIELDS) -> dict:
    """
    Build the demo plan deterministically given ``rng``. Returns
    ``{"growers": [...], "fields": [...]}`` where each field references its
    grower by ``grower_index``. No database access.
    """
    # Unique grower names.
    combos = [(f, l) for f in FIRST_NAMES for l in LAST_NAMES]
    rng.shuffle(combos)

    growers, fields = [], []
    district_names = list(DISTRICTS.keys())
    di = 0  # round-robin district cursor
    field_count = 0
    grower_idx = 0

    while field_count < num_fields:
        first, last = combos[grower_idx % len(combos)]
        n_for_grower = min(weighted_choice(rng, FIELDS_PER_GROWER), num_fields - field_count)
        center_for_grower = None
        growers.append({
            "name": f"{first} {last}",
            "notes": DEMO_GROWER_NOTE,
        })
        for suffix_i in range(n_for_grower):
            district = district_names[di % len(district_names)]
            di += 1
            clat, clon, spread = DISTRICTS[district]
            # random offset within the district spread
            flat = clat + rng.uniform(-spread, spread)
            flon = clon + rng.uniform(-spread, spread)
            crop_type, variety = weighted_choice(
                rng, [((c, v), w) for c, v, _d, w in CROP_MIX]
            )
            size_ha = weighted_choice(rng, FIELD_SIZES_HA)
            polygon = make_polygon(rng, flat, flon, size_ha)
            days_ago = rng.randint(*PLANTING_DATE_RANGE_DAYS)
            planting = (date.today() - timedelta(days=days_ago)).isoformat()
            is_tobacco = crop_type in TOBACCO_CROPS
            suffix = "" if n_for_grower == 1 else f" {chr(ord('A') + suffix_i)}"
            name = f"{DEMO_PREFIX}{first} - {district} - {_CROP_SHORT.get(crop_type, crop_type)}{suffix}"
            grower = growers[grower_idx]
            if center_for_grower is None:
                center_for_grower = polygon_centroid(polygon)
                grower["coordinates"] = center_for_grower
            fields.append({
                "grower_index": grower_idx,
                "district": district,
                "crop_type": crop_type,
                "variety": variety,
                "size_ha": size_ha,
                "planting_date": planting,
                "is_transplanted": is_tobacco,
                "transplant_date": planting if is_tobacco else None,
                "polygon": polygon,
                "centroid": polygon_centroid(polygon),
                "natural_region": NATURAL_REGION_BY_DISTRICT[district],
                "name": name,
            })
            field_count += 1
        grower_idx += 1

    return {"growers": growers, "fields": fields}


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------
def _connect():
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(db_url)


def _tenant_is_institutional(conn, tenant_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT tenant_type FROM tenants WHERE id = %s::uuid AND deleted_at IS NULL", (tenant_id,))
    row = cur.fetchone()
    cur.close()
    return bool(row) and row[0] == "institutional"


def _owner_user_id(conn, tenant_id: str):
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id::text FROM tenant_members WHERE tenant_id = %s::uuid AND member_role='owner' "
        "ORDER BY joined_at ASC LIMIT 1",
        (tenant_id,),
    )
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def _demo_exists(conn, tenant_id: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM fields WHERE tenant_id = %s::uuid AND name LIKE %s LIMIT 1",
        (tenant_id, DEMO_PREFIX + "%"),
    )
    found = cur.fetchone() is not None
    cur.close()
    return found


def _ensure_columns(conn):
    # fields has no natural_region column today — add it (additive, idempotent).
    cur = conn.cursor()
    cur.execute("ALTER TABLE fields ADD COLUMN IF NOT EXISTS natural_region TEXT")
    conn.commit()
    cur.close()


def _clear_demo(conn, tenant_id: str) -> int:
    """Delete ONLY demo-marked fields + growers in this tenant (and their child
    rows). Never touches real data — filtered by the DEMO_SEED marker."""
    import psycopg2.extras  # noqa
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM fields WHERE tenant_id = %s::uuid AND name LIKE %s",
        (tenant_id, DEMO_PREFIX + "%"),
    )
    field_ids = [r[0] for r in cur.fetchall()]
    if field_ids:
        for child in ("daily_log", "daily_logs", "field_inputs", "yield_history", "farm_tasks"):
            try:
                cur.execute(f"DELETE FROM {child} WHERE field_id = ANY(%s)", (field_ids,))
            except Exception:
                conn.rollback()
        cur.execute("DELETE FROM fields WHERE id = ANY(%s)", (field_ids,))
    cur.execute(
        "DELETE FROM growers WHERE tenant_id = %s::uuid AND notes = %s",
        (tenant_id, DEMO_GROWER_NOTE),
    )
    conn.commit()
    cur.close()
    return len(field_ids)


def _insert_plan(conn, tenant_id: str, owner_user_id: str, plan: dict):
    cur = conn.cursor()
    grower_ids = []
    for g in plan["growers"]:
        gid = str(uuid.uuid4())
        coords = g.get("coordinates")
        import json
        cur.execute(
            """
            INSERT INTO growers (id, tenant_id, name, phone, coordinates, created_by_user_id, notes, created_at, updated_at)
            VALUES (%s::uuid, %s::uuid, %s, NULL, %s::jsonb, %s::uuid, %s, NOW(), NOW())
            """,
            (gid, tenant_id, g["name"], json.dumps(coords) if coords else None, owner_user_id, g["notes"]),
        )
        grower_ids.append(gid)

    field_ids = []
    import json
    for f in plan["fields"]:
        fid = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO fields
              (id, tenant_id, user_id, grower_id, name, crop_type, crop, variety,
               planting_date, transplant_date, is_transplanted, size_hectares,
               polygon_coordinates, natural_region, created_at)
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s::jsonb, %s, NOW())
            """,
            (fid, tenant_id, owner_user_id, grower_ids[f["grower_index"]], f["name"],
             f["crop_type"], f["crop_type"], f["variety"], f["planting_date"],
             f["transplant_date"], f["is_transplanted"], f["size_ha"],
             json.dumps(f["polygon"]), f["natural_region"]),
        )
        field_ids.append(fid)
    conn.commit()
    cur.close()
    return grower_ids, field_ids


def _queue_backfill(field_ids):
    """No backfill worker exists; write field ids to a queue file with instructions."""
    path = os.path.join(os.path.dirname(__file__), ".demo_backfill_queue.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(field_ids) + "\n")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Seed demo fields/growers for an institutional tenant.")
    ap.add_argument("--tenant-id", required=True, help="Target institutional tenant UUID")
    ap.add_argument("--clear", action="store_true", help="Remove existing DEMO_SEED data first, then re-seed")
    ap.add_argument("--num-fields", type=int, default=NUM_FIELDS)
    ap.add_argument("--seed", type=int, default=None, help="RNG seed (reproducible plans)")
    args = ap.parse_args()

    conn = _connect()
    try:
        if not _tenant_is_institutional(conn, args.tenant_id):
            print(f"❌ {args.tenant_id} is not an active institutional tenant. Refusing.")
            sys.exit(1)
        owner = _owner_user_id(conn, args.tenant_id)
        if not owner:
            print(f"❌ No owner found for tenant {args.tenant_id}. Refusing.")
            sys.exit(1)

        if args.clear:
            removed = _clear_demo(conn, args.tenant_id)
            print(f"🧹 Cleared {removed} demo field(s) (and their growers) from tenant {args.tenant_id}.")
        elif _demo_exists(conn, args.tenant_id):
            print(
                f"Demo fields already exist in tenant {args.tenant_id}. To re-seed, first run:\n"
                f"  python scripts/seed_demo_fields.py --tenant-id {args.tenant_id} --clear"
            )
            sys.exit(0)

        _ensure_columns(conn)
        rng = random.Random(args.seed)
        plan = build_seed_plan(rng, args.num_fields)
        grower_ids, field_ids = _insert_plan(conn, args.tenant_id, owner, plan)
        queue_path = _queue_backfill(field_ids)

        print(f"""
Seeded {len(grower_ids)} growers and {len(field_ids)} fields in tenant {args.tenant_id}.

Field IDs written to: {queue_path}

Satellite backfill: there is no dedicated backfill worker in this repo. Trigger
Sentinel-2 ingestion per field (the existing per-field analysis), e.g. via the
authenticated POST /fields/{{id}}/analyze endpoint or a batch loop over the queue
file. Sentinel-2 history will populate over the next 24-48 hours depending on
Sentinel Hub rate limits and cloud-free observation availability.

Verify backfill progress with:
  SELECT field_id, COUNT(*) AS obs_count, MAX(log_date) AS latest
  FROM daily_logs
  WHERE field_id IN (SELECT id FROM fields WHERE tenant_id = '{args.tenant_id}'
                                              AND name LIKE 'DEMO_SEED:%')
  GROUP BY field_id ORDER BY obs_count DESC;

Warm/verify KurimaScores after backfill:
  python scripts/recompute_kurima_scores.py --tenant-id {args.tenant_id}
""")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
