-- Migration 014 — Centralized notification service
--
-- Canonical DDL for the notification subsystem (services/notifications). The
-- backend also self-heals these tables on boot (repository.ensure_schema), so
-- this migration is idempotent and safe to apply before or after deploy.
--
--   notifications             the per-user inbox (in-app channel IS this table)
--   notification_deliveries   outbound channel queue (email/push/… per row)
--   notification_preferences  one JSONB preference document per user
--   notification_devices      push tokens registered by the mobile app
--
-- RLS: notifications/preferences/devices are PERSONAL tables (user-scoped,
-- like farm_tasks in migration 010); policies key on public.app_user_id().
-- notification_deliveries is backend-internal (never exposed via PostgREST or
-- user-facing SQL) and carries no direct user_id, so it gets a deny-all policy
-- under FORCE — only the table owner (backend role) touches it.

CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    field_id UUID,
    action_url TEXT,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    dedupe_key TEXT,
    source TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_user_dedupe
    ON public.notifications(user_id, dedupe_key) WHERE dedupe_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_user_created
    ON public.notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
    ON public.notifications(user_id) WHERE read_at IS NULL;

CREATE TABLE IF NOT EXISTS public.notification_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES public.notifications(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    deliver_after TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_deliveries_due
    ON public.notification_deliveries(deliver_after) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS public.notification_preferences (
    user_id TEXT PRIMARY KEY,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.notification_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'android',
    token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_devices_user
    ON public.notification_devices(user_id);

-- ── RLS (FORCE-prep, mirrors migration 010 conventions) ─────────────────────

ALTER TABLE public.notifications            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_devices     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_deliveries  ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['notifications', 'notification_preferences', 'notification_devices'] LOOP
        EXECUTE format('DROP POLICY IF EXISTS us_%1$s ON public.%1$I', t);
        EXECUTE format($p$
            CREATE POLICY us_%1$s ON public.%1$I
            FOR ALL
            USING (user_id::text = public.app_user_id())
            WITH CHECK (user_id::text = public.app_user_id())
        $p$, t);
    END LOOP;
END $$;

-- Backend-internal queue: no user-facing policy. (Owner bypasses non-forced
-- RLS; under FORCE the dispatcher runs as owner via BYPASSRLS — see
-- docs/rls_force_runbook.md.)
DROP POLICY IF EXISTS deny_all_notification_deliveries ON public.notification_deliveries;
CREATE POLICY deny_all_notification_deliveries ON public.notification_deliveries
    FOR ALL USING (false) WITH CHECK (false);
