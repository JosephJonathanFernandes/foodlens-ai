"""Image service: handles saving, retrieving, and metadata for uploaded images."""

import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional

from app.core.config import settings


UPLOAD_DIR = Path("uploads")


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def save_uploaded_file(file_bytes: bytes, filename: Optional[str] = None) -> str:
    """Save an uploaded image to disk and return its URI path."""
    ensure_upload_dir()
    file_id = str(uuid.uuid4())
    ext = Path(filename).suffix if filename and Path(filename).suffix else ".jpg"
    stored_name = f"{file_id}{ext}"
    dest = ensure_upload_dir() / stored_name
    with open(dest, "wb") as f:
        f.write(file_bytes)
    return str(dest)


def get_image_uri(image_id: str) -> Optional[str]:
    """Return the filesystem path for a stored image id if it exists."""
    ensure_upload_dir()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = UPLOAD_DIR / f"{image_id}{ext}"
        if candidate.exists():
            return str(candidate)
    return None


def list_images() -> List[str]:
    ensure_upload_dir()
    return [str(p) for p in UPLOAD_DIR.iterdir() if p.is_file()]


def delete_image(image_id: str) -> bool:
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = UPLOAD_DIR / f"{image_id}{ext}"
        if candidate.exists():
            candidate.unlink()
            return True
    return False
