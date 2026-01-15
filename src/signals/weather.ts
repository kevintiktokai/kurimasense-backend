/**
 * Weather Signal Processing
 * Pure functions for converting raw weather data into weather signals
 */

export interface WeatherSignal {
  fieldId: string
  timestamp: string
  rainfall: number // mm
  temperature: number // Celsius
  dataQuality: 'high' | 'medium' | 'low'
}

/**
 * Convert raw weather data into a WeatherSignal
 * Pure function - deterministic and side-effect free
 */
export function toWeatherSignal(rawWeatherData: any): WeatherSignal {
  return {
    fieldId: rawWeatherData.fieldId,
    timestamp: rawWeatherData.timestamp,
    rainfall: rawWeatherData.current.precipitation,
    temperature: rawWeatherData.current.temperature,
    dataQuality: rawWeatherData.metadata?.dataQuality ?? 'medium',
  }
}
