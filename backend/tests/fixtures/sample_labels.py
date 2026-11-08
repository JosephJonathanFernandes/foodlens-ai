# Sample Food Label Text Fixtures for Testing
# These are used by backend tests to verify extraction pipeline

LABEL_BISCUITS = """
TestCo Biscuits
Brand: TestCo Foods
Net Weight: 100g
Ingredients: Wheat Flour, Sugar, Vegetable Oil, Milk Solids, Salt, Sodium Benzoate (INS 211), Maltodextrin, Artificial Colour (INS 102)
Nutrition Information per 100g:
Energy 350 kcal
Protein 6g
Total Fat 12g
Saturated Fat 4g
Trans Fat 0g
Carbohydrate 55g
Total Sugars 20g
Added Sugars 5g
Dietary Fibre 3g
Sodium 300mg
Salt 0.8g
Contains: Wheat, Milk
May contain: Peanuts
Manufactured by: TestCo Foods Pvt Ltd
FSSAI Licence: 100123456789
Best Before: 6 months from manufacturing
Store in a cool dry place
"""

LABEL_NO_ALLERGENS = """
Pure Honey
Brand: NatureFresh
Ingredients: Honey
Nutrition Information per 100g:
Energy 304 kcal
Protein 0.3g
Total Fat 0g
Carbohydrate 82g
Total Sugars 82g
No added preservatives
Store at room temperature
"""

LABEL_MULTI_LANGUAGE = """
Test Product
मटेरिअल: गेहूं का आटा, शक्कर
Ingredients: Wheat Flour, Sugar, Milk Powder
ปริมาณสุทธิ: 200 ग्राम
Contains: Wheat, Milk
"""

LABEL_BLURRY_SMALL_TEXT = """
Product: X
Ingredients: [small text - hard to read]
Nutrition: [unclear]
"""

EXPECTED_BISCUITS_INGREDIENTS = [
    "Wheat Flour",
    "Sugar",
    "Vegetable Oil",
    "Milk Solids",
    "Salt",
    "Sodium Benzoate (INS 211)",
    "Maltodextrin",
    "Artificial Colour (INS 102)",
]

EXPECTED_BISCUITS_NUTRITION = {
    "energy": {"value": "350", "unit": "kcal"},
    "protein": {"value": "6", "unit": "g"},
    "fat": {"value": "12", "unit": "g"},
    "sat_fat": {"value": "4", "unit": "g"},
    "trans_fat": {"value": "0", "unit": "g"},
    "carb": {"value": "55", "unit": "g"},
    "sugar": {"value": "20", "unit": "g"},
    "added_sugar": {"value": "5", "unit": "g"},
    "fibre": {"value": "3", "unit": "g"},
    "sodium": {"value": "300", "unit": "mg"},
    "salt": {"value": "0.8", "unit": "g"},
}

EXPECTED_BISCUITS_ALLERGENS = {
    "wheat": {"declared": True, "warning_type": "declared"},
    "milk": {"declared": True, "warning_type": "declared"},
    "peanuts": {"declared": False, "warning_type": "may_contain"},
}
