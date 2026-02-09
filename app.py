from flask import Flask, request, jsonify, send_from_directory
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime, date
import os

app = Flask(__name__, static_folder=".")

model = YOLO("helmet.pt")

today_count = 0
current_date = date.today().isoformat()


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


@app.route("/detect", methods=["POST"])
def detect():
    global today_count, current_date

    if "image" not in request.files:
        return jsonify({"error": "No image"}), 400

    file = request.files["image"]
    img = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(img, cv2.IMREAD_COLOR)

    results = model(frame, conf=0.4, verbose=False)

    detections = []
    no_helmet = 0

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]
            conf = float(box.conf[0])

            if label.lower() == "no_helmet":
                no_helmet += 1

            detections.append({
                "label": label,
                "confidence": round(conf, 2)
            })

    today = date.today().isoformat()
    if today != current_date:
        today_count = 0
        current_date = today

    today_count += no_helmet

    return jsonify({
        "detections": detections,
        "no_helmet": no_helmet,
        "today_total": today_count,
        "time": datetime.now().strftime("%H:%M:%S")
    })


@app.route("/stats")
def stats():
    return jsonify({
        "date": current_date,
        "no_helmet": today_count,
        "time": datetime.now().strftime("%H:%M:%S")
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
