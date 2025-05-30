import streamlit as st
import os
import sys
import requests
from dotenv import load_dotenv
from io import StringIO
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services')))
load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
BASE_URL = "https://api.spoonacular.com"

def slugify(title: str, rid: int) -> str:
    s = re.sub(r"[^a-z0-9\- ]", "", title.lower())
    s = re.sub(r"\s+", "-", s)
    return f"https://spoonacular.com/recipes/{s}-{rid}"

def has_inventory_item(recipe, inventory):
    """Returns True if the recipe uses at least one of the user's available ingredients."""
    inventory_set = set(i.strip().lower() for i in inventory.split(","))
    return any(
        ing.get("name", "").strip().lower() in inventory_set
        for ing in recipe.get("extendedIngredients", [])
    )

def search_recipes(inventory, number=20):
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": inventory,
        "number": number,
        "ranking": 1,  # Maximize used ingredients
        "ignorePantry": True
    }
    response = requests.get(f"{BASE_URL}/recipes/findByIngredients", params=params)
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code}, {response.text}")
    return response.json()

def filter_recipes_with_inventory(recipes, inventory, max_count=7):
    inventory_set = set(i.strip().lower() for i in inventory.split(","))
    filtered = []
    seen_titles = set()
    for recipe in recipes:
        if recipe["title"] in seen_titles:
            continue
        used_ingredients = {ing["name"].lower() for ing in recipe.get("usedIngredients", [])}
        if used_ingredients & inventory_set:
            filtered.append(recipe)
            seen_titles.add(recipe["title"])
        if len(filtered) == max_count:
            break
    return filtered


def extract_shopping_list(recipes, inventory):
    inventory_set = set(i.strip().lower() for i in inventory.split(","))
    shopping_items = {}
    for recipe in recipes:
        for ingredient in recipe.get("missedIngredients", []):
            name = ingredient.get("name").strip().lower()
            amount = f"{ingredient.get('amount', '')} {ingredient.get('unit', '')}".strip()
            if name not in inventory_set and name not in shopping_items:
                shopping_items[name] = amount
    return shopping_items



# Streamlit UI setup
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

weekly_plan = []
if submitted:
    with st.spinner("🔍 Generating your meal plan..."):
        try:
            recipes = search_recipes(include, number=20)
            filtered_recipes = filter_recipes_with_inventory(recipes, include, max_count=7)

            if not filtered_recipes:
                st.warning("No recipes found that include your ingredients. Try adjusting your filters.")
            else:
                st.success("✅ Weekly plan generated:")
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                plan_text = StringIO()

                for i, recipe in enumerate(filtered_recipes):
                    st.subheader(f"{days[i]}: {recipe['title']}")
                    st.image(recipe["image"], width=300)
                    st.markdown(f"[View Recipe]({slugify(recipe['title'], recipe['id'])})")
                    st.caption(f"🍽️ Used Ingredients: {', '.join([ing['name'] for ing in recipe.get('usedIngredients', [])])}")
                    plan_text.write(f"{days[i]}: {recipe['title']}\n")

                st.download_button("📥 Download Weekly Plan (.txt)", plan_text.getvalue(), file_name="weekly_meal_plan.txt")

                shopping_list = extract_shopping_list(filtered_recipes, include)
                if shopping_list:
                    st.markdown("### 🛒 Shopping List")
                    shopping_text = StringIO()
                    for item, amount in shopping_list.items():
                        st.write(f"- {item}: {amount}")
                        shopping_text.write(f"- {item}: {amount}\n")
                    st.download_button("📥 Download Shopping List (.txt)", shopping_text.getvalue(), file_name="shopping_list.txt")
        except Exception as e:
            st.error(f"Error: {e}")
