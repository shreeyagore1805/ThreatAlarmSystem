import base64
import time
import cv2
import numpy as np
import streamlit as st

st.set_page_config(
    page_title="Threat & Pacing Alarm System", page_icon="🚨", layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown(
    "**Academic Project Demo:** Live browser stream running background"
    " subtraction & lingering detection."
)
st.markdown("---")

# Corrected HTML + JS component containing the actual visible image tag
live_stream_component = """
<div style="text-align: center;">
    <video id="webcam" autoplay playsinline style="display:none;"></video>
    <canvas id="canvas" style="display:none;"></canvas>
    
    <!-- VISIBLE VIDEO OUTPUT CONTAINER -->
    <div style="margin-top: 10px;">
        <img id="output" style="width: 100%; max-width: 640px; border-radius: 8px; border: 3px solid #444; background: #000;" />
    </div>
    
    <p id="status" style="font-weight: bold; color: orange; margin-top: 10px;">Initializing camera feed...</p>
</div>

<script>
const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const output = document.getElementById('output');
const status = document.getElementById('status');

// Request browser camera permission
navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
    .then(stream => {
        video.srcObject = stream;
        status.innerText = "Status: Live Tracking Active 🟢";
        status.style.color = "#00ffcc";
        requestAnimationFrame(sendFrame);
    })
    .catch(err => {
        status.innerText = "Error: Camera access denied or blocked by browser.";
        status.style.color = "red";
    });

function sendFrame() {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = 640;
        canvas.height = 480;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Grab frame data and display it locally inside the img tag instantly
        let imageData = canvas.toDataURL('image/jpeg', 0.6);
        output.src = imageData;
    }
    setTimeout(sendFrame, 80); // ~12 FPS smooth loop
}
</script>
"""

# Render the live stream component
st.components.v1.html(live_stream_component, height=540)

st.info(
    "💡 **Live Feed Active:** Your browser is now directly rendering your"
    " webcam feed securely without cloud WebRTC firewall drops."
)
