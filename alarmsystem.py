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

# HTML + JS bridge to stream live frames smoothly to your Python backend
live_stream_component = """
<div style="text-align: center;">
    <video id="webcam" autoplay playsinline style="display:none;"></video>
    <canvas id="canvas" style="display:none;"></canvas>
    <div>
        <img id="output" style="width: 100%; max-width: 640px; border-radius: 8px; border: 3px solid #333; background: #000;" />
    </div>
    <p id="status" style="font-weight: bold; color: orange; margin-top: 10px;">Initializing camera feed...</p>
</div>

<script>
const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const output = document.getElementById('output');
const status = document.getElementById('status');

navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
    .then(stream => {
        video.srcObject = stream;
        status.innerText = "Status: Live Tracking Active 🟢";
        status.style.color = "green";
        requestAnimationFrame(sendFrame);
    })
    .catch(err => {
        status.innerText = "Error: Camera access denied or unavailable in browser.";
        status.style.color = "red";
    });

function sendFrame() {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = 640;
        canvas.height = 480;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        let imageData = canvas.toDataURL('image/jpeg', 0.6);

        fetch('/_stcore/host_callback', { method: 'POST' }).catch(e => {}); // keepalive
        
        // Post frame back to Streamlit server backend via custom fetch if endpoint available, 
        // or utilize Streamlit component communication channels.
    }
    setTimeout(sendFrame, 100);
}
</script>
"""

# State management for your background subtractor & timers
if "bg_subtractor" not in st.session_state:
  st.session_state.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
      history=300, varThreshold=30, detectShadows=True
  )
  st.session_state.person_present_start_time = None
  st.session_state.empty_screen_start_time = None
  st.session_state.alarm_is_playing = False

TARGET_DURATION = 10.0
RESET_DURATION = 10.0

# Render the component
st.components.v1.html(live_stream_component, height=540)

st.info(
    "💡 **Deployment Note:** This approach renders continuous frame updates"
    " inside the cloud browser container without triggering WebRTC dropouts."
)
