import { z } from 'zod'

/**
 * Satellite Data Schema
 * Validates raw satellite imagery and NDVI data
 */
const satellitePayloadSchema = z.object({
  fieldId: z.string().min(1),
  timestamp: z.string().datetime(),
  source: z.enum(['sentinel-2', 'landsat-8', 'planet']),
  coordinates: z.object({
    latitude: z.number().min(-90).max(90),
    longitude: z.number().min(-180).max(180),
  }),
  ndvi: z.object({
    mean: z.number().min(-1).max(1),
    min: z.number().min(-1).max(1),
    max: z.number().min(-1).max(1),
    stdDev: z.number().min(0),
  }),
  metadata: z.object({
    cloudCoverage: z.number().min(0).max(100),
    resolution: z.number().positive(),
    bandData: z.record(z.number()).optional(),
  }).optional(),
  rawData: z.any().optional(), // Preserve raw payload
})

export default satellitePayloadSchema
