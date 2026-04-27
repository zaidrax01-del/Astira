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
NEGATIVE_PROMPT = "car, vehicle, human, person, building, house, road, animal, logo, text, object, weapon, gun, tank, airplane"

def transform_to_planet(raw_prompt: str, mode: str) -> str:
    if not re.search(r'\bplanet\b', raw_prompt, re.IGNORECASE):
        raw_prompt += " planet"
    if mode == "image":
        return (f"A highly detailed fictional planet in space inspired by {raw_prompt}. "
                "Transform the concept into a planet surface and atmosphere. "
                "Spherical celestial body, glowing atmosphere, stars, cinematic lighting, ultra realistic, 4k, detailed textures.")
    else:
        return (f"A rotating animated planet in space inspired by {raw_prompt}. "
                "Transform the concept into a planet design. "
                "Short seamless loop animation, duration 3 to 5 seconds, smooth continuous rotation, no cuts, no scene change. "
                "Glowing atmosphere, moving particles, cinematic lighting, ultra realistic, 4k.")

# ------------------ IMAGE GENERATION (ModelsLab) ------------------
def generate_image(prompt: str) -> str:
    if not USE_MODELSLAB:
        logger.warning("No MODELSLAB_API_KEY set. Using placeholder image.")
        return PLACEHOLDER_IMAGE

    headers = {
        "Authorization": f"Bearer {MODELSLAB_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 25,
        "guidance_scale": 7.5
    }
    try:
        response = requests.post(
            "https://api.modelslab.com/api/v2/text2img",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        if "output" in data and isinstance(data["output"], list) and data["output"]:
            return data["output"][0]
        elif "image_url" in data:
            return data["image_url"]
        else:
            logger.error(f"Unexpected response: {data}")
            return PLACEHOLDER_IMAGE
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return PLACEHOLDER_IMAGE

# ------------------ VIDEO GENERATION (ModelsLab) ------------------
def generate_video(prompt: str) -> str:
    if not USE_MODELSLAB:
        logger.warning("No MODELSLAB_API_KEY set. Using placeholder video.")
        return PLACEHOLDER_VIDEO

    headers = {
        "Authorization": f"Bearer {MODELSLAB_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "num_frames": 25,
        "fps": 6
    }
    try:
        response = requests.post(
            "https://api.modelslab.com/api/v2/text2video",
            json=payload,
            headers=headers,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        if "output" in data and isinstance(data["output"], list) and data["output"]:
            return data["output"][0]
        elif "video_url" in data:
            return data["video_url"]
        else:
            logger.error(f"Unexpected video response: {data}")
            return PLACEHOLDER_VIDEO
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
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
    logger.info(f"Transformed prompt ({mode}): {transformed_prompt}")

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
