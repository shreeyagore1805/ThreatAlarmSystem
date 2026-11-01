import time
import cv2
import numpy as np
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# Initialize OpenCV Background Subtractor
bg_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=300, varThreshold=30, detectShadows=True
)

TARGET_DURATION = 10.0  # Lingering threshold (seconds)
RESET_DURATION = 10.0   # Clear cutoff

# Global state variables
person_present_start_time = None
empty_screen_start_time = None
alarm_triggered = False

INDEX_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Threat & Pacing Alarm System</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #111; color: #eee; margin-top: 30px; }
        .video-container { display: inline-block; border: 4px solid #444; border-radius: 8px; overflow: hidden; background: #000; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        img { display: block; max-width: 100%; height: auto; }
        h1 { color: #ff4d4d; }
        p { color: #aaa; }
    </style>
</head>
<body>
    <h1>🚨 Smart Computer Vision Threat & Pacing Alarm System</h1>
    <p><b>Cloud Deployment Simulation (No Webcam Required):</b> Running live background subtraction & threat tracking.</p>
    <div class="video-container">
        <img src="/video_feed" width="640" height="480">
    </div>
</body>
</html>
"""

def generate_simulated_frames():
    global person_present_start_time, empty_screen_start_time, alarm_triggered
    
    # Create a blank canvas to simulate a surveillance frame
    canvas_width, canvas_height = 640, 480
    
    # Simulating a moving object (acting like a person walking into frame)
    obj_x, obj_y = 100, 200
    direction = 5

    while True:
        # Create static background frame
        frame = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        cv2.putText(frame, "CLOUD SURVEILLANCE FEED", (20, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

        # Simulate movement across the screen to trigger OpenCV background subtraction
        obj_x += direction
        if obj_x > 500 or obj_x < 100:
            direction *= -1  # Reverse direction (pacing simulation)

        # Draw a moving simulated "person/threat block"
        cv2.rectangle(frame, (obj_x, obj_y), (obj_x + 60, obj_y + 160), (200, 200, 200), -1)

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
                cv2.putText(frame, "ALARM: LINGERING THREAT (>10s)!", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 3)
                alarm_triggered = True
            else:
                cv2.putText(frame, f"Monitoring Target... Time left: {time_left}s", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
            person_present_start_time = None
            if alarm_triggered:
                if empty_screen_start_time is None:
                    empty_screen_start_time = current_time

                empty_elapsed = current_time - empty_screen_start_time
                empty_time_left = max(0, int(RESET_DURATION - empty_elapsed))

                cv2.putText(frame, f"THREAT FLED! Resetting in: {empty_time_left}s", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                if empty_elapsed >= RESET_DURATION:
                    alarm_triggered = False
                    empty_screen_start_time = None
            else:
                cv2.putText(frame, "Status: Waiting for target...", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Encode frame as JPEG to stream via HTTP to the browser
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Control stream frame rate (~30 fps simulation)
        time.sleep(0.03)

@app.route('/')
def index():
    return render_template_string(INDEX_PAGE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_simulated_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
