"""AI explanation service: structured explanations with validation.

Supports configurable LLM providers (mock, openai, anthropic, gemini).
Never invents data; marks uncertain info clearly.
Distinguishes label facts from AI-generated explanations.
"""

import json
from typing import Optional, Dict, Any

import httpx


class AIExplanationService:
    def __init__(self, provider: Optional[str] = None):
        from app.core.config import settings
        self.provider = provider or settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.base_url = settings.LLM_BASE_URL

    # ------------------------------------------------------------------
    # Public explanation methods
    # ------------------------------------------------------------------

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
                "ai_generated": False,
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
            "ai_generated": False,
        }
        return explanation

    def explain_ingredient_ai(self, raw_name: str, language: str = "en") -> dict:
        """Use an LLM to explain an ingredient not in the knowledge base.
        Clearly marks output as AI-generated and uncertain."""
        if self.provider == "mock":
            return {
                "ingredient": raw_name,
                "simple_name": None,
                "what_it_does": None,
                "why_manufacturers_use_it": None,
                "is_additive": None,
                "regulatory_info": None,
                "considerations": None,
                "scientific_terminology": None,
                "alternative_names": None,
                "e_number": None,
                "ins_number": None,
                "source": "ai_generated",
                "uncertain": True,
                "ai_generated": True,
                "note": "AI-generated explanation (mock provider). Not verified against a knowledge base. Treat as uncertain.",
            }

        prompt = self._build_ingredient_prompt(raw_name, language)
        try:
            response = self._call_llm(prompt, language)
            parsed = self._parse_llm_json(response)
            parsed["source"] = "ai_generated"
            parsed["uncertain"] = True
            parsed["ai_generated"] = True
            parsed["ingredient"] = raw_name
            return parsed
        except Exception as exc:  # pragma: no cover - network dependent
            return {
                "ingredient": raw_name,
                "source": "ai_generated",
                "uncertain": True,
                "ai_generated": True,
                "note": f"AI explanation unavailable: {exc}",
            }

    def explain_nutrition(self, nutrition: dict, language: str = "en") -> dict:
        """Structured nutrition explanation without health judgments."""
        return {
            "values": nutrition,
            "source": "ocr",
            "ai_generated": False,
            "note": "Values are taken directly from the label. No health score is assigned.",
        }

    def explain_product(self, report: dict, language: str = "en") -> str:
        """Generate an 'explain everything' plain-language summary."""
        parts = []
        parts.append(f"Product: {report.get('product_name', 'Unknown product')}")
        parts.append(f"Brand: {report.get('brand', 'Not listed')}")
        parts.append(f"Overall summary: {report.get('summary', 'Not available')}")

        ings = report.get("ingredients", [])
        if ings:
            parts.append(f"\nIngredients ({len(ings)}):")
            for ing in ings[:10]:
                name = ing.get("ingredient") or ing.get("raw_name", "Unknown")
                simple = ing.get("simple_name") or name
                parts.append(f"  - {name} ({simple})")

        alls = report.get("allergens", {})
        if alls:
            parts.append(f"\nAllergens detected: {', '.join(alls.keys())}")

        parts.append("\nThis explanation is based on the label text extracted via OCR. "
                     "No health score is assigned. Consult a healthcare professional for dietary advice.")
        return "\n".join(parts)

    def explain_product_ai(self, report: dict, language: str = "en") -> str:
        """Use an LLM to generate a full 'explain everything' summary."""
        if self.provider == "mock":
            base = self.explain_product(report, language)
            return base + "\n\n[AI 'explain everything' - mock provider placeholder]"

        prompt = self._build_product_prompt(report, language)
        try:
            return self._call_llm(prompt, language)
        except Exception as exc:  # pragma: no cover
            return self.explain_product(report, language) + f"\n\nAI explanation unavailable: {exc}"

    # ------------------------------------------------------------------
    # LLM provider integration (private)
    # ------------------------------------------------------------------

    def _build_ingredient_prompt(self, raw_name: str, language: str) -> str:
        return (
            f"You are a food science expert. Explain the ingredient '{raw_name}' "
            f"in simple {'English' if language == 'en' else language}.\n"
            "Return ONLY valid JSON with keys: ingredient, simple_name, what_it_does, "
            "why_manufacturers_use_it, is_additive, regulatory_info, considerations, "
            "scientific_terminology, alternative_names, e_number, ins_number.\n"
            "If you don't know, set fields to null and mark uncertain true. "
            "Do not invent safety claims or health judgments."
        )

    def _build_product_prompt(self, report: dict, language: str) -> str:
        return (
            f"Explain this food product label in simple, plain {'English' if language == 'en' else language}.\n"
            f"Product: {report.get('product_name', 'Unknown')}\n"
            f"Brand: {report.get('brand', 'Not listed')}\n"
            f"Summary: {report.get('summary', 'Not available')}\n"
            "Write an accessible, balanced summary. Do not assign a health score. "
            "Distinguish label facts from AI explanation. Mention uncertainty where relevant."
        )

    def _call_llm(self, prompt: str, language: str) -> str:
        """Call the configured LLM provider. Returns raw text."""
        if self.provider == "openai":
            return self._call_openai(prompt)
        if self.provider == "anthropic":
            return self._call_anthropic(prompt)
        if self.provider == "gemini":
            return self._call_gemini(prompt)
        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _call_openai(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model or "claude-3-haiku-20240307",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    def _call_gemini(self, prompt: str) -> str:
        url = self.base_url or "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, params=params, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def _parse_llm_json(raw: str) -> Dict[str, Any]:
        """Extract JSON from LLM response, tolerating markdown fences."""
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1] if "```" in text[3:] else text
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Return a safe minimal structure so the caller doesn't crash
            return {
                "ingredient": None,
                "simple_name": None,
                "what_it_does": None,
                "why_manufacturers_use_it": None,
                "is_additive": None,
                "regulatory_info": None,
                "considerations": None,
                "scientific_terminology": None,
                "alternative_names": None,
                "e_number": None,
                "ins_number": None,
                "uncertain": True,
                "ai_generated": True,
                "note": "Failed to parse AI response as JSON.",
            }
