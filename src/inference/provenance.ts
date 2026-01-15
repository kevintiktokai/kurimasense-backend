/**
 * Inference Provenance
 * Phase 6.1 — Provenance & Audit Expansion
 * 
 * Generates view-time provenance data showing HOW inference was produced.
 * Provenance is deterministic and reconstructable, but NOT persisted.
 */

import type { InferenceInput } from '../types/inference.js'
import type { StatusResult } from './status.js'
import type { CategoryResult } from './categories.js'

export interface RuleTrace {
  ruleId: string
  ruleName: string
  evaluated: boolean
  outcome?: string | number
  contributesTo: ('status' | 'trend' | 'confidence' | 'category')[]
}

export interface SignalLineage {
  signalType: 'vegetation' | 'weather'
  timestamp: string
  present: boolean
  dataQuality?: 'high' | 'medium' | 'low'
}

export interface CategoryProvenance {
  category: string
  emittedBy: string[]
  emittedAt: string
}

export interface InferenceProvenance {
  ruleTraces: RuleTrace[]
  signalLineage: SignalLineage[]
  categoryProvenance: CategoryProvenance[]
}

/**
 * Generate provenance data for an inference
 * 
 * Phase 6.1: Provenance is view-time only, deterministic, NOT persisted
 */
export function generateProvenance(
  status: StatusResult | null,
  category: CategoryResult,
  input: InferenceInput,
  confidence: number
): InferenceProvenance {
  const ruleTraces: RuleTrace[] = []
  const signalLineage: SignalLineage[] = []
  const categoryProvenance: CategoryProvenance[] = []

  // Status rules
  ruleTraces.push({
    ruleId: 'status-001',
    ruleName: 'Require vegetation signal',
    evaluated: input.vegetationSignals.length > 0,
    contributesTo: ['status'],
  })

  if (status) {
    ruleTraces.push({
      ruleId: 'status-002',
      ruleName: 'NDVI >= 0.6 (healthy threshold)',
      evaluated: status.ndviMean >= status.threshold.healthy,
      outcome: status.ndviMean >= status.threshold.healthy ? 'true' : 'false',
      contributesTo: ['status'],
    })

    ruleTraces.push({
      ruleId: 'status-003',
      ruleName: 'NDVI >= 0.3 (watch threshold)',
      evaluated: status.ndviMean >= status.threshold.watch,
      outcome: status.ndviMean >= status.threshold.watch ? 'true' : 'false',
      contributesTo: ['status'],
    })

    ruleTraces.push({
      ruleId: 'status-004',
      ruleName: 'NDVI < 0.3 (stressed threshold)',
      evaluated: status.ndviMean < status.threshold.watch,
      outcome: status.ndviMean < status.threshold.watch ? 'true' : 'false',
      contributesTo: ['status'],
    })
  }

  // Confidence rules
  ruleTraces.push({
    ruleId: 'confidence-001',
    ruleName: 'Signal completeness factor',
    evaluated: true,
    outcome: Math.min(40, input.signalCompleteness * 0.4),
    contributesTo: ['confidence'],
  })

  if (input.vegetationSignals.length > 0) {
    const highQualityCount = input.vegetationSignals.filter(s => s.dataQuality === 'high').length
    const qualityRatio = highQualityCount / input.vegetationSignals.length
    ruleTraces.push({
      ruleId: 'confidence-002',
      ruleName: 'Signal quality factor',
      evaluated: true,
      outcome: qualityRatio * 30,
      contributesTo: ['confidence'],
    })
  }

  // Temporal stability rules
  if (input.vegetationSignals.length >= 3) {
    ruleTraces.push({
      ruleId: 'confidence-003',
      ruleName: 'Temporal stability (>=3 signals)',
      evaluated: true,
      outcome: 30,
      contributesTo: ['confidence'],
    })
  } else if (input.vegetationSignals.length === 2) {
    ruleTraces.push({
      ruleId: 'confidence-003',
      ruleName: 'Temporal stability (2 signals)',
      evaluated: true,
      outcome: 20,
      contributesTo: ['confidence'],
    })
  } else if (input.vegetationSignals.length === 1) {
    ruleTraces.push({
      ruleId: 'confidence-003',
      ruleName: 'Temporal stability (1 signal)',
      evaluated: true,
      outcome: 10,
      contributesTo: ['confidence'],
    })
  }

  // Category rules
  if (!status) {
    ruleTraces.push({
      ruleId: 'category-001',
      ruleName: 'No status → forecast',
      evaluated: true,
      contributesTo: ['category'],
    })
  } else if (input.signalCompleteness < 50) {
    ruleTraces.push({
      ruleId: 'category-002',
      ruleName: 'Completeness < 50% → forecast',
      evaluated: true,
      contributesTo: ['category'],
    })
  } else {
    switch (status.status) {
      case 'healthy':
        ruleTraces.push({
          ruleId: 'category-003',
          ruleName: 'Status healthy → observation',
          evaluated: true,
          contributesTo: ['category'],
        })
        break
      case 'watch':
        ruleTraces.push({
          ruleId: 'category-004',
          ruleName: 'Status watch → advisory',
          evaluated: true,
          contributesTo: ['category'],
        })
        break
      case 'stressed':
        ruleTraces.push({
          ruleId: 'category-005',
          ruleName: 'Status stressed → alert',
          evaluated: true,
          contributesTo: ['category'],
        })
        break
    }
  }

  // Signal lineage
  input.vegetationSignals.forEach(signal => {
    signalLineage.push({
      signalType: 'vegetation',
      timestamp: signal.timestamp,
      present: true,
      dataQuality: signal.dataQuality,
    })
  })

  input.weatherSignals.forEach(signal => {
    signalLineage.push({
      signalType: 'weather',
      timestamp: signal.timestamp,
      present: true,
      dataQuality: signal.dataQuality,
    })
  })

  // Category provenance
  const categoryRuleIds = ruleTraces
    .filter(rule => rule.contributesTo.includes('category') && rule.evaluated)
    .map(rule => rule.ruleId)

  categoryProvenance.push({
    category: category.category,
    emittedBy: categoryRuleIds,
    emittedAt: new Date().toISOString(), // View-time generation timestamp (not stored)
  })

  return {
    ruleTraces,
    signalLineage,
    categoryProvenance,
  }
}

