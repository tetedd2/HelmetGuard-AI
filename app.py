from flask import Flask, Response, request, jsonify
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime, date

app = Flask(__name__)
model = YOLO("helmet.pt")

today_count = 0
current_date = date.today().isoformat()

@app.route('/')
def index():
    return open("index.html", encoding="utf-8").read()

# รับภาพจากมือถือ → ตรวจจับ → ส่งภาพกลับ
@app.route('/detect', methods=['POST'])
def detect():
    global today_count, current_date

    file = request.files['image']
    img = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(img, cv2.IMREAD_COLOR)

    if frame is None:
        return "Invalid image", 400

    results = model(frame, conf=0.4)
    no_helmet = 0

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if label.lower() in ["no helmet", "without helmet", "no-helmet"]:
                no_helmet += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, "NO HELMET",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                            (0, 0, 255), 2)

    today = date.today().isoformat()
    if today != current_date:
        today_count = 0
        current_date = today

    if no_helmet > 0:
        today_count += no_helmet

    _, jpg = cv2.imencode('.jpg', frame)
    return Response(jpg.tobytes(), mimetype='image/jpeg')

# API ส่งค่าสถิติ realtime ไป dashboard
@app.route('/stats')
def stats():
    return jsonify({
        "date": current_date,
        "no_helmet": today_count,
        "time": datetime.now().strftime("%H:%M:%S")
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
