import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services')))
from api_utils import get_recipes
import google.generativeai as genai
import os
from dotenv import load_dotenv
from io import StringIO
import random

# Load API keys
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="Smart Recipe App", layout="centered")
st.markdown("<h1 style='text-align: center;'>🍽️ Smart Recipe Generator</h1>", unsafe_allow_html=True)
st.markdown("---")

# Input form
with st.form("recipe_form"):
    st.markdown("### 🔧 Customize your recipe search:")
    diet = st.selectbox("Select a diet", ["none", "vegan", "vegetarian", "gluten free"])
    include = st.text_input("🥕 Ingredients you have (comma-separated)", "rice, tomatoes")
    exclude = st.text_input("🚫 Ingredients to exclude (comma-separated)", "peanut, dairy")
    max_time = st.slider("⏱️ Max cooking time (minutes)", 5, 120, 30)
    servings = st.slider("👥 Number of people to serve", 1, 10, 2)
    submitted = st.form_submit_button("🍳 Generate Recipes")

# Gemini tip
if include:
    st.markdown("### 🤖 Gemini Nutrition Tip")
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"Give a helpful healthy cooking or nutrition tip based on these ingredients: {include}"
        response = model.generate_content(prompt)
        st.info(response.text.strip())
    except Exception as e:
        st.warning(f"Gemini API error: {e}")

# Recipe generation
weekly_plan = []
if submitted:
    with st.spinner("🔍 Searching for recipes..."):
        try:
            recipes = get_recipes(diet, include, exclude, max_time, number=7)
            if recipes:
                st.success(f"✅ Found {len(recipes)} recipe(s):")
                for i, r in enumerate(recipes, 1):
                    weekly_plan.append((i, r))
                    with st.expander(f"{i}. {r['title']}"):
                        st.image(r["image"], width=300)
                        st.write(f"⏱️ {r['readyInMinutes']} min | 👨‍🍳 {servings} people (original: {r['servings']})")
                        st.markdown(f"[📖 View full recipe]({r['sourceUrl']})")
            else:
                st.warning("No recipes found for your filters.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# Weekly Plan and Download
if weekly_plan:
    st.markdown("### 📅 Weekly Meal Plan")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    plan_text = StringIO()
    for i, (index, recipe) in enumerate(weekly_plan):
        line = f"{days[i]}: {recipe['title']}\n"
        st.write(line.strip())
        plan_text.write(line)

    st.download_button("📥 Download Weekly Plan (.txt)", plan_text.getvalue(), file_name="weekly_meal_plan.txt")