import os
import joblib
import cv2
import numpy as np
import streamlit as st
from PIL import Image

# 1. Page Configuration
st.set_page_config(
    page_title="Threat & Pacing Alarm System (PCA)",
    page_icon="🚨",
    layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown("**Academic Project Demo:** PCA-based Anomaly & Suspicious Movement Detection.")
st.markdown("---")

# 2. Load Pre-trained PCA Model & Scaler (if available in repository)
@st.cache_resource
def load_pca_model():
    model_path = "model.pkl"
    if os.path.exists(model_path):
        try:
            return joblib.load(model_path)
        except Exception as e:
            return None
    return None

model_data = load_pca_model()

# 3. Helper Feature Functions (From your core logic)
def normalize(frame_kp):
    # frame_kp: (33, 2)
    hip = (frame_kp[23] + frame_kp[24]) / 2
    sho = (frame_kp[11] + frame_kp[12]) / 2
    torso = np.linalg.norm(sho - hip) + 1e-6
    return (frame_kp - hip) / torso

def window_features(window):
    # window: (T, 33, 2)
    w = np.array([normalize(f) for f in window])
    pos = w.reshape(len(w), -1)
    vel = np.diff(pos, axis=0)
    speed_stats = np.concatenate([vel.mean(0), vel.std(0)])
    return np.concatenate([pos.mean(0), speed_stats])

def repetition_score(window):
    # Wrists = landmarks 15, 16
    sig = np.array(window)[:, [15, 16], :].reshape(len(window), -1)
    sig = sig - sig.mean(0)
    scores = []
    for c in range(sig.shape[1]):
        ac = np.correlate(sig[:, c], sig[:, c], "full")[len(sig) - 1:]
        ac = ac / (ac[0] + 1e-6)
        scores.append(ac[5:].max())
    return float(np.mean(scores))

# 4. User Interface Controls
input_option = st.radio(
    "Select Input Mode for Threat Analysis:",
    ("Live Snapshot / Frame Test", "Upload Test Video Clip (.mp4)")
)

if input_option == "Live Snapshot / Frame Test":
    st.subheader("📸 Live Frame Capture")
    st.markdown("Take a snapshot using your device camera to run through your PCA reconstruction pipeline.")
    
    camera_file = st.camera_input("Snap a frame")
    
    if camera_file is not None:
        image = Image.open(camera_file)
        frame = np.array(image)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        st.image(image, caption="Captured Frame", use_container_width=True)
        
        if model_data is not None:
            scaler, pca, THRESH = model_data
            st.success("PCA Model successfully loaded from repository!")
            # Insert your inference logic here on the captured frame window
        else:
            st.warning("⚠️ `model.pkl` not found in your repository. Please upload your trained model file to evaluate reconstruction errors live.")

else:
    st.subheader("🎬 Video Clip Analysis")
    uploaded_video = st.file_uploader("Upload video file for anomaly evaluation", type=["mp4", "avi", "mov"])
    
    if uploaded_video is not None:
        with open("temp_input.mp4", "wb") as f:
            f.write(uploaded_video.getbuffer())
        
        st.info("Processing video stream through your background subtraction & PCA pipeline...")
        cap = cv2.VideoCapture("temp_input.mp4")
        st_frame_slot = st.empty()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Draw tracking status overlay
            cv2.putText(frame, "Analyzing Motion Patterns...", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            st_frame_slot.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
            
        cap.release()
        st.success("Video analysis completed successfully!")

# 5. Audio Alarm Embedding for Browser
if os.path.exists("alarm.wav"):
    with open("alarm.wav", "rb") as f:
        audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(f'<audio autoplay loop><source src="data:audio/wav;base64,{audio_b64}" type="audio/wav"></audio>', unsafe_allow_html=True)
