import os
import json
import time
import requests
from pathlib import Path
import shutil

class VideoContentGenerator:
    def __init__(self, openrouter_api_key):
        self.openrouter_api_key = openrouter_api_key
        self.base_dir = Path(__file__).parent
        self.session_id = str(int(time.time()))
        self.setup_directories()

    def setup_directories(self):
        """Create necessary directories for the project"""
        self.project_dir = self.base_dir / f"project_{self.session_id}"
        
        # Create subdirectories
        self.dirs = {
            'videos': self.project_dir / 'videos',
            'audio': self.project_dir / 'audio',
            'subtitles': self.project_dir / 'subtitles',
            'images': self.project_dir / 'images'
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def generate_script(self, prompt):
        """Generate script using OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen/qwen-2.5-72b-instruct:free",
            "messages": [
                {"role": "system", "content": "You are a script writer for short videos."},
                {"role": "user", "content": f"Write a short, exciting script (~50-70 words) for a video about: {prompt}"}
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            script = response.json()['choices'][0]['message']['content']
            
            # Save script to file
            script_path = self.project_dir / 'script.txt'
            with open(script_path, 'w') as f:
                f.write(script)
            
            return script
        else:
            raise Exception(f"Script generation failed: {response.text}")

    def generate_voice(self, script):
        """Generate voice using local TTS API"""
        response = requests.post(
            "http://localhost:5002/tts",
            json={
                "text": script,
                "filename": f"speech_{self.session_id}.wav"
            }
        )
        
        if response.status_code == 200:
            audio_path = self.dirs['audio'] / f"speech_{self.session_id}.wav"
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            return audio_path
        else:
            raise Exception(f"Voice generation failed: {response.text}")

    def generate_subtitles(self, script):
        """Generate SRT subtitles using local API"""
        response = requests.post(
            "http://localhost:8000/generate-srt",
            json={
                "script": script,
                "filename": f"subtitles_{self.session_id}"
            }
        )
        
        if response.status_code == 200:
            srt_path = self.dirs['subtitles'] / f"subtitles_{self.session_id}.srt"
            with open(srt_path, 'wb') as f:
                f.write(response.content)
            return srt_path
        else:
            raise Exception(f"Subtitle generation failed: {response.text}")

    def generate_image_prompts(self, script):
        """Generate exactly 3 image prompts using OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen/qwen2.5-vl-72b-instruct:free", 
            "messages": [
                {"role": "system", "content": "Create exactly 3 different scene descriptions from the script for image generation."},
                {"role": "user", "content": f"Create exactly 3 different visual scene descriptions (one per line) from this script: {script}"}
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            prompts = response.json()['choices'][0]['message']['content'].split('\n')
            # Filter empty lines and take exactly 3 prompts
            prompts = [p.strip() for p in prompts if p.strip()][:3]
            if len(prompts) != 3:
                raise Exception("Failed to generate exactly 3 image prompts")
            return prompts
        else:
            raise Exception(f"Image prompts generation failed: {response.text}")

    def generate_ai_video(self, prompts):
        """Generate video by animating exactly 3 images"""
        from together_image import generate_image, download_image
        from image_to_video_test import generate_video_from_image
        
        if len(prompts) != 3:
            raise Exception("Exactly 3 prompts are required")
            
        video_paths = []
        for i, prompt in enumerate(prompts, 1):
            print(f"\nProcessing scene {i}/3...")
            # Generate and save image
            result = generate_image(prompt)
            if result and 'data' in result and len(result['data']) > 0:
                image_url = result['data'][0]['url']
                image_path = download_image(image_url, output_dir=str(self.dirs['images']))
                
                if image_path:
                    print(f"Generating video for scene {i}...")
                    video_path = generate_video_from_image(
                        image_path,
                        f"Animate this scene: {prompt}",
                        output_dir=str(self.dirs['videos']),
                        max_retries=3
                    )
                    if video_path:
                        video_paths.append(video_path)
                        print(f"Scene {i} completed ✅")
                    else:
                        raise Exception(f"Failed to generate video for scene {i}")
                else:
                    raise Exception(f"Failed to save image for scene {i}")
            else:
                raise Exception(f"Failed to generate image for scene {i}")
        
        if len(video_paths) == 3:
            # For now, just return the path to the first video
            # TODO: Add video concatenation logic here
            return video_paths[0]
        raise Exception("Failed to generate all 3 video segments")

    def create_final_movie(self, result):
        """Create final movie from generated content"""
        import subprocess
        from pathlib import Path

        print("\n🎬 Creating final movie...")
        
        try:
            # Step 1: Create concat file for videos and get total duration
            video_list = sorted(self.dirs['videos'].glob('*.mp4'))
            concat_file = self.project_dir / 'concat.txt'
            with open(concat_file, 'w') as f:
                for video in video_list:
                    f.write(f"file '{video.absolute()}'\n")

            # Step 2: Combine all videos with transition
            temp_combined = self.project_dir / 'temp_combined.mp4'
            subprocess.run([
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(concat_file),
                '-filter_complex',
                '[0:v]format=yuv420p,fps=30[v]',
                '-map', '[v]',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                str(temp_combined)
            ], check=True)

            # Get video duration
            probe = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(temp_combined)
            ], capture_output=True, text=True)
            
            import json
            video_duration = float(json.loads(probe.stdout)['format']['duration'])
            
            # Step 3: Process audio to match video duration
            audio_file = next(self.dirs['audio'].glob('*.wav'))
            temp_audio = self.project_dir / 'temp_audio.wav'
            subprocess.run([
                'ffmpeg',
                '-i', str(audio_file),
                '-af', f'apad=whole_dur={video_duration}',
                '-y', str(temp_audio)
            ], check=True)

            # Step 4: Combine video and audio
            temp_with_audio = self.project_dir / 'temp_with_audio.mp4'
            subprocess.run([
                'ffmpeg',
                '-i', str(temp_combined),
                '-i', str(temp_audio),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                str(temp_with_audio)
            ], check=True)

            # Step 5: Add synchronized subtitles
            srt_file = next(self.dirs['subtitles'].glob('*.srt'))
            final_movie = self.project_dir / f'final_movie_{self.session_id}.mp4'
            subprocess.run([
                'ffmpeg',
                '-i', str(temp_with_audio),
                '-vf', f"subtitles={srt_file}:force_style='FontSize=24,Alignment=2'",
                '-c:a', 'copy',
                '-shortest',
                str(final_movie)
            ], check=True)

            # Cleanup temp files
            for temp_file in [concat_file, temp_combined, temp_audio, temp_with_audio]:
                if temp_file.exists():
                    temp_file.unlink()

            print(f"✅ Final movie created at: {final_movie}")
            return True

        except Exception as e:
            print(f"❌ Failed to create final movie: {e}")
            return False

    def create_content(self, prompt):
        """Main method to create all content"""
        try:
            print(f"Creating project directory: {self.project_dir}")
            
            # Generate and save script
            print("Generating script...")
            script = self.generate_script(prompt)
            print(f"Script generated and saved to {self.project_dir/'script.txt'}")
            
            # Generate voice
            print("Generating voice...")
            voice_path = self.generate_voice(script)
            print(f"Voice generated and saved to {voice_path}")
            
            # Generate subtitles
            print("Generating subtitles...")
            srt_path = self.generate_subtitles(script)
            print(f"Subtitles generated and saved to {srt_path}")
            
            # Generate image prompts
            print("Generating image prompts...")
            image_prompts = self.generate_image_prompts(script)
            print(f"Generated {len(image_prompts)} image prompts")
            
            # Generate video from images
            print("Generating video from images...")
            video_path = self.generate_ai_video(image_prompts)
            print(f"Video generated and saved to {video_path}")
            
            result = {
                "project_dir": str(self.project_dir),
                "script": script,
                "voice_path": str(voice_path),
                "srt_path": str(srt_path),
                "image_prompts": image_prompts,
                "video_path": str(video_path)
            }
            
            # Automatically create final movie after content generation
            self.create_final_movie(result)
            
            return result
            
        except Exception as e:
            print(f"Error during content creation: {str(e)}")
            if self.project_dir.exists():
                shutil.rmtree(self.project_dir)
            raise

def main():
    # Replace with your OpenRouter API key
    OPENROUTER_API_KEY = "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"
    
    generator = VideoContentGenerator(OPENROUTER_API_KEY)
    
    prompt = input("Enter your video idea: ")
    
    try:
        result = generator.create_content(prompt)
        print("\nContent creation completed successfully!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Content creation failed: {str(e)}")

if __name__ == "__main__":
    main()
