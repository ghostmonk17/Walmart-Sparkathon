from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directly use your Atlas connection string
# Replace <db_password> with your actual password (URL-encoded if it contains special characters)
connection_string = "mongodb+srv://shreyashshinde30:Shreyashshinde3011@cluster0.gjai1iz.mongodb.net/"

logger.info("Connecting to MongoDB...")
try:
    client = MongoClient(
        connection_string,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
    db = client['walmart_ai']
    cart_collection = db['cart']
    log_collection = db['logs']
except Exception as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    raise