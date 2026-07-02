-- Migration 009 — Sentinel-1 SAR columns on daily_logs (Sprint 4, Slice 3)
--
-- Persist radar backscatter (VV/VH in dB) alongside the optical indices so the
-- Field State Aggregator has a wet-season floor when NDVI is cloud-blocked
-- (closes data-gap G2). Additive + idempotent — safe to re-run, no backfill.
--
-- Also mirrored idempotently in database.py init_db() so the columns self-create
-- on the next backend deploy even if this migration is applied out of band.

ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS sar_vv_db DOUBLE PRECISION;
ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS sar_vh_db DOUBLE PRECISION;

-- ROLLBACK (manual):
--   ALTER TABLE public.daily_logs DROP COLUMN IF EXISTS sar_vv_db;
--   ALTER TABLE public.daily_logs DROP COLUMN IF EXISTS sar_vh_db;
