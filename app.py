from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

API_KEY = "YOUR_MODELSLAB_API_KEY"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        user_prompt = data.get("prompt", "")

        # 🌍 FORCE PLANET STYLE
        final_prompt = f"""
        A highly detailed sci-fi planet NFT.
        Style: {user_prompt}
        Space background, glowing, cinematic lighting,
        ultra realistic, 4k, digital art
        """

        url = "https://modelslab.com/api/v6/realtime/text2img"

        payload = {
            "key": API_KEY,
            "prompt": final_prompt,
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "30",
            "guidance_scale": 7.5
        }

        response = requests.post(url, json=payload)
        result = response.json()

        if "output" not in result:
            return jsonify({"error": "Generation failed", "details": result}), 500

        image_url = result["output"][0]

        # ✅ VERY IMPORTANT: match frontend
        return jsonify({
            "image": image_url
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
