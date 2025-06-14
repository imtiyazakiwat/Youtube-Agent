import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class VideoProcessor:
    def __init__(self):
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov'}
        self.audio_extensions = {'.wav', '.mp3', '.aac', '.m4a'}
        self.subtitle_extensions = {'.srt'}

    def process_folder(self, folder_path):
        """Process media files in project folder"""
        folder = Path(folder_path)
        
        # Get files from project subdirectories
        videos = list(folder.glob('videos/*.mp4'))
        audios = list(folder.glob('audio/*.wav'))
        subtitles = list(folder.glob('subtitles/*.srt'))
        
        if not videos:
            print("❌ No video files found")
            return False

        # Create temporary working directory
        temp_dir = folder / 'temp'
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Prepare output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_output = folder / f"final_movie_{timestamp}.mp4"
            current_video = videos[0]  # Start with first video

            # Combine videos if multiple exist
            if len(videos) > 1:
                concat_output = temp_dir / "combined.mp4"
                if not self._concatenate_videos(videos, concat_output):
                    return False
                current_video = concat_output

            # Add audio if exists
            if audios:
                audio_output = temp_dir / "with_audio.mp4"
                if not self._add_audio(current_video, audios[0], audio_output):
                    return False
                current_video = audio_output

            # Add subtitles if exist
            if subtitles:
                if not self._add_subtitles(current_video, subtitles[0], final_output):
                    return False
            else:
                shutil.copy2(current_video, final_output)

            print(f"✅ Movie saved to: {final_output}")
            return True

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _concatenate_videos(self, videos, output):
        """Concatenate multiple videos"""
        try:
            list_file = output.parent / "list.txt"
            with open(list_file, 'w') as f:
                for video in videos:
                    f.write(f"file '{video.absolute()}'\n")

            cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(list_file),
                   '-c', 'copy', str(output), '-y']
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"❌ Error concatenating videos: {e}")
            return False
        finally:
            if list_file.exists():
                list_file.unlink()

    def _add_audio(self, video, audio, output):
        """Add audio to video"""
        try:
            cmd = ['ffmpeg', '-i', str(video), '-i', str(audio), 
                  '-c:v', 'copy', '-c:a', 'aac', str(output), '-y']
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"❌ Error adding audio: {e}")
            return False

    def _add_subtitles(self, video, subtitle, output):
        """Add subtitles to video"""
        try:
            cmd = ['ffmpeg', '-i', str(video), '-vf', 
                  f"subtitles={subtitle}", str(output), '-y']
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"❌ Error adding subtitles: {e}")
            return False
