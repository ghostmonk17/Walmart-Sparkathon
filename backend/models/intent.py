import re
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load products from JSON
try:
    with open('product.json') as f:
        products_data = json.load(f)
        product_names = [p["name"].lower() for p in products_data]
        logger.info(f"Loaded {len(product_names)} products")
except Exception as e:
    logger.error(f"Failed to load products: {str(e)}")
    products_data = []
    product_names = []

def extract_intent_entities(text):
    try:
        text = text.lower().strip()
        logger.info(f"Extracting intent from: {text}")
        # Enhanced intent detection
        intent = "unknown"
        if any(word in text for word in ["add", "buy", "purchase", "i want", "need"]):
            intent = "add_to_cart"
        elif any(word in text for word in ["remove", "delete", "take out"]):
            intent = "remove_from_cart"
        elif any(phrase in text for phrase in ["what's in", "show cart", "view cart", "my cart"]):
            intent = "show_cart"
        # More robust quantity extraction
        qty = 1
        qty_match = re.search(r'(\d+)|one|two|three|four|five|a|an', text)
        if qty_match:
            if qty_match.group().isdigit():
                qty = int(qty_match.group())
            else:
                numbers = {
                    "one":1, "two":2, "three":3, 
                    "four":4, "five":5, "a":1, "an":1
                }
                qty = numbers.get(qty_match.group().lower(), 1)
        # Improved product matching (handle singular/plural)
        product = "item"
        for prod in products_data:
            prod_name = prod["name"].lower()
            # Check for exact, singular, or plural match
            if prod_name in text or prod_name.rstrip('s') in text or (prod_name + 's') in text:
                product = prod["name"]
                break
            # Also check for partial matches (singular/plural)
            for word in prod_name.split():
                if word in text.split() or word.rstrip('s') in text.split() or (word + 's') in text.split():
                    product = prod["name"]
                    break
        logger.info(f"Extracted entities - Intent: {intent}, Product: {product}, Qty: {qty}")
        return {
            "intent": intent,
            "product": product,
            "quantity": qty
        }
    except Exception as e:
        logger.error(f"Intent extraction failed: {str(e)}")
        return {
            "intent": "unknown",
            "product": "item",
            "quantity": 1
        }