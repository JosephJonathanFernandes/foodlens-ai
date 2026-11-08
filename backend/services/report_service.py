"""Report service: assembles the complete AI food label report with all 12 sections."""

import re
from typing import Dict, Any, Optional, List


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
        ingredient_explanations: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Build the complete structured report with all 12 required sections."""

        # Separate additives from ordinary ingredients
        additives = [i for i in (ingredients or []) if i.get("is_additive")]
        ordinary = [i for i in (ingredients or []) if not i.get("is_additive")]

        # Extract storage/prep info from OCR text
        storage_usage = self._extract_storage_usage(ocr_text)

        # Build unclassified info
        unclassified = self._build_unclassified(ocr_text, classified_sections=None)

        # OCR confidence summary
        ocr_confidence = self._build_ocr_confidence(ocr_text)

        # Overall summary
        summary = self._build_summary(product_name, ingredients, allergens)

        report = {
            # 1. Product overview
            "product_overview": {
                "product_name": product_name,
                "brand": brand,
                "scan_id": scan_id,
            },
            # 2. Complete extracted ingredient list
            "ingredients": ingredients or [],
            # 3. Ingredient-by-ingredient explanations
            "ingredient_explanations": ingredient_explanations or ingredients or [],
            # 4. Nutrition breakdown
            "nutrition": nutrition or {},
            # 5. Additives and preservatives
            "additives": additives,
            # 6. Allergen information
            "allergens": allergens or {},
            # 7. Marketing claims analysis
            "claims": claims or [],
            # 8. Important warnings
            "warnings": self._build_warnings(allergens, additives),
            # 9. Storage and usage information
            "storage_and_usage": storage_usage,
            # 10. Unclassified package information
            "unclassified_info": unclassified,
            # 11. OCR confidence and missing information
            "ocr_confidence": ocr_confidence,
            # 12. Simple overall summary
            "summary": summary,
            "language": language,
        }
        return report

    def translate_report(self, report: dict, target_language: str, translation_service) -> dict:
        """Translate an existing report without rescanning. Preserves scientific terms."""
        if target_language == "en" or not translation_service:
            report["language"] = target_language
            return report

        result = dict(report)
        result["language"] = target_language

        # Translate summary
        if result.get("summary"):
            result["summary"] = translation_service.translate(result["summary"], target_language)

        # Translate product overview
        if result.get("product_overview"):
            po = result["product_overview"]
            if po.get("product_name"):
                po["product_name"] = translation_service.translate(po["product_name"], target_language)
            if po.get("brand"):
                po["brand"] = translation_service.translate(po["brand"], target_language)

        # Translate ingredient explanations (preserve scientific terms/numbers)
        if result.get("ingredient_explanations"):
            result["ingredient_explanations"] = [
                translation_service.translate_ingredient_explanation(ing, target_language)
                for ing in result["ingredient_explanations"]
            ]

        # Translate warnings
        if result.get("warnings"):
            result["warnings"] = [translation_service.translate(w, target_language) for w in result["warnings"]]

        # Translate claims
        if result.get("claims"):
            result["claims"] = [
                {**c, "meaning": translation_service.translate(c.get("meaning", ""), target_language),
                 "caveat": translation_service.translate(c.get("caveat", ""), target_language)}
                for c in result["claims"]
            ]

        # Translate storage & usage note
        if result.get("storage_and_usage", {}).get("note"):
            result["storage_and_usage"]["note"] = translation_service.translate(
                result["storage_and_usage"]["note"], target_language
            )

        return result

    def explain_everything(self, report: dict, ai_service, language: str = "en") -> str:
        """Generate the 'Explain everything' plain-language summary."""
        if ai_service and getattr(ai_service, "provider", None) not in (None, "mock"):
            return ai_service.explain_product_ai(report, language)
        return ai_service.explain_product(report, language) if ai_service else ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_warnings(self, allergens: dict, additives: list) -> List[str]:
        warnings = []
        if allergens:
            warnings.append(
                "Allergens detected - check the Allergens tab if you have food allergies. "
                "This does not guarantee the product is allergen-free."
            )
        else:
            warnings.append(
                "No allergens detected in extracted text. This does not guarantee the product is allergen-free."
            )
        if additives:
            warnings.append(
                f"{len(additives)} additive(s) identified. Review the Additives tab for details. "
                "Presence of an additive does not mean it is harmful at permitted levels."
            )
        return warnings

    def _extract_storage_usage(self, ocr_text: str) -> Dict[str, Any]:
        """Extract storage and preparation instructions from OCR text."""
        storage = {}
        text_lower = ocr_text.lower()

        # Storage keywords
        storage_keywords = ["store", "storage", "keep", "refrigerate", "cool", "dry place", "direct sunlight"]
        prep_keywords = ["prepare", "preparation", "cook", "microwave", "oven", "instructions", "how to use"]

        storage_lines = []
        prep_lines = []
        for line in ocr_text.splitlines():
            lowered = line.lower()
            if any(k in lowered for k in storage_keywords):
                storage_lines.append(line.strip())
            if any(k in lowered for k in prep_keywords):
                prep_lines.append(line.strip())

        storage["storage_instructions"] = storage_lines if storage_lines else [
            "No storage instructions found on the extracted label."
        ]
        storage["preparation_instructions"] = prep_lines if prep_lines else [
            "No preparation instructions found on the extracted label."
        ]
        return storage

    def _build_unclassified(self, ocr_text: str, classified_sections=None) -> Dict[str, Any]:
        """Return any text that could not be classified, preserving it."""
        return {
            "raw_ocr_text": ocr_text,
            "note": "Any text that could not be classified is preserved here. "
                    "Nothing is silently discarded.",
        }

    def _build_ocr_confidence(self, ocr_text: str) -> Dict[str, Any]:
        """OCR confidence summary - placeholder for per-region confidence."""
        return {
            "note": "OCR confidence values are preserved per text region where available. "
                    "Review the OCR Results tab for per-image confidence scores.",
            "total_characters": len(ocr_text),
        }

    def _build_summary(self, product_name, ingredients, allergens) -> str:
        ings = ingredients or []
        count = len(ings)
        additive_count = sum(1 for i in ings if i.get("is_additive"))
        return (
            f"{product_name or 'This product'} contains {count} identified ingredient(s), "
            f"including {additive_count} additive(s). Review the Ingredients tab for details."
        )
