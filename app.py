from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("MODELSLAB_API_KEY")


@app.route("/")
def home():
    return "Backend running 🚀"


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()

        user_prompt = data.get("prompt", "").strip()
        mode = data.get("mode", "image")  # image or video

        if not user_prompt:
            return jsonify({"error": "Prompt required"}), 400

        # 🌍 FORCE PLANET OUTPUT
        base_prompt = f"""
        A unique fictional planet in space inspired by {user_prompt}.
        Transform everything into a planet.
        Spherical celestial body only.
        Highly detailed, glowing atmosphere, cinematic lighting, 4k.
        """

        negative_prompt = "car, vehicle, human, person, building, house, road, logo, text, animal"

        headers = {
            "key": API_KEY
        }

        # ===== IMAGE =====
        if mode == "image":
            url = "https://modelslab.com/api/v6/realtime/text2img"

            payload = {
                "prompt": base_prompt,
                "negative_prompt": negative_prompt,
                "width": "512",
                "height": "512",
                "samples": "1",
                "num_inference_steps": "30",
                "guidance_scale": 7.5
            }

            res = requests.post(url, headers=headers, json=payload)
            result = res.json()

            if "output" not in result or not result["output"]:
                return jsonify({"error": result}), 500

            return jsonify({"image_url": result["output"][0]})

        # ===== VIDEO =====
        elif mode == "video":
            url = "https://modelslab.com/api/v6/video/text2video"

            video_prompt = f"""
            A rotating animated planet in space inspired by {user_prompt}.
            Short seamless loop animation (3–5 seconds).
            Smooth continuous rotation.
            Loopable, no cuts.
            Glowing atmosphere, particles, cinematic lighting, 4k.
            """

            payload = {
                "prompt": video_prompt,
                "negative_prompt": negative_prompt
            }

            res = requests.post(url, headers=headers, json=payload)
            result = res.json()

            if "output" not in result or not result["output"]:
                return jsonify({"error": result}), 500

            return jsonify({"video_url": result["output"][0]})

        else:
            return jsonify({"error": "Invalid mode"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
