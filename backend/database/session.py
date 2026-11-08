"""Database session and base model setup."""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema():
    """Add missing columns/tables for SQLite (simple migration for MVP)."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # Create ocr_results table if missing
    if "ocr_results" not in existing_tables:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ocr_results (
                    id VARCHAR PRIMARY KEY,
                    image_id VARCHAR NOT NULL,
                    text TEXT NOT NULL,
                    confidence INTEGER,
                    box_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(image_id) REFERENCES scan_images (id)
                )
            """))
            conn.commit()

    # Add quality_json column to scan_images if missing
    if "scan_images" in existing_tables:
        columns = {col["name"] for col in inspector.get_columns("scan_images")}
        if "quality_json" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE scan_images ADD COLUMN quality_json TEXT"))
                conn.commit()


def get_db():
    """Yield a database session and close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
