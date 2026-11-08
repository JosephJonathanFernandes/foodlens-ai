"""Report service: assembles the complete AI food label report."""

from typing import Dict, Any, Optional


class ReportService:
    def build_report(
        self,
        scan_id: str,
        product_name: Optional[str],
        brand: Optional[str],
        ingredients: list,
        nutrition: dict,
        allergens: dict,
        claims: list,
        ocr_text: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        report = {
            "scan_id": scan_id,
            "product_overview": {
                "product_name": product_name,
                "brand": brand,
            },
            "ingredients": ingredients,
            "nutrition": nutrition,
            "allergens": allergens,
            "claims": claims,
            "warnings": self._build_warnings(allergens),
            "storage_and_usage": {
                "note": "Storage and preparation instructions extracted from the label will appear here.",
            },
            "unclassified_info": {
                "raw_ocr_text": ocr_text,
                "note": "Any text that could not be classified is preserved here.",
            },
            "ocr_confidence": {
                "note": "OCR confidence values are preserved per text region where available.",
            },
            "summary": self._build_summary(product_name, ingredients, allergens),
            "language": language,
        }
        return report

    def _build_warnings(self, allergens: dict) -> list:
        warnings = []
        if allergens:
            warnings.append("Allergens detected - check the Allergens tab if you have food allergies.")
        else:
            warnings.append("No allergens detected in extracted text. This does not guarantee the product is allergen-free.")
        return warnings

    def _build_summary(self, product_name, ingredients, allergens) -> str:
        ings = ingredients or []
        count = len(ings)
        return f"{product_name or 'This product'} contains {count} identified ingredient(s). Review the Ingredients tab for details."
