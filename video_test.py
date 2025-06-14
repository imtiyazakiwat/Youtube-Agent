import os
from gradio_client import Client
from datetime import datetime
import shutil
import google.generativeai as genai

# Step 1: Generate video prompt using Gemini
def generate_prompt():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key not found. Please set the GOOGLE_API_KEY environment variable")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        response = model.generate_content(
            "Generate a creative and captivating 20-word video scene description. Focus on atmosphere, movement, and visual elements."
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error during prompt generation: {e}")
        raise

# Step 2: Generate video using Hugging Face API
def generate_video_with_prompt(prompt_text):
    client = Client("Lightricks/ltx-video-distilled")

    result = client.predict(
        prompt=prompt_text,
        negative_prompt="worst quality, inconsistent motion, blurry, jittery, distorted",
        input_image_filepath=None,
        input_video_filepath=None,
        height_ui=512,
        width_ui=704,
        mode="text-to-video",
        duration_ui=7,
        ui_frames_to_use=9,
        seed_ui=42,
        randomize_seed=True,
        ui_guidance_scale=1,
        improve_texture_flag=True,
        api_name="/text_to_video"
    )

    video_path = result[0]['video']
    return video_path

# Step 3: Download video
def download_video(video_path, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        shutil.copy(video_path, save_path)
        print(f"✅ Video saved to {save_path}")
    except FileNotFoundError:
        print(f"❌ Error: Source file not found at {video_path}")
    except Exception as e:
        print(f"❌ Error during video saving: {e}")

def retry_operation(operation, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as e:
            if attempt == max_attempts - 1:  # Last attempt
                raise
            print(f"⚠️ Attempt {attempt + 1} failed: {str(e)}")
            print(f"Retrying... ({attempt + 2}/{max_attempts})")

# Main
if __name__ == "__main__":
    print("📝 Generating creative prompt...")
    prompt = generate_prompt()
    print(f"📝 Prompt: {prompt}")

    print("🎬 Generating video from prompt...")
    try:
        video_path = retry_operation(
            lambda: generate_video_with_prompt(prompt)
        )
        print(f"📽️ Video Path: {video_path}")

        # Create output directory in current working directory
        output_dir = os.path.join(os.getcwd(), "output", "videos")
        filename = os.path.join(output_dir, f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        download_video(video_path, filename)
    except Exception as e:
        print(f"❌ Failed to generate video after 3 attempts: {str(e)}")
