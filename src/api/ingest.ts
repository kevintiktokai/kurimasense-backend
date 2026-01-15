import express from 'express'
import { satellitePayloadSchema, weatherPayloadSchema } from '../types/contracts.js'
import { insertSatelliteRecord, insertWeatherRecord, insertVegetationSignal, insertWeatherSignal } from '../db/client.js'
import { toVegetationSignal, toWeatherSignal } from '../signals/index.js'

const router = express.Router()

/**
 * POST /api/ingest/satellite
 * Accept raw satellite data, validate, and store
 */
router.post('/satellite', (req, res) => {
  try {
    // Validate payload
    const validated = satellitePayloadSchema.parse(req.body)
    
    // Store raw payload without transformation
    const rawResult = insertSatelliteRecord(validated)
    
    // Normalize to signal
    const signal = toVegetationSignal(validated)
    
    // Persist signal
    const signalResult = insertVegetationSignal(signal)
    
    res.status(201).json({
      success: true,
      id: rawResult.id,
      signalId: signalResult.id
    })
  } catch (error: any) {
    if (error.name === 'ZodError') {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      })
    }
    
    res.status(500).json({
      success: false,
      error: 'Internal server error'
    })
  }
})

/**
 * POST /api/ingest/weather
 * Accept raw weather data, validate, and store
 */
router.post('/weather', (req, res) => {
  try {
    // Validate payload
    const validated = weatherPayloadSchema.parse(req.body)
    
    // Store raw payload without transformation
    const rawResult = insertWeatherRecord(validated)
    
    // Normalize to signal
    const signal = toWeatherSignal(validated)
    
    // Persist signal
    const signalResult = insertWeatherSignal(signal)
    
    res.status(201).json({
      success: true,
      id: rawResult.id,
      signalId: signalResult.id
    })
  } catch (error: any) {
    if (error.name === 'ZodError') {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      })
    }
    
    res.status(500).json({
      success: false,
      error: 'Internal server error'
    })
  }
})

export default router
