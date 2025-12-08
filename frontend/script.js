/* ------------------------------------------
   GLOBAL VARIABLES FOR CAMERA & AUDIO
------------------------------------------ */
let audioContext = null;
let processor = null;
let inputStream = null;
let ws = null;


/* ------------------------------------------
   STOP CAMERA, MICROPHONE & AUDIO PROCESSING
------------------------------------------ */
function stopLiveStream() {
    console.log("Stopping camera, mic, audioContext, and WebSocket...");

    // Stop camera video tracks
    const video = document.getElementById("video");
    if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }

    // Stop microphone tracks
    if (inputStream) {
        inputStream.getTracks().forEach(track => track.stop());
        inputStream = null;
    }

    // Disconnect audio processor
    if (processor) {
        try { processor.disconnect(); } catch { }
        processor = null;
    }

    // Close audio context
    if (audioContext) {
        try { audioContext.close(); } catch { }
        audioContext = null;
    }

    // Close WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
        ws = null;
    }
}


/* ------------------------------------------
   PAGE NAVIGATION
------------------------------------------ */
function openPage(pageId) {

    // If leaving live page → stop stream
    if (pageId !== "live-page") {
        stopLiveStream();
    }

    // Toggle page visibility
    document.querySelectorAll(".page")
        .forEach(p => p.classList.remove("active"));

    document.getElementById(pageId).classList.add("active");

    // If entering live page → start stream
    if (pageId === "live-page") {
        startCamera();
    }
}


/* ------------------------------------------
   START CAMERA WHEN ENTERING LIVE PAGE
------------------------------------------ */
async function startCamera() {
    const video = document.getElementById("video");

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 360, height: 220 },
            audio: true
        });

        video.srcObject = stream;
        inputStream = stream;

        console.log("Camera & Microphone started.");

    } catch (err) {
        alert("Camera / Microphone access failed: " + err);
    }
}


/* ------------------------------------------
   FILE UPLOAD PREVIEW
------------------------------------------ */
document.getElementById("file-input").onchange = function () {
    const file = this.files[0];
    if (!file) return;

    const url = URL.createObjectURL(file);

    if (file.type.startsWith("video")) {
        document.getElementById("preview").src = url;
        document.getElementById("preview").style.display = "block";
        document.getElementById("audio-preview").style.display = "none";
    } else {
        document.getElementById("audio-preview").src = url;
        document.getElementById("audio-preview").style.display = "block";
        document.getElementById("preview").style.display = "none";
    }
};



/* ------------------------------------------
   SEND MEDIA TO BACKEND (AI TRANSCRIPTION)
------------------------------------------ */
async function sendMediaToBackend() {
    const fileInput = document.getElementById("file-input");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please upload an audio or video file.");
        return;
    }

    // Show loading text
    document.getElementById("upload-transcription").value = "Processing...";
    document.getElementById("upload-translation").value = "Processing...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("http://127.0.0.1:8000/upload-file/", {
            method: "POST",
            body: formData
        });


        const data = await response.json();

        // Display results from backend
        document.getElementById("upload-transcription").value = data.transcription;
        document.getElementById("upload-translation").value = data.translation;

    } catch (error) {
        console.error("Error:", error);
        alert("Backend error. Check console.");
    }
}



/* ------------------------------------------
   PROCESS UPLOADED MEDIA BUTTON (OLD)
   — replaced by sendMediaToBackend()
------------------------------------------ */
function processUpload() {
    alert("Use the new backend-powered button!");
}
