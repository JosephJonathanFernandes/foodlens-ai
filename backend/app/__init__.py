"""FoodLens AI backend package."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings

app = FastAPI(
    title="FoodLens AI",
    description="Intelligent Food Label Scanner & Simplifier API",
    version="0.1.0",
)

# CORS for Expo mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/api/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "foodlens-ai"}
