import express, { Request, Response } from 'express'
import { randomUUID } from 'crypto'
import {
  insertField,
  getFieldById,
  getAllFields,
  getAnalysisRunsByFieldId,
} from '../db/client.js'
import type { CreateFieldInput } from '../types/field.js'

const router = express.Router()

/**
 * GET /api/fields
 * Get all fields
 */
router.get('/', (req: Request, res: Response) => {
  try {
    const fields = getAllFields()
    res.json({
      success: true,
      data: fields
    })
  } catch (error) {
    console.error('Error fetching fields:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to fetch fields'
    })
  }
})

/**
 * GET /api/fields/:id/analysis-runs
 * Get all AnalysisRuns for a specific field
 * 
 * LEGACY / OPTIONAL — NOT REQUIRED FOR V1
 * 
 * ⚠️ IMPORTANT: This endpoint is NOT required for V1 functionality.
 * - V1 insights are served via GET /api/insights (authoritative)
 * - This endpoint is legacy/optional and remains for backward compatibility
 * - Returns stored AnalysisRuns only, no recomputation
 * - Must be defined before /:id route to avoid route conflict
 */
router.get('/:id/analysis-runs', (req: Request, res: Response) => {
  try {
    const idParam = (req.params as any).id as string | string[] | undefined
    const id = Array.isArray(idParam) ? idParam[0] : idParam
    if (!id || typeof id !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Field id is required'
      })
    }
    const runs = getAnalysisRunsByFieldId(id)
    res.json({
      success: true,
      data: runs
    })
  } catch (error) {
    console.error('Error fetching analysis runs for field:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to fetch analysis runs'
    })
  }
})

/**
 * GET /api/fields/:id
 * Get a field by ID
 */
router.get('/:id', (req: Request, res: Response) => {
  try {
    const idParam = (req.params as any).id as string | string[] | undefined
    const id = Array.isArray(idParam) ? idParam[0] : idParam
    if (!id || typeof id !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Field id is required'
      })
    }
    const field = getFieldById(id)
    
    if (!field) {
      return res.status(404).json({
        success: false,
        error: 'Field not found'
      })
    }
    
    res.json({
      success: true,
      data: field
    })
  } catch (error) {
    console.error('Error fetching field:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to fetch field'
    })
  }
})

/**
 * POST /api/fields
 * Create a new field
 */
router.post('/', (req: Request, res: Response) => {
  try {
    const { name, geometry }: CreateFieldInput = req.body
    
    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Field name is required'
      })
    }
    
    // Generate stable ID (UUID)
    const id = randomUUID()
    
    // Create field
    insertField(id, name.trim(), geometry || null)
    
    // Fetch created field
    const field = getFieldById(id)
    
    res.status(201).json({
      success: true,
      data: field
    })
  } catch (error) {
    console.error('Error creating field:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to create field'
    })
  }
})

export default router

