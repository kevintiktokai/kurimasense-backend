/**
 * Provenance API
 * Phase 6.1 — Provenance & Audit Expansion
 * 
 * Provides view-time provenance data for analysis runs.
 * Provenance is deterministic and reconstructable, but NOT persisted.
 * 
 * STRICT RULES:
 * - Provenance is NOT persisted
 * - Provenance does NOT modify InferenceResponse
 * - Provenance is view-time only (reconstructed deterministically)
 */

import express, { Request, Response } from 'express'
import {
  assembleInferenceInput,
  inferCropHealthStatus,
  emitInferenceCategory,
  type Inference,
} from '../inference/index.js'
import { generateProvenance } from '../inference/provenance.js'

const router = express.Router()

/**
 * GET /api/provenance/:analysisRunId
 * Get provenance data for an analysis run
 * 
 * Contract: Returns view-time provenance reconstructed deterministically.
 * Does NOT modify stored AnalysisRun.
 */
router.get('/:analysisRunId', (req: Request, res: Response) => {
  try {
    const { analysisRunId } = req.params

    // Phase 6.1: For now, return error - provenance must be generated from AnalysisRun
    // In full implementation, would:
    // 1. Fetch AnalysisRun by ID
    // 2. Reconstruct InferenceInput from AnalysisRun windowStart/windowEnd
    // 3. Re-run inference rules deterministically (same inputs = same outputs)
    // 4. Generate provenance from reconstructed inference state
    // 5. Return provenance (NOT stored)
    
    return res.status(501).json({
      success: false,
      error: 'Provenance endpoint not yet fully implemented. Provenance must be generated from AnalysisRun data.',
    })
  } catch (error) {
    console.error('Error generating provenance:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to generate provenance',
    })
  }
})

/**
 * POST /api/provenance/generate
 * Generate provenance for a field and time window
 * 
 * Body:
 * - fieldId: string (required)
 * - windowStart: ISO 8601 timestamp (required)
 * - windowEnd: ISO 8601 timestamp (required)
 * 
 * Contract: Generates provenance deterministically. NOT persisted.
 */
router.post('/generate', (req: Request, res: Response) => {
  try {
    const { fieldId, windowStart, windowEnd } = req.body

    if (!fieldId || typeof fieldId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'fieldId is required',
      })
    }

    if (!windowStart || typeof windowStart !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'windowStart is required',
      })
    }

    if (!windowEnd || typeof windowEnd !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'windowEnd is required',
      })
    }

    // Reconstruct inference state deterministically
    const input = assembleInferenceInput(fieldId, windowStart, windowEnd)
    const status = inferCropHealthStatus(input)
    const category = emitInferenceCategory(status, input)
    
    // Calculate confidence (same logic as in assemble.ts)
    let confidence = 0
    confidence += Math.min(40, input.signalCompleteness * 0.4)
    if (input.vegetationSignals.length > 0) {
      const highQualityCount = input.vegetationSignals.filter(s => s.dataQuality === 'high').length
      const qualityRatio = highQualityCount / input.vegetationSignals.length
      confidence += qualityRatio * 30
    }
    if (input.vegetationSignals.length >= 3) {
      confidence += 30
    } else if (input.vegetationSignals.length === 2) {
      confidence += 20
    } else if (input.vegetationSignals.length === 1) {
      confidence += 10
    }
    confidence = Math.round(Math.min(100, confidence))

    // Generate provenance (view-time only, NOT persisted)
    const provenance = generateProvenance(status, category, input, confidence)

    res.json({
      success: true,
      data: provenance,
    })
  } catch (error) {
    console.error('Error generating provenance:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to generate provenance',
    })
  }
})

export default router

