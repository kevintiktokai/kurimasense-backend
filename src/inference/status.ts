/**
 * Crop Health Status Inference
 * Derives health status from vegetation signals using simple thresholds
 */

import type { InferenceInput } from '../types/inference.js'

export type CropHealthStatus = 'healthy' | 'watch' | 'stressed'

export interface StatusResult {
  status: CropHealthStatus
  ndviMean: number
  threshold: {
    healthy: number
    watch: number
  }
}

/**
 * Derive crop health status from the most recent VegetationSignal
 * Uses simple, explainable NDVI thresholds
 */
export function inferCropHealthStatus(input: InferenceInput): StatusResult | null {
  // Require at least one vegetation signal
  if (input.vegetationSignals.length === 0) {
    return null
  }

  // Get most recent vegetation signal
  const mostRecent = input.vegetationSignals[input.vegetationSignals.length - 1]
  const ndviMean = mostRecent.ndvi.mean

  // Simple NDVI thresholds based on agricultural research
  // NDVI > 0.6: healthy vegetation
  // NDVI 0.3-0.6: watch (moderate vegetation)
  // NDVI < 0.3: stressed vegetation
  const thresholds = {
    healthy: 0.6,
    watch: 0.3,
  }

  let status: CropHealthStatus
  if (ndviMean >= thresholds.healthy) {
    status = 'healthy'
  } else if (ndviMean >= thresholds.watch) {
    status = 'watch'
  } else {
    status = 'stressed'
  }

  return {
    status,
    ndviMean,
    threshold: thresholds,
  }
}
