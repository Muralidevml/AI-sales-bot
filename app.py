from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import requests
import pandas as pd
import os

app = Flask(__name__)
CORS(app)  # ✅ Allow frontend & API calls from any origin

# --- OpenRouter API Key ---
OPENROUTER_API_KEY = "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"

# --- Load Products from CSV ---
PRODUCTS_FILE = "products.csv"
if os.path.exists(PRODUCTS_FILE):
    products_df = pd.read_csv(PRODUCTS_FILE)
else:
    products_df = pd.DataFrame([
        {"name": "Gold Necklace", "price": 15000, "description": "22K gold necklace with elegant design"},
        {"name": "Diamond Ring", "price": 25000, "description": "Sparkling diamond ring with 18K white gold"},
        {"name": "Silver Bracelet", "price": 5000, "description": "Stylish silver bracelet with charm pendants"},
    ])
    products_df.to_csv(PRODUCTS_FILE, index=False)

# --- Home redirects directly to UI ---
@app.route("/")
def home():
    return jsonify({"message": "✅ DeepSeek Jewellery Chatbot API is running!"})


# --- Chat UI page (optional, for front-end use) ---
@app.route("/ui")
def ui():
    return render_template("index.html")


# --- Helper: Search Matching Jewellery Items ---
def search_products(query):
    query = query.lower().strip()
    matches = products_df[
        products_df["name"].str.lower().str.contains(query)
        | products_df["description"].str.lower().str.contains(query)
    ]
    return matches.to_dict(orient="records")


# --- Chat API Route ---
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    # Search CSV for matching products
    found_products = search_products(user_message)

    # If products found, build context for AI
    product_context = ""
    if found_products:
        product_context = "Here are matching jewellery products:\n" + "\n".join(
            [f"{p['name']} (₹{p['price']}) - {p['description']}" for p in found_products]
        )
    else:
        product_context = "No matching products found in the catalogue."

    # --- DeepSeek V3.1 Request ---
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI Jewellery Sales Assistant powered by DeepSeek V3.1 (free). "
                    "Answer the user based only on jewellery products from the CSV. "
                    "Do not invent new items or give unrelated suggestions. "
                    "Give elegant, natural, sales-style replies."
                ),
            },
            {"role": "user", "content": user_message},
            {"role": "system", "content": product_context},
        ],
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        data = response.json()
        print("DEBUG:", data)  # Render logs will show this

        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
        else:
            reply = f"⚠️ AI Error: {data.get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        reply = f"❌ Error connecting to AI: {str(e)}"

    return jsonify({
        "reply": reply,
        "products": found_products
    })


# --- Required for Render Deployment ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
