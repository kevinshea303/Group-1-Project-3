import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SPOONACULAR_API_KEY")

def get_recipes(diet, include, exclude, max_time, number=5):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": API_KEY,
        "diet": diet,
        "includeIngredients": include,
        "excludeIngredients": exclude,
        "maxReadyTime": max_time,
        "number": number,
        "addRecipeInformation": True
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("results", [])