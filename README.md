# KurimaSense Backend

Agricultural monitoring backend with raw data ingestion and signal processing.

## Architecture

```
┌─────────────────┐
│  Data Sources   │  Satellite imagery, weather stations, IoT sensors
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  POST /ingest   │  Validate with Zod, store raw JSON
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Raw Records    │  satellite_records, weather_records (JSON blobs)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ POST /signals/  │  Extract metrics, transform, normalize
│     process     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Signals Table  │  Structured time-series data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GET /signals/  │  Query for visualization
│    :fieldId     │
└─────────────────┘
```

## Directory Structure

```
backend/
├── src/
│   ├── api/          API endpoints
│   │   ├── ingest.ts    - POST /api/ingest/{satellite,weather}
│   │   ├── signals.ts   - GET/POST /api/signals
│   │   ├── satellite.js - Legacy (file storage)
│   │   └── weather.js   - Legacy (file storage)
│   ├── db/           Database layer
│   │   └── client.ts    - Simple SQLite client
│   ├── signals/      Signal processing
│   │   └── processor.ts - Transform raw → signals
│   ├── types/        Zod schemas
│   │   ├── satellite.js
│   │   └── weather.js
│   └── index.js      Express server
├── data/             SQLite database files
└── package.json
```

## API Endpoints

### Ingestion
```bash
POST /api/ingest/satellite
POST /api/ingest/weather
```

### Signal Processing
```bash
POST /api/signals/process
GET /api/signals/:fieldId?type=ndvi
```

### Legacy
```bash
POST /api/satellite
GET /api/satellite/:fieldId
POST /api/weather
GET /api/weather/:fieldId
```

## Development

```bash
npm install
npm run dev    # Hot reload with tsx
npm run build  # Compile TypeScript
npm start      # Production
```

Server runs on `http://localhost:3001`

## Data Flow

1. **Ingest** → Validate → Store as JSON
2. **Process** → Extract signals → Store structured
3. **Query** → Retrieve signals for visualization
