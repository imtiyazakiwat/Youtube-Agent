# N8n YouTube/Reel Content Generation Agent

This N8n workflow automates the creation of various assets for short-form video content (like YouTube Shorts or Instagram Reels) based on a simple text prompt. It generates a script, converts it to speech, creates captions, generates relevant AI images and videos, and finds stock footage.

**Workflow Visualization:**

(Consider adding a screenshot of your N8n workflow here)

## Features

*   **Input:** Takes a simple text prompt describing the video idea via an N8n Form Trigger.
*   **Script Generation:** Uses an AI language model (OpenRouter - Qwen) to write a short, engaging script (~50-70 words).
*   **Text-to-Speech (TTS):** Converts the generated script into an audio file (`.wav`) using a local TTS service.
*   **Caption Generation:** Creates subtitle (`.srt`) files based on the script using a local captioning service.
*   **Image/Video Prompt Generation:** Uses an AI language model (OpenRouter - Qwen VL) to create concise prompts suitable for generating visuals based on the script.
*   **AI Image Generation:** Generates an AI image using the Google Gemini API based on the derived prompt.
*   **AI Video Generation:** Generates a short AI video clip using a Hugging Face Space API (ZeroScope v2) based on the derived prompt.
*   **Stock Video Search:** Searches Pexels for relevant stock videos based on the derived prompt.
*   **File Organization:** Creates a unique folder for each execution using the execution ID to store all generated assets.
*   **Outputs:** Saves the script (`.txt`), speech audio (`.wav`), captions (`.srt`), AI image (`.png`), AI video (`.mp4`), and downloaded stock videos (`.mp4`) locally where N8n has write access.

## Prerequisites

1.  **N8n Instance:** A running N8n instance (self-hosted or cloud).
2.  **N8n Nodes:** Ensure the `@n8n/n8n-nodes-langchain` package is installed if using relevant nodes. Standard nodes like `HttpRequest`, `ExecuteCommand`, `ReadWriteFile`, `ItemLists`, `ConvertToFile`, `Code`, `FormTrigger` should be available.
3.  **API Keys & Credentials:**
    *   **OpenRouter:**
        *   An OpenRouter API Key. This needs to be configured as an N8n credential named "OpenRouter account" (or update the nodes to use your credential name). Used for script and image/video prompt generation.
    *   **Google Gemini:**
        *   A Google Cloud API Key with the Generative Language API enabled. This key is currently **hardcoded** in the `Create AI Image` node's query parameters. You **must** edit this node and paste your key.
    *   **Pexels:**
        *   A Pexels API Key. This key is currently **hardcoded** as `DLeEua` in the `Search Videos on Pexel` node's header parameters. You **must** edit this node and replace `DLeEua` with your actual Pexels API Key.
4.  **Local Services (Crucial):**
    *   **Text-to-Speech (TTS) Service:** A TTS service must be running and accessible to your N8n instance at `http://host.docker.internal:5001/tts`. This service needs to accept a POST request with `text` (the script) and `filename` (desired output filename) parameters and return the audio file.
    *   **Caption (SRT) Generation Service:** An SRT generation service must be running and accessible to your N8n instance at `http://host.docker.internal:8000/generate-srt`. This service needs to accept a POST request with `script` (the script) and `filename` (desired base name for the SRT file) and return the SRT file.
    *   **Note on `host.docker.internal`**: This hostname typically works when N8n is running as a Docker container on Docker Desktop (Windows/Mac) to allow the container to reach services running on the host machine. If your N8n setup or local service setup is different (e.g., N8n running directly on host, N8n on Linux Docker, different container network), you will need to **adjust these URLs** accordingly to point correctly to your running TTS and SRT services.
5.  **N8n Permissions:**
    *   **Execute Command:** The N8n instance needs permission to execute the `mkdir` command (enabled via environment variables, e.g., `N8N_ALLOW_NODE=ExecuteCommandNode`).
    *   **File System Access:** N8n needs write permissions to the directory where it's running or a configured data volume to save the generated files (`./{{ $execution.id }}/...`).

## Setup Instructions

1.  **Import Workflow:**
    *   Download the `YoutubeAgent.json` file provided.
    *   In your N8n instance, go to "Workflows" and click "Import from File".
    *   Upload the JSON file.
2.  **Configure Credentials:**
    *   Go to "Credentials" in your N8n instance.
    *   Click "Add Credential".
    *   Search for "OpenRouter API".
    *   Enter your OpenRouter API key and give it a recognizable name (e.g., "OpenRouter account", matching the name in the workflow nodes).
    *   Save the credential. Ensure the `OpenRouter Chat Model` nodes in the workflow are configured to use this credential.
3.  **Configure API Keys in Nodes:**
    *   **Google Gemini:** Open the workflow, find the `Create AI Image` (HttpRequest) node. Go to the "Query Parameters" section and replace the empty `value` for the `key` parameter with your actual Google Gemini API Key.
    *   **Pexels:** Open the workflow, find the `Search Videos on Pexel` (HttpRequest) node. Go to the "Headers" section and replace `DLeEua` in the `Authorization` parameter's value with your actual Pexels API Key.
4.  **Set Up Local Services:**
    *   Ensure your TTS and SRT generation services are running.
    *   Verify that they are accessible from your N8n environment using the URLs specified in the `Create speech` and `Create Caption` nodes (`http://host.docker.internal:5001/tts` and `http://host.docker.internal:8000/generate-srt`).
    *   **Adjust URLs if necessary** based on your specific N8n and service hosting setup (see Prerequisites Note on `host.docker.internal`).
5.  **Enable Execute Command (If Needed):**
    *   If you haven't already, configure your N8n environment variables to allow the Execute Command node. Refer to the N8n documentation on security. For Docker, you might add `-e N8N_ALLOW_NODE=ExecuteCommandNode` to your `docker run` command or `environment` section in `docker-compose.yml`. Restart N8n after changing environment variables.
6.  **Check File Permissions:**
    *   Ensure the user running the N8n process has write permissions in the N8n installation directory or its configured data directory.

## How to Use

1.  **Activate Workflow:** Open the workflow in N8n and toggle the "Active" switch to ON in the top-right corner.
2.  **Trigger:** The workflow uses a "Form Trigger". Access the Production URL provided by the `Write video idea` (Form Trigger) node.
3.  **Submit Prompt:** Enter your video idea into the form field (e.g., "A cat discovering a hidden portal in a bookshelf") and submit.
4.  **Execution:** N8n will execute the workflow. You can monitor the progress in the "Executions" list.
5.  **Retrieve Outputs:** Once the execution is complete, navigate to the N8n server's file system (or the mapped volume). You will find a folder named after the execution ID (e.g., `./123/`). Inside this folder, you will find the generated files:
    *   `script.txt`
    *   `speech<execution_id>.wav`
    *   `script.srt`
    *   `image<execution_id>.png`
    *   `aiVideo<execution_id>.mp4`
    *   `video<pexels_video_id>.mp4` (potentially multiple if the workflow were modified to download more than one)

## Workflow Breakdown

1.  **Input & Setup:** Form Trigger receives the prompt, Execute Command creates a unique output folder.
2.  **Scripting:** OpenRouter LLM generates the script based on the prompt.
3.  **Local Asset Generation:**
    *   The script is saved as `.txt`.
    *   The script is sent to the local TTS service to create `.wav` audio.
    *   The script is sent to the local SRT service to create `.srt` captions.
4.  **Visual Prompting:** Another OpenRouter LLM (VL model) creates short prompts for visual generation from the script.
5.  **API Asset Generation:**
    *   **AI Image:** Google Gemini API is called to create a `.png` image.
    *   **AI Video:** Hugging Face API is called to create and download an `.mp4` video.
    *   **Stock Video:** Pexels API is searched, and the first relevant `.mp4` video is downloaded.
6.  **Saving:** All downloaded/generated binary files (audio, image, videos) are saved to the execution-specific folder.

## Important Notes & Troubleshooting

*   **API Costs & Limits:** Be mindful of the API usage costs and rate limits for OpenRouter, Google Cloud, and Pexels.
*   **Local Service Dependency:** The workflow heavily relies on the **availability and correct functioning** of your local TTS and SRT generation services. Ensure they are running before executing the workflow. Errors in these services will cause the workflow to fail at those steps.
*   **`host.docker.internal`:** This is a common point of failure if your N8n setup doesn't match the Docker Desktop environment assumption. Double-check connectivity from N8n to your local services.
*   **Hugging Face Space Availability:** The AI Video generation relies on a specific Hugging Face Space (`hysts-zeroscope-v2`). These spaces can sometimes be offline, rate-limited, or change their API structure, which would break that part of the workflow.
*   **Execution Time:** Generating AI images and especially videos can take a significant amount of time. The workflow might run for several minutes.
*   **Error Handling:** This workflow has basic implicit error handling (N8n stops on node failure). For production use, consider adding explicit error handling branches.
*   **File Paths:** The workflow assumes it can write to `./{{ $execution.id }}/`. Ensure this relative path works in your N8n environment. You might need to use absolute paths depending on configuration.
