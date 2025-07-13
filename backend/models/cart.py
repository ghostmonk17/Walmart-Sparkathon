from models.database import cart_collection
from pymongo.errors import PyMongoError
import logging

logger = logging.getLogger(__name__)

def add_to_cart(product, qty=1):
    try:
        logger.info(f"Adding to cart: {qty} x {product}")
        # Normalize product name for consistent storage
        normalized_product = product.lower().strip()
        
        # Update or insert the item
        result = cart_collection.update_one(
            {"product": normalized_product},
            {"$inc": {"quantity": qty}},
            upsert=True
        )
        
        # Verify the operation
        if result.upserted_id:
            logger.info(f"Added new item: {normalized_product}")
        else:
            logger.info(f"Updated existing item: {normalized_product}")
            
        # Return the updated cart item
        return cart_collection.find_one({"product": normalized_product}, {"_id": 0})
        
    except PyMongoError as e:
        logger.error(f"Cart update failed: {str(e)}")
        raise

def remove_from_cart(product, qty=1):
    try:
        normalized_product = product.lower().strip()
        logger.info(f"Removing {qty} from cart: {normalized_product}")
        item = cart_collection.find_one({"product": normalized_product})
        if not item:
            logger.warning(f"Product not found: {normalized_product}")
            return
        new_qty = item.get("quantity", 1) - qty
        if new_qty > 0:
            cart_collection.update_one({"product": normalized_product}, {"$set": {"quantity": new_qty}})
            logger.info(f"Decremented quantity of {normalized_product} to {new_qty}")
        else:
            cart_collection.delete_one({"product": normalized_product})
            logger.info(f"Removed {normalized_product} from cart (quantity zero or less)")
    except PyMongoError as e:
        logger.error(f"Cart deletion failed: {str(e)}")
        raise

def show_cart():
    try:
        logger.info("Retrieving cart contents")
        items = list(cart_collection.find({}, {"_id": 0}))
        logger.info(f"Found {len(items)} items in cart")
        # Add price and total_price to each item
        import json
        try:
            with open("product.json") as f:
                products_data = json.load(f)
            price_map = {p["name"].lower(): p.get("price", 0) for p in products_data}
        except Exception as e:
            logger.error(f"Failed to load product prices: {str(e)}")
            price_map = {}
        for item in items:
            product_name = item.get("product", "").lower()
            price = price_map.get(product_name, 0)
            quantity = item.get("quantity", 1)
            item["price"] = price
            item["total_price"] = price * quantity
        return items
    except PyMongoError as e:
        logger.error(f"Cart retrieval failed: {str(e)}")
        return []