import os
from datetime import datetime
from gradio_client import Client
import time
import logging
import base64
import gradio as gr
from together_image import generate_image, download_image

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def video_generation_interface(image_path, prompt):
    """Wrapper function for gradio interface"""
    try:
        client = Client(
            "Lightricks/ltx-video-distilled",
            hf_token=os.getenv("HUGGINGFACE_TOKEN")
        )
        
        result = client.predict(
            str(prompt),
            "worst quality, inconsistent motion, blurry, jittery, distorted",
            image_path,  # Gradio will handle file upload properly
            "",
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
        return result[0] if isinstance(result, tuple) else result
    except Exception as e:
        raise gr.Error(str(e))

def generate_video_from_image(image_path, prompt, output_dir, max_retries=3, delay=5):
    """Generate video using Gradio interface"""
    interface = gr.Interface(
        fn=video_generation_interface,
        inputs=[gr.Image(), gr.Textbox()],
        outputs=gr.Video(),
        title="Image to Video Generation"
    ).launch(show_error=True)
    
    for attempt in range(max_retries):
        try:
            result = interface(image_path, prompt)
            if result:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_path = os.path.join(output_dir, f"generated_video_{timestamp}.mp4")
                os.makedirs(output_dir, exist_ok=True)
                
                if isinstance(result, dict) and 'video' in result:
                    video_path = result['video']
                else:
                    video_path = result
                    
                if os.path.exists(video_path):
                    os.rename(video_path, new_path)
                    print(f"✅ Video saved to: {new_path}")
                    return new_path
            
            raise Exception("Invalid video data received from API")
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
                delay *= 2
            else:
                logger.error("All attempts failed")
                raise

if __name__ == "__main__":
    # First generate and save an image
    prompt = "A majestic Indian palace with intricate architecture"
    result = generate_image(prompt)
    
    if result and 'data' in result and len(result['data']) > 0:
        image_url = result['data'][0]['url']
        output_dir = "project_specific_directory"  # Define your project-specific directory here
        image_path = download_image(image_url, output_dir=output_dir)
        
        if image_path:
            print("🎬 Starting video generation using the image...")
            video_path = generate_video_from_image(
                image_path,
                prompt="Transform this palace into a magical scene with floating lanterns and mystical effects",
                output_dir=output_dir  # Pass the output directory to the video generation function
            )
            
            if video_path:
                print("🎉 Complete! Image and video generation successful!")
            else:
                print("❌ Video generation failed")
    else:
        print("❌ Image generation failed")
