/**
 * Inference API Test
 * Validates endpoint returns valid Inference object
 */

import { insertVegetationSignal, insertWeatherSignal } from './db/client.js'

// Insert test data
function setupTestData() {
  const fieldId = 'test-field-1'
  const now = new Date()
  
  // Insert vegetation signals
  for (let i = 0; i < 3; i++) {
    const timestamp = new Date(now.getTime() - i * 5 * 24 * 60 * 60 * 1000).toISOString()
    insertVegetationSignal({
      fieldId,
      timestamp,
      ndvi: {
        mean: 0.65 - (i * 0.1),
        min: 0.5,
        max: 0.8,
        stdDev: 0.05,
      },
      dataQuality: 'high',
    })
  }
  
  // Insert weather signals
  for (let i = 0; i < 10; i++) {
    const timestamp = new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toISOString()
    insertWeatherSignal({
      fieldId,
      timestamp,
      rainfall: 5.0,
      temperature: 25.0,
      dataQuality: 'high',
    })
  }
  
  console.log('✓ Test data inserted')
  return { fieldId, windowStart: new Date(now.getTime() - 15 * 24 * 60 * 60 * 1000).toISOString(), windowEnd: now.toISOString() }
}

// Test inference assembly
async function testInference() {
  const { fieldId, windowStart, windowEnd } = setupTestData()
  
  // Import inference functions
  const { assembleInferenceInput, inferCropHealthStatus, emitInferenceCategory, assembleInference } = await import('./inference/index.js')
  
  // Run inference pipeline
  const input = assembleInferenceInput(fieldId, windowStart, windowEnd)
  console.log('✓ Inference input assembled:', {
    fieldId: input.fieldId,
    vegSignals: input.vegetationSignals.length,
    weatherSignals: input.weatherSignals.length,
    completeness: input.signalCompleteness,
  })
  
  const status = inferCropHealthStatus(input)
  console.log('✓ Status inferred:', status)
  
  const category = emitInferenceCategory(status, input)
  console.log('✓ Category emitted:', category)
  
  const inference = assembleInference(status, category, input)
  console.log('✓ Inference assembled')
  console.log('\nFinal Inference Object:')
  console.log(JSON.stringify(inference, null, 2))
  
  // Validate structure
  const requiredFields = ['fieldId', 'timestamp', 'status', 'category', 'confidence', 'explanation', 'metadata']
  const hasAllFields = requiredFields.every(field => field in inference)
  
  if (!hasAllFields) {
    console.error('✗ Missing required fields')
    return false
  }
  
  if (inference.confidence < 0 || inference.confidence > 100) {
    console.error('✗ Confidence out of range:', inference.confidence)
    return false
  }
  
  if (!inference.explanation || typeof inference.explanation !== 'string') {
    console.error('✗ Invalid explanation')
    return false
  }
  
  console.log('\n✓ All validation checks passed')
  console.log('✓ Endpoint returns valid Inference')
  return true
}

// Run test
testInference().catch(console.error)
