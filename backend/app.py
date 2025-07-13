from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from models.database import cart_collection, log_collection
from collections import Counter
import os
import uuid
import subprocess
import logging
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the audio_files directory exists
os.makedirs("audio_files", exist_ok=True)

@app.route("/")
def home():
    return send_file("dashboard.html")

@app.route("/api/upload", methods=["POST"])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    session_id = uuid.uuid4().hex
    input_file = f"audio_files/input_{session_id}.wav"
    f = request.files['audio']
    try:
        f.save(input_file)
        logger.info(f"Saved audio to {input_file}")
    except Exception as e:
        logger.error(f"File save failed: {str(e)}")
        return jsonify({"error": f"File save failed: {str(e)}"}), 500
    try:
        result = subprocess.run(
            ["python", "main.py", input_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            logger.error(f"Processing failed: {result.stderr}")
            return jsonify({
                "error": "Audio processing failed",
                "details": result.stderr
            }), 500
        return jsonify({
            "status": "success",
            "message": "Audio processed successfully",
            "session_id": session_id
        })
    except subprocess.TimeoutExpired:
        logger.error("Processing timed out")
        return jsonify({
            "error": "Processing took too long",
            "message": "Please try again with a shorter recording"
        }), 500
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({
            "error": "Processing failed",
            "message": str(e)
        }), 500
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
            logger.info(f"Removed temporary file {input_file}")

@app.route("/api/cart")
def cart():
    try:
        from models.cart import show_cart
        items = show_cart()
        subtotal = sum(item.get("total_price", 0) for item in items)
        return jsonify({
            "cart": items,
            "subtotal": round(subtotal, 2),
            "total": round(subtotal, 2)
        })
    except Exception as e:
        logger.error(f"Cart retrieval failed: {str(e)}")
        return jsonify({"error": "Failed to retrieve cart"}), 500

@app.route("/api/logs")
def logs():
    try:
        logs = list(log_collection.find({}, {"_id": 0}).sort("_id", -1).limit(20))
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Log retrieval failed: {str(e)}")
        return jsonify({"error": "Failed to retrieve logs"}), 500

@app.route("/api/sentiment")
def sentiment():
    try:
        logs = list(log_collection.find({}, {"sentiment": 1}))
        sentiments = Counter(log.get('sentiment', 'NEUTRAL') for log in logs)
        return jsonify({
            "positive": sentiments.get("POSITIVE", 0),
            "negative": sentiments.get("NEGATIVE", 0),
            "neutral": sentiments.get("NEUTRAL", 0)
        })
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        return jsonify({"error": "Failed to analyze sentiment"}), 500

@app.route("/api/products")
def products():
    try:
        import json
        with open("product.json", "r") as f:
            products = json.load(f)
        return jsonify(products)
    except Exception as e:
        logger.error(f"Product retrieval failed: {str(e)}")
        return jsonify({"error": "Failed to retrieve products"}), 500

@app.route("/api/debug", methods=["POST"])
def debug_command():
    try:
        data = request.json
        text = data.get("text", "")
        from models.intent import extract_intent_entities
        from models.cart import add_to_cart, remove_from_cart, show_cart
        entities = extract_intent_entities(text)
        logger.info(f"Debug entities: {entities}")
        if entities["intent"] == "add_to_cart":
            add_to_cart(entities["product"], entities["quantity"])
            cart = show_cart()
        elif entities["intent"] == "remove_from_cart":
            remove_from_cart(entities["product"], entities["quantity"])
            cart = show_cart()
        elif entities["intent"] == "show_cart":
            cart = show_cart()
        else:
            cart = show_cart()
        # Calculate subtotal and total
        try:
            with open("product.json") as f:
                products_data = json.load(f)
            price_map = {p["name"].lower(): p.get("price", 0) for p in products_data}
        except Exception as e:
            logger.error(f"Failed to load product prices: {str(e)}")
            price_map = {}
        subtotal = 0.0
        for item in cart:
            product_name = item.get("product", "").lower()
            price = price_map.get(product_name, 0)
            quantity = item.get("quantity", 1)
            item["price"] = price
            item["total_price"] = price * quantity
            subtotal += price * quantity
        response = {
            "status": "success" if entities["intent"] in ["add_to_cart", "remove_from_cart", "show_cart"] else "error",
            "action": entities["intent"],
            "cart": cart,
            "subtotal": round(subtotal, 2),
            "total": round(subtotal, 2)
        }
        if entities["intent"] == "unknown":
            response["message"] = "Unknown intent"
            return jsonify(response), 400
        return jsonify(response)
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        cart = []
        try:
            from models.cart import show_cart
            cart = show_cart()
        except Exception:
            pass
        return jsonify({
            "status": "error",
            "message": str(e),
            "cart": cart,
            "subtotal": 0.0,
            "total": 0.0
        }), 500

@app.route("/api/checkout", methods=["POST"])
def checkout():
    try:
        from models.cart import show_cart
        from models.database import cart_collection
        # Get current cart
        cart_items = show_cart()
        if not cart_items:
            return jsonify({"error": "Cart is empty"}), 400
        # Save to orders collection
        from models.database import log_collection
        import datetime
        from pymongo import MongoClient
        client = cart_collection.database.client
        orders_collection = client[cart_collection.database.name]["orders"]
        order_doc = {
            "items": cart_items,
            "created_at": datetime.datetime.utcnow(),
            "status": "completed"
        }
        orders_collection.insert_one(order_doc)
        # Clear the cart
        cart_collection.delete_many({})
        return jsonify({"status": "success", "message": "Order placed and cart cleared."})
    except Exception as e:
        logger.error(f"Checkout failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)