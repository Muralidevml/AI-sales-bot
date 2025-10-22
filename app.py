from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import requests
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# --- OpenRouter API Key ---
OPENROUTER_API_KEY = "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"

# --- Load Product Details ---
PRODUCTS_FILE = "products.csv"

if os.path.exists(PRODUCTS_FILE):
    try:
        products_df = pd.read_csv(PRODUCTS_FILE)
        products_df = products_df.fillna("")
        products_df.columns = [col.strip().lower().replace(" ", "_") for col in products_df.columns]

        for col in ["product_id", "category", "sub_category", "karatage", "gross_weight",
                    "diamond_weight", "number_of_stones", "dimensions", "approx_pricing"]:
            if col not in products_df.columns:
                products_df[col] = ""

        products_df["name"] = products_df["product_id"].astype(str)
        products_df["description"] = (
            "Category: " + products_df["category"] +
            ", Sub Category: " + products_df["sub_category"] +
            ", Karatage: " + products_df["karatage"] +
            ", Gross Weight: " + products_df["gross_weight"].astype(str) +
            ", Diamond Weight: " + products_df["diamond_weight"].astype(str) +
            ", Stones: " + products_df["number_of_stones"].astype(str) +
            ", Dimensions: " + products_df["dimensions"].astype(str) +
            ", Price: " + products_df["approx_pricing"]
        )

        unique_categories = sorted(products_df["category"].dropna().unique().tolist())

    except Exception as e:
        print("Error reading CSV:", e)
        products_df = pd.DataFrame(columns=["name", "description"])
        unique_categories = []
else:
    products_df = pd.DataFrame(columns=["name", "description"])
    unique_categories = []

# --- Root ---
@app.route("/")
def home():
    return redirect("/ui")

@app.route("/ui")
def ui():
    return render_template("index.html")

# --- Jewellery Keywords ---
JEWELLERY_KEYWORDS = [
    "ring", "rings", "necklace", "necklaces", "bangle", "bangles",
    "bracelet", "bracelets", "chain", "chains", "earring", "earrings",
    "pendant", "pendants", "anklet", "anklets", "jewellery", "jewelry",
    "everyday wear", "occasion wear", "solitaire", "engagement", "bands", "tennis bracelet"
]

# --- Product Search ---
def search_products(query):
    query = query.lower().strip()
    if "name" not in products_df.columns or "description" not in products_df.columns:
        return []

    matches = products_df[
        products_df["name"].str.lower().str.contains(query, na=False) |
        products_df["description"].str.lower().str.contains(query, na=False) |
        products_df["category"].str.lower().str.contains(query, na=False) |
        products_df["sub_category"].str.lower().str.contains(query, na=False) |
        products_df["approx_pricing"].str.lower().str.contains(query, na=False)
    ]

    return matches.head(10).to_dict(orient="records")

# --- Chat ---
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip().lower()

    # --- Greeting ---
    if any(word in user_message for word in ["hi", "hello", "hey", "hai", "welcome", "start"]):
        categories_list = ", ".join(unique_categories)
        reply = (
            f"💎 **Welcome to our Exclusive Jewellery Boutique!** 💎\n\n"
            f"We specialize in timeless collections designed with grace and craftsmanship.\n\n"
            f"✨ Our featured categories include:\n"
            f"{categories_list}\n\n"
            f"What type of jewellery would you like to explore today?"
        )
        return jsonify({"reply": reply, "products": []})

    # --- Exact Product ID Check ---
    exact_match = products_df[products_df["product_id"].str.lower() == user_message]
    if not exact_match.empty:
        found_products = exact_match.to_dict(orient="records")

        formatted_list = []
        for i, p in enumerate(found_products, start=1):
            formatted = (
                f"{i}️⃣ Produc id : {p.get('product_id', 'N/A')}\n"
                f"💍 Category: {p.get('category', 'N/A')}\n"
                f"✨ Sub Category: {p.get('sub_category', 'N/A')}\n"
                f"🔶 Karatage: {p.get('karatage', 'N/A')}\n"
                f"⚖️ Gross Weight: {p.get('gross_weight', 'N/A')}\n"
                f"💠 Diamond Weight: {p.get('diamond_weight', 'N/A')}\n"
                f"💎 No. of Stones: {p.get('number_of_stones', 'N/A')}\n"
                f"📏 Dimensions: {p.get('dimensions', 'N/A')}\n"
                f"💰 Approx. Price: {p.get('approx_pricing', 'N/A')}\n"
            )
            formatted_list.append(formatted)

        product_text = "\n".join(formatted_list)
        reply = (
            f"💎 Here are the details for Product ID **{user_message.upper()}**:\n\n{product_text}\n"
            "Would you like to see similar items?"
        )

        return jsonify({"reply": reply, "products": found_products})

    # --- Keyword-based Search (including sub-categories like 'everyday wear') ---
    found_products = search_products(user_message)

    if not found_products:
        for keyword in JEWELLERY_KEYWORDS:
            if keyword in user_message:
                found_products = search_products(keyword)
                if found_products:
                    break

    if not found_products:
        return jsonify({
            "reply": "I couldn't find any jewellery matching your search. Could you try another category or keyword?",
            "products": []
        })

    # --- Format Product Info ---
    formatted_list = []
    for i, p in enumerate(found_products, start=1):
        formatted = (
            f"{i}️⃣ Produc id : {p.get('product_id', 'N/A')}\n"
            f"💍 Category: {p.get('category', 'N/A')}\n"
            f"✨ Sub Category: {p.get('sub_category', 'N/A')}\n"
            f"🔶 Karatage: {p.get('karatage', 'N/A')}\n"
            f"⚖️ Gross Weight: {p.get('gross_weight', 'N/A')}\n"
            f"💠 Diamond Weight: {p.get('diamond_weight', 'N/A')}\n"
            f"💎 No. of Stones: {p.get('number_of_stones', 'N/A')}\n"
            f"📏 Dimensions: {p.get('dimensions', 'N/A')}\n"
            f"💰 Approx. Price: {p.get('approx_pricing', 'N/A')}\n"
        )
        formatted_list.append(formatted)

    product_text = "\n".join(formatted_list)

    # --- Jewellery-Focused AI Prompt ---
    system_prompt = (
        "You are an elegant, polite jewellery sales assistant. "
        "Always respond **only about jewellery** — rings, necklaces, earrings, bangles, bracelets, pendants, etc. "
        "If the user asks for something else, bring the topic back to jewellery gracefully. "
        "Describe the products warmly, highlighting design, style, and value. "
        "Be helpful and sales-friendly."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The user asked: {user_message}\n\nMatching jewellery items:\n{product_text}"}
        ],
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({
                "reply": f"⚠️ AI error (Status {response.status_code}): {response.text}",
                "products": found_products
            })

        data = response.json()
        reply = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "⚠️ AI did not return any response.")
        )

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
    app.run(host="0.0.0.0", port=port)
