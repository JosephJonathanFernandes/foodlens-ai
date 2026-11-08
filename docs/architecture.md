# Architecture – FoodLens AI

## High-Level Data Flow

```
Mobile (Expo/React Native)  <--HTTP/JSON+multipart-->  Backend (FastAPI)
        │                                                          │
        ▼                                                          ▼
 Camera / Gallery                                          image_service
        │                                                          │
        ▼                                                          ▼
 Review screen                                      preprocessing_service (OpenCV)
        │                                                     │
        ▼                                                     ▼
 Submit → POST /api/scan/upload                   ocr_service (PaddleOCR/Tesseract)
        │                                                     │
        ▼                                                     ▼
 POST /api/scan/process                          text_extraction_service
        │                                                     │
        ▼                                                     ▼
        └──── report_service ◄── ingredient_service ◄──┘
            (nutrition, allergen, claims,
             ai_explanation, translation)
        │
        ▼
   GET /api/scan/{scan_id}  →  Report screen (mobile)
```

## Module Boundaries (kept separate per the master prompt)

- `image_service.py` — save/retrieve/delete uploaded images
- `preprocessing_service.py` — OpenCV pipeline (resize, rotate, contrast, denoise, sharpen, adaptive threshold, quality assessment)
- `ocr_service.py` — modular OCR interface (PaddleOCR default, Tesseract optional)
- `text_extraction_service.py` — OCR normalization, section classification, field extraction
- `ingredient_service.py` — knowledge-base lookup (ingredients.json)
- `nutrition_service.py` — nutrition value parsing
- `allergen_service.py` — allergen detection (declared vs may-contain)
- `claims_service.py` — marketing claim identification
- `translation_service.py` — modular translation provider
- `ai_explanation_service.py` — structured, validated AI explanations
- `report_service.py` — assembles the complete structured report

## Design Principles

- **No information loss**: raw OCR output is preserved; unclassified text goes to "Other package information".
- **No invented data**: the pipeline never invents ingredients, nutrition values, or dates; uncertain interpretations are marked.
- **Facts vs explanations**: label facts are distinguished from AI-generated explanations.
- **Modular AI**: OCR, identification, explanation, and translation are separate, swappable modules.
- **Multilingual first**: English + 8 Indian languages; scientific names, numbers, units, and E/INS numbers are never translated.

## Mobile Architecture

- Expo Router stack navigation (`app/_layout.tsx`).
- Screens: `index` (Home), `scan` (camera/gallery), `review` (submit), `report`.
- `services/api.ts` — typed fetch client for all backend endpoints.
- `constants/colors.ts` — theme (green accent, warm neutral background), language list.
- TypeScript strict mode; `babel-plugin-module-resolver` maps `@/` to the mobile root.
