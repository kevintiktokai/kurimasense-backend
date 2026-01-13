/**
 * Database Client Usage Examples
 * 
 * This file demonstrates how to use the simple SQLite database client
 * No ORM - just raw SQL queries for maximum control and performance
 */

import db from './client.js'

// ============================================
// EXAMPLE 1: Insert satellite data
// ============================================
export function insertSatelliteData(payload: any) {
  const result = db.run(
    `INSERT INTO satellite_data (
      field_id, timestamp, source, latitude, longitude,
      ndvi_mean, ndvi_min, ndvi_max, ndvi_std_dev,
      cloud_coverage, resolution, raw_data
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(field_id, timestamp, source) DO UPDATE SET
      latitude = excluded.latitude,
      longitude = excluded.longitude,
      ndvi_mean = excluded.ndvi_mean,
      ndvi_min = excluded.ndvi_min,
      ndvi_max = excluded.ndvi_max,
      ndvi_std_dev = excluded.ndvi_std_dev,
      cloud_coverage = excluded.cloud_coverage,
      resolution = excluded.resolution,
      raw_data = excluded.raw_data
    `,
    [
      payload.fieldId,
      payload.timestamp,
      payload.source,
      payload.coordinates.latitude,
      payload.coordinates.longitude,
      payload.ndvi.mean,
      payload.ndvi.min,
      payload.ndvi.max,
      payload.ndvi.stdDev,
      payload.metadata?.cloudCoverage || null,
      payload.metadata?.resolution || null,
      JSON.stringify(payload.rawData || {}),
    ]
  )

  return { id: result.lastInsertRowid, changes: result.changes }
}

// ============================================
// EXAMPLE 2: Query satellite data for a field
// ============================================
export function getSatelliteDataByField(fieldId: string, limit = 100) {
  return db.query(
    `SELECT 
      id, field_id, timestamp, source,
      latitude, longitude,
      ndvi_mean, ndvi_min, ndvi_max, ndvi_std_dev,
      cloud_coverage, resolution,
      created_at
    FROM satellite_data
    WHERE field_id = ?
    ORDER BY timestamp DESC
    LIMIT ?`,
    [fieldId, limit]
  )
}

// ============================================
// EXAMPLE 3: Insert weather data with transaction
// ============================================
export function insertWeatherDataWithForecast(payload: any) {
  return db.transaction(() => {
    // Insert main weather record
    const weatherResult = db.run(
      `INSERT INTO weather_data (
        field_id, timestamp, source, latitude, longitude,
        temperature, humidity, precipitation, wind_speed,
        wind_direction, pressure, solar_radiation, raw_data
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(field_id, timestamp, source) DO UPDATE SET
        latitude = excluded.latitude,
        longitude = excluded.longitude,
        temperature = excluded.temperature,
        humidity = excluded.humidity,
        precipitation = excluded.precipitation,
        wind_speed = excluded.wind_speed,
        wind_direction = excluded.wind_direction,
        pressure = excluded.pressure,
        solar_radiation = excluded.solar_radiation,
        raw_data = excluded.raw_data
      `,
      [
        payload.fieldId,
        payload.timestamp,
        payload.source,
        payload.coordinates.latitude,
        payload.coordinates.longitude,
        payload.current.temperature,
        payload.current.humidity,
        payload.current.precipitation,
        payload.current.windSpeed,
        payload.current.windDirection || null,
        payload.current.pressure || null,
        payload.current.solarRadiation || null,
        JSON.stringify(payload.rawData || {}),
      ]
    )

    const weatherId = weatherResult.lastInsertRowid

    // Insert forecast records if present
    if (payload.forecast && payload.forecast.length > 0) {
      const insertForecast = db.getConnection().prepare(
        `INSERT INTO weather_forecast (
          weather_data_id, timestamp, temperature, humidity,
          precipitation_probability, precipitation
        ) VALUES (?, ?, ?, ?, ?, ?)`
      )

      for (const forecast of payload.forecast) {
        insertForecast.run([
          weatherId,
          forecast.timestamp,
          forecast.temperature,
          forecast.humidity,
          forecast.precipitationProbability,
          forecast.precipitation,
        ])
      }
    }

    return { id: weatherId, changes: weatherResult.changes }
  })
}

// ============================================
// EXAMPLE 4: Get weather data with forecasts
// ============================================
export function getWeatherDataByField(fieldId: string, limit = 100) {
  const weatherData = db.query(
    `SELECT 
      id, field_id, timestamp, source,
      latitude, longitude,
      temperature, humidity, precipitation,
      wind_speed, wind_direction, pressure, solar_radiation,
      created_at
    FROM weather_data
    WHERE field_id = ?
    ORDER BY timestamp DESC
    LIMIT ?`,
    [fieldId, limit]
  )

  // Fetch forecasts for each weather record
  return weatherData.map((weather: any) => {
    const forecasts = db.query(
      `SELECT timestamp, temperature, humidity,
       precipitation_probability, precipitation
       FROM weather_forecast
       WHERE weather_data_id = ?
       ORDER BY timestamp ASC`,
      [weather.id]
    )

    return { ...weather, forecasts }
  })
}

// ============================================
// EXAMPLE 5: Get latest NDVI for a field
// ============================================
export function getLatestNDVI(fieldId: string) {
  return db.queryOne(
    `SELECT ndvi_mean, ndvi_min, ndvi_max, timestamp
     FROM satellite_data
     WHERE field_id = ?
     ORDER BY timestamp DESC
     LIMIT 1`,
    [fieldId]
  )
}

// ============================================
// EXAMPLE 6: Calculate NDVI trends
// ============================================
export function getNDVITrend(fieldId: string, days = 30) {
  return db.query(
    `SELECT 
      DATE(timestamp) as date,
      AVG(ndvi_mean) as avg_ndvi,
      MIN(ndvi_min) as min_ndvi,
      MAX(ndvi_max) as max_ndvi,
      COUNT(*) as sample_count
    FROM satellite_data
    WHERE field_id = ?
      AND timestamp >= datetime('now', '-' || ? || ' days')
    GROUP BY DATE(timestamp)
    ORDER BY date ASC`,
    [fieldId, days]
  )
}

export default db
