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
import {
  insertField,
  insertSeason,
  insertVegetationSignal,
  insertWeatherSignal
} from '../db/client.js'

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
 * Dev-only route to seed demo data for testing/demo purposes.
 * 
 * Creates:
 * - One demo field
 * - One demo season
 * - Vegetation signals (3 observations)
 * - Weather signals (30 daily observations)
 * 
 * Returns: Created field and season IDs
 * 
 * Production: Returns 403 Forbidden
 */
router.post('/seed-demo', (req: Request, res: Response) => {
  // DEV-ONLY: Disable in production
  if (isProduction()) {
    return res.status(403).json({
      success: false,
      error: 'This route is disabled in production'
    })
  }

  try {
    // Generate unique IDs for demo data
    const fieldId = `demo-field-${randomUUID()}`
    const seasonId = `demo-season-${randomUUID()}`
    const fieldName = 'Demo Field'
    const seasonName = '2024/25 Demo Season'

    // Create demo field
    insertField(fieldId, fieldName, null)

    // Create demo season (30 days duration)
    const now = new Date()
    const seasonStart = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString()
    const seasonEnd = now.toISOString()
    insertSeason(seasonId, seasonName, seasonStart, seasonEnd)

    // Insert vegetation signals (3 observations over 30 days)
    for (let i = 0; i < 3; i++) {
      const timestamp = new Date(
        new Date(seasonStart).getTime() + i * 10 * 24 * 60 * 60 * 1000
      ).toISOString()

      insertVegetationSignal({
        fieldId,
        seasonId,
        timestamp,
        ndvi: {
          mean: 0.65 - (i * 0.05), // Decreasing NDVI to show variation
          min: 0.5,
          max: 0.8,
          stdDev: 0.05,
        },
        dataQuality: 'high',
      })
    }

    // Insert weather signals (daily observations)
    for (let i = 0; i < 30; i++) {
      const timestamp = new Date(
        new Date(seasonStart).getTime() + i * 24 * 60 * 60 * 1000
      ).toISOString()

      insertWeatherSignal({
        fieldId,
        seasonId,
        timestamp,
        rainfall: 5.0 + (Math.random() * 10), // Random rainfall 5-15mm
        temperature: 25.0 + (Math.random() * 5), // Random temp 25-30°C
        dataQuality: 'high',
      })
    }

    // Return created IDs
    res.status(201).json({
      success: true,
      data: {
        fieldId,
        seasonId,
        message: 'Demo data seeded successfully. Use GET /api/insights?fieldId=' + fieldId + '&seasonId=' + seasonId + ' to generate an insight.'
      }
    })
  } catch (error: any) {
    // Handle UNIQUE constraint violations gracefully
    if (error?.code === 'SQLITE_CONSTRAINT') {
      return res.status(409).json({
        success: false,
        error: 'Demo data already exists or constraint violation',
        details: error.message
      })
    }

    console.error('Error seeding demo data:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to seed demo data',
      details: error instanceof Error ? error.message : 'Unknown error'
    })
  }
})

export default router
