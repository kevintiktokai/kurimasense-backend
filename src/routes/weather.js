import express from 'express'
import weatherPayloadSchema from '../schemas/weather.js'
import storage from '../storage.js'

const router = express.Router()

/**
 * POST /api/weather
 * Accept and validate raw weather data
 */
router.post('/', async (req, res) => {
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
  } catch (error) {
    if (error.name === 'ZodError') {
      return res.status(400).json({
        success: false,
        message: 'Validation failed',
        errors: error.errors,
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
router.get('/:fieldId', async (req, res) => {
  try {
    const { fieldId } = req.params
    const data = await storage.getWeatherData(fieldId)
    
    res.json({
      success: true,
      count: data.length,
      data,
    })
  } catch (error) {
    console.error('Error retrieving weather data:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
    })
  }
})

export default router
