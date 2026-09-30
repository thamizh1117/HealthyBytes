"""
HealthyBytes: Personalized Calorie and Nutrition Planner
A Flask web application that calculates BMR, TDEE, and macro-nutrient
targets based on user inputs (age, gender, weight, height, activity
level, and goal).
"""

from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# ---------------------------------------------------------------------------
# Activity level multipliers (used to convert BMR -> TDEE)
# ---------------------------------------------------------------------------
ACTIVITY_LEVELS = {
    "sedentary": {
        "label": "Sedentary (little or no exercise)",
        "multiplier": 1.2,
    },
    "light": {
        "label": "Lightly active (light exercise 1-3 days/week)",
        "multiplier": 1.375,
    },
    "moderate": {
        "label": "Moderately active (moderate exercise 3-5 days/week)",
        "multiplier": 1.55,
    },
    "active": {
        "label": "Very active (hard exercise 6-7 days/week)",
        "multiplier": 1.725,
    },
    "athlete": {
        "label": "Extremely active (very hard exercise, physical job)",
        "multiplier": 1.9,
    },
}

# ---------------------------------------------------------------------------
# Goals: calorie adjustment (kcal/day) and macro split (protein/carb/fat %)
# ---------------------------------------------------------------------------
GOALS = {
    "lose": {
        "label": "Lose weight",
        "calorie_adjustment": -500,
        "macros": {"protein": 0.35, "carbs": 0.35, "fat": 0.30},
    },
    "maintain": {
        "label": "Maintain weight",
        "calorie_adjustment": 0,
        "macros": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
    },
    "gain": {
        "label": "Gain muscle",
        "calorie_adjustment": 350,
        "macros": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
    },
}

MIN_CALORIES_FEMALE = 1200
MIN_CALORIES_MALE = 1500


def calculate_bmr(gender, weight_kg, height_cm, age):
    """Mifflin-St Jeor Equation for Basal Metabolic Rate."""
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if gender == "male":
        return base + 5
    else:
        return base - 161


def calculate_plan(gender, age, weight_kg, height_cm, activity, goal):
    """Return a dict with BMR, TDEE, target calories, and macro grams."""
    bmr = calculate_bmr(gender, weight_kg, height_cm, age)
    activity_multiplier = ACTIVITY_LEVELS[activity]["multiplier"]
    tdee = bmr * activity_multiplier

    goal_info = GOALS[goal]
    target_calories = tdee + goal_info["calorie_adjustment"]

    # Enforce a safe minimum calorie floor
    floor = MIN_CALORIES_MALE if gender == "male" else MIN_CALORIES_FEMALE
    target_calories = max(target_calories, floor)

    macros_pct = goal_info["macros"]
    # 1g protein = 4 kcal, 1g carbs = 4 kcal, 1g fat = 9 kcal
    protein_g = (target_calories * macros_pct["protein"]) / 4
    carbs_g = (target_calories * macros_pct["carbs"]) / 4
    fat_g = (target_calories * macros_pct["fat"]) / 9

    # Simple hydration guideline: 35 ml per kg body weight
    water_ml = weight_kg * 35

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "target_calories": round(target_calories),
        "protein_g": round(protein_g),
        "carbs_g": round(carbs_g),
        "fat_g": round(fat_g),
        "water_ml": round(water_ml),
        "water_l": round(water_ml / 1000, 1),
        "activity_label": ACTIVITY_LEVELS[activity]["label"],
        "goal_label": goal_info["label"],
        "macros_pct": macros_pct,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        activity_levels=ACTIVITY_LEVELS,
        goals=GOALS,
    )


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        name = request.form.get("name", "").strip() or "there"
        gender = request.form["gender"]
        age = int(request.form["age"])
        weight = float(request.form["weight"])
        weight_unit = request.form.get("weight_unit", "kg")
        height = float(request.form["height"])
        height_unit = request.form.get("height_unit", "cm")
        activity = request.form["activity"]
        goal = request.form["goal"]

        # Normalize units to metric
        weight_kg = weight * 0.453592 if weight_unit == "lb" else weight
        height_cm = height * 2.54 if height_unit == "in" else height

        if age <= 0 or age > 120 or weight_kg <= 0 or height_cm <= 0:
            raise ValueError("Values out of expected range.")

        if activity not in ACTIVITY_LEVELS or goal not in GOALS:
            raise ValueError("Invalid activity level or goal.")

        plan = calculate_plan(gender, age, weight_kg, height_cm, activity, goal)
        plan["name"] = name

        return render_template("results.html", plan=plan)

    except (KeyError, ValueError) as e:
        return render_template(
            "index.html",
            activity_levels=ACTIVITY_LEVELS,
            goals=GOALS,
            error="Please check your inputs and try again. All fields are required and must be valid numbers.",
        )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
