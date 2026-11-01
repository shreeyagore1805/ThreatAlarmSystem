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
    "**Academic Project Demo:** Detects suspicious lingering and pacing"
    " behavior in real-time using computer vision and background"
    " subtraction."
)

# Sidebar option to choose input mode (fixes cloud network constraints)
app_mode = st.sidebar.selectbox(
    "Choose Input Mode", ["Live Webcam (Browser)", "Upload Test Video File"]
)


# Shared processing logic for both live stream and video files
def process_frame(img, processor_state):
  # Unpack state variables
  bg_subtractor = processor_state["bg_subtractor"]
  start_time = processor_state["start_time"]
  target_duration = 30.0

  fg_mask = bg_subtractor.apply(img)
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
    if processor_state["person_start"] is None:
      processor_state["person_start"] = current_time

    elapsed = current_time - processor_state["person_start"]
    time_left = max(0, int(target_duration - elapsed))

    if best_box is not None:
      x, y, w, h = best_box
      cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)

    if elapsed >= target_duration:
      cv2.putText(
          img,
          "🚨 ALARM: LINGERING THREAT (>30s)! 🚨",
          (20, 50),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.7,
          (0, 0, 255),
          3,
      )
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
  else:
    processor_state["person_start"] = None
    cv2.putText(
        img,
        "Status: Waiting for target...",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )

  return img


if app_mode == "Live Webcam (Browser)":
  st.subheader("🔴 Live Browser Webcam Feed")
  st.markdown(
      "*Note: If network restrictions block the webcam feed, switch to 'Upload"
      " Test Video File' in the sidebar.*"
  )


  class ThreatAlarmProcessor:

    def __init__(self):
      self.state = {
          "bg_subtractor": cv2.createBackgroundSubtractorMOG2(
              history=300, varThreshold=30, detectShadows=True
          ),
          "person_start": None,
      }

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
      img = frame.to_ndarray(format="bgr24")
      processed_img = process_frame(img, self.state)
      return av.VideoFrame.from_ndarray(processed_img, format="bgr24")


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

else:
  st.subheader("📁 Test via Video File Upload")
  st.markdown(
      "Upload a short MP4 video clip to test the threat detection and alarm"
      " trigger instantly!"
  )

  uploaded_file = st.file_uploader(
      "Choose a video file...", type=["mp4", "mov", "avi"]
  )

  if uploaded_file is not None:
    # Save uploaded file temporarily to process with OpenCV
    with open("temp_video.mp4", "wb") as f:
      f.write(uploaded_file.read())

    st.success("Video uploaded successfully! Processing below...")
    st.video("temp_video.mp4")
