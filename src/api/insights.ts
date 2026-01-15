/**
 * Insights API
 * V1: Primary Insight Entrypoint
 * 
 * GET /api/insights?fieldId=X&seasonId=Y
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
 * - Deterministic, explainable logic
 * - No AI/LLM decision-making
 * - Idempotent: same request → same stored Insight
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
 * Returns: Insight object as JSON
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const { fieldId, seasonId } = req.query

    // Step 1: Validate required parameters
    if (!fieldId || typeof fieldId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'fieldId is required and must be a string'
      })
    }
    if (!seasonId || typeof seasonId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'seasonId is required and must be a string'
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

      // Store insight
      insertInsight(
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

      // Fetch stored insight to return
      const storedInsight = getInsightByFieldAndSeason(fieldId, seasonId)
      
      if (!storedInsight) {
        throw new Error('Insight was created but cannot be retrieved')
      }

      return res.json({
        success: true,
        data: storedInsight
      })
    } catch (error: any) {
      // Handle UNIQUE constraint violation (race condition)
      if (error?.message?.includes('already exists')) {
        // Another request created it, fetch and return
        const storedInsight = getInsightByFieldAndSeason(fieldId, seasonId)
        if (storedInsight) {
          return res.json({
            success: true,
            data: storedInsight
          })
        }
      }

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
