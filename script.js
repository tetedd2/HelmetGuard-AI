const video = document.getElementById("camera");

let streamRef = null;
let intervalRef = null;

// ===============================
// START CAMERA
// ===============================
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" },
            audio: false
        });

        video.srcObject = stream;
        streamRef = stream;

        intervalRef = setInterval(captureAndSend, 1000);
        console.log("📷 Camera started");

    } catch (err) {
        alert("ไม่สามารถเปิดกล้องได้: " + err.message);
        console.error(err);
    }
}

// ===============================
// STOP CAMERA
// ===============================
function stopCamera() {
    if (streamRef) {
        streamRef.getTracks().forEach(track => track.stop());
        streamRef = null;
    }

    if (intervalRef) {
        clearInterval(intervalRef);
        intervalRef = null;
    }

    console.log("⛔ Camera stopped");
}

// ===============================
// CAPTURE FRAME → SEND TO FLASK
// ===============================
async function captureAndSend() {
    if (!video.videoWidth) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    const blob = await new Promise(resolve =>
        canvas.toBlob(resolve, "image/jpeg", 0.75)
    );

    const form = new FormData();
    form.append("image", blob, "frame.jpg");

    try {
        const res = await fetch("/detect", {
            method: "POST",
            body: form
        });

        if (!res.ok) throw new Error("Server error");

        const data = await res.json();

        updateDashboard(data);

    } catch (err) {
        console.error("❌ Detect error:", err);
    }
}

// ===============================
// UPDATE DASHBOARD
// ===============================
function updateDashboard(data) {
    if (document.getElementById("nohelmet-count"))
        document.getElementById("nohelmet-count").innerText = data.today_nohelmet;

    if (document.getElementById("last-update"))
        document.getElementById("last-update").innerText = data.time;

    if (data.snapshots)
        renderSnapshots(data.snapshots);
}

// ===============================
// RENDER SNAPSHOT IMAGES
// ===============================
function renderSnapshots(images) {
    const box = document.getElementById("snapshots");
    if (!box) return;

    box.innerHTML = "";

    images.forEach(img => {
        const el = document.createElement("img");
        el.src = img;
        el.style.width = "100%";
        el.style.borderRadius = "12px";
        el.style.marginBottom = "10px";
        el.style.boxShadow = "0 2px 10px rgba(0,0,0,.2)";
        box.appendChild(el);
    });
}
