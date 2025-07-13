from TTS.api import TTS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singleton model instance
_tts_instance = None

def get_tts():
    global _tts_instance
    if _tts_instance is None:
        logger.info("Loading TTS model...")
        _tts_instance = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
        logger.info("TTS model loaded")
    return _tts_instance

def speak_response(text, file_path="response.wav"):
    try:
        tts = get_tts()
        logger.info(f"Generating speech: {text}")
        tts.tts_to_file(text=text, file_path=file_path)
        logger.info(f"Audio saved to {file_path}")
    except Exception as e:
        logger.error(f"TTS failed: {str(e)}")
        raise