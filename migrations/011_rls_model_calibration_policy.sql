-- Migration 011 — model_calibration RLS policy (Sprint 4, Slice 4 — FORCE prep)
--
-- GATED: part of the FORCE cut-over (see docs/rls_force_runbook.md). Safe and
-- behavior-preserving on its own (owner bypasses non-forced RLS); only
-- meaningful once FORCE ROW LEVEL SECURITY is enabled on the table.
--
-- DECISION (runbook Step B, resolved): model_calibration is GLOBAL model-quality
-- data — per-segment aggregate error statistics (crop_type / natural_region /
-- variety / progress-bucket → n_observations, mae_pct, rmse, bias_pct). It has
-- no tenant dimension and holds no tenant PII (no ids, names, volumes, or
-- prices — only model-error aggregates), so the deliberate USING (true) policy
-- is appropriate. Readers: GET /tenants/{id}/calibration (further filters to
-- the tenant's crops in SQL). Writer: POST /admin/calibration/recompute
-- (admin-token-gated).
--
-- With this policy, FORCE on model_calibration is safe (owner is never denied)
-- while still satisfying the "every backend-written table has an explicit
-- policy" invariant — the policy documents the intentional global posture
-- rather than leaving the table as an unexplained gap.

ALTER TABLE public.model_calibration ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mc_global ON public.model_calibration;
CREATE POLICY mc_global ON public.model_calibration
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ROLLBACK (manual):
--   DROP POLICY IF EXISTS mc_global ON public.model_calibration;
