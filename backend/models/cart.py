from database import cart_collection
from pymongo.errors import PyMongoError
import logging

logger = logging.getLogger(__name__)

def add_to_cart(product, qty):
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

def remove_from_cart(product):
    try:
        normalized_product = product.lower().strip()
        logger.info(f"Removing from cart: {normalized_product}")
        result = cart_collection.delete_one({"product": normalized_product})
        
        if result.deleted_count > 0:
            logger.info(f"Successfully removed {normalized_product}")
        else:
            logger.warning(f"Product not found: {normalized_product}")
            
    except PyMongoError as e:
        logger.error(f"Cart deletion failed: {str(e)}")
        raise

def show_cart():
    try:
        logger.info("Retrieving cart contents")
        items = list(cart_collection.find({}, {"_id": 0}))
        logger.info(f"Found {len(items)} items in cart")
        return items
    except PyMongoError as e:
        logger.error(f"Cart retrieval failed: {str(e)}")
        return []