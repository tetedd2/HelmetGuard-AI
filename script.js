const video = document.getElementById("video");

async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false
    });
    video.srcObject = stream;

    setInterval(captureAndSend, 1000); // ตรวจจับทุก 1 วินาที
}


async function captureAndSend() {
    if (!video.videoWidth) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    const blob = await new Promise(r => canvas.toBlob(r, "image/jpeg", 0.7));

    const form = new FormData();
    form.append("image", blob);

    const res = await fetch("/detect", {
        method: "POST",
        body: form
    });

    const data = await res.json();

    document.getElementById("nohelmet-count").innerText = data.today_total;
    document.getElementById("last-update").innerText = data.time;
}
