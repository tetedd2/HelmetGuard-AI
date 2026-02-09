let camera = document.getElementById("camera");

function startCamera(){
    camera.src = "/video_feed";
}

function stopCamera(){
    camera.src = "";
}

async function loadStats(){
    let res = await fetch('/stats');
    let data = await res.json();
    document.getElementById("date").innerText = data.date;
    document.getElementById("count").innerText = data.no_helmet;
}

setInterval(loadStats, 1000);
