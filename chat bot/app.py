from flask import Flask, request, jsonify, render_template, redirect
import requests
import pandas as pd
import os

app = Flask(__name__)

# --- Your OpenRouter API Key ---
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
    return redirect("/ui")

# --- Chat UI page ---
@app.route("/ui")
def ui():
    return render_template("index.html")

# --- Helper: search matching jewellery items ---
def search_products(query):
    query = query.lower()
    matches = products_df[
        products_df["name"].str.lower().str.contains(query)
        | products_df["description"].str.lower().str.contains(query)
    ]
    return matches.to_dict(orient="records")

# --- Chat API route ---
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    # Search for matching products
    found_products = search_products(user_message)

    # Build context for AI
    product_context = ""
    if found_products:
        product_context = "Matching jewellery products:\n" + "\n".join(
            [f"{p['name']} - ₹{p['price']}: {p['description']}" for p in found_products]
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek/deepseek-chat",  # ✅ DeepSeek V3.1 (Free) Model ID
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI Jewellery Sales Assistant powered by DeepSeek V3.1. "
                    "Answer customer questions about jewellery clearly and helpfully. "
                    "If product details are provided, use them to describe features, pricing, and style."
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
        )
        data = response.json()
        print("DEBUG:", data)  # for debugging

        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
        else:
            reply = f"⚠️ AI Error: {data.get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        reply = f"❌ Error connecting to AI: {e}"

    return jsonify({"reply": reply, "products": found_products})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
