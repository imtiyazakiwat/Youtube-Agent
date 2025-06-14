from flask import Flask, request, jsonify
from gradio_client import Client
import time
import os
import shutil
import logging
import base64
from together import Together
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_image_with_together(prompt):
    """
    Generate an image using Together API
    """
    try:
        client = Together(api_key="9c4531eeb315faa17599e185b66b58470a587b7908b6fe81fe921c56d464f3a6")
        response = client.images.generate(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell-Free",
            steps=10,
            n=1
        )
        
        # Convert base64 to image and save it
        image_data = base64.b64decode(response.data[0].b64_json)
        image = Image.open(io.BytesIO(image_data))
        return image
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise

def generate_video_from_image(image_path, prompt, max_retries=3, delay=5):
    """
    Generate video from an image using Lightricks API
    """
    logger.info(f"Starting video generation from image with prompt: {prompt}")
    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries}")
            client = Client("Lightricks/ltx-video-distilled")
            logger.debug("Client loaded")

            result = client.predict(
                prompt=prompt,
                negative_prompt="worst quality, inconsistent motion, blurry, jittery, distorted",
                input_image_filepath=image_path,
                input_video_filepath="",
                height_ui=512,
                width_ui=704,
                mode="image-to-video",
                duration_ui=5,
                ui_frames_to_use=15,
                seed_ui=42,
                randomize_seed=True,
                ui_guidance_scale=1,
                improve_texture_flag=True,
                api_name="/image_to_video"
            )

            logger.info("Video generation successful!")
            return {"status": "success", "result": result[0]}

        except Exception as e:
            logger.error(f"Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                return {"status": "failed", "error": str(e)}

def create_video(project_dir):
    """
    Create a video using the project directory structure.
    Args:
        project_dir (str): Path to the project directory containing script.txt and other assets
    Returns:
        str: Path to the generated video file
    """
    try:
        # Read the script
        script_path = os.path.join(project_dir, 'script.txt')
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script file not found at {script_path}")
            
        with open(script_path, 'r') as f:
            prompt = f.read().strip()
        
        # Create images directory if it doesn't exist
        images_dir = os.path.join(project_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate image using Together API
        image = generate_image_with_together(prompt)
        image_path = os.path.join(images_dir, 'generated_image.png')
        image.save(image_path)
        
        # Generate video from the image
        result = generate_video_from_image(image_path, prompt)
        
        if result["status"] == "failed":
            raise Exception(f"Video generation failed: {result.get('error', 'Unknown error')}")
        
        # Get the video file path from the result
        temp_video_path = result["result"]["video"]
        if not os.path.exists(temp_video_path):
            raise FileNotFoundError(f"Generated video file not found at {temp_video_path}")
        
        # Move the video to the project's video directory
        video_filename = f"final_movie_{os.path.basename(project_dir).split('_')[1]}.mp4"
        videos_dir = os.path.join(project_dir, 'videos')
        os.makedirs(videos_dir, exist_ok=True)
        video_path = os.path.join(videos_dir, video_filename)
        
        # Copy the video file
        shutil.copy2(temp_video_path, video_path)
        
        if not os.path.exists(video_path):
            raise Exception(f"Failed to copy video to project directory at {video_path}")
        
        logger.info(f"Video successfully created at {video_path}")
        return video_path
        
    except Exception as e:
        logger.error(f"Error in create_video: {str(e)}")
        raise Exception(f"Failed to create video: {str(e)}")

# Flask app for standalone usage
app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
            
        result = generate_video_with_retry(prompt)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)

