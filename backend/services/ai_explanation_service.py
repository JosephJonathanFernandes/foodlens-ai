"""AI explanation service: structured explanations with validation."""

from typing import Optional


class AIExplanationService:
    def __init__(self, provider: Optional[str] = None):
        from app.core.config import settings
        self.provider = provider or settings.LLM_PROVIDER

    def explain_ingredient(self, ingredient: Optional[dict], language: str = "en") -> dict:
        """Return a structured, validated explanation for an ingredient.
        Never invents data; marks uncertain info clearly."""
        if ingredient is None:
            return {
                "ingredient": None,
                "simple_name": None,
                "what_it_does": None,
                "why_manufacturers_use_it": None,
                "is_additive": False,
                "regulatory_info": None,
                "considerations": None,
                "scientific_terminology": None,
                "alternative_names": None,
                "e_number": None,
                "ins_number": None,
                "source": "ocr_only",
                "uncertain": True,
                "note": "No reliable knowledge-base information available for this ingredient. Explanation is based on the label text only.",
            }
        explanation = {
            "ingredient": ingredient.get("name"),
            "simple_name": ingredient.get("simple_name"),
            "what_it_does": ingredient.get("function"),
            "why_manufacturers_use_it": ingredient.get("why_used"),
            "is_additive": ingredient.get("is_additive", False),
            "regulatory_info": ingredient.get("regulatory_info"),
            "considerations": ingredient.get("considerations"),
            "scientific_terminology": ingredient.get("scientific_terminology"),
            "alternative_names": ingredient.get("alternative_names"),
            "e_number": ingredient.get("e_number"),
            "ins_number": ingredient.get("ins_number"),
            "source": "knowledge_base",
            "uncertain": False,
        }
        if ingredient is None:
            explanation["note"] = "No reliable knowledge-base information available for this ingredient. Explanation is based on the label text only."
        return explanation

    def explain_nutrition(self, nutrition: dict, language: str = "en") -> dict:
        """Structured nutrition explanation without health judgments."""
        return {
            "values": nutrition,
            "note": "Values are taken directly from the label. No health score is assigned.",
        }

    def explain_product(self, report: dict, language: str = "en") -> str:
        """Generate an 'explain everything' plain-language summary."""
        parts = []
        parts.append(f"Product: {report.get('product_name', 'Unknown product')}")
        parts.append(f"Brand: {report.get('brand', 'Not listed')}")
        parts.append(f"Overall summary: {report.get('summary', 'Not available')}")
        return "\n".join(parts)
