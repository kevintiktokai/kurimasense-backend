/**
 * Decision Context API
 * Phase 7 — Decision Framing
 * 
 * Provides non-actionable, read-only decision contexts to help users structure their decision-making.
 * Decision Contexts clarify considerations, uncertainties, and information gaps
 * without recommending, prioritizing, predicting, or validating actions.
 * 
 * STRICT RULES:
 * - No recommendations or suggestions
 * - No directive language
 * - No urgency or priority implications
 * - No predictions or comparisons
 * - Inference is read-only and authoritative
 * - Single-run scope only
 */

import express, { Request, Response } from 'express'
import { getAnalysisRunById } from '../db/client.js'

const router = express.Router()

/**
 * Generate decision contexts for an analysis run
 * 
 * Phase 7: Non-actionable, read-only frames tied to a single AnalysisRun.
 * Clarifies considerations, uncertainties, and information gaps only.
 */
function generateDecisionContexts(inference: any): Array<{
  domain: string
  inferenceReferences: Array<{ field: string, value: string }>
  considerations: string[]
  uncertainties: string[]
}> {
  const contexts: Array<{
    domain: string
    inferenceReferences: Array<{ field: string, value: string }>
    considerations: string[]
    uncertainties: string[]
  }> = []

  // Irrigation decision context
  if (inference.status) {
    contexts.push({
      domain: 'Irrigation',
      inferenceReferences: [
        { field: 'status', value: inference.status },
        { field: 'confidence', value: inference.confidence },
      ],
      considerations: [
        'Current soil moisture levels',
        'Weather forecasts for the next period',
        'Crop growth stage',
        'Field capacity and water retention characteristics',
        'Irrigation system capacity and availability',
      ],
      uncertainties: [
        'This analysis does not determine whether irrigation is needed',
        'This analysis does not determine optimal irrigation timing',
        'This analysis does not determine irrigation amounts',
      ],
    })
  }

  // Field scouting decision context
  if (inference.status) {
    contexts.push({
      domain: 'Field Scouting',
      inferenceReferences: [
        { field: 'status', value: inference.status },
        { field: 'categories', value: inference.categories?.length > 0 ? `${inference.categories.length} category records` : 'none' },
      ],
      considerations: [
        'Ground truth verification of satellite observations',
        'Specific location of areas of concern within the field',
        'Crop stage and development phase',
        'Historical field conditions and management practices',
        'Weather conditions during the analysis period',
      ],
      uncertainties: [
        'This analysis does not determine whether scouting is needed',
        'This analysis does not determine which areas to scout',
        'This analysis does not determine what to look for during scouting',
      ],
    })
  }

  // General monitoring decision context
  contexts.push({
    domain: 'Monitoring',
    inferenceReferences: [
      { field: 'status', value: inference.status },
      { field: 'trend', value: inference.trend },
      { field: 'confidence', value: inference.confidence },
    ],
    considerations: [
      'Frequency of future observations',
      'Data completeness and coverage',
      'Temporal patterns and changes over time',
      'Consistency with other information sources',
    ],
    uncertainties: [
      'This analysis does not determine monitoring frequency',
      'This analysis does not determine what changes to watch for',
      'This analysis does not determine when to take action',
    ],
  })

  return contexts
}

/**
 * POST /api/decision-context/generate
 * Generate decision contexts for an analysis run
 * 
 * Body:
 * - analysisRunId: string (required)
 * 
 * Contract: Returns non-actionable, read-only decision contexts.
 * No recommendations, directives, urgency, predictions, or comparisons.
 */
router.post('/generate', (req: Request, res: Response) => {
  try {
    const { analysisRunId } = req.body

    if (!analysisRunId || typeof analysisRunId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'analysisRunId is required'
      })
    }

    // Get the analysis run
    const run = getAnalysisRunById(analysisRunId)
    
    if (!run) {
      return res.status(404).json({
        success: false,
        error: 'Analysis run not found'
      })
    }

    // Generate decision contexts (non-actionable, read-only)
    const contexts = generateDecisionContexts(run.inference)

    res.json({
      success: true,
      data: {
        contexts,
        responsibilityStatement: 'KurimaSense does not make decisions or recommendations. Responsibility remains with the user.',
      }
    })
  } catch (error) {
    console.error('Error generating decision contexts:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to generate decision contexts'
    })
  }
})

export default router

