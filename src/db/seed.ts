/**
 * Phase E.5 — Minimal Seed Data
 * 
 * PURPOSE: Unblock golden path testing ONLY
 * 
 * This file exists solely to provide minimal scaffolding
 * for end-to-end operationalization testing.
 * 
 * RULES:
 * - No fake realism
 * - No simulation of intelligence
 * - Clearly temporary
 * - Explicitly non-authoritative
 * 
 * Creates ONLY:
 * - One test field that matches existing signal data
 * - No inference, no analysis runs (user must create these manually)
 */

import { insertField } from './client.js'

/**
 * Seed minimal test field
 * 
 * Phase E.5: This field matches the field_id in existing signal data.
 * This is NOT production data - it's scaffolding for the golden path.
 */
export function seedTestField() {
  try {
    // Phase E.5: Create field matching existing signal data
    // Signal data already exists for 'test-field-1' - we just need the field record
    insertField('test-field-1', 'Test Field 1', null)
    console.log('✅ Seeded test field: test-field-1')
  } catch (error: any) {
    // If field already exists, that's fine (UNIQUE constraint)
    if (error?.code === 'SQLITE_CONSTRAINT') {
      console.log('ℹ️  Test field already exists: test-field-1')
    } else {
      throw error
    }
  }
}

/**
 * Run seed if executed directly
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  seedTestField()
  console.log('Phase E.5 seed complete')
}





