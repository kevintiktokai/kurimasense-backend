/**
 * Vegetation Signal Processing
 * Pure functions for converting raw satellite data into vegetation signals
 */

export interface VegetationSignal {
  fieldId: string
  timestamp: string
  ndvi: {
    mean: number
    min: number
    max: number
    stdDev: number
  }
  dataQuality: 'high' | 'medium' | 'low'
}

/**
 * Convert raw satellite data into a VegetationSignal
 * Pure function - deterministic and side-effect free
 */
export function toVegetationSignal(rawSatelliteData: any): VegetationSignal {
  const cloudCoverage = rawSatelliteData.metadata?.cloudCoverage ?? 100
  
  // Determine data quality based on cloud coverage
  let dataQuality: 'high' | 'medium' | 'low'
  if (cloudCoverage < 10) {
    dataQuality = 'high'
  } else if (cloudCoverage < 30) {
    dataQuality = 'medium'
  } else {
    dataQuality = 'low'
  }

  return {
    fieldId: rawSatelliteData.fieldId,
    timestamp: rawSatelliteData.timestamp,
    ndvi: {
      mean: rawSatelliteData.ndvi.mean,
      min: rawSatelliteData.ndvi.min,
      max: rawSatelliteData.ndvi.max,
      stdDev: rawSatelliteData.ndvi.stdDev,
    },
    dataQuality,
  }
}
