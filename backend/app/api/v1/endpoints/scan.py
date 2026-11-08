"""Scan endpoints: upload, process, get, history, delete."""

import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from database.session import SessionLocal, engine, Base
from models import scan as models
from schemas import scan as schemas
from services import image_service, ocr_service, preprocessing_service, text_extraction_service
from services.ingredient_service import IngredientService
from services.nutrition_service import NutritionService
from services.allergen_service import AllergenService
from services.claims_service import ClaimsService
from services.ai_explanation_service import AIExplanationService
from services.report_service import ReportService
from services.translation_service import TranslationService

router = APIRouter()

# Ensure tables exist
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Instantiate services (singletons for MVP)
ingredient_service = IngredientService()
nutrition_service = NutritionService()
allergen_service = AllergenService()
claims_service = ClaimsService()
ai_service = AIExplanationService()
translation_service = TranslationService()
report_service = ReportService()


@router.post("/upload", response_model=schemas.ScanOut, tags=["scan"])
async def upload_scan(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload one or more package images and create a scan session."""
    scan_id = str(uuid.uuid4())
    scan = models.Scan(id=scan_id, status="idle")
    db.add(scan)

    saved_images: List[schemas.ScanImageBase] = []
    for file in files:
        contents = await file.read()
        uri = image_service.save_uploaded_file(contents, file.filename)
        img = models.ScanImage(
            id=str(uuid.uuid4()),
            scan_id=scan_id,
            uri=uri,
            type="other",
        )
        db.add(img)
        saved_images.append(
            schemas.ScanImageBase(
                id=img.id,
                uri=img.uri,
                type=img.type,
                width=img.width,
                height=img.height,
            )
        )

    db.commit()
    db.refresh(scan)
    return schemas.ScanOut(
        id=scan.id,
        product_name=scan.product_name,
        brand=scan.brand,
        status=scan.status,
        created_at=scan.created_at,
        images=saved_images,
    )


@router.post("/process", response_model=schemas.ScanProcessResponse, tags=["scan"])
def process_scan(
    request: schemas.ScanProcessRequest,
    db: Session = Depends(get_db),
):
    """Run the full extraction pipeline on a scan's images."""
    scan = db.query(models.Scan).filter(models.Scan.id == request.scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan.status = "processing"
    db.commit()

    try:
        images = db.query(models.ScanImage).filter(models.ScanImage.scan_id == request.scan_id).all()
        if not images:
            scan.status = "error"
            db.commit()
            raise HTTPException(status_code=400, detail="No images found for this scan")

        all_text_parts: List[str] = []
        all_fields = []

        for img in images:
            # Preprocess
            try:
                _, quality = preprocessing_service.preprocess(img.uri)
            except Exception:
                quality = {}

            # OCR on original (preserve original)
            try:
                ocr_svc = get_ocr_service()
                ocr_results = ocr_svc.extract_text(img.uri)
                full_text = ocr_svc.extract_full_text(img.uri)
            except Exception as e:
                full_text = f"[OCR unavailable: {e}]"
                ocr_results = []

            all_text_parts.append(f"--- Image {img.type} ---\n{full_text}")
            fields = text_extraction_service.TextExtractionService().extract_fields(full_text, source_image=img.uri)
            all_fields.extend(fields)

        combined_text = "\n".join(all_text_parts)

        # Classification
        classified = text_extraction_service.TextExtractionService().classify_sections(combined_text)

        # Build domain objects
        product_name = scan.product_name
        brand = scan.brand
        for f in all_fields:
            if f.name == "product_name" and not product_name:
                product_name = f.value
            if f.name == "brand" and not brand:
                brand = f.value

        # Ingredient explanations
        ingredient_explanations = []
        ingredients_section = [c for c in classified if c.section == "ingredients"]
        ingredients_text = "\n".join(c.text for c in ingredients_section)
        # crude ingredient split
        raw_ingredients = [i.strip() for i in ingredients_text.replace(",", "\n").splitlines() if i.strip()]
        for raw in raw_ingredients[:50]:
            matched = ingredient_service.match_ingredient(raw)
            ingredient_explanations.append(ai_service.explain_ingredient(matched, language=request.language))

        # Nutrition
        nutrition = nutrition_service.parse(combined_text)
        nutrition_explained = {
            k: ai_service.explain_nutrition({k: v}, language=request.language) if v else None
            for k, v in nutrition.items()
        }

        # Allergens
        allergens = allergen_service.detect(combined_text)

        # Claims
        claims = claims_service.detect(combined_text)

        # Translate non-scientific summary text
        summary = report_service._build_summary(product_name, ingredient_explanations, allergens)
        translated_summary = translation_service.translate(summary, request.language)

        # Build report
        report = report_service.build_report(
            scan_id=scan.id,
            product_name=product_name,
            brand=brand,
            ingredients=ingredient_explanations,
            nutrition=nutrition_explained,
            allergens=allergens,
            claims=claims,
            ocr_text=combined_text,
            language=request.language,
        )
        report["summary"] = translated_summary

        # Persist report
        db_report = models.ScanReport(
            id=str(uuid.uuid4()),
            scan_id=scan.id,
            product_overview=json.dumps(report.get("product_overview", {})),
            summary=report.get("summary", ""),
            raw_ocr_text=combined_text,
            language=request.language,
        )
        db.add(db_report)

        scan.product_name = product_name
        scan.brand = brand
        scan.status = "completed"
        db.commit()
        db.refresh(db_report)

        return schemas.ScanProcessResponse(
            scan_id=scan.id,
            status=scan.status,
            report_id=db_report.id,
        )
    except HTTPException:
        raise
    except Exception as e:
        scan.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/history", response_model=List[schemas.ScanHistoryItem], tags=["scan"])
def history(db: Session = Depends(get_db)):
    scans = db.query(models.Scan).order_by(models.Scan.created_at.desc()).all()
    return [
        schemas.ScanHistoryItem(
            id=s.id,
            product_name=s.product_name,
            brand=s.brand,
            status=s.status,
            created_at=s.created_at,
        )
        for s in scans
    ]


@router.get("/{scan_id}", response_model=schemas.ScanOut, tags=["scan"])
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    images = [
        schemas.ScanImageBase(id=i.id, uri=i.uri, type=i.type, width=i.width, height=i.height)
        for i in scan.images
    ]
    return schemas.ScanOut(
        id=scan.id,
        product_name=scan.product_name,
        brand=scan.brand,
        status=scan.status,
        created_at=scan.created_at,
        images=images,
    )


@router.delete("/{scan_id}", tags=["scan"])
def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    # delete associated images from disk
    for img in scan.images:
        import os
        try:
            if os.path.exists(img.uri):
                os.remove(img.uri)
        except OSError:
            pass
    db.delete(scan)
    db.commit()
    return {"detail": "Scan deleted"}
