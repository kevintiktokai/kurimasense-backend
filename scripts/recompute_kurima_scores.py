#!/usr/bin/env python3
"""
KurimaScore recomputation / warm-up for a tenant's fields (MVP PR 1)
===================================================================
One-shot helper. Iterates every field in a tenant, runs the field-state
aggregator's ``assemble_field_state`` over its ``daily_logs``, and prints the
resulting KurimaScore.

FINDING: the aggregator computes KurimaScores **on-the-fly per request** — there
is no stored score column and no cache beyond the endpoint's short-lived 120s
response cache. So this script does not *store* anything; it is a
validation/warm-up that confirms each demo field produces a score once its
satellite backfill has landed. It is therefore optional, not required for the
demo to work.

Usage:
    python scripts/recompute_kurima_scores.py --tenant-id <uuid>
"""

from __future__ import annotations

import argparse
import os
import sys

# Make the repo root importable when launched as `python scripts/<this>.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.field_state.aggregator import assemble_field_state  # noqa: E402


def _connect():
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(db_url)


def main():
    ap = argparse.ArgumentParser(description="Warm/validate KurimaScores for a tenant's fields.")
    ap.add_argument("--tenant-id", required=True)
    args = ap.parse_args()

    from psycopg2.extras import RealDictCursor
    conn = _connect()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, user_id, tenant_id::text AS tenant_id, grower_id::text AS grower_id,
                   name, crop_type, variety, planting_date, transplant_date, is_transplanted,
                   size_hectares, polygon_coordinates, natural_region, health_score
            FROM fields WHERE tenant_id = %s::uuid
            ORDER BY name
            """,
            (args.tenant_id,),
        )
        fields = cur.fetchall()
        print(f"Found {len(fields)} field(s) in tenant {args.tenant_id}.\n")

        scored = 0
        for f in fields:
            cur.execute(
                "SELECT log_date, ndvi, evi, soil_moisture, cloud_cover FROM daily_logs "
                "WHERE field_id = %s::uuid ORDER BY log_date ASC LIMIT 90",
                (f["id"],),
            )
            logs = [dict(r) for r in cur.fetchall()]
            try:
                state = assemble_field_state(
                    field_row=dict(f), requester_id=None, daily_logs=logs, enforce_owner=False,
                )
                ks = state.kurima_score
                obs = state.indices.current.observation_quality
                print(f"  {f['name'][:48]:<48}  score={ks.score:>3} {ks.label:<10} obs={obs} logs={len(logs)}")
                scored += 1
            except Exception as exc:  # pragma: no cover
                print(f"  {f['name'][:48]:<48}  ERROR: {exc}")
        cur.close()
        print(f"\nComputed {scored}/{len(fields)} scores. (Scores are on-the-fly; nothing stored.)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
