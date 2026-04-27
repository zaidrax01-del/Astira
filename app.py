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
        data = request.get_json() or {}

        prompt = data.get("prompt", "").strip().lower()
        mode = data.get("mode", "image")

        if not prompt:
            return jsonify({
                "status": "error",
                "image": None,
                "message": "Prompt is required"
            }), 400

        # 🔑 Check API key
        if not API_KEY:
            return jsonify({
                "status": "error",
                "image": None,
                "message": "API key missing (set MODELSLAB_API_KEY on Render)"
            }), 500

        # 🌍 Restrict to planets
        if not any(word in prompt for word in PLANET_KEYWORDS):
            return jsonify({
                "status": "error",
                "image": None,
                "message": "Only planet-related prompts allowed"
            }), 400

        # 🔥 Force planet styling
        final_prompt = f"{prompt}, detailed planet, space, cinematic lighting, ultra realistic"

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

        # 🚀 Send request
        response = requests.post(url, json=payload, timeout=60)

        # ⚠️ Handle non-JSON safely
        try:
            result = response.json()
        except:
            return jsonify({
                "status": "error",
                "image": None,
                "message": "Invalid response from AI server"
            }), 500

        print("MODEL RESPONSE:", result)

        # ⏳ Handle async processing
        if result.get("status") == "processing":
            request_id = result.get("id")

            for _ in range(10):
                time.sleep(2)

                fetch_res = requests.post(
                    "https://modelslab.com/api/v6/fetch",
                    json={
                        "key": API_KEY,
                        "request_id": request_id
                    },
                    timeout=30
                )

                try:
                    fetch = fetch_res.json()
                except:
                    continue

                print("FETCH:", fetch)

                if fetch.get("status") == "success":
                    result = fetch
                    break

        # ✅ SUCCESS
        if result.get("status") == "success":
            output = result.get("output")

            if output and len(output) > 0:
                return jsonify({
                    "status": "success",
                    "image": output[0]
                })

            return jsonify({
                "status": "error",
                "image": None,
                "message": "No image returned"
            }), 500

        # ❌ HANDLE API ERROR CLEANLY
        return jsonify({
            "status": "error",
            "image": None,
            "message": result.get("message", "Generation failed")
        }), 200  # 👈 IMPORTANT (no more HTTP 500)

    except Exception as e:
        print("SERVER ERROR:", str(e))
        return jsonify({
            "status": "error",
            "image": None,
            "message": "Server crashed"
        }), 200  # 👈 prevents frontend breaking


@app.route("/health")
def health():
    return "OK 🚀"


if __name__ == "__main__":
    app.run(debug=True)
