import time
import cv2
import numpy as np
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Threat & Pacing Alarm System",
    page_icon="🚨",
    layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown("**Academic Project Demo:** Live camera capture & threat analysis.")

# Initialize Background Subtractor
@st.cache_resource
def get_subtractor():
    return cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=30, detectShadows=True)

bg_subtractor = get_subtractor()

st.markdown("---")
st.subheader("📸 Live Camera Capture")
st.markdown("Click below to take a picture using your device's live camera. The system will analyze it instantly for movement and threats.")

# Native Streamlit live camera widget (Bypasses all WebRTC network errors)
camera_image = st.camera_input("Take a picture")

if camera_image is not None:
    # Convert uploaded image buffer to OpenCV format
    image = Image.open(camera_image)
    frame = np.array(image)
    
    # RGB to BGR for OpenCV processing
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Apply background subtraction
    fg_mask = bg_subtractor.apply(frame_bgr)
    _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    motion_detected = False
    best_box = None
    max_area = 0
    
    for c in contours:
        area = cv2.contourArea(c)
        if area > 250:
            motion_detected = True
            if area > max_area:
                max_area = area
                best_box = cv2.boundingRect(c)
                
    if motion_detected and best_box is not None:
        x, y, w, h = best_box
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.putText(frame_bgr, "ALARM: THREAT / MOTION DETECTED!", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    else:
        cv2.putText(frame_bgr, "Status: Area Clear / Monitoring", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
    # Convert back to RGB for clean display
    result_image = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    
    st.markdown("### Analysis Result:")
    st.image(result_image, use_container_width=True)
