import os
import re
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ CONFIGURATION ------------------
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
USE_REPLICATE = bool(REPLICATE_API_TOKEN)

PLACEHOLDER_IMAGE = "https://placehold.co/1024x1024/1a2a3a/6bc2ff?text=AI+Planet+Image"
PLACEHOLDER_VIDEO = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

if USE_REPLICATE:
    import replicate
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)

# ------------------ FRONTEND ROUTE ------------------
@app.route('/')
def serve_frontend():
    return render_template('index.html')

# ------------------ API ROUTES ------------------
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

def generate_image(prompt: str) -> str:
    if not USE_REPLICATE:
        logger.warning("No REPLICATE_API_TOKEN set. Using placeholder image.")
        return PLACEHOLDER_IMAGE
    try:
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
                "scheduler": "DPMSolverMultistep",
                "num_inference_steps": 25,
                "guidance_scale": 7.5
            }
        )
        return output[0]
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return PLACEHOLDER_IMAGE

def generate_video(prompt: str) -> str:
    if not USE_REPLICATE:
        logger.warning("No REPLICATE_API_TOKEN set. Using placeholder video.")
        return PLACEHOLDER_VIDEO
    try:
        image_prompt = prompt.replace("rotating animated", "static").replace("Short seamless loop animation", "High quality still")
        image_url = generate_image(image_prompt)
        output = replicate.run(
            "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
            input={
                "input_image": image_url,
                "num_frames": 25,
                "fps": 6,
                "motion_bucket_id": 127,
                "cond_aug": 0.02,
                "decoding_t": 7,
                "seed": 42
            }
        )
        return output
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return PLACEHOLDER_VIDEO

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
    return jsonify({"status": "ok", "replicate_available": USE_REPLICATE})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
