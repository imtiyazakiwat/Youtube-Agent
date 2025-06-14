from flask import Flask, request, send_file, jsonify
from gradio_client import Client
import os
import time
import shutil
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SAVE_FOLDER = os.path.join(os.getcwd(), "audio_files")
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Create a thread pool for running blocking operations
thread_pool = ThreadPoolExecutor(max_workers=4)

def _generate_speech_sync(text):
    """
    Internal function to generate speech using Chatterbox in a synchronous way
    """
    try:
        client = Client("ResembleAI/Chatterbox")
        logger.debug("Client created, generating speech...")
        
        result = client.predict(
            text,                  # text input
            None,                  # audio prompt path
            0.5,                   # exaggeration
            0.8,                   # temperature
            0,                     # seed
            0.5,                   # cfg
            api_name="/generate_tts_audio"  # correct API endpoint
        )
        
        logger.debug(f"Speech generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in _generate_speech_sync: {str(e)}")
        raise e

def text_to_speech(text, filename='speech.wav'):
    """
    Generate speech from text and save to a file
    Args:
        text (str): The text to convert to speech
        filename (str): The name of the output file
    Returns:
        dict: Response with file path or error message
    """
    if not text:
        logger.error("No text provided for speech generation")
        return {"error": "Text is required"}

    output_path = os.path.join(SAVE_FOLDER, filename)
    logger.debug(f"Will save audio to: {output_path}")

    try:
        # Run the speech generation in a separate thread
        logger.debug("Starting text-to-speech generation")
        result = thread_pool.submit(_generate_speech_sync, text).result()
        
        logger.debug(f"Got result from Chatterbox: {result}")
        
        if not result or not os.path.exists(result):
            logger.error("No audio file received from Chatterbox")
            return {"error": "Failed to generate audio"}
        
        # Copy the generated file to our desired location
        shutil.copy2(result, output_path)
        logger.debug(f"Copied audio file to: {output_path}")
        
        if not os.path.exists(output_path):
            logger.error("Failed to save audio file")
            return {"error": "Audio file not generated properly"}

        return {"success": True, "file": output_path}

    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return {"error": str(e)}

# Flask app for standalone usage
app = Flask(__name__)

@app.route('/tts', methods=['POST'])
def tts_endpoint():
    try:
        data = request.get_json()
        response = text_to_speech(
            text=data.get('text'),
            filename=data.get('filename', 'speech.wav')
        )
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in tts_endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
