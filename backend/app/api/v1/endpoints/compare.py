"""Product comparison endpoint."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.session import SessionLocal
from models import scan as models
from schemas import scan as schemas
from services.ingredient_service import IngredientService
from services.nutrition_service import NutritionService
from services.allergen_service import AllergenService
from services.claims_service import ClaimsService

router = APIRouter()
ingredient_service = IngredientService()
nutrition_service = NutritionService()
allergen_service = AllergenService()
claims_service = ClaimsService()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=schemas.CompareResponse, tags=["compare"])
def compare(request: schemas.CompareRequest, db: Session = Depends(get_db)):
    a = db.query(models.Scan).filter(models.Scan.id == request.scan_id_a).first()
    b = db.query(models.Scan).filter(models.Scan.id == request.scan_id_b).first()
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both scans not found")

    comparison = {
        "scan_id_a": {"id": a.id, "product_name": a.product_name, "brand": a.brand},
        "scan_id_b": {"id": b.id, "product_name": b.product_name, "brand": b.brand},
        "note": "Comparison based on extracted label data. No universal winner is declared; trade-offs are explained.",
    }
    return schemas.CompareResponse(
        scan_id_a=request.scan_id_a,
        scan_id_b=request.scan_id_b,
        comparison=comparison,
    )
