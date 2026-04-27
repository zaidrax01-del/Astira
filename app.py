from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 🔑 Put your API key in Render ENV (IMPORTANT)
API_KEY = os.getenv("MODELSLAB_API_KEY")

# 🌍 Planet enforcement
def force_planet_prompt(user_prompt):
    return f"A beautiful unique planet in space, {user_prompt}, cinematic lighting, glowing atmosphere, ultra realistic, 4k, space background"

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        user_prompt = data.get("prompt", "")
        mode = data.get("mode", "static")  # static or dynamic

        if not user_prompt:
            return jsonify({"error": "Prompt required"}), 400

        # 🌍 Force planet
        final_prompt = force_planet_prompt(user_prompt)

        # 🔀 Choose API
        if mode == "dynamic":
            url = "https://modelslab.com/api/v6/video/text2video"
        else:
            url = "https://modelslab.com/api/v6/realtime/text2img"

        payload = {
            "key": API_KEY,
            "prompt": final_prompt,
            "negative_prompt": "cars, humans, buildings, text, watermark",
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "30",
            "guidance_scale": 7.5
        }

        response = requests.post(url, json=payload)
        result = response.json()

        print("MODEL RESPONSE:", result)  # 👈 VERY IMPORTANT (check logs)

        # ❌ Handle errors safely
        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        if result.get("status") == "processing":
            return jsonify({"error": "Still generating, try again"}), 202

        # ✅ Extract output safely
        output = result.get("output")

        if not output:
            return jsonify({"error": "No output returned"}), 500

        return jsonify({
            "output": output[0]
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
