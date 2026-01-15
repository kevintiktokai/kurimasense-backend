/**
 * Canonical Inference Input
 * LOCKED: This is the standard input contract for all inference operations
 * 
 * DO NOT modify this interface without team consensus
 */

import type { VegetationSignal } from '../signals/vegetation.js'
import type { WeatherSignal } from '../signals/weather.js'

export interface InferenceInput {
  fieldId: string
  windowStart: string // ISO 8601 timestamp
  windowEnd: string // ISO 8601 timestamp
  
  vegetationSignals: VegetationSignal[]
  weatherSignals: WeatherSignal[]
  
  signalCompleteness: number // percentage (0-100)
}
