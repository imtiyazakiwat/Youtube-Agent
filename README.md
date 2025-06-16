# Story Video Generator

A powerful tool for generating short story videos with AI-generated content, including narration, subtitles, and continuous scene transitions.

## Features

- Generates complete story scripts using Google's Gemini AI
- Creates 6-second video scenes with smooth transitions
- Generates natural-sounding narration using TTS
- Adds synchronized subtitles
- Combines everything into a final video with proper timing
- Maintains scene continuity by using the last frame of each scene

## Prerequisites

1. Python 3.8 or higher
2. FFmpeg installed on your system
3. Google API key for Gemini AI
4. Local services running:
   - Text-to-Speech service (port 5001)
   - SRT Generation service (port 8000)

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables:
   ```bash
   export GOOGLE_API_KEY="your_google_api_key_here"
   ```

## Usage

1. Start the required services:
   ```bash
   ./start_services.sh
   ```

2. Run the story video generator:
   ```bash
   python story_video_generator.py
   ```

   Or use it in your code:
   ```python
   from story_video_generator import StoryVideoGenerator
   
   generator = StoryVideoGenerator(google_api_key="your_key_here")
   result = generator.generate_story_video("A magical adventure in a forest")
   print(f"Video generated: {result['final_video']}")
   ```

## Project Structure

Each generated story creates a project directory with the following structure:
```
story_[timestamp]/
├── audio/
│   └── story_audio.wav
├── subtitles/
│   └── story_subtitles.srt
├── videos/
│   ├── scene_1.mp4
│   ├── scene_2.mp4
│   └── ...
├── images/
│   └── last_frame_*.jpg
├── story_script.json
└── final_story_[timestamp].mp4
```

## How It Works

1. **Script Generation**: Uses Gemini AI to create a story with multiple scenes
2. **Audio Generation**: Creates narration for the entire story
3. **Subtitle Generation**: Generates SRT subtitles synchronized with the audio
4. **Video Generation**:
   - First scene: Generated from text prompt
   - Subsequent scenes: Generated using the last frame of the previous scene
5. **Final Assembly**: Combines all scenes, adds audio and subtitles

## Error Handling

The generator includes comprehensive error handling and logging. Check the logs for detailed information about any issues during generation.

## Contributing

Feel free to submit issues and enhancement requests!
