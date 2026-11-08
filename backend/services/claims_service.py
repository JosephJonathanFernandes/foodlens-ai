"""Marketing claims analyzer: identifies claims and explains what they mean."""

from typing import List, Dict


class ClaimsService:
    CLAIMS = {
        "natural": {
            "meaning": "Suggests ingredients come from natural sources.",
            "caveat": "'Natural' is not always strictly defined; check the ingredient list for what is actually included.",
        },
        "organic": {
            "meaning": "Ingredients produced under organic farming standards.",
            "caveat": "Look for a certification mark/logo to verify the organic claim.",
        },
        "no_added_sugar": {
            "meaning": "No sugar was added during processing.",
            "caveat": "The product may still contain naturally occurring sugars.",
        },
        "sugar_free": {
            "meaning": "Contains no (or negligible) sugar.",
            "caveat": "May contain artificial sweeteners or sugar alcohols; check ingredients.",
        },
        "low_fat": {
            "meaning": "Low in fat compared to a standard version.",
            "caveat": "May contain added sugars or starches to replace fat.",
        },
        "high_protein": {
            "meaning": "Higher protein content than comparable products.",
            "caveat": "Check actual protein grams per serving on the nutrition table.",
        },
        "multigrain": {
            "meaning": "Made with more than one type of grain.",
            "caveat": "Does not necessarily mean whole grain; check if grains are refined.",
        },
        "fortified": {
            "meaning": "Vitamins or minerals have been added.",
            "caveat": "Check which nutrients were added and in what amounts.",
        },
        "zero_cholesterol": {
            "meaning": "Contains no cholesterol.",
            "caveat": "Cholesterol is only in animal products; plant-based foods naturally have none.",
        },
        "made_with_real_fruit": {
            "meaning": "Contains some real fruit content.",
            "caveat": "May contain only a small amount; check fruit percentage and added sugars.",
        },
    }

    def detect(self, text: str) -> List[Dict[str, str]]:
        lowered = text.lower()
        found = []
        for claim, info in self.CLAIMS.items():
            if claim.replace("_", " ") in lowered:
                found.append({
                    "claim": claim,
                    "display": claim.replace("_", " ").title(),
                    "meaning": info["meaning"],
                    "caveat": info["caveat"],
                    "verified": False,  # mark as label claim, not independently verified
                })
        return found
