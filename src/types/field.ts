/**
 * Field Entity Type
 * 
 * Represents a field entity with stable ID, name, optional geometry, and timestamp.
 * Geometry is stored as GeoJSON format (JSON string).
 */

export interface Field {
  id: string
  name: string
  geometry?: string | null // GeoJSON as JSON string
  createdAt: string // ISO 8601 timestamp
}

export interface CreateFieldInput {
  name: string
  geometry?: string | null
}


