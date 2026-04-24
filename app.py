from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Your ModelsLab API key (set this in Render environment variables)
API_KEY = os.getenv("MODELSLAB_API_KEY")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # ModelsLab API endpoint
        url = "https://modelslab.com/api/v6/images/text2img"

        payload = {
            "key": API_KEY,
            "prompt": prompt,
            "negative_prompt": "blurry, bad quality",
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "20",
            "guidance_scale": 7.5,
            "safety_checker": "no"
        }

        response = requests.post(url, json=payload)
        result = response.json()

        print("API RESPONSE:", result)  # debug log

        # ✅ FIX: correct response handling
        if "output" in result and len(result["output"]) > 0:
            image_url = result["output"][0]
            return jsonify({"image": image_url})

        return jsonify({"error": result}), 500

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)