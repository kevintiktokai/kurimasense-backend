import express, { Request, Response } from 'express'
import satellitePayloadSchema from '../types/satellite.js'
import storage from '../db/storage.js'

const router = express.Router()

/**
 * POST /api/satellite
 * Accept and validate raw satellite data
 */
router.post('/', async (req: Request, res: Response) => {
  try {
    // Validate payload with Zod
    const validatedPayload = satellitePayloadSchema.parse(req.body)
    
    // Persist without modification
    const result = await storage.storeSatellite(validatedPayload)
    
    res.status(201).json({
      success: true,
      message: 'Satellite data stored successfully',
      data: result,
    })
  } catch (error: unknown) {
    if (error && typeof error === 'object' && 'name' in error && error.name === 'ZodError' && 'errors' in error) {
      return res.status(400).json({
        success: false,
        message: 'Validation failed',
        errors: (error as unknown as { errors: unknown }).errors,
      })
    }
    
    console.error('Error storing satellite data:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
    })
  }
})

/**
 * GET /api/satellite/:fieldId
 * Retrieve satellite data for a field
 */
router.get('/:fieldId', async (req: Request, res: Response) => {
  try {
    const fieldId = typeof req.params.fieldId === 'string' ? req.params.fieldId : req.params.fieldId[0]
    const data = await storage.getSatelliteData(fieldId)
    
    res.json({
      success: true,
      count: data.length,
      data,
    })
  } catch (error: unknown) {
    console.error('Error retrieving satellite data:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
    })
  }
})

export default router
