-- Migration 004: Deny-by-default RLS on sensitive, backend-only tables.
-- Idempotent: ENABLE ROW LEVEL SECURITY is a no-op if already enabled.
--
-- Security model
-- ==============
-- The backend connects via psycopg2 as the `postgres` role, which OWNS these
-- tables. A table owner BYPASSES RLS as long as FORCE ROW LEVEL SECURITY is NOT
-- set — so the backend's queries are unaffected. Enabling RLS with NO policies
-- denies the public anon / authenticated Supabase roles (the anon key is shipped
-- in the frontend bundle), closing the direct-REST exposure flagged by the
-- Supabase advisory.
--
-- This is the immediate exposure fix, NOT the Sprint 4 work: provable per-tenant
-- isolation needs FORCE ROW LEVEL SECURITY + tenant_id policies, and must follow
-- Workstream 3.5 (migrate the ~25 user_id endpoints, then drop fields.user_id).
--
-- Tables deliberately NOT touched here (need a check of consumer supabase-js
-- usage first): farm_tasks, user_events, alerts, daily_log, knowledge_base,
-- documents. And spatial_ref_sys is PostGIS public reference data (RLS N/A).

-- New financial / outcome-loop tables (sensitive; no client dependency).
ALTER TABLE public.yield_projections   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.harvest_records     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_calibration   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grower_contracts    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.input_disbursements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deliveries          ENABLE ROW LEVEL SECURITY;

-- Existing tenant-isolation core (backend-only; closes the cross-tenant hole).
ALTER TABLE public.tenants        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.growers        ENABLE ROW LEVEL SECURITY;

-- Rollback (if a client legitimately needs direct access to one of these):
--   ALTER TABLE public.<table> DISABLE ROW LEVEL SECURITY;
-- or add a scoped policy rather than disabling.
