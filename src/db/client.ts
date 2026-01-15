import Database from 'better-sqlite3'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import { existsSync, mkdirSync } from 'fs'
import { initializeSchema } from './schema.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const DB_DIR = join(__dirname, '../../data')
const DB_PATH = join(DB_DIR, 'kurimasense.db')

if (!existsSync(DB_DIR)) {
  mkdirSync(DB_DIR, { recursive: true })
}

const db = new Database(DB_PATH)
db.pragma('journal_mode = WAL')

// Initialize raw records tables
db.exec(`
  CREATE TABLE IF NOT EXISTS satellite_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS weather_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
`)

// Initialize signal tables
initializeSchema(db)

/**
 * Insert raw satellite record
 */
export function insertSatelliteRecord(payload: any) {
  const stmt = db.prepare('INSERT INTO satellite_records (payload) VALUES (?)')
  const result = stmt.run(JSON.stringify(payload))
  return { id: result.lastInsertRowid }
}

/**
 * Insert raw weather record
 */
export function insertWeatherRecord(payload: any) {
  const stmt = db.prepare('INSERT INTO weather_records (payload) VALUES (?)')
  const result = stmt.run(JSON.stringify(payload))
  return { id: result.lastInsertRowid }
}

/**
 * Insert vegetation signal
 */
export function insertVegetationSignal(signal: any) {
  const stmt = db.prepare(`
    INSERT INTO vegetation_signals (
      field_id, season_id, timestamp, ndvi_mean, ndvi_min, ndvi_max, ndvi_std_dev, data_quality
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `)
  const result = stmt.run(
    signal.fieldId,
    signal.seasonId,
    signal.timestamp,
    signal.ndvi.mean,
    signal.ndvi.min,
    signal.ndvi.max,
    signal.ndvi.stdDev,
    signal.dataQuality
  )
  return { id: result.lastInsertRowid }
}

/**
 * Insert weather signal
 */
export function insertWeatherSignal(signal: any) {
  const stmt = db.prepare(`
    INSERT INTO weather_signals (
      field_id, season_id, timestamp, rainfall_mm, temperature_c, data_quality
    ) VALUES (?, ?, ?, ?, ?, ?)
  `)
  const result = stmt.run(
    signal.fieldId,
    signal.seasonId,
    signal.timestamp,
    signal.rainfall,
    signal.temperature,
    signal.dataQuality
  )
  return { id: result.lastInsertRowid }
}

/**
 * Observation Retrieval Functions
 * Primary selector: field_id + season_id
 */

/**
 * Get vegetation signals by field_id and season_id
 */
export function getVegetationSignalsByFieldAndSeason(fieldId: string, seasonId: string) {
  const stmt = db.prepare(`
    SELECT field_id, season_id, timestamp, ndvi_mean, ndvi_min, ndvi_max, ndvi_std_dev, data_quality
    FROM vegetation_signals
    WHERE field_id = ? AND season_id = ?
    ORDER BY timestamp ASC
  `)
  return stmt.all(fieldId, seasonId) as any[]
}

/**
 * Get weather signals by field_id and season_id
 */
export function getWeatherSignalsByFieldAndSeason(fieldId: string, seasonId: string) {
  const stmt = db.prepare(`
    SELECT field_id, season_id, timestamp, rainfall_mm, temperature_c, data_quality
    FROM weather_signals
    WHERE field_id = ? AND season_id = ?
    ORDER BY timestamp ASC
  `)
  return stmt.all(fieldId, seasonId) as any[]
}

/**
 * Field Persistence Functions
 */

/**
 * Create a new field
 */
export function insertField(id: string, name: string, geometry?: string | null) {
  const stmt = db.prepare(`
    INSERT INTO fields (id, name, geometry, created_at)
    VALUES (?, ?, ?, datetime('now'))
  `)
  const result = stmt.run(id, name, geometry || null)
  return { id }
}

/**
 * Get a field by ID
 */
export function getFieldById(id: string) {
  const stmt = db.prepare('SELECT * FROM fields WHERE id = ?')
  const row = stmt.get(id) as any
  if (!row) return null
  return {
    id: row.id,
    name: row.name,
    geometry: row.geometry,
    createdAt: row.created_at
  }
}

/**
 * Get all fields
 */
export function getAllFields() {
  const stmt = db.prepare('SELECT * FROM fields ORDER BY created_at DESC')
  const rows = stmt.all() as any[]
  return rows.map(row => ({
    id: row.id,
    name: row.name,
    geometry: row.geometry,
    createdAt: row.created_at
  }))
}

/**
 * Update a field
 */
export function updateField(id: string, name?: string, geometry?: string | null) {
  const updates: string[] = []
  const values: any[] = []
  
  if (name !== undefined) {
    updates.push('name = ?')
    values.push(name)
  }
  
  if (geometry !== undefined) {
    updates.push('geometry = ?')
    values.push(geometry || null)
  }
  
  if (updates.length === 0) {
    return { id, updated: false }
  }
  
  values.push(id)
  const stmt = db.prepare(`UPDATE fields SET ${updates.join(', ')} WHERE id = ?`)
  const result = stmt.run(...values)
  return { id, updated: result.changes > 0 }
}

/**
 * Delete a field
 */
export function deleteField(id: string) {
  const stmt = db.prepare('DELETE FROM fields WHERE id = ?')
  const result = stmt.run(id)
  return { id, deleted: result.changes > 0 }
}

/**
 * Season Persistence Functions
 */

/**
 * Create a new season
 */
export function insertSeason(id: string, name: string, startDate: string, endDate: string) {
  const stmt = db.prepare(`
    INSERT INTO seasons (id, name, start_date, end_date, created_at)
    VALUES (?, ?, ?, ?, datetime('now'))
  `)
  const result = stmt.run(id, name, startDate, endDate)
  return { id }
}

/**
 * Get a season by ID
 */
export function getSeasonById(id: string) {
  const stmt = db.prepare('SELECT * FROM seasons WHERE id = ?')
  const row = stmt.get(id) as any
  if (!row) return null
  return {
    id: row.id,
    name: row.name,
    startDate: row.start_date,
    endDate: row.end_date,
    createdAt: row.created_at
  }
}

/**
 * Get all seasons
 */
export function getAllSeasons() {
  const stmt = db.prepare('SELECT * FROM seasons ORDER BY start_date DESC')
  const rows = stmt.all() as any[]
  return rows.map(row => ({
    id: row.id,
    name: row.name,
    startDate: row.start_date,
    endDate: row.end_date,
    createdAt: row.created_at
  }))
}

/**
 * Update a season
 */
export function updateSeason(id: string, name?: string, startDate?: string, endDate?: string) {
  const updates: string[] = []
  const values: any[] = []
  
  if (name !== undefined) {
    updates.push('name = ?')
    values.push(name)
  }
  
  if (startDate !== undefined) {
    updates.push('start_date = ?')
    values.push(startDate)
  }
  
  if (endDate !== undefined) {
    updates.push('end_date = ?')
    values.push(endDate)
  }
  
  if (updates.length === 0) {
    return { id, updated: false }
  }
  
  values.push(id)
  const stmt = db.prepare(`UPDATE seasons SET ${updates.join(', ')} WHERE id = ?`)
  const result = stmt.run(...values)
  return { id, updated: result.changes > 0 }
}

/**
 * Delete a season
 */
export function deleteSeason(id: string) {
  const stmt = db.prepare('DELETE FROM seasons WHERE id = ?')
  const result = stmt.run(id)
  return { id, deleted: result.changes > 0 }
}

/**
 * Get previous season for a given season (by start_date)
 * Returns the most recent season that started before the given season
 */
export function getPreviousSeason(seasonId: string) {
  const currentSeason = getSeasonById(seasonId)
  if (!currentSeason) {
    return null
  }

  const stmt = db.prepare(`
    SELECT * FROM seasons 
    WHERE start_date < ? 
    ORDER BY start_date DESC 
    LIMIT 1
  `)
  const row = stmt.get(currentSeason.startDate) as any
  if (!row) return null

  return {
    id: row.id,
    name: row.name,
    startDate: row.start_date,
    endDate: row.end_date,
    createdAt: row.created_at
  }
}

/**
 * Get historical mean NDVI for a field across all seasons
 * Returns the average of all NDVI means from all vegetation signals for this field
 */
export function getHistoricalMeanNdvi(fieldId: string): number | null {
  const stmt = db.prepare(`
    SELECT AVG(ndvi_mean) as mean_ndvi
    FROM vegetation_signals
    WHERE field_id = ?
  `)
  const row = stmt.get(fieldId) as any
  if (!row || row.mean_ndvi === null) {
    return null
  }
  return row.mean_ndvi
}

/**
 * Get mean NDVI for a specific field and season
 */
export function getSeasonMeanNdvi(fieldId: string, seasonId: string): number | null {
  const stmt = db.prepare(`
    SELECT AVG(ndvi_mean) as mean_ndvi
    FROM vegetation_signals
    WHERE field_id = ? AND season_id = ?
  `)
  const row = stmt.get(fieldId, seasonId) as any
  if (!row || row.mean_ndvi === null) {
    return null
  }
  return row.mean_ndvi
}

/**
 * AnalysisRun Persistence Functions
 */

/**
 * Create a new analysis run
 * 
 * Phase 4.2: AnalysisRun is immutable - this is the only way to create one
 * Phase D: Explicit error handling - throws on database errors
 */
export function insertAnalysisRun(
  id: string,
  fieldId: string,
  windowStart: string,
  windowEnd: string,
  inference: any
) {
  // Phase D: Validate inference is serializable
  let inferenceJson: string
  try {
    inferenceJson = JSON.stringify(inference)
  } catch (error) {
    throw new Error(`Failed to serialize inference response: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }

  // Phase D: Insert with explicit error propagation
  const stmt = db.prepare(`
    INSERT INTO analysis_runs (id, field_id, window_start, window_end, inference_response, created_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
  `)
  
  try {
    stmt.run(id, fieldId, windowStart, windowEnd, inferenceJson)
    return { id }
  } catch (error: any) {
    // Phase D: Re-throw with context for upstream handling
    if (error?.code === 'SQLITE_CONSTRAINT') {
      throw error // Let caller handle with context
    }
    throw new Error(`Database error inserting analysis run: ${error?.message || 'Unknown error'}`)
  }
}

/**
 * Get an analysis run by ID
 */
export function getAnalysisRunById(id: string) {
  const stmt = db.prepare('SELECT * FROM analysis_runs WHERE id = ?')
  const row = stmt.get(id) as any
  if (!row) return null
  return {
    id: row.id,
    fieldId: row.field_id,
    windowStart: row.window_start,
    windowEnd: row.window_end,
    inference: JSON.parse(row.inference_response), // Map DB column to contract field name
    createdAt: row.created_at
  }
}

/**
 * Get analysis runs by field ID
 */
export function getAnalysisRunsByFieldId(fieldId: string) {
  const stmt = db.prepare(`
    SELECT * FROM analysis_runs 
    WHERE field_id = ? 
    ORDER BY created_at DESC
  `)
  const rows = stmt.all(fieldId) as any[]
  return rows.map(row => ({
    id: row.id,
    fieldId: row.field_id,
    windowStart: row.window_start,
    windowEnd: row.window_end,
    inference: JSON.parse(row.inference_response), // Map DB column to contract field name
    createdAt: row.created_at
  }))
}

/**
 * Insight Persistence Functions
 */

/**
 * Get insight by field_id and season_id
 */
export function getInsightByFieldAndSeason(fieldId: string, seasonId: string) {
  const stmt = db.prepare(`
    SELECT * FROM insights 
    WHERE field_id = ? AND season_id = ?
  `)
  const row = stmt.get(fieldId, seasonId) as any
  if (!row) return null
  
  return {
    id: row.id,
    fieldId: row.field_id,
    seasonId: row.season_id,
    type: row.type,
    severity: row.severity,
    confidence: row.confidence,
    summary: row.summary,
    evidence: JSON.parse(row.evidence), // Parse JSON evidence
    suggestedAction: row.suggested_action,
    generatedAt: row.generated_at,
    createdAt: row.created_at
  }
}

/**
 * Insert a new insight
 * 
 * Note: UNIQUE constraint on (field_id, season_id) is enforced at database level
 */
export function insertInsight(
  id: string,
  fieldId: string,
  seasonId: string,
  type: string,
  severity: string,
  confidence: string,
  summary: string,
  evidence: any,
  suggestedAction: string | null,
  generatedAt: string
) {
  // Serialize evidence to JSON
  let evidenceJson: string
  try {
    evidenceJson = JSON.stringify(evidence)
  } catch (error) {
    throw new Error(`Failed to serialize evidence: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }

  const stmt = db.prepare(`
    INSERT INTO insights (
      id, field_id, season_id, type, severity, confidence, 
      summary, evidence, suggested_action, generated_at, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
  `)
  
  try {
    stmt.run(
      id,
      fieldId,
      seasonId,
      type,
      severity,
      confidence,
      summary,
      evidenceJson,
      suggestedAction || null,
      generatedAt
    )
    return { id }
  } catch (error: any) {
    // Handle UNIQUE constraint violation
    if (error?.code === 'SQLITE_CONSTRAINT' || error?.message?.includes('UNIQUE constraint')) {
      throw new Error(`Insight already exists for field_id='${fieldId}' and season_id='${seasonId}'`)
    }
    throw new Error(`Database error inserting insight: ${error?.message || 'Unknown error'}`)
  }
}

export default db
