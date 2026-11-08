"""API router aggregation for v1."""

from fastapi import APIRouter

from app.api.v1.endpoints import scan, translate, compare, ingredients, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
api_router.include_router(translate.router, prefix="/translate", tags=["translate"])
api_router.include_router(compare.router, prefix="/compare", tags=["compare"])
api_router.include_router(ingredients.router, prefix="/ingredients", tags=["ingredients"])
