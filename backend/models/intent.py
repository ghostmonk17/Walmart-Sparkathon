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
        # Improved product, quantity, and metric extraction
        qty = 1
        metric = None
        product = None
        best_match = None
        best_match_len = 0
        metrics_list = ["kg", "kilogram", "litre", "liter", "dozen", "dozens", "packet", "packets", "bottle", "bottles", "piece", "pieces"]
        for prod in products_data:
            prod_name = prod["name"].lower()
            # Look for patterns like '2 kg rice', '3 packets milk', etc.
            pattern = r"(\d+|one|two|three|four|five|a|an)?\s*(%s)?\s*%s" % ("|".join(metrics_list), re.escape(prod_name))
            match = re.search(pattern, text)
            if match:
                if len(prod_name) > best_match_len:
                    best_match = prod["name"]
                    best_match_len = len(prod_name)
                    qty_str = match.group(1)
                    metric_str = match.group(2)
                    if qty_str:
                        if qty_str.isdigit():
                            qty = int(qty_str)
                        else:
                            numbers = {"one":1, "two":2, "three":3, "four":4, "five":5, "a":1, "an":1}
                            qty = numbers.get(qty_str.lower(), 1)
                    else:
                        qty = 1
                    if metric_str:
                        metric = metric_str
                    else:
                        metric = None
        if best_match:
            product = best_match
        else:
            # fallback to old logic for partial matches
            for prod in products_data:
                prod_name = prod["name"].lower()
                if prod_name in text or prod_name.rstrip('s') in text or (prod_name + 's') in text:
                    product = prod["name"]
                    break
        if not product:
            product = "item"
        logger.info(f"Extracted entities - Intent: {intent}, Product: {product}, Qty: {qty}, Metric: {metric}")
        return {
            "intent": intent,
            "product": product,
            "quantity": qty,
            "metric": metric
        }
    except Exception as e:
        logger.error(f"Intent extraction failed: {str(e)}")
        return {
            "intent": "unknown",
            "product": "item",
            "quantity": 1,
            "metric": None
        }