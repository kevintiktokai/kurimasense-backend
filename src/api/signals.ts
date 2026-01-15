import express from 'express'
import {
  processSatelliteSignals,
  processWeatherSignals,
  storeSignals,
  getSignals
} from '../signals/processor.js'

const router = express.Router()

/**
 * POST /api/signals/process
 * Process raw records into signals
 */
router.post('/process', async (req, res) => {
  try {
    const { fieldId } = req.body

    // Process both satellite and weather records
    const satelliteSignals = processSatelliteSignals(fieldId)
    const weatherSignals = processWeatherSignals(fieldId)

    const allSignals = [...satelliteSignals, ...weatherSignals]
    const result = storeSignals(allSignals)

    res.json({
      success: true,
      message: 'Signals processed',
      processed: result.processed,
      breakdown: {
        satellite: satelliteSignals.length,
        weather: weatherSignals.length
      }
    })
  } catch (error: any) {
    console.error('Signal processing error:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to process signals'
    })
  }
})

/**
 * GET /api/signals/:fieldId
 * Get signals for a field
 */
router.get('/:fieldId', async (req, res) => {
  try {
    const { fieldId } = req.params
    const { type } = req.query

    const signals = getSignals(fieldId, type as string)

    res.json({
      success: true,
      count: signals.length,
      signals
    })
  } catch (error: any) {
    console.error('Signal retrieval error:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve signals'
    })
  }
})

export default router
