from flask import Flask, Response, render_template_string
import cv2
from ultralytics import YOLO
import datetime, os
import pandas as pd

app = Flask(__name__)

# โหลดโมเดล
model = YOLO("helmet.pt")  # ใช้โมเดล helmet ที่คุณมี

# โฟลเดอร์เก็บ log + รูป
os.makedirs("captures", exist_ok=True)
LOG_FILE = "log.csv"

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["time","count"]).to_csv(LOG_FILE, index=False)

cap = None

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Helmet Detection AI</title>
<style>
body{font-family:Segoe UI;text-align:center;background:#0f172a;color:white;}
video,img{border-radius:16px;border:3px solid #38bdf8;margin-top:10px;}
button{padding:12px 25px;font-size:18px;border-radius:12px;border:none;margin:10px;cursor:pointer;}
.stat{font-size:22px;margin-top:15px}
</style>
</head>
<body>

<h1>🚦 AI ตรวจจับหมวกกันน็อก</h1>

<button onclick="start()">เปิดกล้อง</button>
<button onclick="stop()">ปิดกล้อง</button>

<br>
<img src="/video">

<div class="stat">📊 วันนี้พบไม่ใส่หมวก: {{count}} ครั้ง</div>

<script>
function start(){ fetch("/start") }
function stop(){ fetch("/stop") }
</script>

</body>
</html>
"""

@app.route('/')
def index():
    df = pd.read_csv(LOG_FILE)
    today = datetime.date.today().isoformat()
    count = df[df["time"].str.contains(today)].shape[0]
    return render_template_string(HTML, count=count)

@app.route('/start')
def start():
    global cap
    if cap is None:
        cap = cv2.VideoCapture(0)
    return "ok"

@app.route('/stop')
def stop():
    global cap
    if cap:
        cap.release()
        cap = None
    return "ok"

def gen_frames():
    global cap
    while True:
        if cap is None:
            continue
        success, frame = cap.read()
        if not success:
            break

        results = model(frame, conf=0.4)

        no_helmet = 0

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = model.names[cls]

                if label.lower() in ["no helmet","without helmet","no-helmet"]:
                    no_helmet += 1
                    x1,y1,x2,y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),2)
                    cv2.putText(frame,"NO HELMET",(x1,y1-10),
                                cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,0,255),2)

                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    cv2.imwrite(f"captures/{ts}.jpg", frame)

        if no_helmet > 0:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df = pd.read_csv(LOG_FILE)
            df.loc[len(df)] = [now, no_helmet]
            df.to_csv(LOG_FILE,index=False)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
