from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app)

# 🔑 API KEY (set this in Render ENV)
API_KEY = os.getenv("MODELSLAB_API_KEY")

# 🌍 Allowed keywords
PLANET_KEYWORDS = [
    "planet", "world", "moon", "globe",
    "gas giant", "exoplanet", "celestial"
]


# ✅ Serve frontend
@app.route("/")
def home():
    return render_template("index.html")


# 🚀 Generate endpoint
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "").lower()
        mode = data.get("mode", "static")  # static or dynamic

        # ❌ Restrict prompts
        if not any(word in prompt for word in PLANET_KEYWORDS):
            return jsonify({
                "status": "error",
                "message": "❌ Only planet-related prompts allowed"
            }), 400

        # 🔥 Force planet style
        final_prompt = f"{prompt}, detailed planet, space, cinematic lighting, ultra realistic"

        # 🧠 Choose endpoint
        if mode == "dynamic":
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

        # 🚀 Send request
        response = requests.post(url, json=payload)
        result = response.json()

        print("STEP 1 RESPONSE:", result)

        # 🟡 If processing → poll result
        if result.get("status") == "processing":
            request_id = result.get("id")

            fetch_url = "https://modelslab.com/api/v6/fetch"

            for _ in range(10):  # try 10 times
                time.sleep(2)

                check = requests.post(fetch_url, json={
                    "key": API_KEY,
                    "request_id": request_id
                }).json()

                print("FETCH RESPONSE:", check)

                if check.get("status") == "success":
                    result = check
                    break

        # ✅ Success
        if result.get("status") == "success":
            output = result.get("output")

            if not output:
                return jsonify({
                    "status": "error",
                    "message": "No image returned"
                }), 500

            return jsonify({
                "status": "success",
                "type": "video" if mode == "dynamic" else "image",
                "url": output[0]
            })

        # ❌ Fail
        return jsonify({
            "status": "error",
            "message": result.get("message", "Generation failed")
        }), 500

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "status": "error",
            "message": "Server error"
        }), 500


# 🔥 Health check
@app.route("/health")
def health():
    return "OK 🚀"


if __name__ == "__main__":
    app.run(debug=True)
