from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from database import cart_collection, log_collection
from collections import Counter
import os
import uuid
import subprocess
import logging

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
        items = list(cart_collection.find({}, {"_id": 0}))
        return jsonify(items)
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
        from intent import extract_intent_entities
        from cart import add_to_cart, remove_from_cart, show_cart
        entities = extract_intent_entities(text)
        logger.info(f"Debug entities: {entities}")
        if entities["intent"] == "add_to_cart":
            add_to_cart(entities["product"], entities["quantity"])
            cart = show_cart()
            return jsonify({
                "status": "success",
                "action": "add",
                "cart": cart
            })
        elif entities["intent"] == "remove_from_cart":
            remove_from_cart(entities["product"])
            cart = show_cart()
            return jsonify({
                "status": "success",
                "action": "remove",
                "cart": cart
            })
        elif entities["intent"] == "show_cart":
            cart = show_cart()
            return jsonify({
                "status": "success",
                "action": "show",
                "cart": cart
            })
        else:
            cart = show_cart()
            return jsonify({
                "status": "error",
                "message": "Unknown intent",
                "cart": cart
            }), 400
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        cart = []
        try:
            from cart import show_cart
            cart = show_cart()
        except Exception:
            pass
        return jsonify({
            "status": "error",
            "message": str(e),
            "cart": cart
        }), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)