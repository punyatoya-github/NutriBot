"""Canned model outputs used by ``NUTRIBOT_DEMO=1`` (no API key / network needed).

Handy for working on the UI, taking screenshots, and testing the parser.
"""

DEMO_ANALYSIS = {
    "dish": "Pan-seared salmon with asparagus and lemon rice",
    "portion_size": "1 plate - about 420 g (salmon 150 g, rice 1 cup, asparagus 6 spears)",
    "estimated_calories": 640,
    "items": [
        {"name": "Pan-seared salmon", "portion": "150 g", "calories": 310},
        {"name": "Lemon rice", "portion": "1 cup", "calories": 240},
        {"name": "Asparagus", "portion": "6 spears", "calories": 30},
        {"name": "Olive oil & butter", "portion": "1 tbsp", "calories": 60},
    ],
    "nutrients": {
        "protein": "38 g",
        "carbohydrates": "52 g",
        "fats": "28 g",
        "vitamins": [
            {"name": "Vitamin B12", "percentage_dv": "240%"},
            {"name": "Vitamin D", "percentage_dv": "95%"},
            {"name": "Vitamin K", "percentage_dv": "70%"},
            {"name": "Vitamin B6", "percentage_dv": "55%"},
            {"name": "Vitamin C", "percentage_dv": "20%"},
        ],
        "minerals": [
            {"name": "Potassium", "amount": "980 mg"},
            {"name": "Selenium", "amount": "62 mcg"},
            {"name": "Phosphorus", "amount": "430 mg"},
            {"name": "Magnesium", "amount": "85 mg"},
            {"name": "Iron", "amount": "2.4 mg"},
        ],
    },
    "health_score": 82,
    "health_strengths": [
        "Excellent protein and omega-3 fats from the salmon",
        "Asparagus adds fibre, folate and vitamin K",
        "Balanced plate with a sensible portion of carbohydrates",
    ],
    "health_improvements": [
        "Swap part of the white rice for quinoa or brown rice for more fibre",
        "Go lighter on butter to trim saturated fat",
        "Add a second vegetable for more volume and micronutrients",
    ],
    "health_evaluation": (
        "A well-balanced, protein-forward meal. The salmon supplies high-quality protein and heart-healthy fats, "
        "while the vegetables and rice round it out with fibre and slow-release energy. Small tweaks to the grain "
        "and added fats would make it even better."
    ),
}

DEMO_RECIPES = {
    "recipes": [
        {
            "title": "Charred Veggie & Chickpea Grain Bowl",
            "ingredients": ["1 cup cooked quinoa", "1 can chickpeas, drained", "1 zucchini, sliced",
                            "1 red pepper, diced", "2 tbsp olive oil", "1 lemon, juiced", "Salt, pepper, smoked paprika"],
            "steps": ["Heat the oven to 220 C and toss the vegetables and chickpeas with oil and paprika.",
                      "Roast for 20 minutes until charred at the edges.",
                      "Spoon the quinoa into bowls and top with the roasted mix.",
                      "Finish with lemon juice, salt and pepper."],
            "calorie_estimate": 480, "cook_time_minutes": 30, "servings": 2,
        },
        {
            "title": "Creamy Coconut Tomato Soup",
            "ingredients": ["6 ripe tomatoes", "1 onion", "2 garlic cloves", "200 ml coconut milk",
                            "2 cups vegetable stock", "Fresh basil"],
            "instructions": "1. Sauté the onion and garlic until soft. 2. Add chopped tomatoes and stock and simmer for 15 minutes. "
                            "3. Blend until smooth and stir in the coconut milk. 4. Serve topped with basil.",
            "calorie_estimate": 310, "cook_time_minutes": 25, "servings": 3,
        },
        {
            "title": "Lemon-Garlic Zucchini Noodles",
            "ingredients": ["3 zucchini, spiralised", "3 garlic cloves", "1 lemon", "2 tbsp olive oil", "Chilli flakes"],
            "steps": ["Warm the oil and gently fry the garlic and chilli.",
                      "Add the zucchini noodles and cook for 2-3 minutes.",
                      "Squeeze over lemon and serve immediately."],
            "calorie_estimate": 190, "cook_time_minutes": 12, "servings": 2,
        },
    ]
}

# Deliberately messy output to exercise the parser (strings, renamed keys, dict-style vitamins...).
MESSY_ANALYSIS = {
    "dish": "Cheese <b>pizza</b> slice",
    "total_calories": "approx 285 kcal",
    "nutrients": {
        "protein": "12g", "carbs": "36 g", "fat": None,
        "vitamins": {"Calcium": "20%", "Vitamin A": "10%"},
        "minerals": ["Sodium: 640 mg", "Iron: 2 mg"],
    },
    "health_evaluation": "Tasty but high in sodium.",
}
