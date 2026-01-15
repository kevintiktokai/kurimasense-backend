/**
 * Inference API
 * Endpoint for retrieving field inference results
 */

import { Router, Request, Response } from 'express'
import {
  assembleInferenceInput,
  inferCropHealthStatus,
  emitInferenceCategory,
  assembleInference,
  type Inference,
} from '../inference/index.js'
import type { InferenceResponse } from '../types/api.js'
import { inferenceResponseSchema } from '../types/contracts.js'

const router = Router()

/**
 * Transform internal Inference to canonical InferenceResponse
 */
function toInferenceResponse(inference: Inference): InferenceResponse {
  // Convert numeric confidence to categorical
  let confidence: 'high' | 'medium' | 'low'
  if (inference.confidence >= 70) {
    confidence = 'high'
  } else if (inference.confidence >= 40) {
    confidence = 'medium'
  } else {
    confidence = 'low'
  }

  // Extract status string (default to 'watch' if null)
  const status = inference.status?.status || 'watch'

  // Trend is stable for now (no trend inference yet)
  const trend = 'stable' as const

  return {
    fieldId: inference.fieldId,
    generatedAt: inference.timestamp,
    status,
    trend,
    confidence,
    categories: [inference.category],
    explanation: inference.explanation,
  }
}

/**
 * GET /api/inference
 * 
 * Query Parameters:
 * - fieldId: string (required)
 * - windowStart: ISO 8601 timestamp (required)
 * - windowEnd: ISO 8601 timestamp (required)
 * 
 * Returns: Inference object as JSON
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const { fieldId, windowStart, windowEnd } = req.query

    // Validate required parameters
    if (!fieldId || typeof fieldId !== 'string') {
      return res.status(400).json({ error: 'fieldId is required' })
    }
    if (!windowStart || typeof windowStart !== 'string') {
      return res.status(400).json({ error: 'windowStart is required' })
    }
    if (!windowEnd || typeof windowEnd !== 'string') {
      return res.status(400).json({ error: 'windowEnd is required' })
    }

    // Assemble inference input from database
    const input = assembleInferenceInput(fieldId, windowStart, windowEnd)

    // Derive status from vegetation signals
    const status = inferCropHealthStatus(input)

    // Emit category based on status
    const category = emitInferenceCategory(status, input)

    // Assemble final inference object
    const inference = assembleInference(status, category, input)

    // Transform to canonical API response
    const response = toInferenceResponse(inference)

    // Validate response against schema
    const validationResult = inferenceResponseSchema.safeParse(response)
    if (!validationResult.success) {
      console.error('Response validation failed:', validationResult.error)
      throw new Error('Invalid inference response structure')
    }

    // Return as JSON
    res.json(validationResult.data)
  } catch (error) {
    console.error('Inference error:', error)
    res.status(500).json({ error: 'Failed to generate inference' })
  }
})

export default router
