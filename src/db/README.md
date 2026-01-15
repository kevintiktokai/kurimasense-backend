# Database Layer

Simple SQLite database client with no ORM complexity.

## Features

- **Zero ORM overhead** - Direct SQL queries for maximum performance
- **TypeScript support** - Full type safety where you need it
- **Transaction support** - ACID guarantees for complex operations
- **WAL mode** - Better concurrent access performance
- **Auto-migrations** - Schema automatically created on first run

## Database File

Located at: `backend/data/kurimasense.db`

## Schema

### `satellite_data`
Stores satellite imagery and NDVI data from Sentinel-2, Landsat-8, and Planet.

```sql
field_id          TEXT    - Field identifier
timestamp         TEXT    - ISO 8601 timestamp
source            TEXT    - sentinel-2 | landsat-8 | planet
latitude          REAL    - Field latitude
longitude         REAL    - Field longitude
ndvi_mean         REAL    - Average NDVI value
ndvi_min          REAL    - Minimum NDVI value
ndvi_max          REAL    - Maximum NDVI value
ndvi_std_dev      REAL    - NDVI standard deviation
cloud_coverage    REAL    - Cloud coverage percentage
resolution        REAL    - Image resolution in meters
raw_data          TEXT    - JSON of original payload
created_at        TEXT    - Record creation timestamp
```

### `weather_data`
Stores weather station and forecast data.

```sql
field_id          TEXT    - Field identifier
timestamp         TEXT    - ISO 8601 timestamp
source            TEXT    - weather-station | openweather | noaa | forecast
latitude          REAL    - Station latitude
longitude         REAL    - Station longitude
temperature       REAL    - Temperature in Celsius
humidity          REAL    - Humidity percentage
precipitation     REAL    - Precipitation in mm
wind_speed        REAL    - Wind speed in m/s
wind_direction    REAL    - Wind direction in degrees
pressure          REAL    - Atmospheric pressure in hPa
solar_radiation   REAL    - Solar radiation in W/m²
raw_data          TEXT    - JSON of original payload
created_at        TEXT    - Record creation timestamp
```

### `weather_forecast`
Stores forecast data linked to weather records.

```sql
weather_data_id           INTEGER - Foreign key to weather_data
timestamp                 TEXT    - Forecast timestamp
temperature               REAL    - Forecasted temperature
humidity                  REAL    - Forecasted humidity
precipitation_probability REAL    - Chance of precipitation (%)
precipitation             REAL    - Forecasted precipitation (mm)
```

## Usage

### Import the client

```typescript
import db from './db/client.js'
```

### Execute queries

```typescript
// Select query
const results = db.query('SELECT * FROM satellite_data WHERE field_id = ?', ['field-001'])

// Get single row
const latest = db.queryOne('SELECT * FROM satellite_data ORDER BY timestamp DESC LIMIT 1')

// Insert/Update/Delete
const result = db.run('INSERT INTO satellite_data (...) VALUES (?)', [...])
console.log(result.lastInsertRowid, result.changes)
```

### Transactions

```typescript
const result = db.transaction(() => {
  db.run('INSERT INTO weather_data (...) VALUES (?)', [...])
  db.run('INSERT INTO weather_forecast (...) VALUES (?)', [...])
  return { success: true }
})
```

### Advanced usage

```typescript
// Get raw database connection for prepared statements
const stmt = db.getConnection().prepare('SELECT * FROM satellite_data WHERE field_id = ?')
const results = stmt.all('field-001')
```

## Examples

See [examples.ts](./examples.ts) for complete usage examples including:
- Inserting satellite data
- Inserting weather data with forecasts
- Querying data by field
- Calculating NDVI trends
- Transaction handling

## Switching to PostgreSQL

To migrate to PostgreSQL later:

1. Install `pg` package
2. Replace `better-sqlite3` with `pg` in client.ts
3. Update connection string and query syntax
4. Keep the same interface (`query`, `queryOne`, `run`, `transaction`)

The simple interface makes database switching straightforward.
