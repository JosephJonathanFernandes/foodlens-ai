"""Pydantic schemas for the FoodLens AI API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


# ---- Scans ----

class OcrResultBase(BaseModel):
    id: str
    text: str
    confidence: Optional[int] = None  # 0-100
    box: Optional[list] = None  # [x1, y1, x2, y2]

    model_config = ConfigDict(from_attributes=True)


class ScanImageBase(BaseModel):
    id: str
    uri: str
    type: str
    width: Optional[int] = None
    height: Optional[int] = None
    quality: Optional[dict] = None  # blur_score, brightness, contrast, is_blurry
    ocr_results: List[OcrResultBase] = []

    model_config = ConfigDict(from_attributes=True)


class ScanImageCreate(BaseModel):
    id: str
    uri: str
    type: str
    width: Optional[int] = None
    height: Optional[int] = None


class ScanBase(BaseModel):
    id: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanCreate(BaseModel):
    id: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    images: List[ScanImageCreate]


class ScanOut(ScanBase):
    images: List[ScanImageBase] = []


# ---- Scan processing ----

class ScanProcessRequest(BaseModel):
    scan_id: str
    language: str = "en"


class ScanProcessResponse(BaseModel):
    scan_id: str
    status: str
    report_id: Optional[str] = None


# ---- History ----

class ScanHistoryItem(BaseModel):
    id: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    status: str
    created_at: datetime


# ---- Translate ----

class TranslateRequest(BaseModel):
    text: str
    target_language: str
    source_language: str = "en"


class TranslateResponse(BaseModel):
    translated_text: str
    target_language: str
    source_language: str


# ---- Compare ----

class CompareRequest(BaseModel):
    scan_id_a: str
    scan_id_b: str


class CompareResponse(BaseModel):
    scan_id_a: str
    scan_id_b: str
    comparison: Dict[str, Any]


# ---- Ingredient ----

class IngredientOut(BaseModel):
    id: str
    name: str
    simple_name: Optional[str] = None
    function: Optional[str] = None
    why_used: Optional[str] = None
    is_additive: bool = False
    regulatory_info: Optional[str] = None
    considerations: Optional[str] = None
    scientific_terminology: Optional[str] = None
    alternative_names: Optional[str] = None
    e_number: Optional[str] = None
    ins_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractedIngredientOut(BaseModel):
    raw_name: str
    matched: bool
    confidence: Optional[float] = None
    kb_id: Optional[str] = None
    ingredient: Optional[IngredientOut] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractedNutritionOut(BaseModel):
    nutrient: str
    value: Optional[str] = None
    unit: Optional[str] = None
    basis: Optional[str] = None
    raw_line: Optional[str] = None
    normalized_value: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractedAllergenOut(BaseModel):
    allergen: str
    declared: bool
    warning_type: Optional[str] = None
    matched_keywords: Optional[list] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractedClaimOut(BaseModel):
    claim: str
    meaning: Optional[str] = None
    caveat: Optional[str] = None
    verified: bool = False

    model_config = ConfigDict(from_attributes=True)


# ---- Scan detail with extractions ----

class ScanDetailOut(ScanOut):
    ingredients: List[ExtractedIngredientOut] = []
    nutrition: List[ExtractedNutritionOut] = []
    allergens: List[ExtractedAllergenOut] = []
    claims: List[ExtractedClaimOut] = []


# ---- Error ----

class ErrorResponse(BaseModel):
    message: str
    status_code: Optional[int] = None
