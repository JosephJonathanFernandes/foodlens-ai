"""Phase 3 extraction tests using sample label text fixtures (no OCR required)."""

import sys, json
sys.path.insert(0, ".")
sys.path.insert(0, "tests")

from services.ingredient_service import IngredientService
from services.nutrition_service import NutritionService
from services.allergen_service import AllergenService
from services.claims_service import ClaimsService
from services.ai_explanation_service import AIExplanationService
from services.text_extraction_service import TextExtractionService
from tests.fixtures.sample_labels import (
    LABEL_BISCUITS,
    LABEL_NO_ALLERGENS,
    EXPECTED_BISCUITS_INGREDIENTS,
    EXPECTED_BISCUITS_NUTRITION,
    EXPECTED_BISCUITS_ALLERGENS,
)

passed = 0
failed = 0

def check(condition, msg):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {msg}")
    else:
        failed += 1
        print(f"  FAIL: {msg}")

print("=" * 60)
print("PHASE 3 EXTRACTION TESTS (using fixtures)")
print("=" * 60)

ing_svc = IngredientService()
nut_svc = NutritionService()
alg_svc = AllergenService()
claim_svc = ClaimsService()
ai_svc = AIExplanationService()
text_svc = TextExtractionService()

# ---- Ingredient matching ----
print("\n--- Ingredient Matching ---")
for raw in EXPECTED_BISCUITS_INGREDIENTS:
    match = ing_svc.match_ingredient(raw)
    if match:
        kb, conf = match
        check(True, f"'{raw}' matched '{kb['name']}' (conf={conf:.2f})")
    else:
        check(False, f"'{raw}' NOT matched")

# Unmatched ingredient should not crash
result = ing_svc.match_ingredient("Unknown Chemical Z")
check(result is None, "Unknown ingredient returns None")

# ---- Nutrition parsing ----
print("\n--- Nutrition Parsing ---")
nutrition = nut_svc.parse(LABEL_BISCUITS)
for nutrient, expected in EXPECTED_BISCUITS_NUTRITION.items():
    data = nutrition.get(nutrient)
    check(data is not None, f"{nutrient} found")
    if data:
        check(data.get("value") == expected["value"], f"{nutrient} value={data['value']}")
        check(data.get("unit") == expected["unit"], f"{nutrient} unit={data['unit']}")

# No-allergens label should still parse nutrition
nutrition2 = nut_svc.parse(LABEL_NO_ALLERGENS)
check(nutrition2["energy"] is not None, "Honey label has energy value")

# ---- Allergen detection ----
print("\n--- Allergen Detection ---")
allergens = alg_svc.detect(LABEL_BISCUITS)
for allergen, expected in EXPECTED_BISCUITS_ALLERGENS.items():
    data = allergens.get(allergen)
    check(data is not None, f"{allergen} detected")
    if data:
        check(data["declared"] == expected["declared"], f"{allergen} declared={data['declared']}")
        check(data["warning_type"] == expected["warning_type"], f"{allergen} type={data['warning_type']}")

# No-allergen label
allergens2 = alg_svc.detect(LABEL_NO_ALLERGENS)
check(len(allergens2) == 0, "Honey label has no allergens")

summary = alg_svc.summary(allergens)
check("Wheat" in summary or "wheat" in summary.lower(), "Summary mentions wheat")

# ---- Claims detection ----
print("\n--- Claims Detection ---")
claims = claim_svc.detect(LABEL_BISCUITS)
claim_names = [c["claim"] for c in claims]
print(f"  Claims found in biscuits label: {claim_names}")
# Biscuits label has no marketing claims, so this should be empty
check(len(claims) == 0, "Biscuits label has no marketing claims")

# Test claims on a label that has them
claims_label = "No added sugar Fortified with iron Organic Low fat Natural"
claims2 = claim_svc.detect(claims_label)
claim_names2 = [c["claim"] for c in claims2]
check("no_added_sugar" in claim_names2, "Detects 'no added sugar' claim")
check("fortified" in claim_names2, "Detects 'fortified' claim")
check("organic" in claim_names2, "Detects 'organic' claim")

for c in claims2:
    check(c["meaning"] is not None and len(c["meaning"]) > 0, f"Claim '{c['claim']}' has meaning")
    check(c["caveat"] is not None and len(c["caveat"]) > 0, f"Claim '{c['claim']}' has caveat")
    check(c["verified"] is False, f"Claim '{c['claim']}' is not independently verified")

# ---- AI Explanation ----
print("\n--- AI Explanation ---")
kb_match = ing_svc.match_ingredient("Sodium Benzoate")
kb_ing, conf = kb_match
explanation = ai_svc.explain_ingredient(kb_ing, language="en")
check(explanation["ingredient"] == "Sodium Benzoate", "Explanation has ingredient name")
check(explanation["ins_number"] == "211", "Explanation has INS number")
check(explanation["is_additive"] == True, "Marked as additive")
check(explanation["uncertain"] == False, "Not uncertain for KB match")

# Unmatched ingredient explanation
explanation2 = ai_svc.explain_ingredient(None, language="en")
check(explanation2["uncertain"] == True, "Unmatched marked uncertain")
check("note" in explanation2, "Has note for unmatched")

# ---- Text classification ----
print("\n--- Text Classification ---")
classified = text_svc.classify_sections(LABEL_BISCUITS)
sections = {c.section for c in classified}
check("ingredients" in sections, "Classifies ingredients section")
check("nutrition" in sections, "Classifies nutrition section")
check("allergens" in sections, "Classifies allergens section")

# Claims section should be detected on a label with claims
claims_label = "No added sugar\nFortified with iron\nNatural"
classified2 = text_svc.classify_sections(claims_label)
sections2 = {c.section for c in classified2}
check("claims" in sections2, "Classifies claims section on label with claims")

# ---- Field extraction ----
print("\n--- Field Extraction ---")
fields = text_svc.extract_fields(LABEL_BISCUITS, source_image="img1")
field_names = [f.name for f in fields]
check("product_name" in field_names, "Extracts product name")
check("brand" in field_names, "Extracts brand")

print()
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL PHASE 3 FIXTURE TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    sys.exit(1)
