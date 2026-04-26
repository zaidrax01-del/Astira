from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import time
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("MODELSLAB_API_KEY")

# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Generate Planet Image
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # Force planet-only generation 🔒
        final_prompt = f"{prompt}, detailed planet, space background, cinematic lighting, 4k, high quality"

        url = "https://modelslab.com/api/v6/realtime/text2img"

        payload = {
            "key": API_KEY,
            "prompt": final_prompt,
            "negative_prompt": "low quality, blurry, bad anatomy",
            "width": "512",
            "height": "512",
            "safety_checker": False,
            "seed": None,
            "samples": 1,
            "base64": False,
            "webhook": None,
            "track_id": None
        }

        response = requests.post(url, json=payload)
        result = response.json()

        # 🔁 Handle async (VERY IMPORTANT)
        if result.get("status") == "processing":
            fetch_url = result.get("fetch_result")

            # Wait and retry (max 5 times)
            for _ in range(5):
                time.sleep(3)
                r = requests.get(fetch_url)
                result = r.json()

                if result.get("status") == "success":
                    break

        # ✅ Success
        if result.get("status") == "success":
            image_url = result["output"][0]
            return jsonify({"image": image_url})

        # ❌ Failure
        return jsonify({
            "error": "Generation failed",
            "details": result
        }), 500

    except Exception as e:
        return jsonify({
            "error": "Server error",
            "details": str(e)
        }), 500


# Run app
if __name__ == "__main__":
    app.run(debug=True)
