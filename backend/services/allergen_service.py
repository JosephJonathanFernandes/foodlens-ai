"""Allergen service: detects declared allergens and distinguishes warning types."""

from typing import List, Dict, Optional


class AllergenService:
    ALLERGENS = {
        "milk": ["milk", "dairy", "casein", "whey", "lactose", "milk solids"],
        "peanuts": ["peanut", "groundnut"],
        "tree_nuts": ["almond", "cashew", "walnut", "pistachio", "hazelnut", "pecan", "macadamia", "tree nut"],
        "soy": ["soy", "soya", "soybean"],
        "wheat": ["wheat", "maida", "atta"],
        "gluten": ["gluten", "wheat", "barley", "rye", "oats"],
        "eggs": ["egg", "albumen"],
        "fish": ["fish"],
        "crustaceans": ["crab", "prawn", "shrimp", "lobster", "crustacean"],
        "sesame": ["sesame", "til"],
        "mustard": ["mustard"],
    }

    MAY_CONTAIN_KEYWORDS = ["may contain", "traces of", "produced in", "manufactured in", "processed in"]

    def detect(self, text: str) -> Dict[str, dict]:
        """Scan text for declared allergens. Returns dict per allergen with declaration type."""
        lowered = text.lower()
        results: Dict[str, dict] = {}
        for allergen, keywords in self.ALLERGENS.items():
            found = any(kw in lowered for kw in keywords)
            if not found:
                continue
            # Determine warning type
            warning_type = "declared"  # ingredient contains allergen
            for mk in self.MAY_CONTAIN_KEYWORDS:
                if mk in lowered:
                    # crude check: if allergen appears near a may-contain phrase
                    warning_type = "may_contain"
                    break
            results[allergen] = {
                "declared": True,
                "warning_type": warning_type,
                "matched_keywords": [kw for kw in keywords if kw in lowered],
            }
        return results

    def summary(self, results: Dict[str, dict]) -> str:
        if not results:
            return "No allergens were detected in the extracted label text. This does not guarantee the product is allergen-free."
        listed = ", ".join(results.keys())
        return f"Declared allergens detected: {listed}. Always check the full packaging and consult a doctor if you have allergies."
