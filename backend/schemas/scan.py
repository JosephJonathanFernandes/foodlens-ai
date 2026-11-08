"""Pydantic schemas for the FoodLens AI API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


# ---- Scans ----

class ScanImageBase(BaseModel):
    id: str
    uri: str
    type: str
    width: Optional[int] = None
    height: Optional[int] = None

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


# ---- Error ----

class ErrorResponse(BaseModel):
    message: str
    status_code: Optional[int] = None
