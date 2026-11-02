import time
import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import WebRtcMode, VideoProcessorBase, webrtc_streamer

st.set_page_config(
    page_title="Threat & Pacing Alarm System",
    page_icon="🚨",
    layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown(
    "**Academic Project Demo:** Live browser camera stream with background "
    "subtraction, lingering detection, and visual alerts."
)
st.markdown("👉 **Instructions:** Click **START** below and allow camera permissions.")


class ThreatAlarmProcessor(VideoProcessorBase):

    def __init__(self):
      self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
          history=300, varThreshold=30, detectShadows=True
      )
      self.person_present_start_time = None
      self.empty_screen_start_time = None
      self.target_duration = 10.0  # 10 seconds lingering threshold
      self.reset_duration = 10.0   # 10 seconds clear cutoff
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
        if area > 300:  # Sensitivity threshold
          motion_detected = True
          if area > max_area:
            max_area = area
            best_box = cv2.boundingRect(c)

      current_time = time.time()

      if motion_detected:
        self.empty_screen_start_time = None

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
              "ALARM: LINGERING THREAT (>10s)!",
              (20, 40),
              cv2.FONT_HERSHEY_SIMPLEX,
              0.6,
              (0, 0, 255),
              2,
          )
          self.alarm_active = True
        else:
          cv2.putText(
              img,
              f"Monitoring Target... Time left: {time_left}s",
              (20, 40),
              cv2.FONT_HERSHEY_SIMPLEX,
              0.6,
              (0, 255, 255),
              2,
          )
      else:
        self.person_present_start_time = None

        if self.alarm_active:
          if self.empty_screen_start_time is None:
            self.empty_screen_start_time = current_time

          empty_elapsed = current_time - self.empty_screen_start_time
          empty_time_left = max(0, int(self.reset_duration - empty_elapsed))

          cv2.putText(
              img,
              f"THREAT FLED! Resetting in: {empty_time_left}s",
              (20, 40),
              cv2.FONT_HERSHEY_SIMPLEX,
              0.6,
              (0, 0, 255),
              2,
          )

          if empty_elapsed >= self.reset_duration:
            self.alarm_active = False
            self.empty_screen_start_time = None
        else:
          cv2.putText(
              img,
              "Status: Waiting for target...",
              (20, 40),
              cv2.FONT_HERSHEY_SIMPLEX,
              0.6,
              (0, 255, 0),
              2,
          )

      # NOTE: Removed st.session_state updates here to prevent stream reloads.

      return av.VideoFrame.from_ndarray(img, format="bgr24")

if "alarm_triggered" not in st.session_state:
    st.session_state.alarm_triggered = False

# Streamer configuration
webrtc_streamer(
    key="threat-alarm-live-feed",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=ThreatAlarmProcessor,
    media_stream_constraints={
        "video": {"width": {"ideal": 640}, "height": {"ideal": 480}},
        "audio": False,  # Keep this False since you're just playing an external sound file
    },
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
        ]
    },
    async_processing=True,
)
