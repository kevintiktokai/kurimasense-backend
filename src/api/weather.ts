import express, { Request, Response } from 'express'
import weatherPayloadSchema from '../types/weather.js'
import storage from '../db/storage.js'

const router = express.Router()

/**
 * POST /api/weather
 * Accept and validate raw weather data
 */
router.post('/', async (req: Request, res: Response) => {
  try {
    // Validate payload with Zod
    const validatedPayload = weatherPayloadSchema.parse(req.body)
    
    // Persist without modification
    const result = await storage.storeWeather(validatedPayload)
    
    res.status(201).json({
      success: true,
      message: 'Weather data stored successfully',
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
    
    console.error('Error storing weather data:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
    })
  }
})

/**
 * GET /api/weather/:fieldId
 * Retrieve weather data for a field
 */
router.get('/:fieldId', async (req: Request, res: Response) => {
  try {
    const fieldId = typeof req.params.fieldId === 'string' ? req.params.fieldId : req.params.fieldId[0]
    const data = await storage.getWeatherData(fieldId)
    
    res.json({
      success: true,
      count: data.length,
      data,
    })
  } catch (error: unknown) {
    console.error('Error retrieving weather data:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
    })
  }
})

export default router
