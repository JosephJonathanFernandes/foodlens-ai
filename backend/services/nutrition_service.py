"""Nutrition service: parses and explains nutrition values."""

import re
from typing import Dict, List, Optional, Tuple


class NutritionService:
    # Nutrient patterns - match common label text
    # Combined pattern: nutrient keyword (group 1) followed by value (group 2) + unit (group 3) within ~40 chars on same line
    # Unit is required to avoid matching ingredient names like "Sodium Benzoate (INS 211)"
    NUTRIENT_PATTERNS = {
        "energy": r"(energy|kilocalorie|kcal|kilojoule|kj).{0,40}?(\d[\d.,]*)\s*(kcal|kj|kilojoule|kilocalorie)",
        "protein": r"(\bprotein\b).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "fat": r"((?<!saturated\s)(?<!trans\s)(?:total\s+)?fat\b).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "sat_fat": r"(saturated\s+fat).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "trans_fat": r"(trans\s+fat).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "carb": r"((?:total\s+)?carbohydrate\b).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "sugar": r"((?:total\s+)?sugars?\b).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "added_sugar": r"(added\s+sugars?).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "fibre": r"((?:dietary\s+)?(?:fibre|fiber)\b).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "sodium": r"(\bsodium\b).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "salt": r"(\bsalt\b).{0,40}?(\d[\d.,]*)\s*(g|mg)",
        "cholesterol": r"(\bcholesterol\b).{0,40}?(\d[\d.,]*)\s*(g|mg)",
    }

    # Unit conversion factors to per 100g
    UNIT_TO_G = {"g": 1.0, "mg": 0.001, "kg": 1000.0}
    ENERGY_TO_KCAL = {"kcal": 1.0, "kj": 0.239, "kilojoule": 0.239, "kilocalorie": 1.0}

    def __init__(self):
        self._compiled = {k: re.compile(v, re.IGNORECASE) for k, v in self.NUTRIENT_PATTERNS.items()}

    def parse(self, text: str) -> Dict[str, Optional[dict]]:
        """Extract nutrition values from text.
        Returns dict keyed by nutrient name with value, unit, raw_line, basis (per_serving/per_100g).
        Never invents values; returns None for missing nutrients."""
        results: Dict[str, Optional[dict]] = {key: None for key in self.NUTRIENT_PATTERNS}

        # Split into lines and detect basis (per serving vs per 100g)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        current_basis = "per_serving"  # default assumption

        for line in lines:
            lowered = line.lower()

            # Detect basis from section headers
            if re.search(r"per\s+100\s*(g|ml)", lowered):
                current_basis = "per_100g"
            elif re.search(r"per\s+serving", lowered):
                current_basis = "per_serving"
            elif re.search(r"per\s+pack", lowered):
                current_basis = "per_pack"

            for nutrient, pattern in self._compiled.items():
                if results[nutrient] is not None:
                    continue  # already captured
                value_match = pattern.search(lowered)
                if not value_match:
                    continue

                # Combined pattern captured value (group 2) and unit (group 3)
                value = value_match.group(2)
                unit = value_match.group(3)

                # Only record if we found an actual numeric value
                if not value:
                    continue

                results[nutrient] = {
                    "raw_line": line,
                    "value": value,
                    "unit": unit,
                    "basis": current_basis,
                    "source": "ocr",
                }
                break

        return results

    def normalize_to_per_100g(
        self, nutrition: Dict[str, Optional[dict]], serving_size_g: Optional[float] = None
    ) -> Dict[str, Optional[dict]]:
        """Convert per-serving values to per-100g where possible.
        If serving_size_g is provided, normalizes all per-serving values."""
        normalized: Dict[str, Optional[dict]] = {}
        for nutrient, data in nutrition.items():
            if data is None:
                normalized[nutrient] = None
                continue

            value = data.get("value")
            unit = data.get("unit") or ""
            basis = data.get("basis", "per_serving")

            if not value:
                normalized[nutrient] = data
                continue

            try:
                num = float(value.replace(",", "."))
            except ValueError:
                normalized[nutrient] = data
                continue

            # Convert to per 100g
            if basis == "per_100g":
                normalized[nutrient] = {**data, "normalized_value": num, "normalized_unit": unit}
            elif basis == "per_serving" and serving_size_g:
                factor = 100.0 / serving_size_g
                normalized[nutrient] = {
                    **data,
                    "normalized_value": round(num * factor, 2),
                    "normalized_unit": unit,
                }
            else:
                # Can't normalize without serving size
                normalized[nutrient] = {**data, "normalized_value": None, "normalized_unit": unit}

        return normalized

    def explain(self, nutrient: str, value: Optional[str], unit: Optional[str]) -> str:
        """Plain-language explanation of what a number means (no health judgments)."""
        explanations = {
            "energy": f"Energy value of {value or 'not listed'} {unit or ''}. Indicates how much energy the food provides.",
            "protein": f"Protein: {value or 'not listed'} {unit or ''}. Protein supports growth and repair of body tissues.",
            "fat": f"Total fat: {value or 'not listed'} {unit or ''}. Fat is a concentrated energy source.",
            "sat_fat": f"Saturated fat: {value or 'not listed'} {unit or ''}.",
            "trans_fat": f"Trans fat: {value or 'not listed'} {unit or ''}.",
            "carb": f"Carbohydrates: {value or 'not listed'} {unit or ''}. Main energy-providing nutrient.",
            "sugar": f"Total sugars: {value or 'not listed'} {unit or ''}.",
            "added_sugar": f"Added sugars: {value or 'not listed'} {unit or ''}. Sugars added during processing.",
            "fibre": f"Dietary fibre: {value or 'not listed'} {unit or ''}. Supports digestion.",
            "sodium": f"Sodium: {value or 'not listed'} {unit or ''}.",
            "salt": f"Salt: {value or 'not listed'} {unit or ''}.",
            "cholesterol": f"Cholesterol: {value or 'not listed'} {unit or ''}.",
        }
        return explanations.get(nutrient, f"{nutrient}: {value or 'not listed'} {unit or ''}.")
