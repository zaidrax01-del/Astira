from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("MODELSLAB_API_KEY")

PLANET_KEYWORDS = [
    "planet", "world", "moon", "globe",
    "gas giant", "exoplanet", "celestial"
]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()

        prompt = data.get("prompt", "").lower()
        mode = data.get("mode", "image")  # image or video

        if not prompt:
            return jsonify({
                "status": "error",
                "image": None,
                "message": "Prompt required"
            }), 400

        # ❌ Restrict to planet-related prompts
        if not any(word in prompt for word in PLANET_KEYWORDS):
            return jsonify({
                "status": "error",
                "image": None,
                "message": "Only planet-related prompts allowed"
            }), 400

        # 🔥 Force planet output
        final_prompt = f"{prompt}, detailed planet, space, cinematic lighting, ultra realistic"

        # 🔁 Choose API
        if mode == "video":
            url = "https://modelslab.com/api/v6/text2video"
        else:
            url = "https://modelslab.com/api/v6/text2img"

        payload = {
            "key": API_KEY,
            "prompt": final_prompt,
            "negative_prompt": "car, human, building, text, watermark",
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "30"
        }

        # 🚀 Initial request
        response = requests.post(url, json=payload)
        result = response.json()

        print("STEP 1:", result)

        # ⏳ Handle async processing
        if result.get("status") == "processing":
            request_id = result.get("id")

            for _ in range(10):
                time.sleep(2)

                fetch = requests.post(
                    "https://modelslab.com/api/v6/fetch",
                    json={
                        "key": API_KEY,
                        "request_id": request_id
                    }
                ).json()

                print("FETCH:", fetch)

                if fetch.get("status") == "success":
                    result = fetch
                    break

        # ✅ Success
        if result.get("status") == "success":
            output = result.get("output")

            if not output:
                return jsonify({
                    "status": "error",
                    "image": None,
                    "message": "No image returned"
                }), 500

            return jsonify({
                "status": "success",
                "image": output[0]   # 🔥 IMPORTANT (matches your HTML)
            })

        # ❌ Failure
        return jsonify({
            "status": "error",
            "image": None,
            "message": result.get("message", "Generation failed")
        }), 500

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "status": "error",
            "image": None,
            "message": "Server error"
        }), 500


@app.route("/health")
def health():
    return "OK 🚀"


if __name__ == "__main__":
    app.run(debug=True)            "message": "Server error"
        }), 500


# 🔥 Health check
@app.route("/health")
def health():
    return "OK 🚀"


if __name__ == "__main__":
    app.run(debug=True)
