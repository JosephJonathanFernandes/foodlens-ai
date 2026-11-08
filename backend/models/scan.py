"""SQLAlchemy models for scans."""

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
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="images")


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
