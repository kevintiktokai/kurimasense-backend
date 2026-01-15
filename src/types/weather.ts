import { z } from 'zod'

/**
 * Weather Data Schema
 * Validates raw weather station and forecast data
 */
const weatherPayloadSchema = z.object({
  fieldId: z.string().min(1),
  timestamp: z.string().datetime(),
  source: z.enum(['weather-station', 'openweather', 'noaa', 'forecast']),
  coordinates: z.object({
    latitude: z.number().min(-90).max(90),
    longitude: z.number().min(-180).max(180),
  }),
  current: z.object({
    temperature: z.number(), // Celsius
    humidity: z.number().min(0).max(100), // Percentage
    precipitation: z.number().min(0), // mm
    windSpeed: z.number().min(0), // m/s
    windDirection: z.number().min(0).max(360).optional(), // Degrees
    pressure: z.number().positive().optional(), // hPa
    solarRadiation: z.number().min(0).optional(), // W/m²
  }),
  forecast: z.array(z.object({
    timestamp: z.string().datetime(),
    temperature: z.number(),
    humidity: z.number().min(0).max(100),
    precipitationProbability: z.number().min(0).max(100),
    precipitation: z.number().min(0),
  })).optional(),
  metadata: z.object({
    stationId: z.string().optional(),
    dataQuality: z.enum(['high', 'medium', 'low']).optional(),
  }).optional(),
  rawData: z.any().optional(), // Preserve raw payload
})

export default weatherPayloadSchema
