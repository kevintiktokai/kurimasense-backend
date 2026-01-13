/**
 * Season Entity Type
 * 
 * Represents a season entity with stable ID, name, start/end dates, and timestamp.
 * A Season is NOT optional - it is a mandatory, first-class entity per V1 contract.
 */

export interface Season {
  id: string
  name: string // e.g. "2024/25 Maize"
  startDate: string // ISO 8601 timestamp
  endDate: string // ISO 8601 timestamp
  createdAt: string // ISO 8601 timestamp
}

export interface CreateSeasonInput {
  name: string
  startDate: string // ISO 8601 timestamp
  endDate: string // ISO 8601 timestamp
}
