import express, { Request, Response, NextFunction } from 'express'
import cors from 'cors'
import satelliteRoutes from './api/satellite.js'
import weatherRoutes from './api/weather.js'
import ingestRoutes from './api/ingest.js'
import signalsRoutes from './api/signals.js'
import { inferenceRouter, fieldsRouter, analysisRunsRouter, contextRouter, provenanceRouter, interpretationRouter, decisionContextRouter } from './api/index.js'

const app = express()
const PORT = process.env.PORT || 3001

// CORS Configuration
// Ensures OPTIONS requests return immediately, allows localhost:3000, and includes required headers
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: false, // No credentials used in API calls
  optionsSuccessStatus: 200 // Some legacy browsers (IE11) choke on 204
}))

// Middleware
app.use(express.json({ limit: '10mb' }))

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// API routes
app.use('/api/ingest', ingestRoutes)
app.use('/api/signals', signalsRoutes)
app.use('/api/inference', inferenceRouter)
app.use('/api/fields', fieldsRouter)
app.use('/api/analysis-runs', analysisRunsRouter)
app.use('/api/context', contextRouter)
app.use('/api/provenance', provenanceRouter)
app.use('/api/interpretation', interpretationRouter)
app.use('/api/decision-context', decisionContextRouter)
app.use('/api/satellite', satelliteRoutes)
app.use('/api/weather', weatherRoutes)

// Error handling
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Unhandled error:', err)
  res.status(500).json({
    success: false,
    message: 'Internal server error',
  })
})

// Start server
app.listen(PORT, () => {
  console.log(`KurimaSense Backend running on port ${PORT}`)
  console.log(`Health check: http://localhost:${PORT}/health`)
  console.log(`Satellite API: http://localhost:${PORT}/api/satellite`)
  console.log(`Weather API: http://localhost:${PORT}/api/weather`)
})
