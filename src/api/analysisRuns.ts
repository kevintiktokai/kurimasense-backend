/**
 * Analysis Run API
 * LEGACY / OPTIONAL — NOT REQUIRED FOR V1
 * 
 * ⚠️ IMPORTANT: This endpoint is NOT required for V1 functionality.
 * - V1 insights are served via GET /api/insights (authoritative)
 * - analysis_runs are legacy/optional and remain for backward compatibility
 * - No V1 route depends on analysis_runs
 * - Frontend should use /api/insights for V1 functionality
 * 
 * STRICT RULES (NON-NEGOTIABLE):
 * - AnalysisRuns are immutable (no update, delete, recomputation)
 * - Created ONLY via explicit user action (no background jobs, auto-analysis)
 * - Data shape is LOCKED and must match canonical contract exactly
 */

import express, { Request, Response } from 'express'
import { randomUUID } from 'crypto'
import {
  insertAnalysisRun,
  getAnalysisRunById,
  getFieldById,
} from '../db/client.js'
import type { CreateAnalysisRunInput } from '../types/analysisRun.js'
import { inferenceResponseSchema } from '../types/contracts.js'
import {
  assembleInferenceInput,
  inferCropHealthStatus,
  emitInferenceCategory,
  assembleInference,
  type Inference,
} from '../inference/index.js'
import type { InferenceResponse } from '../types/api.js'

const router = express.Router()

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
 * POST /api/analysis-runs
 * Create a new AnalysisRun (immutable snapshot)
 * 
 * Body:
 * - fieldId: string (required)
 * - windowStart: ISO 8601 timestamp (required)
 * - windowEnd: ISO 8601 timestamp (required)
 * 
 * Runs inference deterministically, stores as AnalysisRun, returns stored result.
 * 
 * Contract: AnalysisRuns are immutable and created ONLY via explicit user action.
 */
/**
 * Phase D: Validate ISO 8601 date format
 */
function isValidISO8601(dateString: string): boolean {
  const iso8601Regex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$/
  if (!iso8601Regex.test(dateString)) return false
  
  const date = new Date(dateString)
  return date instanceof Date && !isNaN(date.getTime())
}

router.post('/', (req: Request, res: Response) => {
  try {
    const { fieldId, windowStart, windowEnd } = req.body

    // Phase D: Validate required parameters explicitly
    if (!fieldId || typeof fieldId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'fieldId is required and must be a string',
        whatFailed: 'Parameter validation',
        systemAction: 'Request rejected, no analysis run created'
      })
    }
    if (!windowStart || typeof windowStart !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'windowStart is required and must be a string',
        whatFailed: 'Parameter validation',
        systemAction: 'Request rejected, no analysis run created'
      })
    }
    if (!windowEnd || typeof windowEnd !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'windowEnd is required and must be a string',
        whatFailed: 'Parameter validation',
        systemAction: 'Request rejected, no analysis run created'
      })
    }

    // Phase D: Validate ISO 8601 date format
    if (!isValidISO8601(windowStart)) {
      return res.status(400).json({
        success: false,
        error: 'windowStart must be a valid ISO 8601 timestamp (e.g., 2024-01-01T00:00:00Z)',
        whatFailed: 'Date format validation',
        systemAction: 'Request rejected, no analysis run created'
      })
    }
    if (!isValidISO8601(windowEnd)) {
      return res.status(400).json({
        success: false,
        error: 'windowEnd must be a valid ISO 8601 timestamp (e.g., 2024-01-01T00:00:00Z)',
        whatFailed: 'Date format validation',
        systemAction: 'Request rejected, no analysis run created'
      })
    }

    // Phase D: Validate windowStart < windowEnd
    const startDate = new Date(windowStart)
    const endDate = new Date(windowEnd)
    if (startDate >= endDate) {
      return res.status(400).json({
        success: false,
        error: 'windowStart must be before windowEnd',
        whatFailed: 'Time window validation',
        systemAction: 'Request rejected, no analysis run created'
      })
    }

    // Phase D: Validate field exists
    const field = getFieldById(fieldId)
    if (!field) {
      return res.status(404).json({
        success: false,
        error: `Field with id '${fieldId}' does not exist`,
        whatFailed: 'Field existence validation',
        systemAction: 'Request rejected, no analysis run created'
      })
    }

    // Phase D: Run inference computation (deterministic, runs exactly once)
    // Phase D: Handle inference computation errors explicitly
    let input
    try {
      input = assembleInferenceInput(fieldId, windowStart, windowEnd)
    } catch (error) {
      console.error('Error assembling inference input:', error)
      return res.status(500).json({
        success: false,
        error: 'Failed to assemble inference input from signals',
        whatFailed: 'Signal data assembly',
        whyFailed: error instanceof Error ? error.message : 'Unknown error during signal query',
        systemAction: 'Request aborted, no analysis run created'
      })
    }

    // Phase D: Inference computation (may produce empty data - handled gracefully)
    let status, category, inference
    try {
      status = inferCropHealthStatus(input)
      category = emitInferenceCategory(status, input)
      inference = assembleInference(status, category, input)
    } catch (error) {
      console.error('Error during inference computation:', error)
      return res.status(500).json({
        success: false,
        error: 'Failed to compute inference',
        whatFailed: 'Inference computation',
        whyFailed: error instanceof Error ? error.message : 'Unknown error during inference',
        systemAction: 'Request aborted, no analysis run created'
      })
    }

    // Transform to canonical API response
    const inferenceResponse = toInferenceResponse(inference)

    // Phase D: Validate response against schema (fail explicitly if invalid)
    const validationResult = inferenceResponseSchema.safeParse(inferenceResponse)
    if (!validationResult.success) {
      console.error('Inference response validation failed:', validationResult.error)
      return res.status(500).json({
        success: false,
        error: 'Computed inference response does not match expected schema',
        whatFailed: 'Inference response validation',
        whyFailed: 'Schema validation failed',
        details: validationResult.error.errors,
        systemAction: 'Request aborted, no analysis run created'
      })
    }

    // Phase D: Generate stable ID (UUID)
    const id = randomUUID()

    // Phase D: Store as AnalysisRun (immutable snapshot)
    // Phase D: Handle database errors explicitly
    try {
      insertAnalysisRun(id, fieldId, windowStart, windowEnd, validationResult.data)
    } catch (error: any) {
      // Phase D: Handle SQLite constraint violations
      if (error?.code === 'SQLITE_CONSTRAINT' || error?.message?.includes('UNIQUE constraint')) {
        return res.status(409).json({
          success: false,
          error: 'Analysis run with this ID already exists',
          whatFailed: 'Database constraint violation',
          whyFailed: 'Unique constraint on analysis run ID',
          systemAction: 'Request rejected, no analysis run created'
        })
      }
      
      console.error('Error storing analysis run:', error)
      return res.status(500).json({
        success: false,
        error: 'Failed to store analysis run in database',
        whatFailed: 'Database storage',
        whyFailed: error instanceof Error ? error.message : 'Unknown database error',
        systemAction: 'Request aborted, analysis run not persisted'
      })
    }

    // Phase D: Fetch and return stored analysis run (verify persistence)
    const run = getAnalysisRunById(id)
    
    if (!run) {
      return res.status(500).json({
        success: false,
        error: 'Analysis run was created but cannot be retrieved',
        whatFailed: 'Data retrieval after creation',
        whyFailed: 'Analysis run not found after insert',
        systemAction: 'Analysis run may have been created but retrieval failed'
      })
    }

    res.status(201).json({
      success: true,
      data: run
    })
  } catch (error) {
    // Phase D: Explicit error handling - surface errors calmly and specifically
    console.error('Unexpected error creating analysis run:', error)
    
    // Phase D: Provide specific error information
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    
    res.status(500).json({
      success: false,
      error: 'Unexpected error occurred while creating analysis run',
      whatFailed: 'Analysis run creation',
      whyFailed: errorMessage,
      systemAction: 'Request aborted, no analysis run created',
      // Include stack trace only in development (would be filtered in production)
      ...(process.env.NODE_ENV === 'development' && errorStack && { details: errorStack })
    })
  }
})

/**
 * GET /api/analysis-runs/:id
 * Get an AnalysisRun by ID
 * 
 * Contract: Returns stored data only, no recomputation
 */
router.get('/:id', (req: Request, res: Response) => {
  try {
    const { id } = req.params
    
    // Phase D: Validate ID parameter
    if (!id || typeof id !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Analysis run ID is required',
        whatFailed: 'Parameter validation',
        systemAction: 'Request rejected'
      })
    }
    
    // Phase D: Fetch analysis run (may not exist)
    const run = getAnalysisRunById(id)
    
    if (!run) {
      return res.status(404).json({
        success: false,
        error: `Analysis run with id '${id}' does not exist`,
        whatFailed: 'Analysis run retrieval',
        whyFailed: 'No analysis run found with the provided ID',
        systemAction: 'Request rejected, no data returned'
      })
    }
    
    res.json({
      success: true,
      data: run
    })
  } catch (error) {
    // Phase D: Handle unexpected errors during retrieval
    console.error('Error fetching analysis run:', error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch analysis run',
      whatFailed: 'Analysis run retrieval',
      whyFailed: errorMessage,
      systemAction: 'Request aborted'
    })
  }
})

export default router
