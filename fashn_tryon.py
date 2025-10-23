import base64
import requests
import time
import os

# 📌 API 설정
API_KEY = "fa-O9nzZ97u2dz0-Mtw8hvvXGUX66NAqPWgGjxRn"
BASE_URL = "https://api.fashn.ai/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 로컬 이미지를 base64로 인코딩
def encode_image(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")


# Fashn.ai Try-On API 실행
def run_tryon(model_img_path, garment_img_path, output_filename):
    print(f"🚀 Fashn Try-On 요청 전송 중... ({garment_img_path})")

    # 출력 폴더 자동 생성
    result_dir = "static/results"
    os.makedirs(result_dir, exist_ok=True)
    output_path = os.path.join(result_dir, output_filename)

    model_b64 = encode_image(model_img_path)
    garment_b64 = encode_image(garment_img_path)

    # ✅ category: auto (상의/하의 자동 인식)
    input_data = {
        "model_name": "tryon-v1.6",
        "inputs": {
            "model_image": model_b64,
            "garment_image": garment_b64,
            "category": "auto",
            "segmentation_free": True,
            "moderation_level": "permissive"
        }
    }

    # 1️⃣ /run 요청
    run_response = requests.post(f"{BASE_URL}/run", json=input_data, headers=HEADERS)
    run_data = run_response.json()
    if "id" not in run_data:
        print("❌ API 호출 실패:", run_data)
        return None
    run_id = run_data["id"]

    # 2️⃣ 상태 폴링
    while True:
        status_resp = requests.get(f"{BASE_URL}/status/{run_id}", headers=HEADERS).json()

        if status_resp["status"] == "completed":
            print("✅ 합성 완료 →", output_path)
            output_urls = status_resp["output"]
            img_data = requests.get(output_urls[0]).content
            with open(output_path, "wb") as f:
                f.write(img_data)
            return output_path

        elif status_resp["status"] in ["starting", "in_queue", "processing"]:
            print("⏳ 상태:", status_resp["status"])
            time.sleep(3)

        else:
            print("❌ 실패:", status_resp)
            return None
