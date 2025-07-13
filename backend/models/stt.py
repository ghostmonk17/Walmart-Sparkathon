import whisper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model only once
model = None

def transcribe_audio(file_path="input.wav"):
    global model
    if model is None:
        logger.info("Loading Whisper model...")
        model = whisper.load_model("base")
        logger.info("Whisper model loaded")
    
    logger.info(f"Transcribing audio: {file_path}")
    result = model.transcribe(file_path)
    return result['text']