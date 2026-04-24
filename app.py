from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__, template_folder="templates", static_folder="static")


# Home route
@app.route("/")
def home():
    return render_template("index.html")


# Image generation route (adjust to match your HTML fetch)
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # 🔥 TEMP: using simple working image source (replace later if needed)
        image_url = f"https://image.pollinations.ai/prompt/{prompt}"

        return jsonify({
            "success": True,
            "image": image_url
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Health check (for Render)
@app.route("/test")
def test():
    return "Server is working"


if __name__ == "__main__":
    app.run(debug=True)
