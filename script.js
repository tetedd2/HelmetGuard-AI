const video = document.getElementById("camera");
let stream = null;
let timer = null;

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        });

        video.srcObject = stream;
        await video.play();

        timer = setInterval(captureAndSend, 500); // 2 FPS → เสถียรสุด

    } catch (err) {
        alert("ไม่สามารถเปิดกล้องได้: " + err.message);
        console.error(err);
    }
}

function stopCamera() {
    clearInterval(timer);
    timer = null;

    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }

    video.srcObject = null;
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

    const imgBlob = await res.blob();
    const url = URL.createObjectURL(imgBlob);

    video.poster = url;
}

/* ------------------ UI ------------------ */

function showPage(page) {
    ["live","guide","dashboard"].forEach(p=>{
        document.getElementById("page-"+p).style.display = "none";
        document.getElementById("nav-"+p).classList.remove("active");
    });

    document.getElementById("page-"+page).style.display = "block";
    document.getElementById("nav-"+page).classList.add("active");
}

let history = [];

async function loadDashboard() {
    const res = await fetch("/stats");
    const data = await res.json();

    document.getElementById("nohelmet-count").innerText = data.no_helmet;
    document.getElementById("last-update").innerText = data.time;

    history.push(data.no_helmet);
    if (history.length > 20) history.shift();

    drawChart();
}

setInterval(loadDashboard, 1000);

function drawChart() {
    const c = document.getElementById("chart");
    const ctx = c.getContext("2d");

    ctx.clearRect(0,0,c.width,c.height);

    ctx.beginPath();
    ctx.strokeStyle = "#00ff00";
    ctx.lineWidth = 3;

    history.forEach((v,i)=>{
        let x = i*(c.width/20);
        let y = c.height - (v * 5);
        if(i===0) ctx.moveTo(x,y);
        else ctx.lineTo(x,y);
    });

    ctx.stroke();
}
