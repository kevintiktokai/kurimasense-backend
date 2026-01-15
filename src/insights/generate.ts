/**
 * Insight Generation
 * V1: Deterministic Performance Deviation Insight Generation
 * 
 * This module is the authoritative V1 insight generation logic.
 * It is completely independent of:
 * - analysis_runs (legacy, optional)
 * - inference endpoints (legacy, optional)
 * - inference_response (legacy, optional)
 * 
 * STRICT RULES:
 * - Deterministic: same inputs → same output
 * - Explainable: all logic is auditable
 * - No AI/LLM decision-making
 * - No randomness
 * - No external calls
 * - Type: Performance Deviation only
 * - Severity: Low / Medium / High (based on fixed thresholds)
 * - Confidence: derived from data completeness
 */

import {
  getVegetationSignalsByFieldAndSeason,
  getWeatherSignalsByFieldAndSeason,
  getSeasonById,
  getPreviousSeason,
  getHistoricalMeanNdvi,
  getSeasonMeanNdvi
} from '../db/client.js'

export interface Insight {
  type: 'performance_deviation'
  severity: 'low' | 'medium' | 'high'
  confidence: 'low' | 'medium' | 'high'
  summary: string
  evidence: {
    currentNdvi: number | null
    baselineNdvi: number | null
    baselineType: 'previous_season' | 'historical_mean' | null
    delta: number | null
    deltaPercent: number | null
    signalCompleteness: number
    vegetationSignalCount: number
    weatherSignalCount: number
    thresholds: {
      highSeverity: number
      mediumSeverity: number
    }
  }
  suggestedAction: string | null
}

/**
 * Generate Performance Deviation insight deterministically
 * 
 * @param fieldId - Field identifier (required)
 * @param seasonId - Season identifier (required, must be provided explicitly)
 * @returns Fully formed Insight object
 * 
 * V1 REQUIREMENT: seasonId is MANDATORY
 * - NO automatic season inference
 * - NO default season selection
 * - NO season derivation from dates
 * - Explicit season context is REQUIRED
 * 
 * Logic:
 * 1. Load observations for field + season
 * 2. Load baseline (previous season or historical mean)
 * 3. Compute delta (current - baseline)
 * 4. Assign severity using fixed thresholds
 * 5. Compute confidence from data completeness
 * 6. Return fully formed Insight object
 */
export function generatePerformanceDeviationInsight(
  fieldId: string,
  seasonId: string
): Insight {
  // V1 REQUIREMENT: seasonId must be provided - no inference allowed
  if (!seasonId || typeof seasonId !== 'string' || seasonId.trim().length === 0) {
    throw new Error('seasonId is required and must be a non-empty string. V1 requires explicit season context.')
  }
  // Step 1: Load observations for field + season
  const vegetationSignals = getVegetationSignalsByFieldAndSeason(fieldId, seasonId)
  const weatherSignals = getWeatherSignalsByFieldAndSeason(fieldId, seasonId)
  
  // Get season info for completeness calculation
  const season = getSeasonById(seasonId)
  if (!season) {
    throw new Error(`Season with id '${seasonId}' not found`)
  }
  
  // Calculate current season mean NDVI
  const currentNdvi = getSeasonMeanNdvi(fieldId, seasonId)
  
  // Step 2: Load baseline (previous season or historical mean)
  const previousSeason = getPreviousSeason(seasonId)
  let baselineNdvi: number | null = null
  let baselineType: 'previous_season' | 'historical_mean' | null = null
  
  if (previousSeason) {
    // Try previous season first
    const previousSeasonNdvi = getSeasonMeanNdvi(fieldId, previousSeason.id)
    if (previousSeasonNdvi !== null) {
      baselineNdvi = previousSeasonNdvi
      baselineType = 'previous_season'
    }
  }
  
  // Fall back to historical mean if no previous season data
  if (baselineNdvi === null) {
    const historicalMean = getHistoricalMeanNdvi(fieldId)
    if (historicalMean !== null) {
      baselineNdvi = historicalMean
      baselineType = 'historical_mean'
    }
  }
  
  // Step 3: Compute delta
  let delta: number | null = null
  let deltaPercent: number | null = null
  
  if (currentNdvi !== null && baselineNdvi !== null) {
    delta = currentNdvi - baselineNdvi
    // Calculate percentage change: ((current - baseline) / baseline) * 100
    deltaPercent = (delta / baselineNdvi) * 100
  }
  
  // Step 4: Calculate signal completeness
  const signalCompleteness = calculateSignalCompleteness(
    season.startDate,
    season.endDate,
    vegetationSignals.length,
    weatherSignals.length
  )
  
  // Step 5: Assign severity using fixed thresholds
  // Fixed thresholds for performance deviation:
  // - High severity: delta <= -0.15 (15% or more below baseline)
  // - Medium severity: delta <= -0.08 (8% or more below baseline)
  // - Low severity: delta > -0.08 (less than 8% below baseline, or above baseline)
  const thresholds = {
    highSeverity: -0.15,    // -15% or worse
    mediumSeverity: -0.08   // -8% or worse
  }
  
  let severity: 'low' | 'medium' | 'high'
  if (delta === null || baselineNdvi === null) {
    // No baseline or current data - cannot determine deviation
    severity = 'low'
  } else if (delta <= thresholds.highSeverity) {
    severity = 'high'
  } else if (delta <= thresholds.mediumSeverity) {
    severity = 'medium'
  } else {
    severity = 'low'
  }
  
  // Step 6: Compute confidence from data completeness
  // Fixed thresholds:
  // - High confidence: >= 70% completeness
  // - Medium confidence: >= 40% completeness
  // - Low confidence: < 40% completeness
  let confidence: 'low' | 'medium' | 'high'
  if (signalCompleteness >= 70) {
    confidence = 'high'
  } else if (signalCompleteness >= 40) {
    confidence = 'medium'
  } else {
    confidence = 'low'
  }
  
  // Step 7: Generate summary
  const summary = generateSummary(
    currentNdvi,
    baselineNdvi,
    baselineType,
    delta,
    deltaPercent,
    signalCompleteness,
    vegetationSignals.length,
    weatherSignals.length,
    severity
  )
  
  // Step 8: Generate suggested action
  const suggestedAction = generateSuggestedAction(severity, confidence, delta, baselineNdvi)
  
  // Step 9: Assemble evidence
  const evidence = {
    currentNdvi,
    baselineNdvi,
    baselineType,
    delta,
    deltaPercent: deltaPercent !== null ? Math.round(deltaPercent * 100) / 100 : null, // Round to 2 decimal places
    signalCompleteness,
    vegetationSignalCount: vegetationSignals.length,
    weatherSignalCount: weatherSignals.length,
    thresholds
  }
  
  // Step 10: Return fully formed Insight object
  return {
    type: 'performance_deviation',
    severity,
    confidence,
    summary,
    evidence,
    suggestedAction
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

/**
 * Generate human-readable summary
 */
function generateSummary(
  currentNdvi: number | null,
  baselineNdvi: number | null,
  baselineType: 'previous_season' | 'historical_mean' | null,
  delta: number | null,
  deltaPercent: number | null,
  signalCompleteness: number,
  vegetationCount: number,
  weatherCount: number,
  severity: 'low' | 'medium' | 'high'
): string {
  const parts: string[] = []
  
  // Main performance deviation statement
  if (currentNdvi === null) {
    parts.push(`Insufficient vegetation data available for this season.`)
  } else if (baselineNdvi === null) {
    parts.push(`Current season NDVI is ${currentNdvi.toFixed(3)}. No baseline available for comparison.`)
  } else if (delta === null || deltaPercent === null) {
    parts.push(`Current season NDVI is ${currentNdvi.toFixed(3)}. Baseline NDVI is ${baselineNdvi.toFixed(3)}.`)
  } else {
    const baselineLabel = baselineType === 'previous_season' 
      ? 'previous season' 
      : baselineType === 'historical_mean' 
      ? 'historical average' 
      : 'baseline'
    
    if (delta < 0) {
      parts.push(`Field performance is ${Math.abs(deltaPercent).toFixed(1)}% below ${baselineLabel} (NDVI: ${currentNdvi.toFixed(3)} vs ${baselineNdvi.toFixed(3)}).`)
    } else if (delta > 0) {
      parts.push(`Field performance is ${deltaPercent.toFixed(1)}% above ${baselineLabel} (NDVI: ${currentNdvi.toFixed(3)} vs ${baselineNdvi.toFixed(3)}).`)
    } else {
      parts.push(`Field performance matches ${baselineLabel} (NDVI: ${currentNdvi.toFixed(3)}).`)
    }
  }
  
  // Severity context
  if (severity === 'high') {
    parts.push(`Performance deviation indicates high severity.`)
  } else if (severity === 'medium') {
    parts.push(`Performance deviation indicates medium severity.`)
  } else {
    parts.push(`Performance deviation indicates low severity.`)
  }
  
  // Data quality context
  if (signalCompleteness < 50) {
    parts.push(`Limited data coverage (${signalCompleteness}%) may affect assessment reliability.`)
  } else if (signalCompleteness >= 80) {
    parts.push(`Assessment based on comprehensive data coverage (${signalCompleteness}%).`)
  } else {
    parts.push(`Assessment based on ${signalCompleteness}% data coverage.`)
  }
  
  // Observation count
  parts.push(`Analysis includes ${vegetationCount} vegetation observation${vegetationCount !== 1 ? 's' : ''} and ${weatherCount} weather observation${weatherCount !== 1 ? 's' : ''}.`)
  
  return parts.join(' ')
}

/**
 * Generate suggested action (optional)
 * 
 * V1: Simple, deterministic suggestions based on severity and confidence
 */
function generateSuggestedAction(
  severity: 'low' | 'medium' | 'high',
  confidence: 'low' | 'medium' | 'high',
  delta: number | null,
  baselineNdvi: number | null
): string | null {
  // If confidence is low, suggest data collection
  if (confidence === 'low') {
    return 'Consider collecting additional field observations to improve assessment confidence.'
  }
  
  // If no baseline, suggest investigation
  if (baselineNdvi === null) {
    return 'Establish baseline data for future performance comparisons.'
  }
  
  // Based on severity
  if (severity === 'high') {
    return 'Review field conditions and consider immediate intervention. Verify ground truth through field scouting.'
  } else if (severity === 'medium') {
    return 'Monitor field conditions closely. Consider field scouting to verify satellite observations.'
  }
  
  // Low severity - no action needed
  return null
}
