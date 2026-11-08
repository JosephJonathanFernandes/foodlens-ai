"""Ingredient service: knowledge-base lookup and ingredient explanations."""

import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple


KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parents[1] / "knowledge_base" / "ingredients.json"


class IngredientService:
    def __init__(self):
        self._ingredients: List[dict] = []
        self._load()

    def _load(self):
        try:
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._ingredients = data.get("ingredients", [])
        except FileNotFoundError:
            self._ingredients = []

    def list_all(self) -> List[dict]:
        return self._ingredients

    def get(self, ingredient_id: str) -> Optional[dict]:
        for ing in self._ingredients:
            if ing["id"] == ingredient_id:
                return ing
        return None

    def search(self, query: str) -> List[dict]:
        """Case-insensitive search by name, alternative names, E/INS number."""
        q = query.lower().strip()
        results = []
        for ing in self._ingredients:
            haystack = " ".join([
                ing.get("name", ""),
                ing.get("simple_name", ""),
                ing.get("alternative_names", ""),
                ing.get("e_number", "") or "",
                ing.get("ins_number", "") or "",
            ]).lower()
            if q in haystack:
                results.append(ing)
        return results

    def _normalize_name(self, name: str) -> str:
        """Normalize an ingredient name for matching: lowercase, strip, remove punctuation."""
        name = name.lower().strip()
        # Remove common prefixes/suffixes
        name = re.sub(r"^(contains?|made\s+with|including?)\s+", "", name)
        name = re.sub(r"[^\w\s]", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def match_ingredient(self, ingredient_name: str) -> Optional[Tuple[dict, float]]:
        """Try to match a raw ingredient string to a knowledge-base entry.
        Returns (ingredient_dict, confidence) where confidence is 0.0-1.0.
        Returns None if no match found."""
        name = self._normalize_name(ingredient_name)
        if not name:
            return None

        best_match = None
        best_confidence = 0.0

        for ing in self._ingredients:
            conf = 0.0

            # Exact match on main name
            if ing["name"].lower() == name:
                conf = 1.0
            # Exact match on simple name
            elif ing.get("simple_name", "").lower() == name:
                conf = 0.95
            # Contains match (knowledge base name is contained in ingredient string)
            elif ing["name"].lower() in name:
                conf = 0.85
            # Ingredient string contains knowledge base name
            elif name in ing["name"].lower():
                conf = 0.8
            # Alternative names exact match
            else:
                alt = ing.get("alternative_names", "")
                for part in alt.split(","):
                    part_clean = self._normalize_name(part)
                    if part_clean and part_clean == name:
                        conf = 0.9
                        break
                    elif part_clean and part_clean in name:
                        conf = max(conf, 0.75)
                    elif part_clean and name in part_clean:
                        conf = max(conf, 0.7)

            # E/INS number match
            e_num = ing.get("e_number") or ""
            ins_num = ing.get("ins_number") or ""
            if e_num and e_num.lower() in name:
                conf = max(conf, 0.9)
            if ins_num and ins_num.lower() in name:
                conf = max(conf, 0.9)

            if conf > best_confidence:
                best_confidence = conf
                best_match = ing

        if best_match and best_confidence >= 0.7:
            return (best_match, best_confidence)
        return None

    def match_multiple(self, ingredient_names: List[str]) -> List[dict]:
        """Match multiple ingredient strings. Returns list of match results."""
        results = []
        for raw in ingredient_names:
            match = self.match_ingredient(raw)
            if match:
                ing, conf = match
                results.append({
                    "raw_name": raw,
                    "matched": True,
                    "confidence": conf,
                    "ingredient": ing,
                })
            else:
                results.append({
                    "raw_name": raw,
                    "matched": False,
                    "confidence": 0.0,
                    "ingredient": None,
                })
        return results
