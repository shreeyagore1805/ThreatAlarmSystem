import time
import cv2
import numpy as np
from flask import Flask, Response, render_template_string

app = Flask(__name__)

INDEX_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Threat & Pacing Alarm System</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #111; color: #eee; margin-top: 20px; }
        .video-container { display: inline-block; border: 4px solid #444; border-radius: 8px; overflow: hidden; background: #000; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        video, canvas { display: none; }
        #output { display: block; max-width: 100%; height: auto; }
        h1 { color: #ff4d4d; font-size: 24px; }
        #status { font-weight: bold; color: #00ffcc; margin: 10px; }
    </style>
</head>
<body>
    <h1>🚨 Smart Computer Vision Threat & Pacing Alarm System</h1>
    <p id="status">Status: Requesting camera permissions...</p>
    
    <div class="video-container">
        <video id="webcam" autoplay playsinline></video>
        <canvas id="canvas"></canvas>
        <img id="output" />
    </div>

    <script>
        const video = document.getElementById('webcam');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const output = document.getElementById('output');
        const status = document.getElementById('status');

        // Access laptop webcam directly via browser
        navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
            .then(stream => {
                video.srcObject = stream;
                status.innerText = "Status: Camera Active & Monitoring...";
                requestAnimationFrame(sendFrame);
            })
            .catch(err => {
                status.innerText = "Error: Camera access denied or not available.";
                status.style.color = "red";
            });

        function sendFrame() {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth || 640;
                canvas.height = video.videoHeight || 480;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                let imageData = canvas.toDataURL('image/jpeg', 0.6);

                fetch('/process_frame', {
                    method: 'POST',
                    body: JSON.stringify({ image: imageData }),
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(response => response.json())
                .then(data => {
                    output.src = data.image;
                    setTimeout(sendFrame, 50); // ~20 FPS loop
                })
                .catch(err => {
                    setTimeout(sendFrame, 200);
                });
            } else {
                setTimeout(sendFrame, 100);
            }
        }
    </script>
</body>
</html>
"""

# OpenCV Background Subtractor state (per session/server worker)
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=30, detectShadows=True)
person_present_start_time = None
empty_screen_start_time = None
alarm_triggered = False

TARGET_DURATION = 10.0
RESET_DURATION = 10.0

@app.route('/')
def index():
    return render_template_string(INDEX_PAGE)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    global person_present_start_time, empty_screen_start_time, alarm_triggered
    import base64

    data = request.json if hasattr(request, 'json') else None
    # Fallback for flask request parsing if needed
    from flask import request
    req_data = request.get_json()
    
    if not req_data or 'image' not in req_data:
        return {"image": ""}

    # Decode base64 image coming from browser webcam
    img_data = req_data['image'].split(',')[1]
    np_arr = np.frombuffer(base64.b64decode(img_data), np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return {"image": ""}

    # Apply your exact background subtraction logic
    fg_mask = bg_subtractor.apply(frame)
    _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    best_box = None
    max_area = 0

    for c in contours:
        area = cv2.contourArea(c)
        if area > 500:
            motion_detected = True
            if area > max_area:
                max_area = area
                best_box = cv2.boundingRect(c)

    current_time = time.time()

    if motion_detected:
        empty_screen_start_time = None
        if person_present_start_time is None:
            person_present_start_time = current_time

        elapsed = current_time - person_present_start_time
        time_left = max(0, int(TARGET_DURATION - elapsed))

        if best_box is not None:
            x, y, w, h = best_box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

        if elapsed >= TARGET_DURATION:
            cv2.putText(frame, "ALARM: LINGERING THREAT (>10s)!", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            alarm_triggered = True
        else:
            cv2.putText(frame, f"Monitoring Target... Time left: {time_left}s", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    else:
        person_present_start_time = None
        if alarm_triggered:
            if empty_screen_start_time is None:
                empty_screen_start_time = current_time

            empty_elapsed = current_time - empty_screen_start_time
            empty_time_left = max(0, int(RESET_DURATION - empty_elapsed))

            cv2.putText(frame, f"THREAT FLED! Resetting in: {empty_time_left}s", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            if empty_elapsed >= RESET_DURATION:
                alarm_triggered = False
                empty_screen_start_time = None
        else:
            cv2.putText(frame, "Status: Waiting for target...", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Encode processed frame back to send to browser
    _, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    encoded_image = base64.b64encode(buffer).decode('utf-8')

    return {"image": f"data:image/jpeg;base64,{encoded_image}"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
