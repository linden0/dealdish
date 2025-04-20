from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

API_KEY = "1bc9ff863b244bcdb0ff81d14084e9d1"  # Replace with your key

restriction_to_query = {
    "keto": {"maxCarbs": 20, "minFat": 40, "maxSugar": 5, "excludeIngredients": "sugar,flour,grains,beans"},
    "diabetes": {"maxCarbs": 45, "maxSugar": 5, "maxCalories": 500, "excludeIngredients": "added sugar,high fructose corn syrup"},
    "celiac": {"intolerances": "gluten", "excludeIngredients": "wheat,barley,rye,farro"},
    "pku": {"maxProtein": 5, "excludeIngredients": "meat,fish,eggs,dairy,nuts,soy,wheat"},
    "renal": {"maxProtein": 40, "maxSodium": 1500, "maxPotassium": 2000, "maxPhosphorus": 1000, "excludeIngredients": "bananas,tomatoes,potatoes,dairy,beans,nuts"},
    "hypertension": {"maxSodium": 1400, "excludeIngredients": "salt,sodium,salty snacks,processed meat"},
    "gout": {"excludeIngredients": "red meat,organ meat,anchovies,sardines,beer", "maxProtein": 60},
    "low-fodmap": {"excludeIngredients": "garlic,onion,wheat,apples,beans,broccoli,honey"},
    "high-protein": {"minProtein": 30, "maxCarbs": 50, "maxFat": 30},
    "low-sodium": {"maxSodium": 140},
    "low-calorie": {"maxCalories": 300},
    "caffeine-free": {"maxCaffeine": 0},
    "heart-healthy": {"maxSaturatedFat": 5, "maxCholesterol": 100, "maxSodium": 150}
}


def build_complex_search_call(restriction, api_key, number=10):
    base_url = "https://api.spoonacular.com/recipes/complexSearch"
    params = restriction_to_query.get(restriction, {}).copy()

    params.update({
        "number": number,
        "instructionsRequired": "true",
        "addRecipeNutrition": "true",
        "apiKey": api_key
    })

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API error {response.status_code}: {response.text}")


@app.route("/recipes", methods=["GET"])
def get_recipes():
    restriction = request.args.get("restriction", "gout")
    budget = float(request.args.get("budget", 10))
    num_recipes = int(request.args.get("number", 10))

    IS_HARDCODED = False
    if IS_HARDCODED:
        with open("recipes.json", "r") as f:
          results = json.load(f)
    else:
        results = build_complex_search_call(restriction, API_KEY, num_recipes)
       

    sorted_results = sorted(results.get("results", []), key=lambda r: r.get('pricePerServing', 0) * r.get('servings', 1))
    recipes = []

    for r in sorted_results:
        total_cost = r.get('pricePerServing', 0) * r.get('servings', 1) / 100  # pricePerServing is in cents
        if total_cost <= budget:
            steps = []
            ingredients = set()
            for instruction in r.get('analyzedInstructions', []):
                for step in instruction.get("steps", []):
                    steps.append(step.get("step", ""))
                    for ing in step.get("ingredients", []):
                        ingredients.add((ing.get("name"), ing.get("image")))
            recipes.append({
                "title": r["title"],
                "id": r["id"],
                "totalPrice": round(total_cost, 2),
                "pricePerServing": round(r.get("pricePerServing", 0) / 100, 2),
                "servings": r.get("servings", 1),
                "image": r["image"],
                "readyInMinutes": r["readyInMinutes"],
                "steps": steps,
                "ingredients": list(ingredients)
            })

    return jsonify(recipes)


if __name__ == "__main__":
    app.run(debug=True)
