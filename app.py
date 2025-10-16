from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import requests
import pandas as pd
import os

app = Flask(__name__)
CORS(app)  # ✅ Allow API access from frontend

# --- OpenRouter API Key ---
OPENROUTER_API_KEY = "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"

# --- Load Product Details from CSV ---
PRODUCTS_FILE = "product.csv"
if os.path.exists(PRODUCTS_FILE):
    try:
        products_df = pd.read_csv(PRODUCTS_FILE)
        products_df = products_df.fillna("")  # Avoid NaN issues
    except Exception as e:
        print("Error reading CSV:", e)
        products_df = pd.DataFrame(columns=["name", "price", "description"])
else:
    products_df = pd.DataFrame(columns=["name", "price", "description"])

# --- Root Route ---
@app.route("/")
def home():
    return redirect("/ui")

# --- Frontend Page ---
@app.route("/ui")
def ui():
    return render_template("index.html")

# --- Product Search Function ---
def search_products(query):
    query = query.lower().strip()
    matches = products_df[
        products_df["name"].str.lower().str.contains(query, na=False)
        | products_df["description"].str.lower().str.contains(query, na=False)
    ]
    return matches.to_dict(orient="records")

# --- Chat Endpoint ---
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "Please enter a product name or question.", "products": []})

    # Search in CSV file
    found_products = search_products(user_message)

    # If no matches, reply gracefully
    if not found_products:
        return jsonify({
            "reply": "Sorry, I couldn’t find any matching jewellery products in our catalog.",
            "products": []
        })

    # Build context from CSV
    product_context = "\n".join(
        [f"{p['name']} - ₹{p['price']} : {p['description']}" for p in found_products]
    )

    # Prepare request to OpenRouter
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
                    "You are an AI Jewellery Sales Assistant powered by DeepSeek. "
                    "Use only the provided product details from the CSV file. "
                    "Do not suggest products not listed. "
                    "Be polite and descriptive, mentioning price, features, and craftsmanship."
                ),
            },
            {"role": "system", "content": f"Available Products:\n{product_context}"},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        data = response.json()

        # Parse AI reply safely
        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"]
        else:
            reply = f"⚠️ AI returned no content: {data.get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        reply = f"❌ Error connecting to AI: {e}"

    return jsonify({"reply": reply, "products": found_products})

# --- Health Check ---
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

# --- Run App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

