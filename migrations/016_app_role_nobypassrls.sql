-- 016_app_role_nobypassrls.sql
-- ============================================================================
-- Dedicated NOBYPASSRLS application role — the actual unblock for RLS Step D.
--
-- Finding 2026-07-03 (docs/rls_force_runbook.md): the backend connects as
-- `postgres`, which has BYPASSRLS, so no amount of FORCE gives isolation
-- against the backend. This migration creates `kurimasense_app`, a login role
-- that is subject to row security. Because the role does NOT own the tables,
-- plain ENABLE RLS already binds it — isolation becomes real the moment
-- Render's DATABASE_URL is rotated to this role, even before 017's FORCE
-- (FORCE then only guards hypothetical future owner-role connections).
--
-- Policy model for the app role:
--   * ISOLATION SET (tenant/user-scoped farm data): NO app-role policy. The
--     existing ts_* / us_* policies apply — the role sees rows only when the
--     backend arms the transaction-local GUCs (tenancy.arm_rls_gucs /
--     tenant_scoped_connection). This is the provable-isolation surface.
--   * BOOTSTRAP + GLOBAL tables: explicit USING(true) policies for this role
--     only. tenants/tenant_members/profiles must be readable BEFORE the GUC
--     can be derived (chicken-and-egg documented in the runbook); knowledge /
--     RAG / notification-service tables are cross-tenant by design.
--
-- Apply as postgres. BEFORE applying, replace the password (or run
--   ALTER ROLE kurimasense_app PASSWORD '...'
-- immediately after) and store it in the secret manager. Then follow the
-- cut-over sequence in docs/rls_force_runbook.md (Step D, revised).
--
-- Rollback: rotate DATABASE_URL back to the postgres URL. The role and
-- policies are inert while nothing connects as the role.
-- ============================================================================

-- ── 1. Role ────────────────────────────────────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kurimasense_app') THEN
        CREATE ROLE kurimasense_app
            LOGIN
            NOBYPASSRLS
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            PASSWORD 'CHANGE_ME_BEFORE_APPLY';
    END IF;
END $$;

-- ── 2. Grants (DML only — deliberately NO DDL, and it owns nothing) ───────
GRANT USAGE ON SCHEMA public TO kurimasense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO kurimasense_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO kurimasense_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO kurimasense_app;

-- Objects created later by postgres (future migrations) stay accessible.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO kurimasense_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO kurimasense_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO kurimasense_app;

-- ── 3. Bootstrap policies (identity/membership; NEVER part of isolation) ──
-- The backend must read tenant_members to DERIVE app.tenant_ids, and
-- provisions tenants/profiles rows pre-GUC (create_field, onboarding).
DO $$
DECLARE
    t text;
    bootstrap_tables text[] := ARRAY['tenants', 'tenant_members', 'profiles'];
BEGIN
    FOREACH t IN ARRAY bootstrap_tables LOOP
        IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname = 'public' AND c.relname = t) THEN
            EXECUTE format('DROP POLICY IF EXISTS app_bootstrap_%1$s ON public.%1$I', t);
            EXECUTE format(
                'CREATE POLICY app_bootstrap_%1$s ON public.%1$I FOR ALL TO kurimasense_app USING (true) WITH CHECK (true)', t);
        END IF;
    END LOOP;
END $$;

-- ── 4. Global/service tables (cross-tenant BY DESIGN — documented) ────────
--   user_events      — behavioral event log, service-level writes
--   alerts, daily_log — legacy global tables (backend-only)
--   knowledge_base, documents — RAG corpus, global by nature
--   notifications*   — the notification service fans out across all users
--   crop_varieties   — global catalogue (no RLS today; policy is inert-safe)
DO $$
DECLARE
    t text;
    global_tables text[] := ARRAY[
        'user_events', 'alerts', 'daily_log', 'knowledge_base', 'documents',
        'notifications', 'notification_preferences', 'notification_devices',
        'notification_deliveries', 'crop_varieties'
    ];
BEGIN
    FOREACH t IN ARRAY global_tables LOOP
        IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname = 'public' AND c.relname = t) THEN
            EXECUTE format('DROP POLICY IF EXISTS app_global_%1$s ON public.%1$I', t);
            EXECUTE format(
                'CREATE POLICY app_global_%1$s ON public.%1$I FOR ALL TO kurimasense_app USING (true) WITH CHECK (true)', t);
        END IF;
    END LOOP;
END $$;

-- NOTE (isolation set — intentionally ABSENT above): fields, daily_logs,
-- field_inputs, growers, grower_contracts, input_disbursements, deliveries,
-- harvest_records, yield_projections, scouting_observations, soil_profiles,
-- team_invites, field_activities, field_assignments (ts_*) and farm_tasks,
-- yield_history, chat_logs, chat_sessions (us_*). The app role reaches these
-- ONLY through armed GUCs. model_calibration is covered by mc_global (011).

-- ── 5. Verification: RLS-enabled tables the app role cannot reach at all ──
-- Run after applying; every row returned here must be either in the isolation
-- set (expected — GUC-gated) or a table the backend never touches.
-- SELECT c.relname
-- FROM pg_class c
-- JOIN pg_namespace n ON n.oid = c.relnamespace
-- WHERE n.nspname = 'public' AND c.relrowsecurity
--   AND NOT EXISTS (SELECT 1 FROM pg_policies p
--                   WHERE p.schemaname = 'public' AND p.tablename = c.relname
--                     AND (p.roles = '{public}' OR 'kurimasense_app' = ANY (p.roles)))
-- ORDER BY 1;
