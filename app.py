from flask import Flask, request, jsonify, send_from_directory
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime, date
import os
import uuid

app = Flask(__name__, static_folder=".")

# โหลดโมเดล
model = YOLO("helmet.pt")

# โฟลเดอร์เก็บ snapshot
SNAP_DIR = "snapshots"
os.makedirs(SNAP_DIR, exist_ok=True)

today_nohelmet = 0
today_helmet = 0
current_date = date.today().isoformat()


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


@app.route("/detect", methods=["POST"])
def detect():
    global today_nohelmet, today_helmet, current_date

    if "image" not in request.files:
        return jsonify({"error": "No image"}), 400

    file = request.files["image"]
    img = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(img, cv2.IMREAD_COLOR)

    results = model(frame, conf=0.4, verbose=False)

    helmet_count = 0
    nohelmet_count = 0
    snapshots = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if label.lower() == "helmet":
                helmet_count += 1

            elif label.lower() == "no_helmet":
                nohelmet_count += 1

                crop = frame[y1:y2, x1:x2]
                if crop.size > 0:
                    filename = f"{uuid.uuid4().hex}.jpg"
                    path = os.path.join(SNAP_DIR, filename)
                    cv2.imwrite(path, crop)
                    snapshots.append(path)

    # reset รายวัน
    today = date.today().isoformat()
    if today != current_date:
        today_nohelmet = 0
        today_helmet = 0
        current_date = today

    today_nohelmet += nohelmet_count
    today_helmet += helmet_count

    return jsonify({
        "helmet": helmet_count,
        "no_helmet": nohelmet_count,
        "today_helmet": today_helmet,
        "today_nohelmet": today_nohelmet,
        "snapshots": snapshots[-3:],  # ส่งแค่ 3 รูปล่าสุด
        "time": datetime.now().strftime("%H:%M:%S")
    })


@app.route("/stats")
def stats():
    return jsonify({
        "date": current_date,
        "helmet": today_helmet,
        "no_helmet": today_nohelmet,
        "time": datetime.now().strftime("%H:%M:%S")
    })


@app.route("/snapshots/<path:filename>")
def get_snapshot(filename):
    return send_from_directory(SNAP_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
