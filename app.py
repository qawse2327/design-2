from flask import Flask, render_template, request, jsonify
from fashn_tryon import run_tryon
import os, base64, time # time 모듈 추가
from PIL import Image
from io import BytesIO

app = Flask(__name__)

TOP_DIR = "static/tops"
BOTTOM_DIR = "static/bottoms"
OUTFIT_DIR = "static/outfits" # 'both' 모드를 위한 사전 조합된 이미지 폴더
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
    header, encoded = img_data.split(",", 1)
    decoded = base64.b64decode(encoded)
    img = Image.open(BytesIO(decoded)).convert("RGB")
    img.save(USER_IMG, "JPEG", quality=95)
    return jsonify({"success": True})

@app.route("/tryon", methods=["POST"])
def tryon():
    print("DEBUG: tryon 함수 진입")
    data = request.get_json()
    print("DEBUG: request data", data)

    top = data.get("top")
    bottom = data.get("bottom")
    mode = data.get("mode")

    result_path = None
    
    # [수정됨] 덮어쓰기 방지를 위해 고유한 파일 이름 생성
    timestamp = int(time.time())
    
    # [수정됨] fashn_tryon.py는 output_filename을 받아서 static/results/에 저장하므로,
    # 여기서는 파일 *이름*만 전달합니다.
    result_filename = ""
    garment_to_try = ""

    try:
        if mode == "top" and top:
            result_filename = f"result_top_{timestamp}.jpg"
            garment_to_try = top # top 이미지 경로 (예: static/tops/top1.png)

        elif mode == "bottom" and bottom:
            result_filename = f"result_bottom_{timestamp}.jpg"
            garment_to_try = bottom # bottom 이미지 경로

        elif mode == "both" and top and bottom:
            # [경고] 이 로직은 fashn.ai API가 'both'를 지원하지 않기 때문에,
            # 'static/outfits' 폴더에 'set_X_Y.png' 같은 미리 조합된 파일이 
            # *반드시* 있어야만 작동합니다.
            try:
                # 이 파일명 파싱 로직은 'top1.png', 'bottom2.png' 같은 이름에만 작동합니다.
                top_num = os.path.basename(top).replace("top", "").split(".")[0]
                bottom_num = os.path.basename(bottom).replace("bottom", "").split(".")[0]
                
                outfit_name = f"set_{top_num}_{bottom_num}.png" # 또는 .jpg?
                outfit_path = os.path.join(OUTFIT_DIR, outfit_name)

                if not os.path.exists(outfit_path):
                     print(f"DEBUG: 'both' 모드 오류. {outfit_path} 파일이 없습니다.")
                     return jsonify({"error": f"해당 조합의 'set' 파일이 서버에 없습니다."}), 400
                
                result_filename = f"result_set_{top_num}_{bottom_num}_{timestamp}.jpg"
                garment_to_try = outfit_path # 미리 조합된 outfit 이미지 경로

            except Exception as e:
                print(f"DEBUG: 'both' 모드 파일 이름 파싱 오류: {e}")
                return jsonify({"error": "파일 이름 규칙이 맞지 않아 'both' 모드 처리에 실패했습니다."}), 400
        
        if not garment_to_try:
             return jsonify({"error": "합성할 옷 정보가 없습니다."}), 400

        # fashn_tryon.py 호출
        # USER_IMG: 사용자 사진, garment_to_try: 옷 사진, result_filename: 저장할 파일 *이름*
        result_path = run_tryon(USER_IMG, garment_to_try, result_filename)

    except Exception as e:
        print(f"DEBUG: tryon 예외 발생: {e}")
        return jsonify({"error": f"서버 내부 오류: {e}"}), 500

    if result_path:
        # fashn_tryon.py가 'static/results/...' 경로를 반환
        return jsonify({"result": result_path})
    else:
        return jsonify({"error": "합성 실패"}), 400

# [수정됨] /result 라우트가 쿼리 파라미터로 정확한 이미지 경로를 받도록 수정
@app.route("/result")
def result_page():
    # 1. 'select.html'의 JS가 넘겨준 'image' 파라미터를 받습니다.
    image_path = request.args.get("image")

    # 2. 이미지 경로가 없거나, 해당 파일이 실제로 존재하지 않으면 404 오류
    if not image_path or not os.path.exists(image_path):
        return "결과 이미지를 찾을 수 없거나 경로가 잘못되었습니다.", 404
        
    # 3. 템플릿에 정확한 경로 전달
    return render_template("result.html", result_image=image_path)


if __name__ == "__main__":
    app.run(debug=True)
