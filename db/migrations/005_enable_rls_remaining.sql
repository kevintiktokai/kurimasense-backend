-- Migration 005: Enable RLS on the remaining backend-only tables.
-- Follows 004. Verified the consumer frontend (kurima-sense) only ever calls
-- supabase-js `.from('profiles')` — no .rpc(), no dynamic .from(var) — so these
-- six are never touched with the anon/authenticated key. Backend bypasses RLS
-- (postgres owner role / service_role), so the app is unaffected.
--
-- Idempotent. Deny-by-default (no policies). Not the Sprint 4 FORCE-RLS work.
--
-- spatial_ref_sys is intentionally excluded: it is PostGIS public reference data
-- (SRID/EPSG definitions), extension-managed, non-sensitive. Enabling RLS there
-- risks breaking spatial queries for no security benefit.

ALTER TABLE public.farm_tasks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_events    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_log      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents      ENABLE ROW LEVEL SECURITY;
