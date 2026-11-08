"""Translation service with a modular provider interface."""

from app.core.config import settings


class TranslationService:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.TRANSLATION_PROVIDER

    def translate(self, text: str, target_language: str, source_language: str = "en") -> str:
        """Translate text. Falls back to returning original text if translation unavailable."""
        if target_language == source_language or not text:
            return text

        if self.provider == "mock":
            # Deterministic placeholder: clearly labelled as mock/demo translation
            return f"[{target_language.upper()} - demo placeholder] {text}"

        # Extend here with real providers (google, azure, libre) when API keys configured.
        return text

    def translate_fields(self, fields: dict, target_language: str) -> dict:
        """Translate text values in a dict, preserving keys and numbers/scientific terms."""
        if target_language == "en":
            return fields
        translated = {}
        for key, value in fields.items():
            if isinstance(value, str):
                translated[key] = self.translate(value, target_language)
            elif isinstance(value, dict):
                translated[key] = self.translate_fields(value, target_language)
            elif isinstance(value, list):
                translated[key] = [self.translate_fields(item, target_language) if isinstance(item, dict) else item for item in value]
            else:
                translated[key] = value
        return translated
