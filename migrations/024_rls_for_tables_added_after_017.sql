-- 024: close the RLS gap that opens every time a table is added.
--
-- THE STRUCTURAL PROBLEM
-- ---------------------
-- Migration 017 forces RLS on a **hardcoded array** of table names, written
-- when 017 was written. Every tenant-scoped table added since has silently
-- missed it, because nothing fails when a table is left out — it just isn't
-- isolated, and reads exactly like one that is.
--
-- Three tables were added after 017:
--
--   018  field_section_analysis   ENABLE + policy, never FORCEd
--   019  seasons                  ENABLE + policy, never FORCEd
--   022  document_issues          no RLS at all
--
-- The first two are a defence-in-depth gap: the backend runs as
-- kurimasense_app, a non-owner, and plain ENABLE already binds a non-owner
-- (migration 016). FORCE closes the owner path — migrations, ops consoles, and
-- any legacy connection string still pointed at postgres.
--
-- `document_issues` is the real one. It has no policy, so it is isolated
-- against nothing, and two of its own queries carry no tenant predicate:
--
--   get_by_issue_number()  SELECT ... WHERE issue_number = %s
--   mark_forwarded()       UPDATE  ... WHERE issue_number = %s
--
-- Both are correct today only because document_routes calls `_assert_visible`
-- first. That is a single application-layer check standing between one tenant
-- and another tenant's issuance record — the client, the hectares, the coverage
-- window. Everywhere else in this schema the database enforces that too, and a
-- registry of what was issued to whom is not the table to make an exception of.
--
-- Behaviour does not change. `services/documents/registry.py` already arms the
-- GUCs on every connection it opens (`_conn` -> `arm_rls_gucs`), so the policy
-- below is satisfied by the queries as they stand, and a row that RLS hides
-- returns None, which the routes already render as 404 — the same answer
-- `_assert_visible` gives.
--
-- tests/test_rls_coverage.py fails if a future tenant-scoped table repeats this.
--
-- Rollback (per table, instant):
--   ALTER TABLE public.<t> NO FORCE ROW LEVEL SECURITY;

-- --------------------------------------------------------------------------
-- document_issues — enable, policy, force.
-- --------------------------------------------------------------------------
ALTER TABLE public.document_issues ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ts_document_issues ON public.document_issues;
CREATE POLICY ts_document_issues ON public.document_issues
    FOR ALL
    USING (tenant_id = ANY (public.app_tenant_ids()))
    WITH CHECK (tenant_id = ANY (public.app_tenant_ids()));

-- --------------------------------------------------------------------------
-- The FORCE sweep for everything added after 017.
--
-- Guarded on table existence for the same reason 017 is: this runs against
-- installations at different points in the migration sequence.
-- --------------------------------------------------------------------------
DO $$
DECLARE
    t text;
    added_since_017 text[] := ARRAY[
        'field_section_analysis',  -- 018
        'seasons',                 -- 019
        'document_issues'          -- 022
    ];
BEGIN
    FOREACH t IN ARRAY added_since_017 LOOP
        IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname = 'public' AND c.relname = t) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
            EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', t);
        END IF;
    END LOOP;
END $$;

-- Verify — this should list every tenant-scoped table, not a subset:
--
--   SELECT relname, relrowsecurity, relforcerowsecurity
--   FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
--   WHERE n.nspname = 'public' AND relrowsecurity
--   ORDER BY 1;
--
-- And the counterpart check, which is the one that catches the next omission:
--
--   SELECT c.relname
--   FROM pg_class c
--   JOIN pg_namespace n ON n.oid = c.relnamespace
--   JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id'
--   WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relforcerowsecurity
--   ORDER BY 1;
