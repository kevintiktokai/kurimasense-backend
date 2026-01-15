/**
 * Inference Input Assembly
 * Functions to construct InferenceInput from persisted signals
 */

import db, { getSeasonById, getVegetationSignalsByFieldAndSeason, getWeatherSignalsByFieldAndSeason } from '../db/client.js'
import type { InferenceInput } from '../types/inference.js'
import type { VegetationSignal } from '../signals/vegetation.js'
import type { WeatherSignal } from '../signals/weather.js'

/**
 * Assemble InferenceInput for a given field and season
 * season_id is the primary selector; timestamp window is derived from season dates
 * 
 * Overload 1: fieldId + seasonId (new, preferred)
 * Overload 2: fieldId + windowStart + windowEnd (legacy, for backward compatibility)
 */
export function assembleInferenceInput(
  fieldId: string,
  seasonIdOrWindowStart: string,
  windowEnd?: string
): InferenceInput {
  let windowStart: string
  let windowEndValue: string
  let vegetationRows: any[]
  let weatherRows: any[]

  // Determine if this is the new signature (seasonId) or old signature (windowStart, windowEnd)
  if (windowEnd === undefined) {
    // New signature: fieldId + seasonId
    const seasonId = seasonIdOrWindowStart
    const season = getSeasonById(seasonId)
    if (!season) {
      throw new Error(`Season with id '${seasonId}' not found`)
    }

    windowStart = season.startDate
    windowEndValue = season.endDate

    // Query vegetation signals by field_id and season_id (primary selector)
    vegetationRows = getVegetationSignalsByFieldAndSeason(fieldId, seasonId)

    // Query weather signals by field_id and season_id (primary selector)
    weatherRows = getWeatherSignalsByFieldAndSeason(fieldId, seasonId)
  } else {
    // Legacy signature: fieldId + windowStart + windowEnd
    // Fall back to timestamp-based query for backward compatibility
    windowStart = seasonIdOrWindowStart
    windowEndValue = windowEnd

    // Query vegetation signals within window (legacy)
    vegetationRows = db.prepare(`
      SELECT field_id, season_id, timestamp, ndvi_mean, ndvi_min, ndvi_max, ndvi_std_dev, data_quality
      FROM vegetation_signals
      WHERE field_id = ? AND timestamp >= ? AND timestamp <= ?
      ORDER BY timestamp ASC
    `).all(fieldId, windowStart, windowEndValue)

    // Query weather signals within window (legacy)
    weatherRows = db.prepare(`
      SELECT field_id, season_id, timestamp, rainfall_mm, temperature_c, data_quality
      FROM weather_signals
      WHERE field_id = ? AND timestamp >= ? AND timestamp <= ?
      ORDER BY timestamp ASC
    `).all(fieldId, windowStart, windowEndValue)
  }

  // Transform database rows to signal objects
  const vegetationSignals: VegetationSignal[] = vegetationRows.map((row: any) => ({
    fieldId: row.field_id,
    timestamp: row.timestamp,
    ndvi: {
      mean: row.ndvi_mean,
      min: row.ndvi_min,
      max: row.ndvi_max,
      stdDev: row.ndvi_std_dev,
    },
    dataQuality: row.data_quality as 'high' | 'medium' | 'low',
  }))

  const weatherSignals: WeatherSignal[] = weatherRows.map((row: any) => ({
    fieldId: row.field_id,
    timestamp: row.timestamp,
    rainfall: row.rainfall_mm,
    temperature: row.temperature_c,
    dataQuality: row.data_quality as 'high' | 'medium' | 'low',
  }))

  // Calculate signal completeness
  const signalCompleteness = calculateSignalCompleteness(
    windowStart,
    windowEndValue,
    vegetationSignals.length,
    weatherSignals.length
  )

  return {
    fieldId,
    windowStart,
    windowEnd: windowEndValue,
    vegetationSignals,
    weatherSignals,
    signalCompleteness,
  }
}

/**
 * Calculate signal completeness percentage
 * Based on expected observation frequency within time window
 */
function calculateSignalCompleteness(
  windowStart: string,
  windowEnd: string,
  vegetationCount: number,
  weatherCount: number
): number {
  const start = new Date(windowStart)
  const end = new Date(windowEnd)
  const daysInWindow = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))

  // Expected frequencies:
  // - Satellite imagery: every 5 days
  // - Weather observations: daily
  const expectedVegetation = Math.ceil(daysInWindow / 5)
  const expectedWeather = daysInWindow

  const totalExpected = expectedVegetation + expectedWeather
  const totalActual = vegetationCount + weatherCount

  if (totalExpected === 0) return 0

  const completeness = (totalActual / totalExpected) * 100
  return Math.min(100, Math.round(completeness))
}
