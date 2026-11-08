# API Documentation – FoodLens AI

Base URL: `http://<host>:8000`  
Interactive docs (Swagger UI): `http://<host>:8000/docs`  
Alternative spec: `http://<host>:8000/openapi.json`

## Authentication

None in Phase 1 (MVP). Add API keys / JWT in a later phase.

## Endpoints

### Health
`GET /api/health`

Returns `{"status": "ok", "service": "foodlens-ai"}`.

### Scan Upload
`POST /api/scan/upload`

Multipart form. Field `files` (repeatable, one or more images).

**Response:** `ScanOut` — scan id, status, created_at, and list of `ScanImage` (id, uri, type, width, height).

### Scan Process
`POST /api/scan/process`

Body: `{ "scan_id": string, "language": "en" }`

Runs the full pipeline: preprocess → OCR → text extraction → ingredient/nutrition/allergen/claims → report.

**Response:** `{ "scan_id": string, "status": "completed", "report_id": string }`.

### Get Scan
`GET /api/scan/{scan_id}`

**Response:** `ScanOut` with images and status.

### History
`GET /api/scan/history`

**Response:** List of `ScanHistoryItem` (id, product_name, brand, status, created_at), newest first.

### Delete Scan
`DELETE /api/scan/{scan_id}`

Removes the scan, its report, and its image files from disk.

### Translate
`POST /api/translate`

Body: `{ "text": string, "target_language": string, "source_language": "en" }`

**Response:** `{ "translated_text": string, "target_language": string, "source_language": string }`.

### Ingredient Lookup
`GET /api/ingredients/{ingredient_id}`

**Response:** Ingredient object (name, simple_name, function, why_used, is_additive, regulatory_info, considerations, scientific_terminology, alternative_names, e_number, ins_number).

### Compare
`POST /api/compare`

Body: `{ "scan_id_a": string, "scan_id_b": string }`

**Response:** `{ "scan_id_a": ..., "scan_id_b": ..., "comparison": {...} }`.

## Pydantic Schemas

Key models: `ScanOut`, `ScanImageBase`, `ScanHistoryItem`, `TranslateRequest/Response`, `CompareRequest/Response`, `IngredientOut`, `ErrorResponse`.

## Error Handling

Errors return JSON bodies like `{"message": "...", "status_code": 404}` with appropriate HTTP status codes (400, 404, 500).

## Providers (configurable via backend/.env)

- `OCR_ENGINE`: `paddleocr` | `tesseract`
- `LLM_PROVIDER`: `openai` | `anthropic` | `gemini` | `mock`
- `TRANSLATION_PROVIDER`: `google` | `azure` | `libre` | `mock`

`mock` is the default so the MVP runs without paid API keys. Translation output is clearly labelled as a demo placeholder.
