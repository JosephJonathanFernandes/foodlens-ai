"""Translation endpoint."""

from fastapi import APIRouter, HTTPException
from schemas import scan as schemas
from services.translation_service import TranslationService

router = APIRouter()
translation_service = TranslationService()


@router.post("", response_model=schemas.TranslateResponse, tags=["translate"])
def translate(request: schemas.TranslateRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    translated = translation_service.translate(request.text, request.target_language, request.source_language)
    return schemas.TranslateResponse(
        translated_text=translated,
        target_language=request.target_language,
        source_language=request.source_language,
    )
