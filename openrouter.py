import requests
import json

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": "Bearer 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",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://youtube-agent.imtiyaz.dev",  # ✅ Replace with your domain or GitHub link
        "X-Title": "Youtube-Agent",  # ✅ Your app/project name
    },
    data=json.dumps({
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                        }
                    }
                ]
            }
        ]
    })
)

print(json.dumps(response.json(), indent=2))
