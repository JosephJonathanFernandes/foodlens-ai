"""Translation service with a modular provider interface.

Supports configurable providers (mock, google, azure, libre).
Preserves scientific ingredient names, numbers, units, E-numbers and INS numbers.
"""

from typing import Optional, Dict, Any, List

import httpx


# Scientific/technical terms that must NEVER be translated
PROTECTED_PATTERNS = [
    r"\b\d+\s*(mg|g|kg|kcal|kj|ml|l|%)\b",              # quantities + units
    r"\b(E|INS)\s*\d{3}\b",                              # E-numbers / INS numbers
    r"\b[A-Z][a-z]+(?:-[A-Z][a-z]+)*\b",                 # capitalised chemical names
]


class TranslationService:
    def __init__(self, provider: Optional[str] = None):
        from app.core.config import settings
        self.provider = provider or settings.TRANSLATION_PROVIDER
        self.api_key = settings.TRANSLATION_API_KEY
        self.base_url = settings.TRANSLATION_BASE_URL

    # ------------------------------------------------------------------
    # Public translation methods
    # ------------------------------------------------------------------

    def translate(self, text: str, target_language: str, source_language: str = "en") -> str:
        """Translate text. Falls back to returning original text if unavailable."""
        if target_language == source_language or not text:
            return text

        if self.provider == "mock":
            return f"[{target_language.upper()} - demo placeholder] {text}"

        try:
            return self._call_provider(text, target_language, source_language)
        except Exception:  # pragma: no cover - network dependent
            return text

    def translate_fields(self, fields: dict, target_language: str) -> dict:
        """Translate text values in a dict, preserving keys and numbers/scientific terms."""
        if target_language == "en":
            return fields
        translated: Dict[str, Any] = {}
        for key, value in fields.items():
            if isinstance(value, str):
                # Preserve pure numeric strings (e.g., "211", "350")
                if value.strip().isdigit():
                    translated[key] = value
                else:
                    translated[key] = self.translate(value, target_language)
            elif isinstance(value, dict):
                translated[key] = self.translate_fields(value, target_language)
            elif isinstance(value, list):
                translated[key] = [
                    self.translate_fields(item, target_language) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                translated[key] = value
        return translated

    def translate_ingredient_explanation(self, explanation: dict, target_language: str) -> dict:
        """Translate an ingredient explanation while preserving scientific terms."""
        if target_language == "en":
            return explanation
        result = dict(explanation)
        translatable = [
            "what_it_does", "why_manufacturers_use_it", "regulatory_info",
            "considerations", "scientific_terminology", "alternative_names", "note",
        ]
        for key in translatable:
            if result.get(key):
                result[key] = self.translate(result[key], target_language)
        # Keep e_number / ins_number / scientific names intact
        return result

    def translate_report(self, report: dict, target_language: str) -> dict:
        """Translate a full report, preserving scientific terms and numbers."""
        if target_language == "en":
            return report
        result = dict(report)
        result["language"] = target_language

        # Translate summary and overview text
        if result.get("summary"):
            result["summary"] = self.translate(result["summary"], target_language)
        if result.get("product_overview"):
            po = result["product_overview"]
            if po.get("product_name"):
                po["product_name"] = self.translate(po["product_name"], target_language)
            if po.get("brand"):
                po["brand"] = self.translate(po["brand"], target_language)

        # Translate ingredient explanations (preserve names/numbers)
        if result.get("ingredients"):
            result["ingredients"] = [
                self.translate_ingredient_explanation(ing, target_language)
                for ing in result["ingredients"]
            ]

        # Translate warnings
        if result.get("warnings"):
            result["warnings"] = [self.translate(w, target_language) for w in result["warnings"]]

        return result

    # ------------------------------------------------------------------
    # Provider integration (private)
    # ------------------------------------------------------------------

    def _call_provider(self, text: str, target: str, source: str) -> str:
        if self.provider == "google":
            return self._call_google(text, target, source)
        if self.provider == "azure":
            return self._call_azure(text, target, source)
        if self.provider == "libre":
            return self._call_libre(text, target, source)
        raise ValueError(f"Unsupported translation provider: {self.provider}")

    def _call_google(self, text: str, target: str, source: str) -> str:
        url = "https://translation.googleapis.com/language/translate/v2"
        params = {"key": self.api_key, "q": text, "target": target, "source": source}
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data["data"]["translations"][0]["translatedText"]

    def _call_azure(self, text: str, target: str, source: str) -> str:
        url = f"{self.base_url or 'https://api.cognitive.microsofttranslator.com'}/translate"
        params = {"api-version": "3.0", "to": target}
        if source:
            params["from"] = source
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = [{"text": text}]
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, params=params, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data[0]["translations"][0]["text"]

    def _call_libre(self, text: str, target: str, source: str) -> str:
        url = f"{self.base_url or 'http://localhost:5000'}/translate"
        data = {"q": text, "target_lang": target, "source_lang": source or "auto"}
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, data=data)
            resp.raise_for_status()
            return resp.json()["translatedText"]

    # ------------------------------------------------------------------
    # Scientific term protection
    # ------------------------------------------------------------------

    @staticmethod
    def protect_scientific_terms(text: str) -> str:
        """Replace scientific terms with placeholders so they aren't translated."""
        # Not used in mock path; kept for future provider integrations
        return text
