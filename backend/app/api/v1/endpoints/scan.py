"""Scan endpoints: upload, process, get, history, delete."""

import json
import os
import tempfile
import uuid
from typing import List, Optional

import cv2

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from database.session import SessionLocal, engine, Base, ensure_schema
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

# Ensure tables exist (create + simple migration)
ensure_schema()
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
            # Preprocess and assess quality
            try:
                processed_image, quality = preprocessing_service.preprocess(img.uri)
                img.set_quality(quality)
            except Exception:
                quality = {}
                processed_image = None

            # Determine which image to OCR: use preprocessed if original is blurry
            is_blurry = quality.get("is_blurry", False) if quality else False
            ocr_source = processed_image if (is_blurry and processed_image is not None) else img.uri
            ocr_source_path = None
            if processed_image is not None and is_blurry:
                # Save preprocessed image to a temp file for OCR
                tmp_dir = tempfile.mkdtemp()
                ocr_source_path = os.path.join(tmp_dir, f"preprocessed_{img.id}.jpg")
                try:
                    cv2.imwrite(ocr_source_path, processed_image)
                except Exception:
                    ocr_source_path = img.uri
            else:
                ocr_source_path = img.uri

            # OCR
            try:
                ocr_svc = get_ocr_service()
                ocr_results = ocr_svc.extract_text(ocr_source_path)
                full_text = ocr_svc.extract_full_text(ocr_source_path)
                # Clean up temp preprocessed file
                if ocr_source_path and ocr_source_path != img.uri and os.path.exists(ocr_source_path):
                    try:
                        os.remove(ocr_source_path)
                    except Exception:
                        pass
            except Exception as e:
                full_text = f"[OCR unavailable: {e}]"
                ocr_results = []

            # Store per-image OCR results with confidence
            for r in ocr_results:
                db_ocr = models.OcrResult(
                    id=str(uuid.uuid4()),
                    image_id=img.id,
                    text=r.text,
                    confidence=int(r.confidence * 100) if r.confidence is not None else None,
                    box_json=json.dumps(list(r.box)) if r.box else None,
                )
                db.add(db_ocr)

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

        # Ingredient extraction
        ingredient_explanations = []
        ingredients_section = [c for c in classified if c.section == "ingredients"]
        ingredients_text = "\n".join(c.text for c in ingredients_section)
        # crude ingredient split - handle commas and newlines
        raw_ingredients = [i.strip() for i in ingredients_text.replace(",", "\n").splitlines() if i.strip()]

        extracted_ingredients = []
        for raw in raw_ingredients[:50]:
            match = ingredient_service.match_ingredient(raw)
            if match:
                kb_ing, confidence = match
                ingredient_explanations.append(
                    ai_service.explain_ingredient(kb_ing, language=request.language)
                )
                extracted_ingredients.append({
                    "raw_name": raw,
                    "matched": True,
                    "confidence": round(confidence * 100),
                    "kb_id": kb_ing["id"],
                    "source_image": None,  # could be enhanced to track which image
                })
            else:
                ingredient_explanations.append(
                    ai_service.explain_ingredient(None, language=request.language)
                )
                extracted_ingredients.append({
                    "raw_name": raw,
                    "matched": False,
                    "confidence": None,
                    "kb_id": None,
                    "source_image": None,
                })

        # Persist extracted ingredients
        for ei in extracted_ingredients:
            db_ing = models.ExtractedIngredient(
                id=str(uuid.uuid4()),
                scan_id=scan.id,
                raw_name=ei["raw_name"],
                matched=ei["matched"],
                confidence=ei["confidence"],
                kb_id=ei["kb_id"],
                source_image_id=None,
            )
            db.add(db_ing)

        # Nutrition extraction
        nutrition = nutrition_service.parse(combined_text)
        extracted_nutrition = []
        for nutrient, data in nutrition.items():
            if data is None:
                continue
            extracted_nutrition.append({
                "nutrient": nutrient,
                "value": data.get("value"),
                "unit": data.get("unit"),
                "basis": data.get("basis"),
                "raw_line": data.get("raw_line"),
            })
            db_nut = models.ExtractedNutrition(
                id=str(uuid.uuid4()),
                scan_id=scan.id,
                nutrient=nutrient,
                value=data.get("value"),
                unit=data.get("unit"),
                basis=data.get("basis"),
                raw_line=data.get("raw_line"),
            )
            db.add(db_nut)

        nutrition_explained = {
            k: ai_service.explain_nutrition({k: v}, language=request.language) if v else None
            for k, v in nutrition.items()
        }

        # Allergen extraction
        allergens = allergen_service.detect(combined_text)
        extracted_allergens = []
        for allergen, data in allergens.items():
            extracted_allergens.append({
                "allergen": allergen,
                "declared": data.get("declared", False),
                "warning_type": data.get("warning_type"),
                "matched_keywords": data.get("matched_keywords", []),
            })
            db_all = models.ExtractedAllergen(
                id=str(uuid.uuid4()),
                scan_id=scan.id,
                allergen=allergen,
                declared=data.get("declared", False),
                warning_type=data.get("warning_type"),
                matched_keywords=json.dumps(data.get("matched_keywords", [])),
            )
            db.add(db_all)

        # Claims extraction
        claims = claims_service.detect(combined_text)
        extracted_claims = []
        for claim in claims:
            extracted_claims.append({
                "claim": claim["claim"],
                "meaning": claim["meaning"],
                "caveat": claim["caveat"],
                "verified": claim.get("verified", False),
            })
            db_claim = models.ExtractedClaim(
                id=str(uuid.uuid4()),
                scan_id=scan.id,
                claim=claim["claim"],
                meaning=claim["meaning"],
                caveat=claim["caveat"],
                verified=claim.get("verified", False),
            )
            db.add(db_claim)

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
        schemas.ScanImageBase(
            id=i.id,
            uri=i.uri,
            type=i.type,
            width=i.width,
            height=i.height,
            quality=i.get_quality(),
            ocr_results=[
                schemas.OcrResultBase(
                    id=r.id,
                    text=r.text,
                    confidence=r.confidence,
                    box=r.get_box(),
                )
                for r in i.ocr_results
            ],
        )
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


@router.get("/{scan_id}/ocr", response_model=List[schemas.ScanImageBase], tags=["scan"])
def get_ocr_results(scan_id: str, db: Session = Depends(get_db)):
    """Return per-image OCR results with confidence and quality metrics."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return [
        schemas.ScanImageBase(
            id=i.id,
            uri=i.uri,
            type=i.type,
            width=i.width,
            height=i.height,
            quality=i.get_quality(),
            ocr_results=[
                schemas.OcrResultBase(
                    id=r.id,
                    text=r.text,
                    confidence=r.confidence,
                    box=r.get_box(),
                )
                for r in i.ocr_results
            ],
        )
        for i in scan.images
    ]


@router.delete("/{scan_id}", tags=["scan"])
def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    # delete associated images from disk
    for img in scan.images:
        try:
            if os.path.exists(img.uri):
                os.remove(img.uri)
        except OSError:
            pass
    db.delete(scan)
    db.commit()
    return {"detail": "Scan deleted"}


@router.get("/{scan_id}/ingredients", response_model=List[schemas.ExtractedIngredientOut], tags=["scan"])
def get_scan_ingredients(scan_id: str, db: Session = Depends(get_db)):
    """Return extracted ingredients for a scan with knowledge-base matches."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    results = []
    for ei in db.query(models.ExtractedIngredient).filter(models.ExtractedIngredient.scan_id == scan_id).all():
        kb_ing = ingredient_service.get(ei.kb_id) if ei.kb_id else None
        results.append(
            schemas.ExtractedIngredientOut(
                raw_name=ei.raw_name,
                matched=ei.matched,
                confidence=ei.confidence,
                kb_id=ei.kb_id,
                ingredient=schemas.IngredientOut.model_validate(kb_ing) if kb_ing else None,
            )
        )
    return results


@router.get("/{scan_id}/nutrition", response_model=List[schemas.ExtractedNutritionOut], tags=["scan"])
def get_scan_nutrition(scan_id: str, db: Session = Depends(get_db)):
    """Return extracted nutrition values for a scan."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return [
        schemas.ExtractedNutritionOut(
            nutrient=n.nutrient,
            value=n.value,
            unit=n.unit,
            basis=n.basis,
            raw_line=n.raw_line,
            normalized_value=n.normalized_value,
        )
        for n in db.query(models.ExtractedNutrition).filter(models.ExtractedNutrition.scan_id == scan_id).all()
    ]


@router.get("/{scan_id}/allergens", response_model=List[schemas.ExtractedAllergenOut], tags=["scan"])
def get_scan_allergens(scan_id: str, db: Session = Depends(get_db)):
    """Return detected allergens for a scan."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return [
        schemas.ExtractedAllergenOut(
            allergen=a.allergen,
            declared=a.declared,
            warning_type=a.warning_type,
            matched_keywords=json.loads(a.matched_keywords) if a.matched_keywords else None,
        )
        for a in db.query(models.ExtractedAllergen).filter(models.ExtractedAllergen.scan_id == scan_id).all()
    ]


@router.get("/{scan_id}/claims", response_model=List[schemas.ExtractedClaimOut], tags=["scan"])
def get_scan_claims(scan_id: str, db: Session = Depends(get_db)):
    """Return detected marketing claims for a scan."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return [
        schemas.ExtractedClaimOut(
            claim=c.claim,
            meaning=c.meaning,
            caveat=c.caveat,
            verified=c.verified,
        )
        for c in db.query(models.ExtractedClaim).filter(models.ExtractedClaim.scan_id == scan_id).all()
    ]


@router.get("/report/{scan_id}", tags=["report"])
def get_full_report(scan_id: str, db: Session = Depends(get_db)):
    """Return the complete 12-section report for a scan."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    report = {
        "scan_id": scan.id,
        "product_name": scan.product_name,
        "brand": scan.brand,
        "status": scan.status,
        "language": "en",
        "images": [
            {
                "id": i.id,
                "uri": i.uri,
                "type": i.type,
                "quality": i.get_quality(),
            }
            for i in scan.images
        ],
        "ingredients": [
            {
                "raw_name": ei.raw_name,
                "matched": ei.matched,
                "confidence": ei.confidence,
                "kb_id": ei.kb_id,
            }
            for ei in db.query(models.ExtractedIngredient)
            .filter(models.ExtractedIngredient.scan_id == scan_id).all()
        ],
        "nutrition": [
            {
                "nutrient": n.nutrient,
                "value": n.value,
                "unit": n.unit,
                "basis": n.basis,
                "raw_line": n.raw_line,
            }
            for n in db.query(models.ExtractedNutrition)
            .filter(models.ExtractedNutrition.scan_id == scan_id).all()
        ],
        "allergens": [
            {
                "allergen": a.allergen,
                "declared": a.declared,
                "warning_type": a.warning_type,
                "matched_keywords": json.loads(a.matched_keywords) if a.matched_keywords else None,
            }
            for a in db.query(models.ExtractedAllergen)
            .filter(models.ExtractedAllergen.scan_id == scan_id).all()
        ],
        "claims": [
            {
                "claim": c.claim,
                "meaning": c.meaning,
                "caveat": c.caveat,
                "verified": c.verified,
            }
            for c in db.query(models.ExtractedClaim)
            .filter(models.ExtractedClaim.scan_id == scan_id).all()
        ],
    }
    return report


@router.post("/translate/report", tags=["report"])
def translate_report(
    scan_id: str,
    target_language: str,
    db: Session = Depends(get_db),
):
    """Translate an existing report without rescanning. Preserves scientific terms."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if target_language == "en":
        return {"detail": "Already in English", "language": "en"}

    # Build report from DB
    report = {
        "scan_id": scan.id,
        "product_name": scan.product_name,
        "brand": scan.brand,
        "summary": "",
        "product_overview": {"product_name": scan.product_name, "brand": scan.brand},
        "ingredient_explanations": [],
        "warnings": [],
        "claims": [],
        "storage_and_usage": {"note": ""},
        "language": target_language,
    }

    # Add ingredients
    for ei in db.query(models.ExtractedIngredient).filter(models.ExtractedIngredient.scan_id == scan_id).all():
        kb_ing = ingredient_service.get(ei.kb_id) if ei.kb_id else None
        report["ingredient_explanations"].append({
            "ingredient": kb_ing["name"] if kb_ing else ei.raw_name,
            "simple_name": kb_ing.get("simple_name") if kb_ing else None,
            "what_it_does": kb_ing.get("function") if kb_ing else None,
            "uncertain": not ei.matched,
        })

    # Add warnings from allergens
    allergens = db.query(models.ExtractedAllergen).filter(models.ExtractedAllergen.scan_id == scan_id).all()
    if allergens:
        report["warnings"].append("Allergens detected - check the Allergens tab if you have food allergies.")
    else:
        report["warnings"].append("No allergens detected in extracted text.")

    translated = translation_service.translate_report(report, target_language)
    return translated
