"""Ingredient service: knowledge-base lookup and ingredient explanations."""

import json
from pathlib import Path
from typing import List, Optional, Dict

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

    def match_ingredient(self, ingredient_name: str) -> Optional[dict]:
        """Try to match a raw ingredient string to a knowledge-base entry."""
        name = ingredient_name.lower().strip()
        # Direct name match
        for ing in self._ingredients:
            if ing["name"].lower() == name:
                return ing
        # Alternative names
        for ing in self._ingredients:
            alt = ing.get("alternative_names", "")
            for part in alt.split(","):
                if part.strip().lower() == name:
                    return ing
        return None
