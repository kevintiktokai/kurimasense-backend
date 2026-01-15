/**
 * Signal Processing Layer
 * 
 * Transforms raw ingested records into actionable crop health signals.
 * No real-time processing - runs on demand or via scheduled jobs.
 */

import db from '../db/client.js'

/**
 * Process satellite records into NDVI signals
 */
export function processSatelliteSignals(fieldId: string) {
  // Get all unprocessed satellite records
  const stmt = db.prepare(
    'SELECT id, payload FROM satellite_records WHERE id NOT IN (SELECT source_id FROM signals WHERE source_type = ?)'
  )
  const records = stmt.all('satellite') as Array<{ id: number; payload: string }>

  const signals: any[] = []

  for (const record of records) {
    const data = JSON.parse(record.payload) as any
    
    if (data.fieldId === fieldId || !fieldId) {
      // Extract NDVI signal
      signals.push({
        source_type: 'satellite',
        source_id: record.id,
        field_id: data.fieldId,
        signal_type: 'ndvi',
        timestamp: data.timestamp,
        value: data.ndvi.mean,
        metadata: JSON.stringify({
          source: data.source,
          min: data.ndvi.min,
          max: data.ndvi.max,
          stdDev: data.ndvi.stdDev,
          cloudCoverage: data.metadata?.cloudCoverage,
          coordinates: data.coordinates
        })
      })
    }
  }

  return signals
}

/**
 * Process weather records into environmental signals
 */
export function processWeatherSignals(fieldId: string) {
  const stmt = db.prepare(
    'SELECT id, payload FROM weather_records WHERE id NOT IN (SELECT source_id FROM signals WHERE source_type = ?)'
  )
  const records = stmt.all('weather') as Array<{ id: number; payload: string }>

  const signals: any[] = []

  for (const record of records) {
    const data = JSON.parse(record.payload) as any
    
    if (data.fieldId === fieldId || !fieldId) {
      // Temperature signal
      signals.push({
        source_type: 'weather',
        source_id: record.id,
        field_id: data.fieldId,
        signal_type: 'temperature',
        timestamp: data.timestamp,
        value: data.current.temperature,
        metadata: JSON.stringify({ source: data.source })
      })

      // Humidity signal
      signals.push({
        source_type: 'weather',
        source_id: record.id,
        field_id: data.fieldId,
        signal_type: 'humidity',
        timestamp: data.timestamp,
        value: data.current.humidity,
        metadata: JSON.stringify({ source: data.source })
      })

      // Precipitation signal
      if (data.current.precipitation > 0) {
        signals.push({
          source_type: 'weather',
          source_id: record.id,
          field_id: data.fieldId,
          signal_type: 'precipitation',
          timestamp: data.timestamp,
          value: data.current.precipitation,
          metadata: JSON.stringify({ source: data.source })
        })
      }
    }
  }

  return signals
}

/**
 * Store processed signals
 */
export function storeSignals(signals: any[]) {
  // Create signals table if not exists
  db.exec(`
    CREATE TABLE IF NOT EXISTS signals (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_type TEXT NOT NULL,
      source_id INTEGER NOT NULL,
      field_id TEXT NOT NULL,
      signal_type TEXT NOT NULL,
      timestamp TEXT NOT NULL,
      value REAL NOT NULL,
      metadata TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(source_type, source_id, signal_type)
    );
    CREATE INDEX IF NOT EXISTS idx_signals_field ON signals(field_id, timestamp);
    CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(signal_type, field_id);
  `)

  const stmt = db.prepare(`
    INSERT INTO signals (source_type, source_id, field_id, signal_type, timestamp, value, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source_type, source_id, signal_type) DO UPDATE SET
      value = excluded.value,
      metadata = excluded.metadata
  `)

  for (const signal of signals) {
    stmt.run(
      signal.source_type,
      signal.source_id,
      signal.field_id,
      signal.signal_type,
      signal.timestamp,
      signal.value,
      signal.metadata
    )
  }

  return { processed: signals.length }
}

/**
 * Get signals for a field
 */
export function getSignals(fieldId: string, signalType?: string) {
  let sql = 'SELECT * FROM signals WHERE field_id = ?'
  const params: any[] = [fieldId]

  if (signalType) {
    sql += ' AND signal_type = ?'
    params.push(signalType)
  }

  sql += ' ORDER BY timestamp DESC LIMIT 1000'

  return db.prepare(sql).all(params)
}

export default {
  processSatelliteSignals,
  processWeatherSignals,
  storeSignals,
  getSignals
}
