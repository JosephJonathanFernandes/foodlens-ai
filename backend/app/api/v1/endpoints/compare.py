"""Product comparison endpoint with real comparison logic."""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database.session import SessionLocal
from models import scan as models
from schemas import scan as schemas
from services.nutrition_service import NutritionService
from services.ingredient_service import IngredientService


router = APIRouter()
nutrition_service = NutritionService()
ingredient_service = IngredientService()


def ingredient_service_get(kb_id: Optional[str]) -> Optional[dict]:
    """Lazy helper to look up a knowledge-base ingredient by id."""
    return ingredient_service.get(kb_id) if kb_id else None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _safe_float(val: Optional[str]) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _normalize_per_100g(nutrition_list: List[dict]) -> Dict[str, Optional[dict]]:
    """Normalize nutrition values to per 100g where possible."""
    result: Dict[str, Optional[dict]] = {}
    for n in nutrition_list:
        nutrient = n.get("nutrient")
        value = _safe_float(n.get("value"))
        unit = n.get("unit")
        basis = n.get("basis")
        normalized = n.get("normalized_value")

        if value is None:
            result[nutrient] = None
            continue

        # If we have a pre-computed normalized value, use it
        if normalized is not None:
            try:
                result[nutrient] = {
                    "value": float(normalized),
                    "unit": unit,
                    "basis": "per_100g",
                }
            except (ValueError, TypeError):
                result[nutrient] = {
                    "value": value,
                    "unit": unit,
                    "basis": basis,
                }
            continue

        # If already per 100g, use as-is
        if basis == "per_100g":
            result[nutrient] = {
                "value": value,
                "unit": unit,
                "basis": "per_100g",
            }
            continue

        # Per serving without serving size - can't normalize
        result[nutrient] = {
            "value": value,
            "unit": unit,
            "basis": basis or "unknown",
        }
    return result


def _compare_nutrition(
    a_nutrition: List[dict], b_nutrition: List[dict]
) -> Dict[str, Any]:
    """Compare nutrition between two products, normalized to per 100g."""
    a_norm = _normalize_per_100g(a_nutrition)
    b_norm = _normalize_per_100g(b_nutrition)

    all_nutrients = set(list(a_norm.keys()) + list(b_norm.keys()))
    comparison = {}

    # Priority order for display
    priority = [
        "energy", "protein", "fat", "sat_fat", "trans_fat",
        "carb", "sugar", "added_sugar", "fibre", "sodium", "salt", "cholesterol",
    ]
    ordered = [n for n in priority if n in all_nutrients] + [
        n for n in sorted(all_nutrients) if n not in priority
    ]

    for nutrient in ordered:
        a_val = a_norm.get(nutrient)
        b_val = b_norm.get(nutrient)

        comparison[nutrient] = {
            "product_a": a_val,
            "product_b": b_val,
            "unit": (a_val or b_val or {}).get("unit") if (a_val or b_val) else None,
        }

        # Determine which is higher (for trade-off explanation, not a winner)
        if a_val and b_val and a_val.get("value") is not None and b_val.get("value") is not None:
            av = a_val["value"]
            bv = b_val["value"]
            if av > bv:
                comparison[nutrient]["higher"] = "a"
                comparison[nutrient]["difference"] = round(av - bv, 2)
            elif bv > av:
                comparison[nutrient]["higher"] = "b"
                comparison[nutrient]["difference"] = round(bv - av, 2)
            else:
                comparison[nutrient]["higher"] = "equal"
                comparison[nutrient]["difference"] = 0

    return comparison


def _compare_ingredients(
    a_ingredients: List[dict], b_ingredients: List[dict]
) -> Dict[str, Any]:
    """Compare ingredients between two products."""
    a_names = set()
    b_names = set()
    a_additives = set()
    b_additives = set()

    for ing in a_ingredients:
        name = ing.get("ingredient", {}).get("name") or ing.get("raw_name", "")
        a_names.add(name.lower())
        if ing.get("ingredient", {}).get("is_additive"):
            a_additives.add(name.lower())

    for ing in b_ingredients:
        name = ing.get("ingredient", {}).get("name") or ing.get("raw_name", "")
        b_names.add(name.lower())
        if ing.get("ingredient", {}).get("is_additive"):
            b_additives.add(name.lower())

    common = a_names & b_names
    only_a = a_names - b_names
    only_b = b_names - a_names

    return {
        "product_a_count": len(a_names),
        "product_b_count": len(b_names),
        "common": sorted(common),
        "only_in_a": sorted(only_a),
        "only_in_b": sorted(only_b),
        "additives_a": len(a_additives),
        "additives_b": len(b_additives),
        "common_additives": sorted(a_additives & b_additives),
        "only_additives_a": sorted(a_additives - b_additives),
        "only_additives_b": sorted(b_additives - b_additives),
    }


def _compare_allergens(
    a_allergens: List[dict], b_allergens: List[dict]
) -> Dict[str, Any]:
    """Compare allergens between two products."""
    a_set = set()
    b_set = set()
    a_may = set()
    b_may = set()

    for al in a_allergens:
        name = al.get("allergen", "")
        a_set.add(name.lower())
        if al.get("warning_type") == "may_contain":
            a_may.add(name.lower())

    for al in b_allergens:
        name = al.get("allergen", "")
        b_set.add(name.lower())
        if al.get("warning_type") == "may_contain":
            b_may.add(name.lower())

    return {
        "product_a": sorted(a_set),
        "product_b": sorted(b_set),
        "common": sorted(a_set & b_set),
        "only_in_a": sorted(a_set - b_set),
        "only_in_b": sorted(b_set - a_set),
        "may_contain_a": sorted(a_may),
        "may_contain_b": sorted(b_may),
    }


def _compare_claims(
    a_claims: List[dict], b_claims: List[dict]
) -> Dict[str, Any]:
    """Compare marketing claims between two products."""
    a_set = set(c.get("claim", "") for c in a_claims)
    b_set = set(c.get("claim", "") for c in b_claims)

    return {
        "product_a": sorted(a_set),
        "product_b": sorted(b_set),
        "common": sorted(a_set & b_set),
        "only_in_a": sorted(a_set - b_set),
        "only_in_b": sorted(b_set - a_set),
    }


@router.post("", response_model=schemas.CompareResponse, tags=["compare"])
def compare(request: schemas.CompareRequest, db: Session = Depends(get_db)):
    a = db.query(models.Scan).filter(models.Scan.id == request.scan_id_a).first()
    b = db.query(models.Scan).filter(models.Scan.id == request.scan_id_b).first()
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both scans not found")

    # Fetch extracted data
    a_ingredients = [
        {
            "raw_name": ei.raw_name,
            "matched": ei.matched,
            "confidence": ei.confidence,
            "kb_id": ei.kb_id,
            "ingredient": (
                {
                    "name": (ingredient_service_get(ei.kb_id) or {}).get("name"),
                    "simple_name": (ingredient_service_get(ei.kb_id) or {}).get("simple_name"),
                    "is_additive": (ingredient_service_get(ei.kb_id) or {}).get("is_additive", False),
                }
                if ei.kb_id else None
            ),
        }
        for ei in db.query(models.ExtractedIngredient)
        .filter(models.ExtractedIngredient.scan_id == request.scan_id_a).all()
    ]
    b_ingredients = [
        {
            "raw_name": ei.raw_name,
            "matched": ei.matched,
            "confidence": ei.confidence,
            "kb_id": ei.kb_id,
            "ingredient": (
                {
                    "name": (ingredient_service_get(ei.kb_id) or {}).get("name"),
                    "simple_name": (ingredient_service_get(ei.kb_id) or {}).get("simple_name"),
                    "is_additive": (ingredient_service_get(ei.kb_id) or {}).get("is_additive", False),
                }
                if ei.kb_id else None
            ),
        }
        for ei in db.query(models.ExtractedIngredient)
        .filter(models.ExtractedIngredient.scan_id == request.scan_id_b).all()
    ]

    a_nutrition = [
        {
            "nutrient": n.nutrient,
            "value": n.value,
            "unit": n.unit,
            "basis": n.basis,
            "normalized_value": n.normalized_value,
        }
        for n in db.query(models.ExtractedNutrition)
        .filter(models.ExtractedNutrition.scan_id == request.scan_id_a).all()
    ]
    b_nutrition = [
        {
            "nutrient": n.nutrient,
            "value": n.value,
            "unit": n.unit,
            "basis": n.basis,
            "normalized_value": n.normalized_value,
        }
        for n in db.query(models.ExtractedNutrition)
        .filter(models.ExtractedNutrition.scan_id == request.scan_id_b).all()
    ]

    a_allergens = [
        {
            "allergen": al.allergen,
            "declared": al.declared,
            "warning_type": al.warning_type,
        }
        for al in db.query(models.ExtractedAllergen)
        .filter(models.ExtractedAllergen.scan_id == request.scan_id_a).all()
    ]
    b_allergens = [
        {
            "allergen": al.allergen,
            "declared": al.declared,
            "warning_type": al.warning_type,
        }
        for al in db.query(models.ExtractedAllergen)
        .filter(models.ExtractedAllergen.scan_id == request.scan_id_b).all()
    ]

    a_claims = [
        {"claim": c.claim, "meaning": c.meaning, "caveat": c.caveat}
        for c in db.query(models.ExtractedClaim)
        .filter(models.ExtractedClaim.scan_id == request.scan_id_a).all()
    ]
    b_claims = [
        {"claim": c.claim, "meaning": c.meaning, "caveat": c.caveat}
        for c in db.query(models.ExtractedClaim)
        .filter(models.ExtractedClaim.scan_id == request.scan_id_b).all()
    ]

    # Build comparison
    nutrition_comp = _compare_nutrition(a_nutrition, b_nutrition)
    ingredients_comp = _compare_ingredients(a_ingredients, b_ingredients)
    allergens_comp = _compare_allergens(a_allergens, b_allergens)
    claims_comp = _compare_claims(a_claims, b_claims)

    # Build trade-off explanation (no universal winner)
    trade_offs = _build_trade_offs(nutrition_comp, ingredients_comp, allergens_comp, claims_comp)

    comparison = {
        "scan_id_a": {"id": a.id, "product_name": a.product_name, "brand": a.brand},
        "scan_id_b": {"id": b.id, "product_name": b.product_name, "brand": b.brand},
        "nutrition": nutrition_comp,
        "ingredients": ingredients_comp,
        "allergens": allergens_comp,
        "claims": claims_comp,
        "trade_offs": trade_offs,
        "note": "Comparison based on extracted label data. Values normalized to per 100g where possible. "
                "No universal winner is declared; each product has trade-offs depending on your dietary needs.",
    }

    return schemas.CompareResponse(
        scan_id_a=request.scan_id_a,
        scan_id_b=request.scan_id_b,
        comparison=comparison,
    )


def _build_trade_offs(
    nutrition: Dict[str, Any],
    ingredients: Dict[str, Any],
    allergens: Dict[str, Any],
    claims: Dict[str, Any],
) -> List[str]:
    """Build human-readable trade-off explanations. No universal winner."""
    offs: List[str] = []

    # Sugar trade-off
    sugar = nutrition.get("sugar", {})
    if sugar.get("product_a") and sugar.get("product_b"):
        av = sugar["product_a"].get("value")
        bv = sugar["product_b"].get("value")
        if av and bv:
            if av < bv:
                offs.append(
                    f"Product A has less total sugar ({av}{sugar.get('unit','')} vs {bv}{sugar.get('unit','')} per 100g), "
                    f"which may be preferable if you're watching sugar intake."
                )
            elif bv < av:
                offs.append(
                    f"Product B has less total sugar ({bv}{sugar.get('unit','')} vs {av}{sugar.get('unit','')} per 100g), "
                    f"which may be preferable if you're watching sugar intake."
                )

    # Sodium trade-off
    sodium = nutrition.get("sodium", {})
    if sodium.get("product_a") and sodium.get("product_b"):
        av = sodium["product_a"].get("value")
        bv = sodium["product_b"].get("value")
        if av and bv:
            if av < bv:
                offs.append(
                    f"Product A has less sodium ({av}{sodium.get('unit','')} vs {bv}{sodium.get('unit','')} per 100g)."
                )
            elif bv < av:
                offs.append(
                    f"Product B has less sodium ({bv}{sodium.get('unit','')} vs {av}{sodium.get('unit','')} per 100g)."
                )

    # Additives trade-off
    if ingredients.get("additives_a") and ingredients.get("additives_b"):
        if ingredients["additives_a"] < ingredients["additives_b"]:
            offs.append(
                f"Product A has fewer additives ({ingredients['additives_a']} vs {ingredients['additives_b']})."
            )
        elif ingredients["additives_b"] < ingredients["additives_a"]:
            offs.append(
                f"Product B has fewer additives ({ingredients['additives_b']} vs {ingredients['additives_a']})."
            )

    # Allergens
    if allergens.get("only_in_a"):
        offs.append(
            f"Product A contains allergens not in Product B: {', '.join(allergens['only_in_a'])}."
        )
    if allergens.get("only_in_b"):
        offs.append(
            f"Product B contains allergens not in Product A: {', '.join(allergens['only_in_b'])}."
        )

    # Claims unique to each
    if claims.get("only_in_a"):
        offs.append(
            f"Product A makes claims not found in Product B: {', '.join(claims['only_in_a'])}."
        )
    if claims.get("only_in_b"):
        offs.append(
            f"Product B makes claims not found in Product A: {', '.join(claims['only_in_b'])}."
        )

    if not offs:
        offs.append(
            "The products are nutritionally similar based on extracted label data. "
            "Choose based on your personal dietary preferences and needs."
        )

    return offs
