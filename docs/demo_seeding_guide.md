# Demo data seeding guide

**This is demo data, not production.** `scripts/seed_demo_fields.py` seeds ~40
fields and their growers into an **institutional** tenant using fictional
Zimbabwean grower names on **real GPS polygons** in real tobacco districts
(Centenary, Mt Darwin, Bindura, Karoi, Chinhoyi, Murehwa, Marondera, Headlands).
Sentinel-2 returns genuine satellite data for those coordinates — only the names
and field labels are synthetic.

The script is **manual and not exposed via any API**.

## Seed
```bash
python scripts/seed_demo_fields.py --tenant-id <institutional-tenant-uuid>
# optional: --num-fields 40   --seed 42 (reproducible)
```
- Refuses to run without `--tenant-id`, and refuses any tenant that isn't an
  active **institutional** tenant.
- Creates one grower per 1-3 fields (most have 1), each field with a square
  polygon sized to its hectares, a crop/variety from the demo mix (≈80% flue-cured
  tobacco), a planting date 60-180 days back, and a Natural Region.
- All demo rows are marked `DEMO_SEED: ` (field name) / a fixed demo note (grower).

## Verify the seed
```sql
SELECT count(*) FROM fields  WHERE tenant_id = '<uuid>' AND name LIKE 'DEMO_SEED:%';
SELECT count(*) FROM growers WHERE tenant_id = '<uuid>' AND notes LIKE 'DEMO_SEED:%';
```

## Satellite backfill
There is **no dedicated backfill worker** in this repo, so the seed writes the new
field IDs to `scripts/.demo_backfill_queue.txt` and prints instructions. Trigger
Sentinel-2 ingestion per field (the existing per-field analysis, e.g. the
authenticated `POST /fields/{id}/analyze`, looped over the queue). History fills
over 24-48 hours subject to Sentinel Hub rate limits and cloud-free passes.

Monitor progress:
```sql
SELECT field_id, COUNT(*) AS obs_count, MAX(log_date) AS latest
FROM daily_logs
WHERE field_id IN (SELECT id FROM fields WHERE tenant_id = '<uuid>'
                                            AND name LIKE 'DEMO_SEED:%')
GROUP BY field_id ORDER BY obs_count DESC;
```

## Warm / validate KurimaScores (optional)
```bash
python scripts/recompute_kurima_scores.py --tenant-id <uuid>
```
KurimaScores are computed **on-the-fly** by the aggregator (no stored column), so
this is a validation/warm-up, not a required step.

## Clear the demo data
```bash
python scripts/seed_demo_fields.py --tenant-id <uuid> --clear
```
- ⚠️ `--clear` is destructive **within the demo scope only**. It deletes rows
  matched by the `DEMO_SEED:` marker (field name) / demo note (grower) — it never
  touches real fields/growers. Do not rely on tenant_id alone; the marker is the
  guard.

## Notes / findings
- The real fields size column is `size_hectares` (not `area_hectares`).
- `fields` had no `natural_region` column; the script adds it idempotently
  (`ALTER TABLE fields ADD COLUMN IF NOT EXISTS natural_region TEXT`).
- No `profiles`/`tenant_members` rows are created — only `fields` and `growers`.
- Phone numbers are left NULL (no fake numbers).
