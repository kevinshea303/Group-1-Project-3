import streamlit as st
import os, sys, requests, re
from dotenv import load_dotenv
from io import StringIO
import google.generativeai as genai

# ──────── Load API Keys ────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services')))
load_dotenv()
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

BASE_URL = "https://api.spoonacular.com"

# ──────── Utilities ────────
def slugify(title: str, rid: int) -> str:
    s = re.sub(r"[^a-z0-9\- ]", "", title.lower())
    s = re.sub(r"\s+", "-", s)
    return f"https://spoonacular.com/recipes/{s}-{rid}"

def clean_csv(text: str) -> str:
    return ",".join([t.strip() for t in text.split(",") if t.strip()])

def pantry_match(recipe, inv_set):
    for ing in recipe["usedIngredients"]:
        if any(word in ing["name"].lower() for word in inv_set):
            return True
    return False

def search_recipes(inventory, number=20):
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": inventory,
        "number": number,
        "ranking": 1,
        "ignorePantry": True
    }
    r = requests.get(f"{BASE_URL}/recipes/findByIngredients", params=params)
    r.raise_for_status()
    return r.json()

def filter_recipes_with_inventory(recipes, inventory, max_count=7):
    inventory_set = set(i.strip().lower() for i in inventory.split(","))
    filtered = []
    seen = set()
    for recipe in recipes:
        if recipe["title"] in seen:
            continue
        used = {i["name"].lower() for i in recipe["usedIngredients"]}
        if used & inventory_set:
            filtered.append(recipe)
            seen.add(recipe["title"])
        if len(filtered) >= max_count:
            break
    return filtered

def extract_shopping_list(recipes, inventory):
    inventory_set = set(i.strip().lower() for i in inventory.split(","))
    shopping_items = {}
    for recipe in recipes:
        for ingredient in recipe.get("missedIngredients", []):
            name = ingredient["name"].strip().lower()
            amount = f"{ingredient.get('amount', '')} {ingredient.get('unit', '')}".strip()
            if name not in inventory_set and name not in shopping_items:
                shopping_items[name] = amount
    return shopping_items

def get_substitution_suggestion(ingredient_name):
    try:
        prompt = f"Suggest one or two common substitutes for: {ingredient_name}. Keep it simple with short justifications."
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error fetching suggestion: {e}"

def calculate_food_waste_score(recipes):
    counter = {}
    for r in recipes:
        for ing in r["missedIngredients"]:
            name = ing["name"].lower()
            counter[name] = counter.get(name, 0) + 1
    single_use = sum(1 for v in counter.values() if v == 1)
    total = len(counter)
    if total == 0:
        return 100, "Perfect reuse! No extra ingredients needed."
    score = max(0, 100 - int((single_use / total) * 100))
    return score, f"{single_use} of {total} shopping items are only used in one recipe."

def get_gemini_tip(ingredients):
    try:
        prompt = f"Give a helpful nutrition or cooking tip for ingredients: {ingredients}."
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini API error: {e}"

# ──────── Streamlit UI ────────
st.set_page_config(page_title="Smart Recipe App", layout="centered")
st.markdown("<h1 style='text-align: center;'>🍽️ Smart Recipe Generator</h1>", unsafe_allow_html=True)
st.markdown("---")

with st.form("recipe_form"):
    st.markdown("### 🔧 Customize your recipe search:")
    diet = st.selectbox("Select a diet", ["none", "vegan", "vegetarian", "gluten free"])
    include = st.text_input("🥕 Ingredients you have (comma-separated)", "rice, tomatoes")
    exclude = st.text_input("🚫 Ingredients to exclude (comma-separated)", "peanut, dairy")
    max_time = st.slider("⏱️ Max cooking time (minutes)", 5, 120, 30)
    servings = st.slider("👥 Number of people to serve", 1, 10, 2)
    submitted = st.form_submit_button("🍳 Generate Weekly Plan")

if submitted:
    with st.spinner("🔍 Generating your meal plan..."):
        try:
            recipes = search_recipes(include, number=40)
            filtered_recipes = filter_recipes_with_inventory(recipes, include, max_count=7)

            if not filtered_recipes:
                st.warning("No recipes found that include your ingredients.")
            else:
                st.success("✅ Weekly plan generated!")
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                plan_text = StringIO()

                for i, recipe in enumerate(filtered_recipes):
                    st.subheader(f"{days[i]}: {recipe['title']}")
                    st.image(recipe["image"], width=300)
                    st.markdown(f"[📖 View Recipe]({slugify(recipe['title'], recipe['id'])})")
                    used = [ing["name"] for ing in recipe["usedIngredients"]]
                    st.caption(f"🍽️ Used Ingredients: {', '.join(used) if used else 'None'}")
                    plan_text.write(f"{days[i]}: {recipe['title']}\n")

                st.download_button("📥 Download Weekly Plan", plan_text.getvalue(), "weekly_meal_plan.txt")

                # ── Shopping List + Substitutes ──
                shopping_list = extract_shopping_list(filtered_recipes, include)
                if shopping_list:
                    st.markdown("### 🛒 Shopping List + Substitutes")
                    txt = StringIO()
                    for item, amount in shopping_list.items():
                        st.write(f"- **{item}**: {amount}")
                        suggestion = get_substitution_suggestion(item)
                        st.caption(f"🔁 Substitute tip: {suggestion}")
                        txt.write(f"{item}: {amount} — Suggestion: {suggestion}\n")
                    st.download_button("📥 Download Shopping List", txt.getvalue(), "shopping_list.txt")

                    # ── Food Waste Score ──
                    score, explanation = calculate_food_waste_score(filtered_recipes)
                    st.markdown("### ♻️ Food Waste Score")
                    st.metric(label="Score", value=f"{score} / 100")
                    st.caption(explanation)

                # ── Gemini Tip ──
                st.markdown("### 🤖 Gemini Nutrition Tip")
                st.info(get_gemini_tip(include))

        except Exception as e:
            st.error(f"Error: {e}")
