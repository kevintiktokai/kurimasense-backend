# V1 Audit: Analysis Runs, Inference, and Inference Response Usage

**Date:** 2024  
**Purpose:** Identify all backend routes where `analysis_runs`, `inference`, and `inference_response` are used as "final output" (returned to frontend as primary result)

**V1 Requirement:** Insights are the primary V1 output. `analysis_runs`, `inference`, and `inference_response` are **NON-AUTHORITATIVE** and must NOT be required for V1 functionality.

---

## Summary

**Total Routes Using These Entities as Final Output: 4**

All identified routes are **NON-REQUIRED** for V1. They can remain in the codebase but should not be dependencies for the V1 Insight Engine.

---

## Detailed Audit Results

### 1. GET /api/inference
**File:** `src/api/inference.ts`  
**Lines:** 60-103  
**Status:** ⚠️ **RETURNS INFERENCE_RESPONSE AS FINAL OUTPUT**

**Behavior:**
- Computes inference on-the-fly (not stored)
- Returns `InferenceResponse` directly as JSON response
- Uses `assembleInferenceInput()`, `inferCropHealthStatus()`, `emitInferenceCategory()`, `assembleInference()`
- Transforms internal `Inference` to canonical `InferenceResponse`

**V1 Impact:** 
- ❌ **NOT REQUIRED** for V1
- This endpoint computes and returns inference directly
- V1 should use `/api/insights` instead (to be implemented)

**Dependencies:**
- `inference/input.ts` - `assembleInferenceInput()`
- `inference/status.ts` - `inferCropHealthStatus()`
- `inference/categories.ts` - `emitInferenceCategory()`
- `inference/assemble.ts` - `assembleInference()`
- `types/api.ts` - `InferenceResponse` interface
- `types/contracts.ts` - `inferenceResponseSchema`

---

### 2. POST /api/analysis-runs
**File:** `src/api/analysisRuns.ts`  
**Lines:** 86-271  
**Status:** ⚠️ **RETURNS ANALYSIS_RUN AS FINAL OUTPUT**

**Behavior:**
- Creates new `AnalysisRun` record
- Computes inference deterministically
- Stores `AnalysisRun` with embedded `inference_response` (JSON)
- Returns stored `AnalysisRun` object (which contains `inference` field)

**Response Structure:**
```json
{
  "success": true,
  "data": {
    "id": "...",
    "fieldId": "...",
    "windowStart": "...",
    "windowEnd": "...",
    "inference": { ... InferenceResponse ... },
    "createdAt": "..."
  }
}
```

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1
- This endpoint creates and returns `AnalysisRun` (which embeds `inference_response`)
- V1 should use `/api/insights` instead (to be implemented)

**Dependencies:**
- `db/client.ts` - `insertAnalysisRun()`, `getAnalysisRunById()`
- `db/schema.ts` - `ANALYSIS_RUNS_TABLE`
- `types/analysisRun.ts` - `AnalysisRun`, `CreateAnalysisRunInput`
- All inference computation functions (same as `/api/inference`)

---

### 3. GET /api/analysis-runs/:id
**File:** `src/api/analysisRuns.ts`  
**Lines:** 279-323  
**Status:** ⚠️ **RETURNS ANALYSIS_RUN AS FINAL OUTPUT**

**Behavior:**
- Retrieves stored `AnalysisRun` by ID
- Returns `AnalysisRun` object (which contains `inference` field)
- No recomputation - returns stored data only

**Response Structure:**
```json
{
  "success": true,
  "data": {
    "id": "...",
    "fieldId": "...",
    "windowStart": "...",
    "windowEnd": "...",
    "inference": { ... InferenceResponse ... },
    "createdAt": "..."
  }
}
```

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1
- This endpoint returns stored `AnalysisRun` (which embeds `inference_response`)
- V1 should use `/api/insights?fieldId=X&seasonId=Y` instead (to be implemented)

**Dependencies:**
- `db/client.ts` - `getAnalysisRunById()`
- `types/analysisRun.ts` - `AnalysisRun` interface

---

### 4. GET /api/fields/:id/analysis-runs
**File:** `src/api/fields.ts`  
**Lines:** 40-62  
**Status:** ⚠️ **RETURNS ARRAY OF ANALYSIS_RUNS AS FINAL OUTPUT**

**Behavior:**
- Retrieves all `AnalysisRun` records for a specific field
- Returns array of `AnalysisRun` objects (each contains `inference` field)
- Ordered by `created_at DESC`

**Response Structure:**
```json
{
  "success": true,
  "data": [
    {
      "id": "...",
      "fieldId": "...",
      "windowStart": "...",
      "windowEnd": "...",
      "inference": { ... InferenceResponse ... },
      "createdAt": "..."
    },
    ...
  ]
}
```

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1
- This endpoint returns array of `AnalysisRun` objects (each embeds `inference_response`)
- V1 should use `/api/insights?fieldId=X&seasonId=Y` instead (to be implemented)

**Dependencies:**
- `db/client.ts` - `getAnalysisRunsByFieldId()`
- `types/analysisRun.ts` - `AnalysisRun` interface

---

## Routes That Use These Entities But Don't Return Them as Final Output

These routes use `analysis_runs` or `inference_response` internally but return different data structures. They are **NOT** marked as problematic for V1, but are listed for completeness.

### 5. POST /api/decision-context/generate
**File:** `src/api/decisionContext.ts`  
**Lines:** 122-160  
**Status:** ✅ **USES BUT DOES NOT RETURN INFERENCE_RESPONSE**

**Behavior:**
- Takes `analysisRunId` as input
- Retrieves `AnalysisRun` to access `run.inference`
- Generates decision contexts based on inference data
- Returns decision contexts (not the inference itself)

**V1 Impact:**
- ⚠️ **MAY NOT BE REQUIRED** for V1 (depends on product requirements)
- Uses `inference_response` but returns different structure
- If V1 doesn't need decision contexts, this can be ignored

---

### 6. POST /api/interpretation/assist
**File:** `src/api/interpretation.ts`  
**Lines:** 149-206  
**Status:** ✅ **USES BUT DOES NOT RETURN INFERENCE_RESPONSE**

**Behavior:**
- Takes `analysisRunId` and `query` as input
- Retrieves `AnalysisRun` to access `run.inference`
- Generates interpretation response based on inference data
- Returns interpretation text (not the inference itself)

**V1 Impact:**
- ⚠️ **MAY NOT BE REQUIRED** for V1 (depends on product requirements)
- Uses `inference_response` but returns different structure
- If V1 doesn't need interpretation assistance, this can be ignored

---

### 7. GET /api/provenance/:analysisRunId
**File:** `src/api/provenance.ts`  
**Lines:** 32-55  
**Status:** ✅ **NOT FULLY IMPLEMENTED**

**Behavior:**
- Currently returns 501 (Not Implemented)
- Would use `AnalysisRun` to generate provenance
- Would return provenance data (not the inference itself)

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1 (not implemented)

---

### 8. POST /api/provenance/generate
**File:** `src/api/provenance.ts`  
**Lines:** 68-129  
**Status:** ✅ **USES BUT DOES NOT RETURN INFERENCE_RESPONSE**

**Behavior:**
- Takes `fieldId`, `windowStart`, `windowEnd` as input
- Reconstructs inference state deterministically
- Generates provenance data
- Returns provenance (not the inference itself)

**V1 Impact:**
- ⚠️ **MAY NOT BE REQUIRED** for V1 (depends on product requirements)
- Uses inference computation but returns different structure
- If V1 doesn't need provenance, this can be ignored

---

## Database Schema Dependencies

### analysis_runs Table
**File:** `src/db/schema.ts`  
**Lines:** 43-52

**Structure:**
```sql
CREATE TABLE IF NOT EXISTS analysis_runs (
  id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL,
  window_start TEXT NOT NULL,
  window_end TEXT NOT NULL,
  inference_response TEXT NOT NULL,  -- JSON blob
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
```

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1
- This table stores `AnalysisRun` records with embedded `inference_response`
- V1 should use `insights` table instead (to be created)

---

## Database Functions

### insertAnalysisRun()
**File:** `src/db/client.ts`  
**Lines:** 308-339

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1
- Used by `POST /api/analysis-runs`

---

### getAnalysisRunById()
**File:** `src/db/client.ts`  
**Lines:** 344-356

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1
- Used by:
  - `GET /api/analysis-runs/:id`
  - `POST /api/decision-context/generate`
  - `POST /api/interpretation/assist`

---

### getAnalysisRunsByFieldId()
**File:** `src/db/client.ts`  
**Lines:** 361-376

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1
- Used by `GET /api/fields/:id/analysis-runs`

---

## Type Definitions

### InferenceResponse
**File:** `src/types/api.ts`  
**Lines:** 8-22

**V1 Impact:**
- ⚠️ **MAY BE USED** for V1 (if insights use similar structure)
- Currently used by `analysis_runs` and `/api/inference`
- V1 insights may have different structure

---

### AnalysisRun
**File:** `src/types/analysisRun.ts`  
**Lines:** 21-28

**V1 Impact:**
- ❌ **NOT REQUIRED** for V1
- This type represents the `analysis_runs` table structure
- V1 should use `Insight` type instead (to be created)

---

## Inference Computation Functions

These functions are used to compute inference, but they are **NOT** the final output themselves. They are building blocks.

### assembleInferenceInput()
**File:** `src/inference/input.ts`

**V1 Impact:**
- ✅ **MAY BE USED** for V1
- This function assembles input data from signals
- V1 insight generation may use similar logic

---

### inferCropHealthStatus()
**File:** `src/inference/status.ts`

**V1 Impact:**
- ⚠️ **MAY BE USED** for V1
- This function determines crop health status
- V1 insights may use similar logic but with different output structure

---

### emitInferenceCategory()
**File:** `src/inference/categories.ts`

**V1 Impact:**
- ⚠️ **MAY BE USED** for V1
- This function emits inference categories
- V1 insights may use similar logic but with different output structure

---

### assembleInference()
**File:** `src/inference/assemble.ts`

**V1 Impact:**
- ⚠️ **MAY BE USED** for V1
- This function assembles final inference object
- V1 insights may use similar logic but with different output structure

---

## Key Findings

### ✅ Confirmed: These Are NOT Required for V1

1. **GET /api/inference** - Returns `InferenceResponse` directly (computed, not stored)
2. **POST /api/analysis-runs** - Creates and returns `AnalysisRun` (embeds `inference_response`)
3. **GET /api/analysis-runs/:id** - Returns stored `AnalysisRun` (embeds `inference_response`)
4. **GET /api/fields/:id/analysis-runs** - Returns array of `AnalysisRun` (each embeds `inference_response`)

### ⚠️ Secondary Routes (Use But Don't Return)

5. **POST /api/decision-context/generate** - Uses `inference_response` but returns decision contexts
6. **POST /api/interpretation/assist** - Uses `inference_response` but returns interpretation
7. **POST /api/provenance/generate** - Uses inference computation but returns provenance

### 📋 Database & Types

- `analysis_runs` table - NOT required for V1
- `AnalysisRun` type - NOT required for V1
- `InferenceResponse` type - MAY be used (if insights use similar structure)
- Inference computation functions - MAY be used (as building blocks for insight generation)

---

## Recommendations

1. **DO NOT DELETE** any of these routes or tables yet
2. **DO NOT** make them dependencies for V1 Insight Engine
3. **DO** implement `/api/insights` endpoint as the authoritative V1 output
4. **DO** ensure V1 insights are stored in `insights` table (to be created)
5. **DO** ensure V1 insights use `field_id` and `season_id` (not `window_start`/`window_end`)
6. **DO** ensure V1 insights have UNIQUE constraint on `(field_id, season_id)`

---

## Next Steps

1. ✅ **COMPLETED:** Audit all routes using `analysis_runs`, `inference`, `inference_response`
2. ⏭️ **NEXT:** Implement V1 Insight Engine with `/api/insights` endpoint
3. ⏭️ **NEXT:** Create `insights` table with UNIQUE(field_id, season_id) constraint
4. ⏭️ **NEXT:** Implement deterministic insight generation logic
5. ⏭️ **NEXT:** Ensure insights are stored once and returned on subsequent requests

---

**End of Audit**
