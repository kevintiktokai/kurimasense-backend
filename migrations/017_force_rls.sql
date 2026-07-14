-- 017_force_rls.sql
-- ============================================================================
-- FORCE ROW LEVEL SECURITY on the isolation set — belt-and-braces AFTER the
-- backend runs as kurimasense_app (migration 016 + DATABASE_URL rotation).
--
-- ⚠️ Sequencing matters (docs/rls_force_runbook.md, Step D revised):
--   1. 015 applied and DB_SELF_HEAL_SCHEMA=false (no runtime DDL).
--   2. 016 applied, password rotated, DATABASE_URL switched to kurimasense_app,
--      soak green. At this point isolation is ALREADY LIVE for the app role
--      (non-owner ⇒ plain ENABLE RLS binds it).
--   3. THEN apply this. FORCE closes the last gap: the table OWNER (postgres —
--      migrations, ops consoles, any legacy connection string still in use)
--      also becomes subject to the policies.
--
-- Deliberately NOT forced: tenants, tenant_members, profiles (bootstrap
-- exemption — forcing them locks out GUC derivation and ops), and the global
-- tables (they carry USING(true) policies anyway, so FORCE would be noise).
--
-- Note for ops after FORCE: psql sessions as postgres will see zero rows in
-- these tables unless they arm the GUCs, e.g.
--   SELECT set_config('app.tenant_ids', '{<uuid>}', false);
-- That friction is the feature.
--
-- Rollback (per table, instant): ALTER TABLE public.<t> NO FORCE ROW LEVEL SECURITY;
-- ============================================================================

DO $$
DECLARE
    t text;
    isolation_tables text[] := ARRAY[
        -- tenant-scoped (ts_* policies, migration 008/012/013)
        'fields', 'daily_logs', 'field_inputs', 'growers', 'grower_contracts',
        'input_disbursements', 'deliveries', 'harvest_records',
        'yield_projections', 'scouting_observations', 'soil_profiles',
        'team_invites', 'field_activities', 'field_assignments',
        -- user-scoped personal data (us_* policies, migration 010)
        'farm_tasks', 'yield_history', 'chat_logs', 'chat_sessions'
    ];
BEGIN
    FOREACH t IN ARRAY isolation_tables LOOP
        IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname = 'public' AND c.relname = t) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
            EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', t);
        END IF;
    END LOOP;
END $$;

-- Verify:
-- SELECT relname, relrowsecurity, relforcerowsecurity
-- FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
-- WHERE n.nspname = 'public' AND relforcerowsecurity
-- ORDER BY 1;
