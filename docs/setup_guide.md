# Setup Guide – FoodLens AI

## Overview

FoodLens AI is a monorepo with a React Native/Expo mobile app and a FastAPI backend. This guide walks you through getting both running and testing on a physical Android phone using Expo Go (no Android Studio required).

## Prerequisites

- Node.js and npm
- Python 3.10+ and pip
- An Android phone with the **Expo Go** app installed

## Step 1 – Backend

```powershell
cd foodlens-ai/backend
cp .env.example .env
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify: open `http://localhost:8000/api/health` → should return `{"status":"ok"}`.  
Interactive API docs: `http://localhost:8000/docs`.

## Step 2 – Mobile

```powershell
cd foodlens-ai/mobile
cp .env.example .env   # set EXPO_PUBLIC_API_BASE_URL if using a physical phone
npm install
npx expo start
```

Press `a` in the terminal to run on an Android device/emulator, or scan the QR code with Expo Go on your physical phone.

### Physical phone (no Android Studio)

- Install Expo Go from the Play Store.
- Phone and computer must be on the same Wi-Fi.
- Set `EXPO_PUBLIC_API_BASE_URL=http://<YOUR_IP>:8000` in `mobile/.env`.
- Allow port 8000 through your computer's firewall.

## Step 3 – Test the flow

1. Home screen → tap **Scan Food Label**.
2. Capture front / back / side / close-up images, or **Upload Package Image** from the gallery.
3. Review images; remove any you don't want.
4. Tap **Submit** → images upload to the backend and are processed.
5. The report screen opens with the processed scan.

## Backend Endpoints (Phase 1)

- `GET /api/health`
- `POST /api/scan/upload` (multipart, one or more images)
- `POST /api/scan/process` (runs the extraction pipeline)
- `GET /api/scan/{scan_id}`
- `GET /api/scan/history`
- `DELETE /api/scan/{scan_id}`
- `POST /api/translate`
- `POST /api/compare`
- `GET /api/ingredients/{ingredient_id}`

## Notes

- API keys/secrets belong in `.env`, never in source control.
- `paddleocr`/`paddlepaddle` is optional — install separately if a wheel exists for your Python version; otherwise the OCR service degrades gracefully.
- The backend stores scans and images in `./foodlens.db` and `./uploads/` (created automatically).
