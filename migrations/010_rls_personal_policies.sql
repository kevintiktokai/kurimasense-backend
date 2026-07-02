-- Migration 010 — Personal-table RLS policies (Sprint 4, Slice 4 — FORCE prep)
--
-- GATED: part of the FORCE cut-over (see docs/rls_force_runbook.md). Applying it
-- is SAFE and behavior-preserving on its own (owner bypasses non-forced RLS), but
-- it is only meaningful once FORCE ROW LEVEL SECURITY is enabled. Apply during
-- the FORCE step, not before.
--
-- Covers the tables that are PERSONAL (user-scoped), not tenant-scoped, and thus
-- were deliberately excluded from migration 008: farm_tasks, chat_logs,
-- yield_history. Under FORCE, the backend owner would otherwise be denied on
-- these, so they need a policy keyed on the per-request app.user_id GUC
-- (set transaction-locally by tenancy.tenant_scoped_connection alongside
-- app.tenant_ids).
--
-- Type-robust: user_id is TEXT on farm_tasks/chat_logs and uuid on yield_history,
-- so the predicate casts the column to text and compares to the GUC string
-- (tenancy sets app.user_id = str(user_id), the canonical uuid/text form).

-- GUC accessor: the caller's user id as text, NULL when unset/empty (so an
-- unset connection — anon/authenticated PostgREST — matches no rows).
CREATE OR REPLACE FUNCTION public.app_user_id()
RETURNS text
LANGUAGE sql
STABLE
SET search_path = ''
AS $$
    SELECT NULLIF(current_setting('app.user_id', true), '')
$$;

-- RLS is already enabled on farm_tasks (migration 004/005). Enable defensively on
-- the others in case they were missed (idempotent, no-op if already enabled).
ALTER TABLE public.farm_tasks    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.yield_history ENABLE ROW LEVEL SECURITY;
-- chat_logs may not exist in every environment; guard it.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema='public' AND table_name='chat_logs') THEN
        EXECUTE 'ALTER TABLE public.chat_logs ENABLE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS us_chat_logs ON public.chat_logs';
        EXECUTE $p$
            CREATE POLICY us_chat_logs ON public.chat_logs
            FOR ALL
            USING (user_id::text = public.app_user_id())
            WITH CHECK (user_id::text = public.app_user_id())
        $p$;
    END IF;
END $$;

DROP POLICY IF EXISTS us_farm_tasks ON public.farm_tasks;
CREATE POLICY us_farm_tasks ON public.farm_tasks
    FOR ALL
    USING (user_id::text = public.app_user_id())
    WITH CHECK (user_id::text = public.app_user_id());

DROP POLICY IF EXISTS us_yield_history ON public.yield_history;
CREATE POLICY us_yield_history ON public.yield_history
    FOR ALL
    USING (user_id::text = public.app_user_id())
    WITH CHECK (user_id::text = public.app_user_id());

-- model_calibration: global model data, no per-row owner. Decide at FORCE time —
-- either keep a dedicated owner path exempt from FORCE, or add USING (true) after
-- confirming it holds no tenant PII. NOT handled here.

-- ROLLBACK (manual):
--   DROP POLICY IF EXISTS us_farm_tasks ON public.farm_tasks;
--   DROP POLICY IF EXISTS us_yield_history ON public.yield_history;
--   DROP POLICY IF EXISTS us_chat_logs ON public.chat_logs;
--   DROP FUNCTION IF EXISTS public.app_user_id();
