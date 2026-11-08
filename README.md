# FoodLens AI

> An intelligent, multilingual food label scanner and simplifier that helps consumers understand everything printed on food packaging — ingredients, nutrition facts, allergens, additives, marketing claims, and more — explained in simple English and Indian languages.

Built with **React Native + Expo (SDK 58)** for mobile and **FastAPI + SQLite** for the backend. Works on physical Android phones via Expo Go — no Android Studio required.

---

## 🎯 Vision

FoodLens AI is **not just an OCR app**. It's a complete AI-powered food-label understanding system:

- Scan the **front, back, sides, and close-ups** of a package — multiple images per product
- Extract and organize every readable detail (ingredients, nutrition, allergens, dates, FSSAI licence, claims, warnings, customer care, etc.)
- Explain ingredients and nutrition in **simple, transparent language** — no arbitrary health scores, no fear-mongering
- Translate explanations into **Hindi, Marathi, Tamil, Telugu, Kannada, Bengali, Gujarati, Malayalam** (and English)
- Preserve original scientific names, numbers, units, E-numbers, and INS numbers

---

## 📱 Features

| Feature | Status |
|---------|--------|
| Multi-image package scanning (camera + gallery) | ✅ Phase 1 |
| Image review, remove, retake | ✅ Phase 1 |
| Home dashboard with language selector | ✅ Phase 1 |
| Backend API (upload, process, history, translate, compare, ingredient lookup) | ✅ Phase 1 |
| Image preprocessing pipeline (OpenCV) | ✅ Phase 2 |
| OCR integration (PaddleOCR / Tesseract) | ✅ Phase 2 |
| Ingredient extraction & explanations | ✅ Phase 3 |
| Nutrition analysis | ✅ Phase 3 |
| Allergen detection | ✅ Phase 3 |
| AI explanations + multilingual translation | ✅ Phase 4 |
| Complete product report UI | ✅ Phase 4 |
| Scan history + product comparison | ✅ Phase 5 |
| Automated testing | ✅ Phase 6 |

---

## 🏗️ Project Structure

```
foodlens-ai/
├── mobile/                  # Expo React Native app (TypeScript)
│   ├── app/                 # Expo Router screens
│   │   ├── index.tsx        # Home screen
│   │   ├── scan.tsx         # Multi-image scanner
│   │   ├── review.tsx       # Review & submit
│   │   └── report.tsx       # Product report
│   ├── services/api.ts      # Backend API client
│   ├── constants/colors.ts  # Theme + 9-language list
│   ├── types/index.ts       # TypeScript types
│   ├── babel.config.js
│   ├── tsconfig.json
│   ├── app.json
│   └── .env.example
├── backend/                 # FastAPI API (Python)
│   ├── app/main.py
│   ├── app/core/config.py
│   ├── app/api/v1/endpoints/   # scan, translate, compare, ingredients, health
│   ├── services/            # 11 modular services
│   │   ├── image_service.py
│   │   ├── preprocessing_service.py
│   │   ├── ocr_service.py
│   │   ├── text_extraction_service.py
│   │   ├── ingredient_service.py
│   │   ├── nutrition_service.py
│   │   ├── allergen_service.py
│   │   ├── claims_service.py
│   │   ├── translation_service.py
│   │   ├── ai_explanation_service.py
│   │   └── report_service.py
│   ├── models/scan.py       # SQLAlchemy models
│   ├── schemas/scan.py      # Pydantic schemas
│   ├── database/session.py
│   ├── knowledge_base/ingredients.json
│   ├── requirements.txt
│   ├── .env.example
│   └── main.py
├── docs/
│   ├── setup_guide.md
│   ├── architecture.md
│   └── api_documentation.md
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** and **npm**
- **Python 3.10+** and **pip**
- An Android phone with **Expo Go** installed (from the Play Store)

### 1. Clone the repo

```bash
git clone https://github.com/JosephJonathanFernandes/foodlens-ai.git
cd foodlens-ai
```

### 2. Backend

```powershell
cd backend
cp .env.example .env        # edit .env if needed (API keys, CORS, ports)
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify: `http://localhost:8000/api/health` → `{"status":"ok"}`  
Interactive docs: `http://localhost:8000/docs`

### 3. Mobile

```powershell
cd mobile
cp .env.example .env        # set EXPO_PUBLIC_API_BASE_URL for physical phone
npm install
npx expo start
```

Press **`a`** for Android emulator, or scan the QR code with **Expo Go** on your physical phone.

#### Testing on a physical Android phone (no Android Studio)
1. Install **Expo Go** from the Google Play Store.
2. Make sure your phone and computer are on the same Wi-Fi.
3. In `mobile/.env`, set `EXPO_PUBLIC_API_BASE_URL=http://<YOUR_COMPUTER_IP>:8000`
4. Allow port `8000` through your computer's firewall.
5. Scan the QR code from the terminal with Expo Go.

---

## 🧪 Testing

### Backend Tests

The backend includes comprehensive test coverage:

```powershell
cd foodlens-ai/backend

# Service unit tests (no server required)
python tests/test_services.py

# API endpoint tests (requires running server)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
python tests/test_endpoints.py
python tests/test_report_translate.py

# Or run with pytest
pip install pytest
pytest tests/
```

**Test coverage:**
- 81 service unit tests (preprocessing, translation, AI explanation, ingredient, allergen, claims, nutrition, report)
- 37 API endpoint tests (health, upload, process, get, history, translate, ingredient, compare, delete)
- 28 report & translation tests (full report, translate report, sub-resources, error handling)

### Mobile Tests

```powershell
cd foodlens-ai/mobile
npm install
npx jest
```

**Test coverage:**
- Constants (theme colors, language list, sizes)
- API service (health, translate, ingredient lookup, compare with mocked fetch)

---

## ⚙️ Environment Variables

Never hardcode API keys. Create `.env` files from the `.env.example` templates.

**`backend/.env`**
```env
DATABASE_URL=sqlite:///./foodlens.db
OCR_ENGINE=paddleocr
LLM_PROVIDER=mock
LLM_API_KEY=
TRANSLATION_PROVIDER=mock
CORS_ORIGINS=*
SECRET_KEY=replace-with-a-strong-secret-key
```

**`mobile/.env`**
```env
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000
```

Providers marked `mock` run without paid API keys (output is clearly labelled as demo placeholder). Swap in real providers (OpenAI, Gemini, Google Translate, Azure, etc.) by updating `.env`.

---

## 🔌 API Endpoints (Phase 1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/scan/upload` | Upload one or more package images (multipart) |
| `POST` | `/api/scan/process` | Run the full extraction pipeline |
| `GET` | `/api/scan/{scan_id}` | Get a scan and its images |
| `GET` | `/api/scan/history` | List all scans |
| `DELETE` | `/api/scan/{scan_id}` | Delete a scan |
| `POST` | `/api/translate` | Translate text |
| `POST` | `/api/compare` | Compare two scans |
| `GET` | `/api/ingredients/{ingredient_id}` | Ingredient knowledge-base lookup |

---

## 🧠 Design Principles

1. **No information loss.** Raw OCR output is preserved; unclassified text goes to "Other package information."
2. **No invented data.** The pipeline never invents ingredients, nutrition values, or dates. Uncertain interpretations are marked.
3. **Facts vs. explanations.** Label facts are clearly distinguished from AI-generated explanations.
4. **No arbitrary health scores.** Ingredients and nutrition are explained transparently — nothing is automatically labelled "dangerous."
5. **Modular AI.** OCR, identification, explanation, and translation are separate, swappable services.
6. **Multilingual first.** Scientific names, numbers, units, and E/INS numbers are never translated.

---

## 🧪 Testing

```powershell
cd backend
python -m pytest tests/
```

---

## 📄 License

MIT

---

## 🗺️ Roadmap

- **Phase 2:** OpenCV preprocessing + OCR integration + raw text extraction
- **Phase 3:** Ingredient, nutrition, allergen extraction + knowledge base
- **Phase 4:** AI explanations + multilingual translation + full report UI
- **Phase 5:** Scan history UI + product comparison + UI refinement
- **Phase 6:** Automated testing + error handling + docs + performance
