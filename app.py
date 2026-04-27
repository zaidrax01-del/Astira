from flask import Flask, request, jsonify, render_template
import requests
import os
import time

app = Flask(__name__)

API_KEY = os.getenv("MODELSLAB_API_KEY")

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        user_prompt = data.get("prompt", "").lower()
        mode = data.get("mode", "static")  # static or dynamic

        # 🔒 FORCE PLANET ONLY
        allowed_words = ["planet", "galaxy", "world", "cosmic", "space", "orb"]

        if not any(word in user_prompt for word in allowed_words):
            return jsonify({
                "error": "❌ Only planet-related prompts allowed"
            }), 400

        # ✨ Improve prompt automatically
        final_prompt = f"high quality detailed space planet, {user_prompt}, glowing, cosmic background, 4k"

        # ========================
        # 🖼 STATIC IMAGE
        # ========================
        if mode == "static":
            url = "https://modelslab.com/api/v6/realtime/text2img"

            payload = {
                "key": API_KEY,
                "prompt": final_prompt,
                "negative_prompt": "car, human, animal, building",
                "width": "512",
                "height": "512",
                "safety_checker": False
            }

            res = requests.post(url, json=payload)
            result = res.json()

            # 🧠 handle processing
            while result.get("status") == "processing":
                time.sleep(2)
                fetch_url = result.get("fetch_result")
                res = requests.get(fetch_url)
                result = res.json()

            if "output" not in result:
                return jsonify({"error": result}), 500

            return jsonify({
                "type": "image",
                "url": result["output"][0]
            })


        # ========================
        # 🎥 DYNAMIC VIDEO
        # ========================
        elif mode == "dynamic":
            url = "https://modelslab.com/api/v6/text2video"

            payload = {
                "key": API_KEY,
                "prompt": final_prompt + ", rotating planet, cinematic animation",
                "seconds": 3
            }

            res = requests.post(url, json=payload)
            result = res.json()

            # 🧠 wait for video
            while result.get("status") == "processing":
                time.sleep(3)
                fetch_url = result.get("fetch_result")
                res = requests.get(fetch_url)
                result = res.json()

            if "output" not in result:
                return jsonify({"error": result}), 500

            return jsonify({
                "type": "video",
                "url": result["output"][0]
            })

        else:
            return jsonify({"error": "Invalid mode"}), 400

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
