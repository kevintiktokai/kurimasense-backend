/**
 * Inference Assembly
 * Combines status, category, and completeness into final inference output
 */

import type { InferenceInput } from '../types/inference.js'
import type { StatusResult } from './status.js'
import type { CategoryResult } from './categories.js'

export interface Inference {
  fieldId: string
  timestamp: string
  status: StatusResult | null
  category: CategoryResult
  confidence: number // 0-100
  explanation: string
  metadata: {
    windowStart: string
    windowEnd: string
    signalCompleteness: number
    vegetationSignalCount: number
    weatherSignalCount: number
  }
}

/**
 * Assemble final Inference object from component outputs
 */
export function assembleInference(
  status: StatusResult | null,
  category: CategoryResult,
  input: InferenceInput
): Inference {
  const confidence = computeConfidence(status, input)
  const explanation = generateExplanation(status, category, input, confidence)

  return {
    fieldId: input.fieldId,
    timestamp: new Date().toISOString(),
    status,
    category,
    confidence,
    explanation,
    metadata: {
      windowStart: input.windowStart,
      windowEnd: input.windowEnd,
      signalCompleteness: input.signalCompleteness,
      vegetationSignalCount: input.vegetationSignals.length,
      weatherSignalCount: input.weatherSignals.length,
    },
  }
}

/**
 * Compute confidence based on deterministic rules
 * 
 * Confidence factors:
 * - Signal completeness (0-40 points)
 * - Signal agreement (0-30 points)
 * - Temporal stability (0-30 points)
 */
function computeConfidence(
  status: StatusResult | null,
  input: InferenceInput
): number {
  let confidence = 0

  // Factor 1: Signal completeness (0-40 points)
  // Higher completeness = higher confidence
  confidence += Math.min(40, input.signalCompleteness * 0.4)

  // Factor 2: Signal agreement (0-30 points)
  // High-quality signals = higher confidence
  if (input.vegetationSignals.length > 0) {
    const highQualityCount = input.vegetationSignals.filter(
      s => s.dataQuality === 'high'
    ).length
    const qualityRatio = highQualityCount / input.vegetationSignals.length
    confidence += qualityRatio * 30
  }

  // Factor 3: Temporal stability (0-30 points)
  // More observations over time = higher confidence
  if (input.vegetationSignals.length >= 3) {
    confidence += 30
  } else if (input.vegetationSignals.length === 2) {
    confidence += 20
  } else if (input.vegetationSignals.length === 1) {
    confidence += 10
  }

  return Math.round(Math.min(100, confidence))
}

/**
 * Generate human-readable explanation
 */
function generateExplanation(
  status: StatusResult | null,
  category: CategoryResult,
  input: InferenceInput,
  confidence: number
): string {
  const parts: string[] = []

  // Current condition
  parts.push(category.message)

  // Signal quality context
  if (input.signalCompleteness < 50) {
    parts.push(`Data coverage is limited at ${input.signalCompleteness}%, which affects assessment reliability.`)
  } else if (input.signalCompleteness < 80) {
    parts.push(`Assessment based on ${input.signalCompleteness}% data coverage.`)
  } else {
    parts.push(`Assessment based on comprehensive data coverage (${input.signalCompleteness}%).`)
  }

  // Observation count
  const vegCount = input.vegetationSignals.length
  const weatherCount = input.weatherSignals.length
  parts.push(`Analysis includes ${vegCount} vegetation observation${vegCount !== 1 ? 's' : ''} and ${weatherCount} weather observation${weatherCount !== 1 ? 's' : ''}.`)

  return parts.join(' ')
}
