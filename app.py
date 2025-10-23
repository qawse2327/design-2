from flask import Flask, render_template, request, jsonify
from fashn_tryon import run_tryon
import os, base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)

TOP_DIR = "static/tops"
BOTTOM_DIR = "static/bottoms"
OUTFIT_DIR = "static/outfits"
USER_IMG = "static/user.jpg"
RESULT_DIR = "static/results"
os.makedirs(RESULT_DIR, exist_ok=True)

# 메인 페이지
@app.route("/")
def index():
    return render_template("index.html")

# 촬영 페이지
@app.route("/capture")
def capture_page():
    return render_template("capture.html")

# 의류 선택 페이지
@app.route("/select")
def select_page():
    tops = [f"{TOP_DIR}/{f}" for f in os.listdir(TOP_DIR)]
    bottoms = [f"{BOTTOM_DIR}/{f}" for f in os.listdir(BOTTOM_DIR)]
    return render_template("select.html", tops=tops, bottoms=bottoms)

# 사진 업로드
@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json()
    img_data = data.get("image")
    header, encoded = img_data.split(",", 1)
    decoded = base64.b64decode(encoded)
    img = Image.open(BytesIO(decoded)).convert("RGB")
    img.save(USER_IMG, "JPEG", quality=95)
    return jsonify({"success": True})

# Try-On 실행
@app.route("/tryon", methods=["POST"])
def tryon():
    data = request.get_json()
    top = data.get("top")
    bottom = data.get("bottom")
    mode = data.get("mode")

    result_path = None
    if mode == "top" and top:
        result_path = run_tryon(USER_IMG, top, "result_top.jpg")
    elif mode == "bottom" and bottom:
        result_path = run_tryon(USER_IMG, bottom, "result_bottom.jpg")
    elif mode == "both" and top and bottom:
        top_num = os.path.basename(top).replace("top", "").split(".")[0]
        bottom_num = os.path.basename(bottom).replace("bottom", "").split(".")[0]
        outfit = f"{OUTFIT_DIR}/set_{top_num}_{bottom_num}.png"
        result_path = run_tryon(USER_IMG, outfit, f"result_set_{top_num}_{bottom_num}.jpg")

    return jsonify({"result": result_path})

# 결과 페이지
@app.route("/result")
def result_page():
    last_result = sorted(os.listdir(RESULT_DIR), key=lambda x: os.path.getmtime(os.path.join(RESULT_DIR, x)))[-1]
    return render_template("result.html", result_image=f"{RESULT_DIR}/{last_result}")

if __name__ == "__main__":
    app.run(debug=True)
