from flask import Flask, render_template, request, jsonify
from fashn_tryon import run_tryon
import os, base64, time
from PIL import Image
from io import BytesIO

app = Flask(__name__)

TOP_DIR = "static/tops"
BOTTOM_DIR = "static/bottoms"
OUTFIT_DIR = "static/outfits"
USER_IMG = "static/user.jpg"
RESULT_DIR = "static/results"
os.makedirs(RESULT_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/capture")
def capture_page():
    return render_template("capture.html")

@app.route("/select")
def select_page():
    tops = [f"{TOP_DIR}/{f}" for f in os.listdir(TOP_DIR)]
    bottoms = [f"{BOTTOM_DIR}/{f}" for f in os.listdir(BOTTOM_DIR)]
    return render_template("select.html", tops=tops, bottoms=bottoms)

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json()
    img_data = data.get("image")
    if not img_data:
        return jsonify({"error": "No image data received"}), 400

    try:
        if "," in img_data:
            header, encoded = img_data.split(",", 1)
        else:
            encoded = img_data
        decoded = base64.b64decode(encoded)
        img = Image.open(BytesIO(decoded)).convert("RGB")
        img.save(USER_IMG, "JPEG", quality=95)
        return jsonify({"success": True})
    except Exception as e:
        print("DEBUG: Image decode error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/tryon", methods=["POST"])
def tryon():
    data = request.get_json()
    top = data.get("top")
    bottom = data.get("bottom")
    mode = data.get("mode")
    timestamp = int(time.time())
    result_filename = ""
    garment_to_try = ""
    try:
        if mode == "top" and top:
            result_filename = f"result_top_{timestamp}.jpg"
            garment_to_try = top
        elif mode == "bottom" and bottom:
            result_filename = f"result_bottom_{timestamp}.jpg"
            garment_to_try = bottom
        elif mode == "both" and top and bottom:
            top_num = os.path.basename(top).replace("top", "").split(".")[0]
            bottom_num = os.path.basename(bottom).replace("bottom", "").split(".")[0]
            outfit_name = f"set_{top_num}_{bottom_num}.png"
            outfit_path = os.path.join(OUTFIT_DIR, outfit_name)
            if not os.path.exists(outfit_path):
                return jsonify({"error": f"Outfit file {outfit_name} not found"}), 400
            result_filename = f"result_set_{top_num}_{bottom_num}_{timestamp}.jpg"
            garment_to_try = outfit_path
        if not garment_to_try:
            return jsonify({"error": "No garment selected"}), 400
        result_path = run_tryon(USER_IMG, garment_to_try, result_filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if result_path:
        return jsonify({"result": result_path})
    else:
        return jsonify({"error": "Try-on failed"}), 400

@app.route("/result")
def result_page():
    image_path = request.args.get("image")
    if not image_path or not os.path.exists(image_path):
        return "Result image not found", 404
    return render_template("result.html", result_image=image_path)

if __name__ == "__main__":
    # 외부 접속 + HTTPS
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=('cert.pem','key.pem'))
