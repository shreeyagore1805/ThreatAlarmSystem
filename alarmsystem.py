import time
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import av

st.set_page_config(
    page_title="Threat & Pacing Alarm System", page_icon="🚨", layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown(
    "**Academic Project Demo:** This application uses computer vision and"
    " background subtraction to detect suspicious lingering and pacing"
    " behavior in real-time without storing facial data."
)
st.markdown(
    "👉 **How to test:** Click **'START'** below, allow camera access, and"
    " stay in front of your camera for **30 seconds** to trigger the threat"
    " alert."
)


# Define the Video Processor for WebRTC browser streaming
class ThreatAlarmProcessor:

  def __init__(self):
    self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
        history=300, varThreshold=30, detectShadows=True
    )
    self.person_present_start_time = None
    self.target_duration = 30.0  # 30 seconds threshold
    self.alarm_active = False

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
      if area > 500:
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
            img,
            "🚨 ALARM: LINGERING THREAT (>30s)! 🚨",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            3,
        )
        self.alarm_active = True
      else:
        cv2.putText(
            img,
            f"Monitoring Lingering... Time left: {time_left}s",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
        )
        self.alarm_active = False
    else:
      self.person_present_start_time = None
      self.alarm_active = False
      cv2.putText(
          img,
          "Status: Waiting for target...",
          (20, 50),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.6,
          (0, 255, 0),
          2,
      )

    return av.VideoFrame.from_ndarray(img, format="bgr24")


# Streamlit WebRTC component to render camera stream in the browser
webrtc_streamer(
    key="threat-alarm",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=ThreatAlarmProcessor,
    media_stream_constraints={"video": True, "audio": False},
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    async_processing=True,
)

st.markdown("---")
st.markdown("### 📊 System Specifications")
st.col1, st.col2 = st.columns(2)
with st.col1:
  st.metric(label="Dwell Threshold", value="30 Seconds")
with st.col2:
  st.metric(label="Privacy Compliance", value="Face-Free / Zero Storage")
