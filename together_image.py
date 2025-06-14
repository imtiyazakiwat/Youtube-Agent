import requests
import os
from datetime import datetime

API_KEY = "9c4531eeb315faa17599e185b66b58470a587b7908b6fe80fe921c56d464f3a6"
ENDPOINT = "https://api.together.xyz/v1/images/generations"

def generate_image(prompt):
    payload = {
        "model": "black-forest-labs/FLUX.1-schnell-Free",
        "prompt": prompt,
        "steps": 4,
        "n": 1,
        "width": 704,
        "height": 512
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print(f"🚀 Sending request with steps={payload['steps']}…")
    response = requests.post(ENDPOINT, json=payload, headers=headers)
    print(f"⏱ HTTP {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        print("❌ Response isn't JSON:")
        print(response.text)
        return None

    if response.status_code != 200:
        print("❌ Error response:")
        print(data)
        return None

    print("✅ Success:")
    print(data)
    return data

def download_image(url, output_dir):
    """Download image to specified output directory"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated_image_{timestamp}.jpg"
    filepath = os.path.join(output_dir, filename)
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"✅ Image saved to: {filepath}")
        return filepath
    else:
        print("❌ Failed to download image")
        return None
