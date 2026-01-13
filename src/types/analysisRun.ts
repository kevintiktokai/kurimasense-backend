/**
 * AnalysisRun Entity Type
 * 
 * Phase 4.2 — Analysis Run Persistence
 * 
 * Stores a snapshot of an InferenceResponse for a field and time window.
 * The inference result is persisted as-is and not recomputed on read.
 * 
 * Canonical Data Contract (LOCKED):
 * - id is permanent
 * - createdAt is server-generated
 * - windowStart < windowEnd (validated once)
 * - inference is embedded, not referenced
 * - No derived fields
 * - No UI metadata
 * - No execution metadata
 */

import type { InferenceResponse } from './api.js'

export interface AnalysisRun {
  id: string
  fieldId: string
  windowStart: string // ISO 8601 timestamp
  windowEnd: string // ISO 8601 timestamp
  inference: InferenceResponse // Full snapshot (embedded)
  createdAt: string // ISO 8601 timestamp
}

export interface CreateAnalysisRunInput {
  fieldId: string
  windowStart: string
  windowEnd: string
  inference: InferenceResponse
}

