import time
import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import WebRtcMode, VideoProcessorBase, webrtc_streamer
import requests

st.set_page_config(
    page_title="Threat & Pacing Alarm System (PCA)",
    page_icon="🚨",
    layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown("**Academic Project Demo:** Real-time pose anomaly detection using **PCA and MediaPipe**.")
st.markdown("👉 **Instructions:** Click **START** below and allow camera permissions.")

# Helper function for TURN credentials (to fix the Streamlit Cloud connection error)
@st.cache_data(ttl=3600)
def get_ice_servers():
    fallback = [{"urls": ["stun:stun.l.google.com:19302"]}]
    try:
        app = st.secrets["METERED_APP"]
        key = st.secrets["METERED_API_KEY"]
        r = requests.get(
            f"https://{app}.metered.live/api/v1/turn/credentials",
            params={"apiKey": key},
            timeout=10,
        )
        r.raise_for_status()
        return fallback + r.json()
    except Exception:
        return fallback

# Feature extraction functions matching your training pipeline
def normalize_frame(frame_kp):
    # frame_kp: (33, 2)
    hip = (frame_kp[23] + frame_kp[24]) / 2
    sho = (frame_kp[11] + frame_kp[12]) / 2
    torso = np.linalg.norm(sho - hip) + 1e-6
    return (frame_kp - hip) / torso

def window_features(window):
    # window: (T, 33, 2)
    w = np.array([normalize_frame(f) for f in window])
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


class PCAThreatProcessor(VideoProcessorBase):
    def __init__(self):
        import mediapipe as mp
        self.pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.buf = []
        self.strikes = 0
        
        # Note: In a full deployment, you'd train your model, save it via joblib as 'model.pkl', 
        # and upload it to your GitHub repo so it loads here:
        # self.scaler, self.pca, self.thresh = joblib.load("model.pkl")
        
        # Fallback dummy threshold values if model.pkl isn't uploaded yet so the app doesn't crash:
        self.has_model = False 

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        res = self.pose.process(rgb_img)
        
        status_text = "Status: Waiting for target..."
        color = (0, 255, 0)
        
        if res.pose_landmarks:
            # Draw skeletal connections manually or just track coordinates
            kp = np.array([[l.x, l.y] for l in res.pose_landmarks.landmark])
            self.buf.append(kp)
            
            status_text = f"Tracking Pose... Buffer: {len(self.buf)}/30"
            color = (0, 255, 255)
            
            if len(self.buf) == 30:
                # Once we have a 30-frame window, we evaluate features
                feat = window_features(self.buf)
                rep = repetition_score(self.buf)
                
                # If you have your trained model loaded:
                if self.has_model:
                    # f_scaled = self.scaler.transform([feat])
                    # recon = self.pca.inverse_transform(self.pca.transform(f_scaled))
                    # err = ((f_scaled - recon) ** 2).mean()
                    # anomalous = err > self.thresh or (err > 0.7 * self.thresh and rep > 0.8)
                    pass
                else:
                    # Simulated logic placeholder until model.pkl is added
                    anomalous = rep > 0.85  
                
                if anomalous:
                    self.strikes += 1
                else:
                    self.strikes = max(0, self.strikes - 1)
                
                if self.strikes >= 3:
                    status_text = "🚨 ALARM: SUSPICIOUS MOVEMENT DETECTED! 🚨"
                    color = (0, 0, 255)
                
                # Slide buffer window (50% overlap)
                self.buf = self.buf[15:]

        cv2.putText(
            img, status_text, (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
        )
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# Streamlit WebRTC configuration
webrtc_streamer(
    key="pca-threat-alarm",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=PCAThreatProcessor,
    media_stream_constraints={"video": True, "audio": False},
    rtc_configuration={"iceServers": get_ice_servers()},
    async_processing=True,
)
