import express from 'express'
import satellitePayloadSchema from '../schemas/satellite.js'
import storage from '../storage.js'

const router = express.Router()

/**
 * POST /api/satellite
 * Accept and validate raw satellite data
 */
router.post('/', async (req, res) => {
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
  } catch (error) {
    if (error.name === 'ZodError') {
      return res.status(400).json({
        success: false,
        message: 'Validation failed',
        errors: error.errors,
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
router.get('/:fieldId', async (req, res) => {
  try {
    const { fieldId } = req.params
    const data = await storage.getSatelliteData(fieldId)
    
    res.json({
      success: true,
      count: data.length,
      data,
    })
  } catch (error) {
    console.error('Error retrieving satellite data:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
    })
  }
})

export default router
