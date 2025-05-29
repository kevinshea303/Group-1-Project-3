# 🍽️ Smart Recipe Generator

This is a Streamlit-based recipe recommendation app that uses the Spoonacular API to suggest meals based on your diet and available ingredients — and gives AI nutrition tips using Google Gemini.

## 🚀 Features

- Input ingredients, exclude allergens, select diet and cooking time
- Real-time recipe results with photos and links
- 🤖 Nutrition tip from Gemini AI based on your ingredients

## 🛠️ Setup

1. Clone or download this project.
2. Create a `.env` file in the root folder:
```
SPOONACULAR_API_KEY=your_spoonacular_key
GEMINI_API_KEY=your_google_key
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run the app:
```
streamlit run frontend/app.py
```