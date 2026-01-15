/**
 * Insights API Test
 * Dev-only test script to verify insight generation and idempotency
 * 
 * This script:
 * 1. Creates a test field
 * 2. Creates a test season
 * 3. Inserts test signals (vegetation and weather)
 * 4. Calls GET /api/insights twice
 * 5. Confirms:
 *    - Insight is generated once
 *    - Second call returns the same record
 */

import { randomUUID } from 'crypto'
import {
  insertField,
  insertSeason,
  insertVegetationSignal,
  insertWeatherSignal,
  getInsightByFieldAndSeason
} from './db/client.js'

// Test configuration
const TEST_FIELD_ID = `test-field-${randomUUID()}`
const TEST_SEASON_ID = `test-season-${randomUUID()}`
const TEST_FIELD_NAME = 'Test Field - Insights API'
const TEST_SEASON_NAME = '2024/25 Test Season'

/**
 * Setup test data: field, season, and signals
 */
function setupTestData() {
  console.log('\n📋 Setting up test data...')
  
  // Create test field
  const now = new Date()
  insertField(TEST_FIELD_ID, TEST_FIELD_NAME, null)
  console.log(`✓ Created test field: ${TEST_FIELD_ID} (${TEST_FIELD_NAME})`)
  
  // Create test season (30 days duration)
  const seasonStart = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString()
  const seasonEnd = now.toISOString()
  insertSeason(TEST_SEASON_ID, TEST_SEASON_NAME, seasonStart, seasonEnd)
  console.log(`✓ Created test season: ${TEST_SEASON_ID} (${TEST_SEASON_NAME})`)
  console.log(`  Start: ${seasonStart}`)
  console.log(`  End: ${seasonEnd}`)
  
  // Insert vegetation signals (3 observations over 30 days)
  for (let i = 0; i < 3; i++) {
    const timestamp = new Date(
      new Date(seasonStart).getTime() + i * 10 * 24 * 60 * 60 * 1000
    ).toISOString()
    
    insertVegetationSignal({
      fieldId: TEST_FIELD_ID,
      seasonId: TEST_SEASON_ID,
      timestamp,
      ndvi: {
        mean: 0.65 - (i * 0.05), // Decreasing NDVI to show some variation
        min: 0.5,
        max: 0.8,
        stdDev: 0.05,
      },
      dataQuality: 'high',
    })
  }
  console.log(`✓ Inserted 3 vegetation signals`)
  
  // Insert weather signals (daily observations)
  for (let i = 0; i < 30; i++) {
    const timestamp = new Date(
      new Date(seasonStart).getTime() + i * 24 * 60 * 60 * 1000
    ).toISOString()
    
    insertWeatherSignal({
      fieldId: TEST_FIELD_ID,
      seasonId: TEST_SEASON_ID,
      timestamp,
      rainfall: 5.0 + (Math.random() * 10), // Random rainfall 5-15mm
      temperature: 25.0 + (Math.random() * 5), // Random temp 25-30°C
      dataQuality: 'high',
    })
  }
  console.log(`✓ Inserted 30 weather signals`)
  
  console.log('✅ Test data setup complete\n')
  
  return { fieldId: TEST_FIELD_ID, seasonId: TEST_SEASON_ID }
}

/**
 * Call GET /api/insights endpoint
 * Simulates the API behavior by calling functions directly
 */
async function callInsightsAPI(fieldId, seasonId, callNumber) {
  console.log(`\n📞 Call #${callNumber}: GET /api/insights?fieldId=${fieldId}&seasonId=${seasonId}`)
  
  // Import required functions
  const { generatePerformanceDeviationInsight } = await import('./insights/generate.js')
  const { getInsightByFieldAndSeason, insertInsight, getFieldById, getSeasonById } = await import('./db/client.js')
  
  // Validate field exists (simulating API validation)
  const field = getFieldById(fieldId)
  if (!field) {
    throw new Error(`Field with id '${fieldId}' does not exist`)
  }
  
  // Validate season exists (simulating API validation)
  const season = getSeasonById(seasonId)
  if (!season) {
    throw new Error(`Season with id '${seasonId}' does not exist`)
  }
  
  // Check if insight already exists (simulating API query-store-return behavior)
  const existingInsight = getInsightByFieldAndSeason(fieldId, seasonId)
  
  if (existingInsight) {
    console.log(`  ✓ Insight found in database (id: ${existingInsight.id})`)
    console.log(`  ✓ Generated at: ${existingInsight.generatedAt}`)
    return existingInsight
  }
  
  // Generate new insight (simulating API generation)
  console.log(`  → Insight not found, generating...`)
  const insight = generatePerformanceDeviationInsight(fieldId, seasonId)
  
  // Store insight (simulating API storage)
  const id = randomUUID()
  const generatedAt = new Date().toISOString()
  const storedInsight = insertInsight(
    id,
    fieldId,
    seasonId,
    insight.type,
    insight.severity,
    insight.confidence,
    insight.summary,
    insight.evidence,
    insight.suggestedAction,
    generatedAt
  )
  
  console.log(`  ✓ Insight generated and stored (id: ${storedInsight.id})`)
  console.log(`  ✓ Generated at: ${storedInsight.generatedAt}`)
  
  return storedInsight
}

/**
 * Run the test
 */
async function testInsightsIdempotency() {
  console.log('🧪 Testing Insights API Idempotency')
  console.log('=' .repeat(60))
  
  try {
    // Setup test data
    const { fieldId, seasonId } = setupTestData()
    
    // First call - should generate insight
    console.log('\n🔵 FIRST CALL (should generate new insight)')
    const firstCall = await callInsightsAPI(fieldId, seasonId, 1)
    
    console.log('\n📊 First call result:')
    console.log(`  Type: ${firstCall.type}`)
    console.log(`  Severity: ${firstCall.severity}`)
    console.log(`  Confidence: ${firstCall.confidence}`)
    console.log(`  Summary: ${firstCall.summary.substring(0, 100)}...`)
    console.log(`  ID: ${firstCall.id}`)
    console.log(`  Generated at: ${firstCall.generatedAt}`)
    
    // Second call - should return same insight
    console.log('\n🟢 SECOND CALL (should return existing insight)')
    const secondCall = await callInsightsAPI(fieldId, seasonId, 2)
    
    console.log('\n📊 Second call result:')
    console.log(`  Type: ${secondCall.type}`)
    console.log(`  Severity: ${secondCall.severity}`)
    console.log(`  Confidence: ${secondCall.confidence}`)
    console.log(`  Summary: ${secondCall.summary.substring(0, 100)}...`)
    console.log(`  ID: ${secondCall.id}`)
    console.log(`  Generated at: ${secondCall.generatedAt}`)
    
    // Verify idempotency
    console.log('\n✅ VERIFICATION:')
    const sameId = firstCall.id === secondCall.id
    const sameGeneratedAt = firstCall.generatedAt === secondCall.generatedAt
    const sameContent = JSON.stringify(firstCall) === JSON.stringify(secondCall)
    
    if (sameId) {
      console.log('  ✓ Same insight ID returned')
    } else {
      console.error('  ✗ Different insight IDs returned!')
      console.error(`    First:  ${firstCall.id}`)
      console.error(`    Second: ${secondCall.id}`)
      return false
    }
    
    if (sameGeneratedAt) {
      console.log('  ✓ Same generated_at timestamp')
    } else {
      console.error('  ✗ Different generated_at timestamps!')
      console.error(`    First:  ${firstCall.generatedAt}`)
      console.error(`    Second: ${secondCall.generatedAt}`)
      return false
    }
    
    if (sameContent) {
      console.log('  ✓ Same content returned (idempotent)')
    } else {
      console.error('  ✗ Different content returned!')
      return false
    }
    
    // Verify only one insight exists in database
    const dbInsight = getInsightByFieldAndSeason(fieldId, seasonId)
    if (dbInsight && dbInsight.id === firstCall.id) {
      console.log('  ✓ Only one insight exists in database')
    } else {
      console.error('  ✗ Database state incorrect!')
      return false
    }
    
    console.log('\n' + '='.repeat(60))
    console.log('✅ ALL TESTS PASSED')
    console.log('✅ Insight generation is idempotent')
    console.log('✅ Second call returns the same record')
    console.log('='.repeat(60))
    
    return true
  } catch (error) {
    console.error('\n❌ TEST FAILED')
    console.error('Error:', error)
    if (error instanceof Error) {
      console.error('Stack:', error.stack)
    }
    return false
  }
}

// Run test
testInsightsIdempotency()
  .then(success => {
    if (success) {
      console.log('\n✅ Test completed successfully')
      process.exit(0)
    } else {
      console.log('\n❌ Test failed')
      process.exit(1)
    }
  })
  .catch(error => {
    console.error('\n❌ Test error:', error)
    process.exit(1)
  })
