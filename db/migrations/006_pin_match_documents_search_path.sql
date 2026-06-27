-- Migration 006: Pin search_path on the RAG vector-search function.
-- A function with a mutable search_path can be influenced via search_path
-- manipulation; pinning it is the Supabase-recommended hardening
-- (lint 0011_function_search_path_mutable).
--
-- Loops over all match_documents overloads so it works regardless of signature.
-- Idempotent. The documents table and pgvector operators live in public, so
-- `public, pg_temp` resolves everything the function needs.

DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT p.oid::regprocedure AS sig
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'match_documents'
  LOOP
    EXECUTE format('ALTER FUNCTION %s SET search_path = public, pg_temp', r.sig);
  END LOOP;
END $$;
