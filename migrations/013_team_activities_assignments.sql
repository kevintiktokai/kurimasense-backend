-- Migration 013 — Institutional operations: team roles, invites, agronomist
-- activities, and field assignments.
--
-- 1. tenant_members grows an extensible role vocabulary (admin / manager /
--    agronomist / field_officer / analyst alongside the legacy owner / officer /
--    viewer) plus a status column so members can be suspended without losing
--    history. Suspended members are excluded from tenant context at auth time.
-- 2. team_invites — code-based invites so an org admin can onboard teammates
--    without email infrastructure: the admin shares the short code out-of-band;
--    the teammate signs up and redeems it (POST /team/invites/accept).
-- 3. field_activities — the permanent professional field timeline: visits,
--    inspections, recommendations, observations, consultations.
-- 4. field_assignments — operational assignment of fields to team members,
--    with full history (one ACTIVE assignment per field via partial unique
--    index; reassignment closes the old row and inserts a new one).
--
-- RLS: all new tables are direct-tenant tables (tenant_id column) and get the
-- same ts_* policy shape as migration 008. Enabled but not FORCEd — the backend
-- owner bypasses until the FORCE cutover, exactly like the sibling tables.

-- ── 1. tenant_members: extended roles + status ───────────────────────────────
ALTER TABLE tenant_members DROP CONSTRAINT IF EXISTS tenant_members_member_role_check;
ALTER TABLE tenant_members ADD CONSTRAINT tenant_members_member_role_check
    CHECK (member_role IN ('owner', 'admin', 'manager', 'agronomist',
                           'field_officer', 'analyst', 'officer', 'viewer'));

ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE tenant_members DROP CONSTRAINT IF EXISTS tenant_members_status_check;
ALTER TABLE tenant_members ADD CONSTRAINT tenant_members_status_check
    CHECK (status IN ('active', 'suspended'));

-- Admin bookkeeping for members added before their profile carries a name.
ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS email TEXT;

-- ── 2. team_invites ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS team_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT,
    member_role TEXT NOT NULL DEFAULT 'field_officer'
        CHECK (member_role IN ('admin', 'manager', 'agronomist',
                               'field_officer', 'analyst', 'viewer')),
    code TEXT NOT NULL UNIQUE,
    invited_by_user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    accepted_by_user_id UUID,
    revoked_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS idx_team_invites_tenant ON team_invites(tenant_id, created_at DESC);

-- ── 3. field_activities ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS field_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    activity_type TEXT NOT NULL
        CHECK (activity_type IN ('visit', 'inspection', 'recommendation',
                                 'fertilizer_advice', 'chemical_advice',
                                 'irrigation_advice', 'pest_observation',
                                 'disease_observation', 'consultation',
                                 'note', 'other')),
    title TEXT NOT NULL,
    notes TEXT,
    recommendation TEXT,
    visit_date DATE DEFAULT CURRENT_DATE,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    photo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_field_activities_field ON field_activities(field_id, visit_date DESC);
CREATE INDEX IF NOT EXISTS idx_field_activities_tenant ON field_activities(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_field_activities_user ON field_activities(user_id, created_at DESC);

-- ── 4. field_assignments ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS field_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    assignee_user_id UUID NOT NULL,
    assigned_by_user_id UUID,
    note TEXT,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    unassigned_at TIMESTAMP WITH TIME ZONE
);
-- One ACTIVE assignment per field; closed rows form the history.
CREATE UNIQUE INDEX IF NOT EXISTS uq_field_assignments_active
    ON field_assignments(field_id) WHERE unassigned_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_field_assignments_assignee
    ON field_assignments(assignee_user_id) WHERE unassigned_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_field_assignments_field
    ON field_assignments(field_id, assigned_at DESC);

-- ── RLS (mirrors migration 008 direct-tenant pattern) ───────────────────────
ALTER TABLE team_invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_assignments ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['team_invites', 'field_activities', 'field_assignments'] LOOP
        EXECUTE format('DROP POLICY IF EXISTS ts_%1$s ON public.%1$I', t);
        EXECUTE format($f$
            CREATE POLICY ts_%1$s ON public.%1$I
            FOR ALL
            USING (tenant_id = ANY (public.app_tenant_ids()))
            WITH CHECK (tenant_id = ANY (public.app_tenant_ids()))
        $f$, t);
    END LOOP;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- ROLLBACK (manual):
--   DROP POLICY IF EXISTS ts_team_invites ON public.team_invites;
--   DROP POLICY IF EXISTS ts_field_activities ON public.field_activities;
--   DROP POLICY IF EXISTS ts_field_assignments ON public.field_assignments;
--   DROP TABLE IF EXISTS field_assignments;
--   DROP TABLE IF EXISTS field_activities;
--   DROP TABLE IF EXISTS team_invites;
--   ALTER TABLE tenant_members DROP COLUMN IF EXISTS status;
--   ALTER TABLE tenant_members DROP COLUMN IF EXISTS display_name;
--   ALTER TABLE tenant_members DROP COLUMN IF EXISTS email;
--   ALTER TABLE tenant_members DROP CONSTRAINT tenant_members_member_role_check;
--   ALTER TABLE tenant_members ADD CONSTRAINT tenant_members_member_role_check
--       CHECK (member_role IN ('owner', 'officer', 'viewer'));
-- ─────────────────────────────────────────────────────────────────────────────
