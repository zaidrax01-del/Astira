import os
import re
import logging
import requests
import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ CONFIGURATION ------------------
MODELSLAB_API_KEY = os.environ.get("MODELSLAB_API_KEY", "GoVcDK5X0lCBO7g5EqA5nadFa271inGouA7Rs2YIciqejZfaTfF9G1pJkzlX")
MODELSLAB_IMAGE_URL = "https://modelslab.com/api/v6/images/text2img"

PLACEHOLDER_VIDEO = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

# ------------------ FRONTEND ROUTE ------------------
@app.route('/')
def serve_frontend():
    return render_template('index.html')

# ------------------ PROMPT TRANSFORMATION ------------------
NEGATIVE_PROMPT = "car, vehicle, human, person, building, house, road, animal, logo, text, object, weapon, gun, tank, airplane, blurry, low quality, deformed"

def transform_to_planet(raw_prompt: str, mode: str) -> str:
    if not re.search(r'\bplanet\b', raw_prompt, re.IGNORECASE):
        raw_prompt += " planet"
    
    if mode == "image":
        return f"A highly detailed fictional planet in space inspired by {raw_prompt}. Spherical celestial body, glowing atmosphere, stars, cinematic lighting, ultra realistic, 4k, detailed textures, vibrant colors."
    else:
        return f"A rotating animated planet in space inspired by {raw_prompt}. Short seamless loop animation, smooth continuous rotation, glowing atmosphere, moving particles, cinematic lighting, ultra realistic, 4k."

# ------------------ IMAGE GENERATION (ModelsLab v6) ------------------
def generate_image(prompt: str) -> str:
    logger.info(f"Generating image with prompt: {prompt[:100]}...")
    
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "width": "1024",
        "height": "1024",
        "samples": "1",
        "model_id": "flux-klein",
        "key": MODELSLAB_API_KEY
    }
    
    try:
        logger.info(f"Sending request to {MODELSLAB_IMAGE_URL}")
        response = requests.post(MODELSLAB_IMAGE_URL, json=payload, timeout=120)
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response keys: {data.keys() if data else 'None'}")
            
            # Handle ModelsLab response - image URL is in future_links
            if "future_links" in data and data["future_links"]:
                image_url = data["future_links"][0]
                logger.info(f"✅ Image generated successfully: {image_url}")
                return image_url
            
            # Alternative response formats
            elif "output" in data and data["output"]:
                image_url = data["output"][0] if isinstance(data["output"], list) else data["output"]
                logger.info(f"✅ Image from output: {image_url}")
                return image_url
            
            elif "image_url" in data:
                logger.info(f"✅ Image from image_url: {data['image_url']}")
                return data["image_url"]
            
            elif "images" in data and data["images"]:
                logger.info(f"✅ Image from images: {data['images'][0]}")
                return data["images"][0]
            
            else:
                logger.error(f"Unexpected response format: {data}")
                # If we have an ID, we could poll the fetch endpoint
                if "id" in data:
                    fetch_url = f"https://modelslab.com/api/v6/images/fetch/{data['id']}"
                    logger.info(f"Trying to fetch from: {fetch_url}")
                    time.sleep(2)  # Wait a bit
                    fetch_response = requests.get(fetch_url, params={"key": MODELSLAB_API_KEY})
                    if fetch_response.status_code == 200:
                        fetch_data = fetch_response.json()
                        if "output" in fetch_data and fetch_data["output"]:
                            return fetch_data["output"][0]
                
                return f"https://placehold.co/1024x1024/1a2a3a/ff6666?text=No+image+URL"
        else:
            error_text = response.text[:200]
            logger.error(f"API error {response.status_code}: {error_text}")
            return f"https://placehold.co/1024x1024/1a2a3a/ff6666?text=Error:{response.status_code}"
            
    except requests.exceptions.Timeout:
        logger.error("Request timeout - API took too long")
        return "https://placehold.co/1024x1024/1a2a3a/ffaa44?text=Timeout"
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return f"https://placehold.co/1024x1024/1a2a3a/ff6666?text=Exception"

def generate_video(prompt: str) -> str:
    logger.info(f"Video generation requested (placeholder for now)")
    return PLACEHOLDER_VIDEO

# ------------------ MAIN ROUTE ------------------
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "error": "No JSON body"}), 400

    raw_prompt = data.get('prompt', '').strip()
    mode = data.get('mode', 'image')

    if not raw_prompt:
        return jsonify({"status": "error", "error": "Missing prompt"}), 400

    transformed_prompt = transform_to_planet(raw_prompt, mode)
    logger.info(f"Mode: {mode}")

    try:
        if mode == 'image':
            image_url = generate_image(transformed_prompt)
            return jsonify({"status": "success", "image": image_url})
        else:
            video_url = generate_video(transformed_prompt)
            return jsonify({"status": "success", "image": video_url})
    except Exception as e:
        logger.exception("Unexpected error")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
