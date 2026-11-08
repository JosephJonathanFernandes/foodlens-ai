"""Phase 6: Unit tests for preprocessing, translation, and AI explanation services."""

import sys
import os
sys.path.insert(0, ".")

from services.preprocessing_service import preprocess, assess_quality, resize_image, enhance_contrast, reduce_noise, sharpen, adaptive_threshold, correct_rotation
from services.translation_service import TranslationService
from services.ai_explanation_service import AIExplanationService
from services.ingredient_service import IngredientService
from services.allergen_service import AllergenService
from services.claims_service import ClaimsService
from services.nutrition_service import NutritionService
from services.report_service import ReportService

import numpy as np
from PIL import Image
import io

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
print("PHASE 6: SERVICE UNIT TESTS")
print("=" * 60)


def make_test_image():
    """Create a simple test image as numpy array."""
    img = Image.new("RGB", (200, 200), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image.open(buf)


# ---- Preprocessing tests ----
print("\n--- Preprocessing ---")

# Create a temp image file
test_img = Image.new("RGB", (100, 100), color="white")
test_path = "/tmp/test_preprocess.png"
test_img.save(test_path)

# Test resize
img = np.array(test_img)
resized = resize_image(img, max_dimension=50)
check(resized.shape[0] <= 50 and resized.shape[1] <= 50, "Resize reduces image size")

# Test quality assessment
quality = assess_quality(img)
check("blur_score" in quality, "Quality assessment has blur_score")
check("brightness" in quality, "Quality assessment has brightness")
check("contrast" in quality, "Quality assessment has contrast")
check("is_blurry" in quality, "Quality assessment has is_blurry")
check(isinstance(quality["is_blurry"], bool), "Quality assessment returns boolean is_blurry")

# Test contrast enhancement
enhanced = enhance_contrast(img)
check(enhanced.shape == img.shape, "Enhanced contrast preserves shape")

# Test noise reduction
denoised = reduce_noise(img)
check(denoised.shape == img.shape, "Denoising preserves shape")

# Test sharpening
sharpened = sharpen(img)
check(sharpened.shape == img.shape, "Sharpening preserves shape")

# Test adaptive threshold
thresh = adaptive_threshold(img)
check(thresh.shape[:2] == img.shape[:2], "Adaptive threshold preserves dimensions")
# Thresholded image should be binary (0 or 255)
unique_vals = np.unique(thresh)
check(len(unique_vals) <= 2, "Adaptive threshold produces binary image")

# Test rotation correction (should not crash)
rotated = correct_rotation(img)
check(rotated.shape == img.shape, "Rotation correction preserves shape")

# Test full preprocess pipeline
processed, quality = preprocess(test_path)
check(processed is not None, "Preprocess returns processed image")
check("blur_score" in quality, "Preprocess returns quality metrics")
check(os.path.exists(test_path), "Original image preserved")

# Clean up
os.remove(test_path)

# ---- Translation tests ----
print("\n--- Translation ---")

ts_en = TranslationService(provider="mock")
ts_hi = TranslationService(provider="mock")

# Same language returns original
result = ts_en.translate("Hello", "en", "en")
check(result == "Hello", "Same language returns original")

# Mock translation adds placeholder
result = ts_hi.translate("Hello world", "hi", "en")
check("[HI" in result, "Mock translation adds language placeholder")
check("Hello world" in result, "Mock translation preserves original text")

# Empty text
result = ts_hi.translate("", "hi", "en")
check(result == "", "Empty text returns empty")

# Translate fields preserves structure
fields = {"name": "Sodium Benzoate", "value": "211", "nested": {"inner": "test"}}
translated = ts_en.translate_fields(fields, "hi")
check(translated["name"].startswith("[HI"), "Translated fields translates string values")
check(translated["value"] == "211", "Translated fields preserves numbers")

# Translate report preserves scientific terms
report = {
    "summary": "This product contains Sodium Benzoate (INS 211).",
    "product_overview": {"product_name": "Test Product", "brand": "TestCo"},
    "language": "en",
}
translated_report = ts_en.translate_report(report, "hi")
check(translated_report["language"] == "hi", "Translated report sets language")
check("INS 211" in translated_report["summary"], "Translated report preserves INS numbers")
check("Sodium Benzoate" in translated_report["summary"], "Translated report preserves ingredient names")

# ---- AI Explanation tests ----
print("\n--- AI Explanation ---")

ai = AIExplanationService(provider="mock")

# Unmatched ingredient
exp = ai.explain_ingredient(None, language="en")
check(exp["uncertain"] == True, "Unmatched ingredient marked uncertain")
check("note" in exp, "Unmatched ingredient has note")
check(exp["ai_generated"] == False, "Unmatched ingredient not AI-generated")

# KB-matched ingredient
kb_ing = {
    "name": "Sodium Benzoate",
    "simple_name": "Sodium benzoate",
    "function": "Preservative",
    "why_used": "Inhibits microbial growth",
    "is_additive": True,
    "ins_number": "211",
    "e_number": "E211",
}
exp = ai.explain_ingredient(kb_ing, language="en")
check(exp["uncertain"] == False, "KB-matched ingredient not uncertain")
check(exp["ins_number"] == "211", "KB-matched ingredient has INS number")
check(exp["is_additive"] == True, "KB-matched ingredient marked as additive")
check(exp["ai_generated"] == False, "KB ingredient not AI-generated")

# AI explain product (mock)
report = {
    "product_name": "Test Product",
    "brand": "TestCo",
    "summary": "Test summary",
    "ingredients": [],
    "allergens": {},
}
product_exp = ai.explain_product(report, language="en")
check("Test Product" in product_exp, "Product explanation includes product name")
check("Test summary" in product_exp, "Product explanation includes summary")

# Mock AI ingredient explanation
ai_exp = ai.explain_ingredient_ai("Unknown Chemical X", language="en")
check(ai_exp["ai_generated"] == True, "AI explanation marked as AI-generated")
check(ai_exp["uncertain"] == True, "AI explanation marked uncertain")
check("mock" in ai_exp.get("note", "").lower(), "AI explanation notes mock provider")

# ---- Ingredient service tests ----
print("\n--- Ingredient Service ---")

ing_svc = IngredientService()

# Search
results = ing_svc.search("sodium")
check(len(results) >= 1, "Ingredient search finds sodium benzoate")

# Get by ID
ing = ing_svc.get("sodium_benzoate")
check(ing is not None, "Ingredient get returns sodium benzoate")
check(ing["name"] == "Sodium Benzoate", "Ingredient name correct")

# Match
match = ing_svc.match_ingredient("Sodium Benzoate (INS 211)")
check(match is not None, "Ingredient match finds sodium benzoate")
kb, conf = match
check(conf >= 0.8, "Ingredient match confidence high")

# No match
match = ing_svc.match_ingredient("Unknown Chemical")
check(match is None, "Ingredient match returns None for unknown")

# List all
all_ings = ing_svc.list_all()
check(len(all_ings) >= 5, "Ingredient service has multiple ingredients")

# ---- Allergen service tests ----
print("\n--- Allergen Service ---")

alg_svc = AllergenService()

# Detect declared allergen
result = alg_svc.detect("Contains: Wheat, Milk")
check("wheat" in result, "Allergen detection finds wheat")
check("milk" in result, "Allergen detection finds milk")
check(result["wheat"]["warning_type"] == "declared", "Wheat is declared allergen")

# Detect may contain
result = alg_svc.detect("May contain: Peanuts")
check("peanuts" in result, "Allergen detection finds peanuts in may contain")
check(result["peanuts"]["warning_type"] == "may_contain", "Peanuts marked may_contain")

# Detect cross contamination
result = alg_svc.detect("Produced in a facility that also processes tree nuts")
check("tree_nuts" in result, "Allergen detection finds tree nuts")
check(result["tree_nuts"]["warning_type"] == "cross_contamination", "Tree nuts marked cross_contamination")

# No allergens
result = alg_svc.detect("Ingredients: Sugar, Salt, Water")
check(len(result) == 0, "No allergens in simple ingredients")

# Summary
summary = alg_svc.summary({"wheat": {"warning_type": "declared"}})
check("wheat" in summary.lower(), "Summary mentions wheat")

# ---- Claims service tests ----
print("\n--- Claims Service ---")

claim_svc = ClaimsService()

# Detect claims
claims = claim_svc.detect("No added sugar Fortified with iron Organic")
claim_names = [c["claim"] for c in claims]
check("no_added_sugar" in claim_names, "Claims service detects no added sugar")
check("fortified" in claim_names, "Claims service detects fortified")
check("organic" in claim_names, "Claims service detects organic")

# Check claim structure
for c in claims:
    check("meaning" in c and len(c["meaning"]) > 0, f"Claim {c['claim']} has meaning")
    check("caveat" in c and len(c["caveat"]) > 0, f"Claim {c['claim']} has caveat")
    check(c["verified"] == False, f"Claim {c['claim']} not verified")

# No claims
claims = claim_svc.detect("Ingredients: Sugar, Salt")
check(len(claims) == 0, "No claims in simple ingredients")

# ---- Nutrition service tests ----
print("\n--- Nutrition Service ---")

nut_svc = NutritionService()

# Parse nutrition
label = "Energy 350 kcal\nProtein 6g\nTotal Fat 12g\nSodium 300mg"
nutrition = nut_svc.parse(label)
check(nutrition["energy"] is not None, "Nutrition parse finds energy")
check(nutrition["energy"]["value"] == "350", "Nutrition parse energy value correct")
check(nutrition["protein"]["value"] == "6", "Nutrition parse protein value correct")
check(nutrition["sodium"]["value"] == "300", "Nutrition parse sodium value correct")

# Explain nutrition
exp = nut_svc.explain("energy", "350", "kcal")
check("350" in exp, "Nutrition explain includes value")
check("kcal" in exp, "Nutrition explain includes unit")

# Normalize to per 100g
norm = nut_svc.normalize_to_per_100g({"energy": {"value": "200", "unit": "kcal", "basis": "per_serving"}}, serving_size_g=50)
check(norm["energy"]["normalized_value"] == 400.0, "Nutrition normalize to per 100g works")

# ---- Report service tests ----
print("\n--- Report Service ---")

rep_svc = ReportService()

# Build report
report = rep_svc.build_report(
    scan_id="test-123",
    product_name="Test Product",
    brand="TestCo",
    ingredients=[{"name": "Sugar", "is_additive": False}],
    nutrition={"energy": {"value": "350", "unit": "kcal"}},
    allergens={"wheat": {"warning_type": "declared"}},
    claims=[{"claim": "natural", "meaning": "test", "caveat": "test"}],
    ocr_text="Test OCR text",
    language="en",
)

check(report["product_overview"]["scan_id"] == "test-123", "Report has scan_id")
check(report["product_overview"]["product_name"] == "Test Product", "Report has product name")
check(len(report["ingredients"]) == 1, "Report has 1 ingredient")
check(len(report["warnings"]) > 0, "Report has warnings")
check("summary" in report, "Report has summary")
check(len(report["summary"]) > 0, "Report summary not empty")

# Translate report
translated = rep_svc.translate_report(report, "hi", TranslationService(provider="mock"))
check(translated["language"] == "hi", "Translated report sets language")
check("[HI" in translated["summary"], "Translated report summary has placeholder")

# Explain everything (mock)
exp_everything = rep_svc.explain_everything(report, ai, language="en")
check("Test Product" in exp_everything, "Explain everything includes product name")

print()
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL PHASE 6 SERVICE TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    exit(1)
