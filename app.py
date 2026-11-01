import cv2
import numpy as np
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Threat & Pacing Alarm System", page_icon="🚨", layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown(
    "**Academic Project Demo:** Cloud-deployed threat and lingering detection system."
)
st.markdown("---")

# Initialize Background Subtractor (cached for performance)


@st.cache_resource
def get_subtractor():
  return cv2.createBackgroundSubtractorMOG2(
      history=300, varThreshold=30, detectShadows=True
  )


bg_subtractor = get_subtractor()

# Choose input mode
input_mode = st.radio(
    "Select Input Method for Detection:",
    ("Live Camera Snapshot", "Upload Video / Test Clip"),
)

if input_mode == "Live Camera Snapshot":
  st.subheader("📸 Live Camera Capture")
  st.markdown(
      "Click the button below to snap a picture using your device camera."
  )

  camera_image = st.camera_input("Take a snapshot")

  if camera_image is not None:
    # Convert image to OpenCV format
    image = Image.open(camera_image)
    frame = np.array(image)
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Apply background subtraction
    fg_mask = bg_subtractor.apply(frame_bgr)
    _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    motion_detected = False
    best_box = None
    max_area = 0

    for c in contours:
      area = cv2.contourArea(c)
      if area > 250:  # Sensitivity threshold
        motion_detected = True
        if area > max_area:
          max_area = area
          best_box = cv2.boundingRect(c)

    if motion_detected and best_box is not None:
      x, y, w, h = best_box
      cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 255), 2)
      cv2.putText(
          frame_bgr,
          "🚨 ALARM: THREAT / MOTION DETECTED!",
          (20, 40),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.6,
          (0, 0, 255),
          2,
      )
    else:
      cv2.putText(
          frame_bgr,
          "Status: Area Clear / Monitoring",
          (20, 40),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.6,
          (0, 255, 0),
          2,
      )

    # Convert back to RGB for display
    result_image = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    st.image(result_image, caption="Analyzed Output", use_container_width=True)

else:
  st.subheader("📂 Video File Analysis")
  uploaded_file = st.file_uploader(
      "Upload a test video clip (.mp4, .avi)", type=["mp4", "mov", "avi"]
  )

  if uploaded_file is not None:
    with open("temp_vid.mp4", "wb") as f:
      f.write(uploaded_file.getbuffer())

    cap = cv2.VideoCapture("temp_vid.mp4")
    st_frame = st.empty()

    st.info("Processing video frames through background subtractor...")
    while cap.isOpened():
      ret, frame = cap.read()
      if not ret:
        break

      fg_mask = bg_subtractor.apply(frame)
      _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
      contours, _ = cv2.findContours(
          thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
      )

      motion_detected = False
      for c in contours:
        if cv2.contourArea(c) > 250:
          motion_detected = True
          x, y, w, h = cv2.boundingRect(c)
          cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

      if motion_detected:
        cv2.putText(
            frame,
            "🚨 ALARM: LINGERING THREAT DETECTED!",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
      else:
        cv2.putText(
            frame,
            "Status: Monitoring...",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

      st_frame.image(
          cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
          channels="RGB",
          use_container_width=True,
      )
    cap.release()
    st.success("Video processing complete!")
