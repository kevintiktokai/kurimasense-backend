/**
 * Inference Categories
 * Emits categorized messages based on status and inference input
 */

import type { InferenceInput } from '../types/inference.js'
import type { StatusResult } from './status.js'

export type InferenceCategory = 'observation' | 'advisory' | 'alert' | 'forecast'

export interface CategoryResult {
  category: InferenceCategory
  message: string
}

/**
 * Emit inference category based on status and input completeness
 * 
 * Category rules:
 * - observation: factual statement about current state
 * - advisory: watch condition detected, non-urgent
 * - alert: stressed condition detected, urgent attention
 * - forecast: insufficient data, future observation needed
 */
export function emitInferenceCategory(
  status: StatusResult | null,
  input: InferenceInput
): CategoryResult {
  // No vegetation data available
  if (!status) {
    return {
      category: 'forecast',
      message: 'No vegetation data available. Next observation needed to assess crop health.'
    }
  }

  // Insufficient data completeness
  if (input.signalCompleteness < 50) {
    return {
      category: 'forecast',
      message: `Limited data coverage (${input.signalCompleteness}%). Additional observations recommended for accurate assessment.`
    }
  }

  // Status-based categorization
  switch (status.status) {
    case 'healthy':
      return {
        category: 'observation',
        message: `Crops are healthy with NDVI of ${status.ndviMean.toFixed(2)}. Vegetation is vigorous.`
      }

    case 'watch':
      return {
        category: 'advisory',
        message: `Crops show moderate vegetation with NDVI of ${status.ndviMean.toFixed(2)}. Monitor for changes.`
      }

    case 'stressed':
      return {
        category: 'alert',
        message: `Crops are stressed with NDVI of ${status.ndviMean.toFixed(2)}. Immediate attention recommended.`
      }
  }
}
