"""Ingredient lookup endpoint."""

from fastapi import APIRouter, HTTPException
from services.ingredient_service import IngredientService
from schemas import scan as schemas

router = APIRouter()
ingredient_service = IngredientService()


@router.get("/{ingredient_id}", response_model=schemas.IngredientOut, tags=["ingredients"])
def get_ingredient(ingredient_id: str):
    ing = ingredient_service.get(ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ing
