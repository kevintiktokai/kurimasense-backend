/**
 * Context API
 * Phase 5 — Context Expansion
 * 
 * Provides read-only context data for analysis runs.
 * Context is descriptive only and does not influence inference.
 * 
 * STRICT RULES:
 * - Context is NOT persisted
 * - Context is NOT stored as historical truth
 * - Context does NOT modify inference
 * - Context is loaded only via explicit user action
 */

import express, { Request, Response } from 'express'
import { assembleInferenceInput } from '../inference/input.js'

const router = express.Router()

/**
 * GET /api/context/:fieldId
 * Get context data for a field and time window
 * 
 * Query Parameters:
 * - windowStart: ISO 8601 timestamp (required)
 * - windowEnd: ISO 8601 timestamp (required)
 * 
 * Returns: Context data with source, time window, freshness, and descriptive data
 * 
 * Contract: Context is read-only and descriptive only. Not persisted.
 */
router.get('/:fieldId', (req: Request, res: Response) => {
  try {
    const fieldIdParam = (req.params as any).fieldId as string | string[] | undefined
    const fieldId = Array.isArray(fieldIdParam) ? fieldIdParam[0] : fieldIdParam
    const { windowStart, windowEnd } = req.query

    if (!fieldId || typeof fieldId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'fieldId is required'
      })
    }

    if (!windowStart || typeof windowStart !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'windowStart is required'
      })
    }

    if (!windowEnd || typeof windowEnd !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'windowEnd is required'
      })
    }

    // Phase E: Context is descriptive only, factual and raw
    // Fetch actual signal data from database (read-only, not persisted as context)
    const windowStartString = windowStart as string
    const windowEndString = windowEnd as string

    const input = assembleInferenceInput(fieldId, windowStartString, windowEndString)
    
    // Phase E: Build factual, non-interpretive context data
    const context = {
      source: 'Database signals (vegetation_signals, weather_signals)',
      timeWindow: {
        start: windowStartString,
        end: windowEndString,
      },
      fetchedAt: new Date().toISOString(),
      data: {
        'Vegetation signals': `${input.vegetationSignals.length} observations`,
        'Weather signals': `${input.weatherSignals.length} observations`,
        'Signal completeness': `${input.signalCompleteness}%`,
        'Vegetation timestamps': input.vegetationSignals.length > 0
          ? input.vegetationSignals.map((s: any) => s.timestamp).join(', ')
          : 'None',
        'Weather timestamps': input.weatherSignals.length > 0
          ? input.weatherSignals.map((s: any) => s.timestamp).join(', ')
          : 'None',
      },
    }

    res.json({
      success: true,
      data: context,
    })
  } catch (error) {
    console.error('Error fetching context:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to fetch context data',
    })
  }
})

export default router

