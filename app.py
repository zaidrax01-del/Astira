from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import time
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

        if not API_KEY:
            print("❌ API KEY MISSING")
            return jsonify({"error": "API key not set on server"}), 500

        data = request.get_json()
        print("📦 Incoming data:", data)

        prompt = data.get("prompt")
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        final_prompt = f"{prompt}, detailed planet, space, cinematic lighting, 4k"
        print("🎯 Final prompt:", final_prompt)

        url = "https://modelslab.com/api/v6/realtime/text2img"

        payload = {
            "key": API_KEY,
            "prompt": final_prompt,
            "width": "512",
            "height": "512",
            "samples": 1
        }

        print("🚀 Sending request to Modelslab...")
        response = requests.post(url, json=payload)

        print("📡 Raw response:", response.text)

        result = response.json()
        print("🧠 Parsed response:", result)

        # Handle async processing
        if result.get("status") == "processing":
            fetch_url = result.get("fetch_result")

            if not fetch_url:
                return jsonify({"error": "No fetch URL returned"}), 500

            print("⏳ Processing... polling")

            for i in range(5):
                time.sleep(3)
                poll = requests.get(fetch_url).json()
                print(f"🔄 Poll {i+1}:", poll)

                if poll.get("status") == "success":
                    return jsonify({"image": poll["output"][0]})

            return jsonify({"error": "Still processing, try again"}), 500

        # Success instantly
        if result.get("status") == "success":
            return jsonify({"image": result["output"][0]})

        # Failure
        return jsonify({
            "error": "Model failed",
            "details": result
        }), 500

    except Exception as e:
        print("❌ SERVER ERROR:", str(e))
        return jsonify({
            "error": "Server crashed",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
