"""Nutrition service: parses and explains nutrition values."""

import re
from typing import Dict, List, Optional, Tuple


class NutritionService:
    # Units commonly seen on Indian food labels
    UNIT_PATTERNS = {
        "energy": r"(energy|kcal|kj|kilojoule|kilocalorie)",
        "protein": r"protein",
        "fat": r"(total fat|fat)",
        "sat_fat": r"saturated fat",
        "trans_fat": r"trans fat",
        "carb": r"(carbohydrate|total carbohydrate|total carbs)",
        "sugar": r"(total sugars|sugars|sugar)",
        "added_sugar": r"added sugars",
        "fibre": r"(dietary fibre|dietary fiber|fibre|fiber)",
        "sodium": r"sodium",
        "salt": r"salt",
        "cholesterol": r"cholesterol",
    }

    def parse(self, text: str) -> Dict[str, Optional[dict]]:
        """Extract nutrition values from text. Returns dict keyed by nutrient name.
        Never invents values; returns None for missing nutrients."""
        results: Dict[str, Optional[dict]] = {key: None for key in self.UNIT_PATTERNS}
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines:
            lowered = line.lower()
            for nutrient, pattern in self.UNIT_PATTERNS.items():
                if not re.search(pattern, lowered):
                    continue
                # Try to capture a value and unit on the same line
                value_match = re.search(r"([\d.,]+)\s*(kcal|kj|g|mg|mg/100g|g/100g|kcal/100g|%|per\s*serving)?", lowered)
                results[nutrient] = {
                    "raw_line": line,
                    "value": value_match.group(1) if value_match else None,
                    "unit": value_match.group(2) if value_match else None,
                    "source": "ocr",
                }
                break
        return results

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
