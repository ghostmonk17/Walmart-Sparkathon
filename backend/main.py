from models.stt import transcribe_audio
from models.tts import speak_response
from models.intent import extract_intent_entities
from models.sentiment import detect_sentiment
from models.cart import add_to_cart, remove_from_cart, show_cart
from models.database import log_collection
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handle_action(entities):
    try:
        intent = entities['intent']
        product = entities['product']
        qty = entities['quantity']

        if intent == "add_to_cart":
            add_to_cart(product, qty)
            return f"Added {qty} {product} to your cart."
        elif intent == "remove_from_cart":
            remove_from_cart(product)
            return f"Removed {product} from your cart."
        elif intent == "show_cart":
            cart = show_cart()
            if cart:
                return "Your cart has: " + ", ".join(f"{item['quantity']} {item['product']}" for item in cart)
            else:
                return "Your cart is empty."
        else:
            return "Sorry, I didn't understand that. Can you rephrase?"
    except Exception as e:
        logger.error(f"Action handling failed: {str(e)}")
        return "I encountered an error processing your request. Please try again."

def main(input_file="input.wav"):
    try:
        logger.info(f"Processing audio file: {input_file}")
        
        # Transcribe audio
        text = transcribe_audio(input_file)
        logger.info(f"You said: {text}")

        # Sentiment analysis
        label, score = detect_sentiment(text)
        logger.info(f"Sentiment: {label} ({score})")

        # Handle negative sentiment
        if label == "NEGATIVE":
            response = "You sound frustrated. Let me connect you to a support agent."
            logger.info(f"AI: {response}")
            speak_response(response, "audio_files/response.wav")
            return

        # Extract intent
        entities = extract_intent_entities(text)
        logger.info(f"Extracted entities: {entities}")

        # Generate response
        reply = handle_action(entities)
        logger.info(f"AI: {reply}")

        # Speak response
        speak_response(reply, "audio_files/response.wav")

        # Log interaction
        log_collection.insert_one({
            "user_input": text,
            "intent": entities,
            "response": reply,
            "sentiment": label
        })
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise  # Re-raise to capture in subprocess

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "input.wav"
    main(input_file)