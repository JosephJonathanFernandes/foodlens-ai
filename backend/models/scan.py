"""SQLAlchemy models for scans."""

import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database.session import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, index=True)
    product_name = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    status = Column(String, default="idle")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = relationship("ScanImage", back_populates="scan", cascade="all, delete-orphan")
    report = relationship("ScanReport", back_populates="scan", uselist=False, cascade="all, delete-orphan")


class ScanImage(Base):
    __tablename__ = "scan_images"

    id = Column(String, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)
    uri = Column(String, nullable=False)
    type = Column(String, nullable=False)  # front, back, side, closeup, other
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    quality_json = Column(Text, nullable=True)  # JSON: blur_score, brightness, contrast, is_blurry
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="images")
    ocr_results = relationship("OcrResult", back_populates="image", cascade="all, delete-orphan")

    def get_quality(self) -> dict:
        if self.quality_json:
            try:
                return json.loads(self.quality_json)
            except Exception:
                return {}
        return {}

    def set_quality(self, quality: dict):
        self.quality_json = json.dumps(quality)


class ScanReport(Base):
    __tablename__ = "scan_reports"

    id = Column(String, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False, unique=True)
    product_overview = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    raw_ocr_text = Column(Text, nullable=True)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="report")


class OcrResult(Base):
    __tablename__ = "ocr_results"

    id = Column(String, primary_key=True, index=True)
    image_id = Column(String, ForeignKey("scan_images.id"), nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Integer, nullable=True)  # 0-100
    box_json = Column(Text, nullable=True)  # JSON: [x1, y1, x2, y2]
    created_at = Column(DateTime, default=datetime.utcnow)

    image = relationship("ScanImage", back_populates="ocr_results")

    def get_box(self):
        if self.box_json:
            try:
                return json.loads(self.box_json)
            except Exception:
                return None
        return None


class ExtractedIngredient(Base):
    __tablename__ = "extracted_ingredients"

    id = Column(String, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)
    raw_name = Column(String, nullable=False)
    matched = Column(Boolean, default=False)
    confidence = Column(Integer, nullable=True)  # 0-100
    kb_id = Column(String, nullable=True)  # knowledge base id if matched
    source_image_id = Column(String, ForeignKey("scan_images.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan")
    source_image = relationship("ScanImage")


class ExtractedNutrition(Base):
    __tablename__ = "extracted_nutrition"

    id = Column(String, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)
    nutrient = Column(String, nullable=False)  # energy, protein, fat, etc.
    value = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    basis = Column(String, nullable=True)  # per_serving, per_100g, per_pack
    raw_line = Column(Text, nullable=True)
    normalized_value = Column(String, nullable=True)  # per 100g normalized
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan")


class ExtractedAllergen(Base):
    __tablename__ = "extracted_allergens"

    id = Column(String, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)
    allergen = Column(String, nullable=False)  # milk, peanuts, etc.
    declared = Column(Boolean, default=False)
    warning_type = Column(String, nullable=True)  # declared, may_contain, cross_contamination
    matched_keywords = Column(Text, nullable=True)  # JSON list
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan")


class ExtractedClaim(Base):
    __tablename__ = "extracted_claims"

    id = Column(String, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)
    claim = Column(String, nullable=False)  # natural, organic, sugar_free, etc.
    meaning = Column(Text, nullable=True)
    caveat = Column(Text, nullable=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan")
