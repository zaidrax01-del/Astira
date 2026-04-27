import os
import re
import logging
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ CONFIGURATION ------------------
MODELSLAB_API_KEY = os.environ.get("MODELSLAB_API_KEY")
USE_MODELSLAB = bool(MODELSLAB_API_KEY)

PLACEHOLDER_IMAGE = "https://placehold.co/1024x1024/1a2a3a/6bc2ff?text=AI+Planet+Image"
PLACEHOLDER_VIDEO = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

# ------------------ FRONTEND ROUTE ------------------
@app.route('/')
def serve_frontend():
    return render_template('index.html')

# ------------------ PROMPT TRANSFORMATION ------------------
NEGATIVE_PROMPT = "car, vehicle, human, person, building, house, road, animal, logo, text, object"

def transform_to_planet(raw_prompt: str, mode: str) -> str:
    if not re.search(r'\bplanet\b', raw_prompt, re.IGNORECASE):
        raw_prompt += " planet"
    if mode == "image":
        return f"A highly detailed fictional planet in space inspired by {raw_prompt}. Spherical celestial body, glowing atmosphere, stars, cinematic lighting, ultra realistic, 4k."
    else:
        return f"A rotating animated planet in space inspired by {raw_prompt}. Short seamless loop animation, smooth continuous rotation, glowing atmosphere, cinematic lighting, ultra realistic, 4k."

# ------------------ IMAGE GENERATION ------------------
def generate_image(prompt: str) -> str:
    if not USE_MODELSLAB:
        logger.warning("No MODELSLAB_API_KEY set. Using placeholder.")
        return PLACEHOLDER_IMAGE

    logger.info(f"Attempting to generate image with prompt: {prompt[:100]}...")
    
    # Try different possible ModelsLab endpoints
    endpoints = [
        "https://api.modelslab.com/api/v2/text2img",
        "https://api.modelslab.com/v1/image/generate",
        "https://modelslab.com/api/v2/text2img"
    ]
    
    headers = {
        "Authorization": f"Bearer {MODELSLAB_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Common payload formats
    payload_formats = [
        {"prompt": prompt, "negative_prompt": NEGATIVE_PROMPT, "width": 1024, "height": 1024},
        {"inputs": prompt, "parameters": {"negative_prompt": NEGATIVE_PROMPT}},
        {"text": prompt, "negative_text": NEGATIVE_PROMPT}
    ]
    
    for endpoint in endpoints:
        for payload in payload_formats:
            try:
                logger.info(f"Trying endpoint: {endpoint}")
                response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Response data (truncated): {str(data)[:500]}")
                    
                    # Try different response formats
                    if "output" in data and data["output"]:
                        return data["output"][0] if isinstance(data["output"], list) else data["output"]
                    elif "image_url" in data:
                        return data["image_url"]
                    elif "images" in data and data["images"]:
                        return data["images"][0]
                    elif "url" in data:
                        return data["url"]
                    elif "data" in data and isinstance(data["data"], list):
                        return data["data"][0]
            except Exception as e:
                logger.error(f"Error with endpoint {endpoint}: {e}")
                continue
    
    logger.error("All ModelsLab endpoints failed")
    return PLACEHOLDER_IMAGE

# ------------------ VIDEO GENERATION ------------------
def generate_video(prompt: str) -> str:
    if not USE_MODELSLAB:
        return PLACEHOLDER_VIDEO
    
    logger.info(f"Video generation attempted (placeholder for now)")
    # ModelsLab video endpoint - adjust based on your API docs
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
    logger.info(f"Mode: {mode}, Transformed prompt: {transformed_prompt}")

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
    return jsonify({"status": "ok", "modelslab_available": USE_MODELSLAB})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
