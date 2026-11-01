import time
import av
import cv2
import requests
import streamlit as st
from streamlit_webrtc import WebRtcMode, VideoProcessorBase, webrtc_streamer

st.set_page_config(
    page_title="Threat & Pacing Alarm System",
    page_icon="🚨",
    layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown("**Academic Project Demo:** Live browser camera stream with background subtraction and lingering threat tracking.")
st.markdown("👉 **Instructions:** Click **START** below and allow camera permissions.")

# Helper function to fetch TURN credentials securely from Streamlit Secrets
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
    except Exception as e:
        st.warning(f"TURN not configured properly, using STUN only ({e})")
        return fallback

class ThreatAlarmProcessor(VideoProcessorBase):
    def __init__(self):
        # Initialize OpenCV Background Subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=30, detectShadows=True
        )
        self.person_present_start_time = None
        self.target_duration = 30.0  # 30 seconds threshold for lingering threat

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(img)
        _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        motion_detected = False
        best_box = None
        max_area = 0

        for c in contours:
            area = cv2.contourArea(c)
            if area > 250:  # Sensitive contour threshold for motion tracking
                motion_detected = True
                if area > max_area:
                    max_area = area
                    best_box = cv2.boundingRect(c)

        current_time = time.time()

        if motion_detected:
            if self.person_present_start_time is None:
                self.person_present_start_time = current_time

            elapsed = current_time - self.person_present_start_time
            time_left = max(0, int(self.target_duration - elapsed))

            if best_box is not None:
                x, y, w, h = best_box
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)

            if elapsed >= self.target_duration:
                cv2.putText(
                    img, "ALARM: LINGERING THREAT (>30s)!", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 3
                )
            else:
                cv2.putText(
                    img, f"Monitoring Lingering... Time left: {time_left}s", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
                )
        else:
            self.person_present_start_time = None
            cv2.putText(
                img, "Status: Waiting for target...", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# Streamlit WebRTC configuration with STUN + TURN credentials
webrtc_streamer(
    key="threat-alarm-live-feed",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=ThreatAlarmProcessor,
    media_stream_constraints={"video": True, "audio": False},
    rtc_configuration={"iceServers": get_ice_servers()},
    async_processing=True,
)
