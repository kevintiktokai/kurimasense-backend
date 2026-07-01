-- Migration 008 — Per-tenant RLS policies (Sprint 4, Slice 4: provable isolation)
--
-- Adds tenant-scoped Row-Level-Security POLICIES keyed on a per-request GUC
-- (`app.tenant_ids`) to the tenant-scoped tables. This is STEP 1 of the RLS
-- hardening and is intentionally SAFE + REVERSIBLE:
--
--   * RLS is already ENABLED on these tables (migrations 004/005) but NOT forced.
--   * The backend connects as the table OWNER, which BYPASSES RLS unless
--     `FORCE ROW LEVEL SECURITY` is set. This migration does NOT force RLS, so
--     the running app is completely unaffected (owner keeps bypassing).
--   * For non-owner roles (anon / authenticated PostgREST clients) the new
--     policies grant a row only when `app.tenant_ids` contains its tenant. Those
--     clients never set the GUC, so `app_tenant_ids()` returns '{}' and they see
--     zero extra rows — the deny-by-default posture is preserved.
--
-- Enforcement against the backend owner (FORCE + per-request GUC wiring) is the
-- gated STEP 2, tracked in SECURITY_HARDENING_SPRINT4.md / the FORCE runbook.
--
-- Reversible: see the "-- ROLLBACK" block at the bottom.

-- ─────────────────────────────────────────────────────────────────────────────
-- GUC accessor: returns the caller's tenant ids as uuid[], defensively.
--   * Missing setting  -> '{}'  (never NULL, never errors)
--   * Empty string     -> '{}'
-- STABLE + pinned search_path (no table refs; hardened against search_path abuse).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.app_tenant_ids()
RETURNS uuid[]
LANGUAGE sql
STABLE
SET search_path = ''
AS $$
    SELECT CASE
        WHEN COALESCE(current_setting('app.tenant_ids', true), '') = '' THEN '{}'::uuid[]
        ELSE current_setting('app.tenant_ids', true)::uuid[]
    END
$$;

-- Direct-tenant tables: a `tenant_id` column scopes the row.
--   ts_<table>: FOR ALL (SELECT/INSERT/UPDATE/DELETE) — USING gates reads &
--   update/delete visibility, WITH CHECK gates the written row.
DO $$
DECLARE
    t text;
    direct_tables text[] := ARRAY[
        'tenant_members','growers','fields','grower_contracts',
        'input_disbursements','deliveries','harvest_records',
        'yield_projections','scouting_observations'
    ];
BEGIN
    FOREACH t IN ARRAY direct_tables LOOP
        EXECUTE format('DROP POLICY IF EXISTS ts_%1$s ON public.%1$I', t);
        EXECUTE format($f$
            CREATE POLICY ts_%1$s ON public.%1$I
            FOR ALL
            USING (tenant_id = ANY (public.app_tenant_ids()))
            WITH CHECK (tenant_id = ANY (public.app_tenant_ids()))
        $f$, t);
    END LOOP;
END $$;

-- `tenants` itself is scoped by its own id.
DROP POLICY IF EXISTS ts_tenants ON public.tenants;
CREATE POLICY ts_tenants ON public.tenants
    FOR ALL
    USING (id = ANY (public.app_tenant_ids()))
    WITH CHECK (id = ANY (public.app_tenant_ids()));

-- Field-scoped tables with NO tenant_id column: scope through the parent field.
DROP POLICY IF EXISTS ts_daily_logs ON public.daily_logs;
CREATE POLICY ts_daily_logs ON public.daily_logs
    FOR ALL
    USING (field_id IN (SELECT id FROM public.fields WHERE tenant_id = ANY (public.app_tenant_ids())))
    WITH CHECK (field_id IN (SELECT id FROM public.fields WHERE tenant_id = ANY (public.app_tenant_ids())));

DROP POLICY IF EXISTS ts_field_inputs ON public.field_inputs;
CREATE POLICY ts_field_inputs ON public.field_inputs
    FOR ALL
    USING (field_id IN (SELECT id FROM public.fields WHERE tenant_id = ANY (public.app_tenant_ids())))
    WITH CHECK (field_id IN (SELECT id FROM public.fields WHERE tenant_id = ANY (public.app_tenant_ids())));

-- NOTE (deferred to the FORCE step, see runbook):
--   * farm_tasks / chat_logs  — personal (no tenant_id); need an `app.user_id`
--     GUC policy before FORCE.
--   * model_calibration        — global model data (no tenant dimension); needs
--     a decision (owner-only path) before FORCE.
--   * fields/daily_logs/field_inputs already carry `auth.uid() = user_id`
--     PostgREST policies; the ts_* policies are additive (permissive OR), so a
--     direct-client user still sees exactly their own rows.

-- ─────────────────────────────────────────────────────────────────────────────
-- ROLLBACK (manual):
--   DROP POLICY IF EXISTS ts_tenants ON public.tenants;
--   DROP POLICY IF EXISTS ts_tenant_members ON public.tenant_members;
--   DROP POLICY IF EXISTS ts_growers ON public.growers;
--   DROP POLICY IF EXISTS ts_fields ON public.fields;
--   DROP POLICY IF EXISTS ts_grower_contracts ON public.grower_contracts;
--   DROP POLICY IF EXISTS ts_input_disbursements ON public.input_disbursements;
--   DROP POLICY IF EXISTS ts_deliveries ON public.deliveries;
--   DROP POLICY IF EXISTS ts_harvest_records ON public.harvest_records;
--   DROP POLICY IF EXISTS ts_yield_projections ON public.yield_projections;
--   DROP POLICY IF EXISTS ts_scouting_observations ON public.scouting_observations;
--   DROP POLICY IF EXISTS ts_daily_logs ON public.daily_logs;
--   DROP POLICY IF EXISTS ts_field_inputs ON public.field_inputs;
--   DROP FUNCTION IF EXISTS public.app_tenant_ids();
-- ─────────────────────────────────────────────────────────────────────────────
