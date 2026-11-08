"""Text extraction service: normalizes OCR output and classifies sections."""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExtractedField:
    name: str
    value: str
    confidence: Optional[float] = None
    source_image: Optional[str] = None
    box: Optional[tuple] = None


@dataclass
class SectionClassification:
    section: str  # e.g. "ingredients", "nutrition", "allergens", "other"
    text: str
    confidence: float = 0.0


class TextExtractionService:
    def __init__(self):
        # Simple keyword-based classifiers (extensible, deterministic, no hallucination)
        self.section_keywords = {
            "ingredients": ["ingredients", "ingredient", "contains", "made with"],
            "nutrition": ["nutrition", "energy", "calories", "fat", "protein", "carbohydrate", "sodium", "sugar", "fibre", "fiber"],
            "allergens": ["allergen", "contains", "may contain", "traces of", "produced in"],
            "manufacturing": ["manufactured", "manufacturer", "packed", "batch", "mfg", "mfg date"],
            "dates": ["expiry", "best before", "use by", "date of manufacture", "exp", "best before end"],
            "additives": ["ins", "e-number", "e number", "preservative", "additive", "colour", "color", "sweetener"],
            "claims": ["natural", "organic", "no added sugar", "sugar free", "low fat", "high protein", "multigrain", "fortified"],
            "storage": ["store", "storage", "keep", "refrigerate", "cool", "dry place"],
            "preparation": ["prepare", "preparation", "cooking", "instructions", "how to use"],
            "customer_care": ["customer care", "consumer care", "helpline", "contact", "email", "phone"],
            "fssai": ["fssai", "licence", "license", "registration"],
        }

    def normalize(self, raw_text: str) -> str:
        """Normalize OCR text: collapse whitespace, strip, preserve line structure."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return "\n".join(lines)

    def classify_sections(self, text: str) -> List[SectionClassification]:
        """Classify lines into sections. Unclassified lines go to 'other'."""
        classified: List[SectionClassification] = []
        other_lines: List[str] = []
        for line in text.splitlines():
            lowered = line.lower()
            matched = False
            for section, keywords in self.section_keywords.items():
                for kw in keywords:
                    if kw in lowered:
                        classified.append(SectionClassification(section=section, text=line, confidence=0.6))
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                other_lines.append(line)
        if other_lines:
            classified.append(SectionClassification(section="other", text="\n".join(other_lines), confidence=0.3))
        return classified

    def extract_fields(self, text: str, source_image: Optional[str] = None) -> List[ExtractedField]:
        """Heuristic field extraction. Returns raw fields without inventing values."""
        fields: List[ExtractedField] = []
        lowered = text.lower()

        # Product name heuristic: first meaningful line
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            fields.append(ExtractedField(name="product_name", value=lines[0], source_image=source_image))

        # Brand heuristic: look for "brand:" or use product name
        brand_match = re.search(r"brand\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
        if brand_match:
            fields.append(ExtractedField(name="brand", value=brand_match.group(1).strip(), source_image=source_image))

        # Serving size
        serving_match = re.search(r"serving\s*size\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
        if serving_match:
            fields.append(ExtractedField(name="serving_size", value=serving_match.group(1).strip(), source_image=source_image))

        # Net quantity
        qty_match = re.search(r"(net\s*qty|net\s*weight|quantity)\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
        if qty_match:
            fields.append(ExtractedField(name="net_quantity", value=qty_match.group(2).strip(), source_image=source_image))

        # Dates
        for label, pattern in [("manufacturing_date", r"mfg\s*date[:\-]\s*([^\n]+)"),
                               ("expiry_date", r"expiry[:\-]\s*([^\n]+)"),
                               ("best_before", r"best\s*before[:\-]\s*([^\n]+)"),
                               ("batch_number", r"batch\s*(?:no|number)[:\-]\s*([^\n]+)")]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                fields.append(ExtractedField(name=label, value=m.group(1).strip(), source_image=source_image))

        # FSSAI
        fssai_match = re.search(r"fssai[^\n]{0,40}", text, re.IGNORECASE)
        if fssai_match:
            fields.append(ExtractedField(name="fssai_licence", value=fssai_match.group(0).strip(), source_image=source_image))

        return fields
