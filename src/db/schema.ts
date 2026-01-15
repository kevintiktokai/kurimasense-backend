/**
 * Database Schema
 * Minimal and auditable tables for signal storage
 */

export const VEGETATION_SIGNALS_TABLE = `
  CREATE TABLE IF NOT EXISTS vegetation_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id TEXT NOT NULL,
    season_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    ndvi_mean REAL NOT NULL,
    ndvi_min REAL NOT NULL,
    ndvi_max REAL NOT NULL,
    ndvi_std_dev REAL NOT NULL,
    data_quality TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
`

export const WEATHER_SIGNALS_TABLE = `
  CREATE TABLE IF NOT EXISTS weather_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id TEXT NOT NULL,
    season_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    rainfall_mm REAL NOT NULL,
    temperature_c REAL NOT NULL,
    data_quality TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
`

export const FIELDS_TABLE = `
  CREATE TABLE IF NOT EXISTS fields (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    geometry TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )
`

export const ANALYSIS_RUNS_TABLE = `
  CREATE TABLE IF NOT EXISTS analysis_runs (
    id TEXT PRIMARY KEY,
    field_id TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    inference_response TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )
`

export const SEASONS_TABLE = `
  CREATE TABLE IF NOT EXISTS seasons (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )
`

export const INSIGHTS_TABLE = `
  CREATE TABLE IF NOT EXISTS insights (
    id TEXT PRIMARY KEY,
    field_id TEXT NOT NULL,
    season_id TEXT NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence TEXT NOT NULL,
    suggested_action TEXT,
    generated_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(field_id, season_id)
  )
`

/**
 * Migrate existing tables to add season_id column if it doesn't exist
 * This handles the case where tables already exist without season_id
 */
function migrateSeasonIdColumn(db: any): void {
  // Check if season_id column exists in vegetation_signals
  try {
    const vegCheck = db.prepare("PRAGMA table_info(vegetation_signals)").all()
    const hasSeasonId = vegCheck.some((col: any) => col.name === 'season_id')
    
    if (!hasSeasonId) {
      // Add season_id column (nullable for now, will be enforced at application level)
      // Note: SQLite doesn't support adding NOT NULL columns to existing tables
      // We'll add it as nullable and enforce NOT NULL in application logic
      db.exec('ALTER TABLE vegetation_signals ADD COLUMN season_id TEXT')
    }
  } catch (error) {
    // Table doesn't exist yet, will be created with season_id
  }

  // Check if season_id column exists in weather_signals
  try {
    const weatherCheck = db.prepare("PRAGMA table_info(weather_signals)").all()
    const hasSeasonId = weatherCheck.some((col: any) => col.name === 'season_id')
    
    if (!hasSeasonId) {
      // Add season_id column (nullable for now, will be enforced at application level)
      db.exec('ALTER TABLE weather_signals ADD COLUMN season_id TEXT')
    }
  } catch (error) {
    // Table doesn't exist yet, will be created with season_id
  }
}

export function initializeSchema(db: any): void {
  db.exec(VEGETATION_SIGNALS_TABLE)
  db.exec(WEATHER_SIGNALS_TABLE)
  db.exec(FIELDS_TABLE)
  db.exec(ANALYSIS_RUNS_TABLE)
  db.exec(SEASONS_TABLE)
  db.exec(INSIGHTS_TABLE)
  
  // Migrate existing tables to add season_id if needed
  migrateSeasonIdColumn(db)
}
