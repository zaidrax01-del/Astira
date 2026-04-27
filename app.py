from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 🔑 Your Modelslab API key (set this in Render ENV)
API_KEY = os.getenv("MODELSLAB_API_KEY")

# 🌍 Allowed keywords (to enforce planet-only)
PLANET_KEYWORDS = [
    "planet", "world", "globe", "moon", "gas giant",
    "exoplanet", "celestial", "orbit", "space planet"
]


# ✅ Serve your HTML
@app.route("/")
def home():
    return render_template("index.html")


# 🚀 Generate image
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "").lower()

        # ❌ Reject non-planet prompts
        if not any(word in prompt for word in PLANET_KEYWORDS):
            return jsonify({
                "status": "error",
                "message": "❌ Only planet-related prompts are allowed."
            }), 400

        # 🔥 Force it into planet style
        final_prompt = f"{prompt}, detailed planet, space background, cinematic lighting, ultra realistic"

        url = "https://modelslab.com/api/v6/realtime/text2img"

        payload = {
            "key": API_KEY,
            "prompt": final_prompt,
            "negative_prompt": "car, human, building, text, watermark",
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "30",
            "guidance_scale": 7.5,
            "safety_checker": "no"
        }

        response = requests.post(url, json=payload)
        result = response.json()

        print("Modelslab response:", result)  # 🔍 helps debug in logs

        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "image": result["output"][0]
            })

        else:
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


# 🔥 Health check (optional but useful)
@app.route("/health")
def health():
    return "OK 🚀"


if __name__ == "__main__":
    app.run(debug=True)
