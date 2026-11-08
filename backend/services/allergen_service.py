"""Allergen service: detects declared allergens and distinguishes warning types."""

import re
from typing import Dict, List, Optional


class AllergenService:
    ALLERGENS = {
        "milk": ["milk", "dairy", "casein", "whey", "lactose", "milk solids", "milk powder"],
        "peanuts": ["peanut", "groundnut"],
        "tree_nuts": [
            "almond", "cashew", "walnut", "pistachio", "hazelnut", "pecan",
            "macadamia", "tree nut", "brazil nut", "chestnut",
        ],
        "soy": ["soy", "soya", "soybean"],
        "wheat": ["wheat", "maida", "atta"],
        "gluten": ["gluten", "wheat", "barley", "rye", "oats"],
        "eggs": ["egg", "albumen"],
        "fish": ["fish"],
        "crustaceans": ["crab", "prawn", "shrimp", "lobster", "crustacean"],
        "sesame": ["sesame", "til"],
        "mustard": ["mustard"],
    }

    # Phrases that indicate a warning rather than a declared ingredient
    MAY_CONTAIN_PHRASES = [
        r"may\s+contain",
        r"traces?\s+of",
        r"produced\s+in\s+a\s+facility",
        r"manufactured\s+in\s+a\s+facility",
        r"processed\s+in\s+a\s+facility",
        r"made\s+on\s+shared\s+equipment",
        r"may\s+have\s+been\s+in\s+contact\s+with",
    ]

    DECLARED_PHRASES = [
        r"contains?:",
        r"ingredients?:",
        r"made\s+with",
        r"containing",
    ]

    def detect(self, text: str) -> Dict[str, dict]:
        """Scan text for allergens and distinguish declaration types.

        Returns dict per allergen with:
          - declared: bool (is it a declared ingredient)
          - warning_type: 'declared' | 'may_contain' | 'cross_contamination' | None
          - matched_keywords: list of keywords found
          - context: surrounding text snippet
        """
        lowered = text.lower()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        results: Dict[str, dict] = {}

        for allergen, keywords in self.ALLERGENS.items():
            matches: List[dict] = []
            for kw in keywords:
                # Find all occurrences of this keyword
                for m in re.finditer(re.escape(kw), lowered):
                    start = max(0, m.start() - 60)
                    end = min(len(lowered), m.end() + 60)
                    context = lowered[start:end]

                    # Determine warning type from context
                    warning_type = self._classify_context(context)

                    matches.append({
                        "keyword": kw,
                        "context": context.strip(),
                        "warning_type": warning_type,
                    })

            if not matches:
                continue

            # Determine overall classification for this allergen
            has_declared = any(m["warning_type"] == "declared" for m in matches)
            has_may_contain = any(m["warning_type"] == "may_contain" for m in matches)
            has_cross_contamination = any(
                m["warning_type"] == "cross_contamination" for m in matches
            )

            if has_declared:
                warning_type = "declared"
            elif has_may_contain:
                warning_type = "may_contain"
            elif has_cross_contamination:
                warning_type = "cross_contamination"
            else:
                warning_type = "declared"  # default if just found in ingredient list

            results[allergen] = {
                "declared": has_declared,
                "warning_type": warning_type,
                "matched_keywords": [m["keyword"] for m in matches],
                "contexts": [m["context"] for m in matches[:3]],
            }

        return results

    def _classify_context(self, context: str) -> str:
        """Classify the context around an allergen keyword."""
        for phrase in self.MAY_CONTAIN_PHRASES:
            if re.search(phrase, context):
                if "facility" in context or "equipment" in context or "contact" in context:
                    return "cross_contamination"
                return "may_contain"
        for phrase in self.DECLARED_PHRASES:
            if re.search(phrase, context):
                return "declared"
        return "declared"  # default

    def summary(self, results: Dict[str, dict]) -> str:
        if not results:
            return (
                "No allergens were detected in the extracted label text. "
                "This does not guarantee the product is allergen-free. "
                "Always check the full packaging and consult a doctor if you have allergies."
            )

        declared = [a for a, r in results.items() if r["warning_type"] == "declared"]
        may_contain = [a for a, r in results.items() if r["warning_type"] == "may_contain"]
        cross_contam = [a for a, r in results.items() if r["warning_type"] == "cross_contamination"]

        parts = []
        if declared:
            parts.append(f"Declared allergens: {', '.join(declared)}")
        if may_contain:
            parts.append(f"May contain: {', '.join(may_contain)}")
        if cross_contam:
            parts.append(f"Cross-contamination risk: {', '.join(cross_contam)}")

        parts.append(
            "This does not guarantee the product is allergen-free. "
            "Always check the full packaging and consult a doctor if you have allergies."
        )
        return ". ".join(parts) + "."
