import base64
import os
import streamlit as st

st.set_page_config(
    page_title="Threat & Pacing Alarm System", page_icon="🚨", layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown(
    "**Academic Project Demo:** Live browser stream with motion detection,"
    " warning timers, and audio alarm."
)
st.markdown("---")

# Load alarm.wav file as Base64 so the browser can play it locally when triggered
alarm_audio_html = ""
if os.path.exists("alarm.wav"):
  with open("alarm.wav", "rb") as f:
    audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode()
    alarm_audio_html = f"""
    <audio id="alarmSound" loop>
        <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">
    </audio>
    """
else:
  # Fallback synth beep if alarm.wav isn't found
  alarm_audio_html = """
    <audio id="alarmSound" loop>
        <source src="https://www.soundjay.com/buttons/sounds/beep-01a.mp3" type="audio/mp3">
    </audio>
    """

# Complete Client-Side Live Tracker + Motion Detection + Alarm System
live_system_html = (
    """
<div style="text-align: center;">
    <video id="webcam" autoplay playsinline style="display:none;"></video>
    <canvas id="canvas" style="display:none;"></canvas>
    
    <div style="margin-top: 10px; position: relative; display: inline-block;">
        <canvas id="outputCanvas" width="640" height="480" style="width: 100%; max-width: 640px; border-radius: 8px; border: 3px solid #333; background: #000;"></canvas>
    </div>
    
    <p id="status" style="font-weight: bold; color: orange; margin-top: 10px;">Requesting camera permissions...</p>
    
    """
    + alarm_audio_html
    + """
</div>

<script>
const video = document.getElementById('webcam');
const srcCanvas = document.getElementById('canvas');
const srcCtx = srcCanvas.getContext('2d');
const outCanvas = document.getElementById('outputCanvas');
const outCtx = outCanvas.getContext('2d');
const statusText = document.getElementById('status');
const alarmSound = document.getElementById('alarmSound');

let personPresentStartTime = null;
let emptyScreenStartTime = null;
let alarmIsPlaying = false;
const TARGET_DURATION = 10.0; // 10 seconds lingering threshold
const RESET_DURATION = 10.0;  // 10 seconds clear cutoff

// Simple background frame reference for browser-side motion detection
let bgData = null;

navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
    .then(stream => {
        video.srcObject = stream;
        statusText.innerText = "Status: Live Tracking & Threat Analysis Active 🟢";
        statusText.style.color = "#00ffcc";
        requestAnimationFrame(processLoop);
    })
    .catch(err => {
        statusText.innerText = "Error: Camera access denied or blocked by browser.";
        statusText.style.color = "red";
    });

function processLoop() {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
        srcCanvas.width = 640;
        srcCanvas.height = 480;
        srcCtx.drawImage(video, 0, 0, srcCanvas.width, srcCanvas.height);
        
        let frame = srcCtx.getImageData(0, 0, 640, 480);
        let data = frame.data;

        // Initialize background model on first frame
        if (!bgData) {
            bgData = new Uint8ClampedArray(data);
        }

        let motionPixels = 0;
        let minX = 640, minY = 480, maxX = 0, maxY = 0;

        // Simple background subtraction & bounding box calculation in browser
        for (let i = 0; i < data.length; i += 4) {
            let r = data[i], g = data[i+1], b = data[i+2];
            let br = bgData[i], bg = bgData[i+1], bb = bgData[i+2];
            
            let diff = Math.abs(r - br) + Math.abs(g - bg) + Math.abs(b - bb);
            if (diff > 70) { // Motion threshold
                motionPixels++;
                let pixelIndex = i / 4;
                let x = pixelIndex % 640;
                let y = Math.floor(pixelIndex / 640);
                
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
            }
        }

        // Draw camera frame to output display
        outCtx.putImageData(frame, 0, 0);

        let currentTime = Date.now() / 1000;
        let motionDetected = motionPixels > 1500; // Sensitivity area filter

        if (motionDetected) {
            emptyScreenStartTime = null;
            if (personPresentStartTime === null) {
                personPresentStartTime = currentTime;
            }

            let elapsed = currentTime - personPresentStartTime;
            let timeLeft = Math.max(0, Math.ceil(TARGET_DURATION - elapsed));

            // Draw Yellow Bounding Box around movement
            outCtx.strokeStyle = "#00ffff";
            outCtx.lineWidth = 3;
            outCtx.strokeRect(minX, minY, maxX - minX, maxY - minY);

            if (elapsed >= TARGET_DURATION) {
                // Trigger Warning & Alarm Sound
                outCtx.fillStyle = "red";
                outCtx.font = "bold 22px Arial";
                outCtx.fillText("🚨 ALARM: LINGERING THREAT (>10s)! 🚨", 20, 40);

                if (!alarmIsPlaying) {
                    alarmSound.play().catch(e => console.log("Audio play blocked by browser policy"));
                    alarmIsPlaying = true;
                }
            } else {
                outCtx.fillStyle = "#00ffff";
                outCtx.font = "bold 20px Arial";
                outCtx.fillText("Monitoring Target... Time left: " + timeLeft + "s", 20, 40);
            }
        } else {
            personPresentStartTime = null;

            if (alarmIsPlaying) {
                if (emptyScreenStartTime === null) {
                    emptyScreenStartTime = currentTime;
                }
                let emptyElapsed = currentTime - emptyScreenStartTime;
                let emptyTimeLeft = Math.max(0, Math.ceil(RESET_DURATION - emptyElapsed));

                outCtx.fillStyle = "red";
                outCtx.font = "bold 20px Arial";
                outCtx.fillText("🚨 THREAT FLED! Resetting in: " + emptyTimeLeft + "s", 20, 40);

                if (emptyElapsed >= RESET_DURATION) {
                    alarmSound.pause();
                    alarmSound.currentTime = 0;
                    alarmIsPlaying = false;
                    emptyScreenStartTime = null;
                }
            } else {
                outCtx.fillStyle = "#00ff00";
                outCtx.font = "bold 20px Arial";
                outCtx.fillText("Status: Waiting for target...", 20, 40);
            }
        }
    }
    setTimeout(processLoop, 80); // ~12 FPS real-time processing loop
}
</script>
"""
)

# Render component
st.components.v1.html(live_system_html, height=580)
