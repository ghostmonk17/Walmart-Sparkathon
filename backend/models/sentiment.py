from transformers import pipeline
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model only once
_sentiment_pipeline = None

def detect_sentiment(text):
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        logger.info("Loading sentiment model...")
        _sentiment_pipeline = pipeline("sentiment-analysis")
        logger.info("Sentiment model loaded")
    
    logger.info(f"Analyzing sentiment: {text}")
    result = _sentiment_pipeline(text)[0]
    return result['label'], result['score']