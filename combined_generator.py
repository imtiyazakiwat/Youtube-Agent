import os
from datetime import datetime
import google.generativeai as genai
from video_test import generate_video_with_prompt, retry_operation, download_video
from together_image import generate_image, download_image

def generate_prompts():
    """Generate both image and video prompts using Gemini"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key not found. Please set the GOOGLE_API_KEY environment variable")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        # Generate image prompt
        image_response = model.generate_content(
            "Generate a creative and captivating image description in 15 words. Focus on visual elements and atmosphere."
        )
        image_prompt = image_response.text.strip()

        # Generate video prompt
        video_response = model.generate_content(
            "Generate a creative and captivating 20-word video scene description. Focus on story, event, coutry , people , education etc and visual elements."
        )
        video_prompt = video_response.text.strip()

        return image_prompt, video_prompt
    except Exception as e:
        print(f"❌ Error during prompt generation: {e}")
        raise

def main():
    # Create output directories
    base_dir = os.path.join(os.getcwd(), "output")
    image_dir = os.path.join(base_dir, "images")
    video_dir = os.path.join(base_dir, "videos")
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)

    # Step 1: Generate prompts
    print("📝 Generating creative prompts...")
    image_prompt, video_prompt = generate_prompts()
    print(f"🎨 Image Prompt: {image_prompt}")
    print(f"🎬 Video Prompt: {video_prompt}")

    # Step 2: Generate image
    print("\n🎨 Generating image...")
    image_data = generate_image(image_prompt)
    if image_data and 'output' in image_data:
        image_url = image_data['output'][0]
        download_image(image_url, image_dir)

    # Step 3: Generate video
    print("\n🎬 Generating video...")
    try:
        video_path = retry_operation(
            lambda: generate_video_with_prompt(video_prompt)
        )
        print(f"📽️ Video Path: {video_path}")

        video_filename = os.path.join(video_dir, f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        download_video(video_path, video_filename)
    except Exception as e:
        print(f"❌ Failed to generate video after 3 attempts: {str(e)}")

if __name__ == "__main__":
    main()
