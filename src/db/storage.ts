import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const DATA_DIR = path.join(__dirname, '../data')

/**
 * Simple file-based storage for raw payloads
 * Stores data without modification
 */
class Storage {
  constructor() {
    this.ensureDataDir()
  }

  async ensureDataDir(): Promise<void> {
    try {
      await fs.mkdir(DATA_DIR, { recursive: true })
      await fs.mkdir(path.join(DATA_DIR, 'satellite'), { recursive: true })
      await fs.mkdir(path.join(DATA_DIR, 'weather'), { recursive: true })
    } catch (error: unknown) {
      console.error('Failed to create data directories:', error)
    }
  }

  /**
   * Store satellite data
   */
  async storeSatellite(payload: unknown): Promise<{ id: string; stored: boolean; path: string }> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const payloadObj = payload as { fieldId: string }
    const filename = `satellite-${payloadObj.fieldId}-${timestamp}.json`
    const filepath = path.join(DATA_DIR, 'satellite', filename)
    
    await fs.writeFile(filepath, JSON.stringify(payload, null, 2))
    
    return {
      id: filename,
      stored: true,
      path: filepath,
    }
  }

  /**
   * Store weather data
   */
  async storeWeather(payload: unknown): Promise<{ id: string; stored: boolean; path: string }> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const payloadObj = payload as { fieldId: string }
    const filename = `weather-${payloadObj.fieldId}-${timestamp}.json`
    const filepath = path.join(DATA_DIR, 'weather', filename)
    
    await fs.writeFile(filepath, JSON.stringify(payload, null, 2))
    
    return {
      id: filename,
      stored: true,
      path: filepath,
    }
  }

  /**
   * Retrieve satellite data for a field
   */
  async getSatelliteData(fieldId: string): Promise<unknown[]> {
    const dir = path.join(DATA_DIR, 'satellite')
    const files = await fs.readdir(dir)
    
    const fieldFiles = files.filter(f => f.includes(`satellite-${fieldId}`))
    const data = await Promise.all(
      fieldFiles.map(async (file) => {
        const content = await fs.readFile(path.join(dir, file), 'utf-8')
        return JSON.parse(content)
      })
    )
    
    return data.sort((a: unknown, b: unknown) => {
      const aObj = a as { timestamp: string }
      const bObj = b as { timestamp: string }
      return new Date(bObj.timestamp).getTime() - new Date(aObj.timestamp).getTime()
    })
  }

  /**
   * Retrieve weather data for a field
   */
  async getWeatherData(fieldId: string): Promise<unknown[]> {
    const dir = path.join(DATA_DIR, 'weather')
    const files = await fs.readdir(dir)
    
    const fieldFiles = files.filter(f => f.includes(`weather-${fieldId}`))
    const data = await Promise.all(
      fieldFiles.map(async (file) => {
        const content = await fs.readFile(path.join(dir, file), 'utf-8')
        return JSON.parse(content)
      })
    )
    
    return data.sort((a: unknown, b: unknown) => {
      const aObj = a as { timestamp: string }
      const bObj = b as { timestamp: string }
      return new Date(bObj.timestamp).getTime() - new Date(aObj.timestamp).getTime()
    })
  }
}

export default new Storage()
