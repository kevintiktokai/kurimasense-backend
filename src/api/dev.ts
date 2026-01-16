/**
 * Dev-Only Demo Routes
 * 
 * STRICT RULES:
 * - DEV-ONLY: Disabled in production (NODE_ENV === 'production')
 * - Demo logic reuses real insight generation paths
 * - Does NOT refactor existing logic
 * - Does NOT change production behavior
 * - Does NOT touch frontend code
 * - Minimal, explicit, and reversible
 */

import { Router, Request, Response } from 'express'
import { randomUUID } from 'crypto'
import db from '../db/client.js'
import {
  insertField,
  insertSeason,
  getInsightByFieldAndSeason,
  insertInsight
} from '../db/client.js'
import { generatePerformanceDeviationInsight } from '../insights/generate.js'

const router = Router()

/**
 * Check if running in production
 */
function isProduction(): boolean {
  return process.env.NODE_ENV === 'production'
}

/**
 * POST /api/dev/seed-demo
 * 
 * ⚠️ DEV ONLY - SAFE TO DELETE - NOT PART OF V1 CORE LOGIC
 * 
 * This route is for development and demo purposes only.
 * It can be safely deleted without affecting V1 functionality.
 * It is NOT part of the V1 core logic or production requirements.
 * 
 * Dev-only route to seed demo data for testing/demo purposes.
 * 
 * Creates or reuses:
 * - Demo Field with id "demo-field-1"
 * - Demo Season with id "demo-season-2024"
 * - 4-6 synthetic NDVI observations showing gradual stress
 * 
 * Returns: { success, fieldId, seasonId, insightId }
 * 
 * Production: Returns 403 Forbidden
 */
router.post('/seed-demo', (req: Request, res: Response) => {
  // Reject if production
  if (isProduction()) {
    return res.status(403).json({
      success: false,
      error: 'This route is disabled in production'
    })
  }

  try {
    const fieldId = 'demo-field-1'
    const seasonId = 'demo-season-2024'
    const fieldName = 'Demo Field'
    const seasonName = '2024/25 Demo Season'

    // Create or reuse demo field (ON CONFLICT DO NOTHING)
    try {
      insertField(fieldId, fieldName, null)
    } catch (error: any) {
      // Field already exists - that's fine, reuse it
      if (error?.code !== 'SQLITE_CONSTRAINT') {
        throw error
      }
    }

    // Create or reuse demo season (30 days duration)
    const now = new Date()
    const seasonStart = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString()
    const seasonEnd = now.toISOString()
    
    try {
      insertSeason(seasonId, seasonName, seasonStart, seasonEnd)
    } catch (error: any) {
      // Season already exists - that's fine, reuse it
      if (error?.code !== 'SQLITE_CONSTRAINT') {
        throw error
      }
    }

    // Insert 4-6 synthetic NDVI observations showing gradual stress
    // NDVI values decrease over time to show stress progression
    const ndviObservations = [
      { mean: 0.70, min: 0.65, max: 0.75, stdDev: 0.03 }, // Day 0: Healthy
      { mean: 0.65, min: 0.60, max: 0.70, stdDev: 0.04 }, // Day 7: Slight decline
      { mean: 0.58, min: 0.53, max: 0.63, stdDev: 0.05 }, // Day 14: Moderate stress
      { mean: 0.50, min: 0.45, max: 0.55, stdDev: 0.05 }, // Day 21: Increased stress
      { mean: 0.42, min: 0.37, max: 0.47, stdDev: 0.05 }, // Day 25: High stress
      { mean: 0.35, min: 0.30, max: 0.40, stdDev: 0.05 }, // Day 28: Severe stress
    ]

    // Check for existing signals to avoid duplicates (ON CONFLICT DO NOTHING behavior)
    const checkSignalStmt = db.prepare(`
      SELECT id FROM vegetation_signals 
      WHERE field_id = ? AND season_id = ? AND timestamp = ?
    `)
    
    // Insert vegetation signals (skip if already exists)
    const insertVegStmt = db.prepare(`
      INSERT INTO vegetation_signals (
        field_id, season_id, timestamp, ndvi_mean, ndvi_min, ndvi_max, ndvi_std_dev, data_quality
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `)

    for (let i = 0; i < ndviObservations.length; i++) {
      const daysOffset = i * 5 // Spread observations over ~28 days
      const timestamp = new Date(
        new Date(seasonStart).getTime() + daysOffset * 24 * 60 * 60 * 1000
      ).toISOString()

      // Check if signal already exists (ON CONFLICT DO NOTHING behavior)
      const existing = checkSignalStmt.get(fieldId, seasonId, timestamp)
      if (existing) {
        continue // Skip if already exists
      }

      const ndvi = ndviObservations[i]
      
      // Insert new signal
      insertVegStmt.run(
        fieldId,
        seasonId,
        timestamp,
        ndvi.mean,
        ndvi.min,
        ndvi.max,
        ndvi.stdDev,
        'high' // data_quality must be "high"
      )
    }

    // Generate and store insight using existing logic (deterministic and idempotent)
    // This reuses the same path as GET /api/insights
    let insightId: string | null = null
    
    // Check if insight already exists
    const existingInsight = getInsightByFieldAndSeason(fieldId, seasonId)
    
    if (existingInsight) {
      // Insight already exists - reuse it (idempotent behavior)
      insightId = existingInsight.id
    } else {
      // Generate insight deterministically using existing function
      // This function loads observations, computes baseline, calculates delta, and assigns severity
      const insight = generatePerformanceDeviationInsight(fieldId, seasonId)

      // Generate stable ID and timestamp
      const id = randomUUID()
      const generatedAt = new Date().toISOString()

      // Store insight using existing persistence logic
      // insertInsight handles UNIQUE constraint and returns existing if race condition occurs
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
      
      insightId = storedInsight.id
    }

    // Return JSON response
    res.status(201).json({
      success: true,
      fieldId,
      seasonId,
      insightId
    })
  } catch (error: any) {
    console.error('Error seeding demo data:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to seed demo data',
      details: error instanceof Error ? error.message : 'Unknown error'
    })
  }
})

export default router
