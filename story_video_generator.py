import os
import json
import time
import shutil
import logging
import google.generativeai as genai
from pathlib import Path
from datetime import datetime
from flask import Flask, request, send_file
import requests
from gradio_client import Client
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoryVideoGenerator:
    def __init__(self, google_api_key, openrouter_api_key=None):
        """Initialize the story video generator with API keys"""
        self.google_api_key = google_api_key
        self.openrouter_api_key = openrouter_api_key
        self.base_dir = Path(__file__).parent
        self.session_id = str(int(time.time()))
        self.setup_directories()
        self.setup_services()
        
    def setup_directories(self):
        """Create necessary directories for the project"""
        self.project_dir = self.base_dir / f"story_{self.session_id}"
        
        # Create subdirectories
        self.dirs = {
            'videos': self.project_dir / 'videos',
            'audio': self.project_dir / 'audio',
            'subtitles': self.project_dir / 'subtitles',
            'images': self.project_dir / 'images',
            'temp': self.project_dir / 'temp'
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
    def setup_services(self):
        """Initialize API clients and services"""
        genai.configure(api_key=self.google_api_key)
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        self.video_client = Client("Lightricks/ltx-video-distilled")
        self.tts_client = Client("ResembleAI/Chatterbox")
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
    def generate_story_script(self, topic, num_scenes=4, scene_duration=6):
        """Generate a complete story script with scene descriptions using Gemini"""
        try:
            prompt = f"""You are a creative story writer for children's videos. Create a short story about {topic} with exactly {num_scenes} scenes.
            Each scene should be exactly {scene_duration} seconds long when narrated.
            
            IMPORTANT: You must respond with ONLY a valid JSON object in this exact format, with no additional text:
            {{
                "title": "Story Title",
                "scenes": [
                    {{
                        "narration": "Scene 1 narration text (2-3 sentences)",
                        "visual_description": "Detailed visual description for video generation of scene 1"
                    }},
                    {{
                        "narration": "Scene 2 narration text (2-3 sentences)",
                        "visual_description": "Detailed visual description for video generation of scene 2"
                    }},
                    {{
                        "narration": "Scene 3 narration text (2-3 sentences)",
                        "visual_description": "Detailed visual description for video generation of scene 3"
                    }},
                    {{
                        "narration": "Scene 4 narration text (2-3 sentences)",
                        "visual_description": "Detailed visual description for video generation of scene 4"
                    }}
                ]
            }}
            
            Rules:
            1. Each scene's narration should be 2-3 sentences that can be narrated in exactly {scene_duration} seconds
            2. Each visual description should be detailed and specific for video generation
            3. The story should flow naturally between scenes
            4. Keep the language simple and engaging for children
            5. Respond with ONLY the JSON object, no other text"""
            
            response = self.gemini_model.generate_content(prompt)
            
            # Extract the JSON string from the response
            response_text = response.text.strip()
            
            # Try to find JSON content if there's any surrounding text
            try:
                # First try direct JSON parsing
                story_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        story_data = json.loads(json_match.group())
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from response: {response_text}")
                        raise Exception(f"Invalid JSON in response: {str(e)}")
                else:
                    logger.error(f"No JSON found in response: {response_text}")
                    raise Exception("No valid JSON found in the response")
            
            # Validate the story data structure
            if not isinstance(story_data, dict):
                raise Exception("Response is not a dictionary")
            if "title" not in story_data or "scenes" not in story_data:
                raise Exception("Missing required fields in story data")
            if not isinstance(story_data["scenes"], list) or len(story_data["scenes"]) != num_scenes:
                raise Exception(f"Expected {num_scenes} scenes, got {len(story_data['scenes'])}")
            
            # Save the script
            script_path = self.project_dir / 'story_script.json'
            with open(script_path, 'w') as f:
                json.dump(story_data, f, indent=2)
                
            return story_data
            
        except Exception as e:
            logger.error(f"Error generating story script: {e}")
            raise
            
    def generate_audio(self, text, filename):
        """Generate audio narration using TTS service"""
        try:
            result = self.tts_client.predict(
                text,
                None,  # audio prompt
                0.5,   # exaggeration
                0.8,   # temperature
                0,     # seed
                0.5,   # cfg
                api_name="/generate_tts_audio"
            )
            
            if not result or not os.path.exists(result):
                raise Exception("No audio file received from TTS service")
                
            output_path = self.dirs['audio'] / filename
            shutil.copy2(result, output_path)
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            raise
            
    def generate_subtitles(self, text, filename):
        """Generate SRT subtitles for the narration"""
        try:
            response = requests.post(
                "http://localhost:8000/generate-srt",
                json={
                    "script": text,
                    "filename": filename
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Subtitle generation failed: {response.text}")
                
            srt_path = self.dirs['subtitles'] / f"{filename}.srt"
            with open(srt_path, 'wb') as f:
                f.write(response.content)
            return srt_path
            
        except Exception as e:
            logger.error(f"Error generating subtitles: {e}")
            raise
            
    def generate_video_scene(self, prompt, image_path=None, is_first_scene=False):
        """Generate a video scene from prompt and optional image"""
        try:
            from video_test import generate_video_with_prompt, retry_operation, download_video
            
            # Generate video using the working approach from combined_generator.py
            logger.info(f"Generating video for prompt: {prompt}")
            video_path = retry_operation(
                lambda: generate_video_with_prompt(prompt)
            )
            
            if not video_path:
                raise Exception("Failed to generate video")
                
            # Save the video to our project directory
            output_path = self.dirs['videos'] / f"scene_{len(list(self.dirs['videos'].glob('*.mp4'))) + 1}.mp4"
            download_video(video_path, str(output_path))
            logger.info(f"Video saved to: {output_path}")
            
            # Extract last frame for next scene if needed
            if not is_first_scene:
                last_frame = self.dirs['images'] / f"last_frame_{len(list(self.dirs['videos'].glob('*.mp4')))}.jpg"
                logger.info(f"Extracting last frame to: {last_frame}")
                subprocess.run([
                    'ffmpeg', '-sseof', '-1', '-i', str(output_path),
                    '-update', '1', '-q:v', '1', str(last_frame)
                ], check=True, capture_output=True)
                return output_path, last_frame
            
            return output_path, None
            
        except Exception as e:
            logger.error(f"Error generating video scene: {e}")
            raise
            
    def combine_videos(self, video_paths, audio_path, subtitle_path):
        """Combine all video scenes with audio and subtitles"""
        try:
            # Create concat file
            concat_file = self.dirs['temp'] / 'concat.txt'
            with open(concat_file, 'w') as f:
                for video in video_paths:
                    f.write(f"file '{video.absolute()}'\n")
                    
            # Combine videos
            temp_combined = self.dirs['temp'] / 'combined.mp4'
            subprocess.run([
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                str(temp_combined)
            ], check=True, capture_output=True)
            
            # Add audio
            temp_with_audio = self.dirs['temp'] / 'with_audio.mp4'
            subprocess.run([
                'ffmpeg',
                '-i', str(temp_combined),
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                str(temp_with_audio)
            ], check=True, capture_output=True)
            
            # Add subtitles
            final_output = self.project_dir / f'final_story_{self.session_id}.mp4'
            subprocess.run([
                'ffmpeg',
                '-i', str(temp_with_audio),
                '-vf', f"subtitles={subtitle_path}:force_style='FontSize=24,Alignment=2'",
                '-c:a', 'copy',
                str(final_output)
            ], check=True, capture_output=True)
            
            # Cleanup
            shutil.rmtree(self.dirs['temp'])
            self.dirs['temp'].mkdir()
            
            return final_output
            
        except Exception as e:
            logger.error(f"Error combining videos: {e}")
            raise
            
    def generate_story_video(self, topic):
        """Main method to generate a complete story video"""
        try:
            logger.info(f"Starting story video generation for topic: {topic}")
            
            # Generate story script
            story_data = self.generate_story_script(topic)
            logger.info("Story script generated successfully")
            
            # Generate audio for the entire story
            full_narration = " ".join(scene["narration"] for scene in story_data["scenes"])
            audio_path = self.generate_audio(full_narration, "story_audio.wav")
            logger.info("Audio generated successfully")
            
            # Generate subtitles
            subtitle_path = self.generate_subtitles(full_narration, "story_subtitles")
            logger.info("Subtitles generated successfully")
            
            # Generate videos for each scene
            video_paths = []
            last_frame = None
            
            for i, scene in enumerate(story_data["scenes"]):
                logger.info(f"Generating video for scene {i+1}/{len(story_data['scenes'])}")
                video_path, last_frame = self.generate_video_scene(
                    scene["visual_description"],
                    last_frame,
                    is_first_scene=(i == 0)
                )
                video_paths.append(video_path)
                
            logger.info("All video scenes generated successfully")
            
            # Combine everything into final video
            final_video = self.combine_videos(video_paths, audio_path, subtitle_path)
            logger.info(f"Final video generated successfully: {final_video}")
            
            return {
                "project_dir": str(self.project_dir),
                "story_data": story_data,
                "audio_path": str(audio_path),
                "subtitle_path": str(subtitle_path),
                "video_paths": [str(p) for p in video_paths],
                "final_video": str(final_video)
            }
            
        except Exception as e:
            logger.error(f"Error in story video generation: {e}")
            if self.project_dir.exists():
                shutil.rmtree(self.project_dir)
            raise

def main():
    """Example usage of the StoryVideoGenerator"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("Please set the GOOGLE_API_KEY environment variable")
        
    generator = StoryVideoGenerator(google_api_key)
    result = generator.generate_story_video("A magical adventure in a forest")
    print(f"Story video generated successfully!")
    print(f"Final video: {result['final_video']}")

if __name__ == "__main__":
    main() 