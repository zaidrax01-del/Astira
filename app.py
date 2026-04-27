from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("MODELSLAB_API_KEY")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        print("🔥 /generate called")

        data = request.get_json()
        print("Incoming data:", data)

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        prompt = data.get("prompt")
        mode = data.get("mode", "static")

        if not prompt:
            return jsonify({"error": "Prompt missing"}), 400

        if not API_KEY:
            return jsonify({"error": "API key missing on server"}), 500

        # 🌍 Force planet style
        final_prompt = f"A beautiful unique planet in space, {prompt}, glowing atmosphere, cinematic lighting, 4k, ultra realistic"

        print("Final prompt:", final_prompt)

        # Choose endpoint
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

        print("Sending request to Modelslab...")

        response = requests.post(url, json=payload, timeout=60)

        print("Status Code:", response.status_code)
        print("Raw response:", response.text)

        try:
            result = response.json()
        except:
            return jsonify({"error": "Invalid JSON from API", "raw": response.text}), 500

        print("Parsed result:", result)

        # Handle API error
        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        if result.get("status") == "processing":
            return jsonify({"error": "Still processing, try again"}), 202

        output = result.get("output")

        if not output:
            return jsonify({"error": "No output in response", "full": result}), 500

        return jsonify({
            "output": output[0]
        })

    except Exception as e:
        print("💥 SERVER ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
