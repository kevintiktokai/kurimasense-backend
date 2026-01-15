/**
 * Insights API
 * V1: Primary Insight Entrypoint (AUTHORITATIVE)
 * 
 * GET /api/insights?fieldId=X&seasonId=Y
 * 
 * This is the ONLY V1 insight entrypoint. It is completely independent of:
 * - analysis_runs (legacy, optional)
 * - inference endpoints (legacy, optional)
 * - inference_response (legacy, optional)
 * 
 * Behavior:
 * 1. Validate fieldId and seasonId
 * 2. Query insights table for (field_id, season_id)
 * 3. If found → return immediately
 * 4. If NOT found:
 *    - Generate insight deterministically
 *    - Store it
 *    - Return it
 * 
 * STRICT RULES:
 * - Insights are the authoritative V1 output
 * - NO dependency on analysis_runs or inference endpoints
 * - Deterministic, explainable logic
 * - No AI/LLM decision-making
 * - Idempotent: same request → same stored Insight
 * - One insight per field per season (enforced by UNIQUE constraint)
 * - seasonId is MANDATORY: NO automatic inference, NO defaults, explicit context required
 */

import { Router, Request, Response } from 'express'
import { randomUUID } from 'crypto'
import { getInsightByFieldAndSeason, insertInsight, getFieldById, getSeasonById } from '../db/client.js'
import { generatePerformanceDeviationInsight } from '../insights/generate.js'

const router = Router()

/**
 * GET /api/insights
 * 
 * Query Parameters:
 * - fieldId: string (required)
 * - seasonId: string (required)
 * 
 * V1 REQUIREMENT: seasonId is MANDATORY
 * - NO automatic season inference
 * - NO default season selection
 * - NO season derivation from dates
 * - Explicit season context is REQUIRED
 * 
 * Returns: Insight object as JSON
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const { fieldId, seasonId } = req.query

    // Step 1: Validate required parameters
    // V1 REQUIREMENT: fieldId is mandatory
    if (!fieldId || typeof fieldId !== 'string' || fieldId.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'fieldId is required and must be a non-empty string'
      })
    }

    // V1 REQUIREMENT: seasonId is mandatory - NO inference allowed
    // This ensures explicit season context for all insight queries
    if (!seasonId || typeof seasonId !== 'string' || seasonId.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'seasonId is required and must be a non-empty string. V1 requires explicit season context - no automatic season inference is allowed.'
      })
    }

    // Validate field exists
    const field = getFieldById(fieldId)
    if (!field) {
      return res.status(404).json({
        success: false,
        error: `Field with id '${fieldId}' does not exist`
      })
    }

    // Validate season exists
    const season = getSeasonById(seasonId)
    if (!season) {
      return res.status(404).json({
        success: false,
        error: `Season with id '${seasonId}' does not exist`
      })
    }

    // Step 2: Query insights table for (field_id, season_id)
    const existingInsight = getInsightByFieldAndSeason(fieldId, seasonId)

    // Step 3: If found → return immediately
    if (existingInsight) {
      return res.json({
        success: true,
        data: existingInsight
      })
    }

    // Step 4: If NOT found → generate, store, return
    try {
      // Generate insight deterministically
      // This function loads observations, computes baseline, calculates delta, and assigns severity
      const insight = generatePerformanceDeviationInsight(fieldId, seasonId)

      // Generate stable ID and timestamp
      const id = randomUUID()
      const generatedAt = new Date().toISOString()

      // Store insight (or return existing if UNIQUE constraint fails)
      // This guarantees idempotency and race safety
      const storedInsight = insertInsight(
        id,
        fieldId,
        seasonId,
        insight.type,
        insight.severity,
        insight.confidence,
        insight.summary,
        insight.evidence,
        insight.suggestedAction,
        generatedAt
      )

      // Return the stored insight (either newly inserted or existing)
      return res.json({
        success: true,
        data: storedInsight
      })
    } catch (error: any) {
      console.error('Error generating insight:', error)
      return res.status(500).json({
        success: false,
        error: 'Failed to generate insight',
        details: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  } catch (error) {
    console.error('Unexpected error in insights endpoint:', error)
    res.status(500).json({
      success: false,
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    })
  }
})

export default router
