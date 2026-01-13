/**
 * Canonical API Response Contracts
 * 
 * DO NOT modify without team consensus
 * These interfaces define the external API surface
 */

export interface InferenceResponse {
  fieldId: string
  generatedAt: string

  status: 'healthy' | 'watch' | 'stressed'
  trend: 'improving' | 'stable' | 'declining'
  confidence: 'high' | 'medium' | 'low'

  categories: Array<{
    category: 'observation' | 'advisory' | 'alert' | 'forecast'
    message: string
  }>

  explanation: string
}
