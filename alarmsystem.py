import time
import cv2
import numpy as np
import streamlit as st

st.set_page_config(
    page_title="Threat & Pacing Alarm System", page_icon="🚨", layout="centered"
)

st.title("🚨 Smart Computer Vision Threat & Pacing Alarm System")
st.markdown(
    "**Academic Project Demo:** Real-time background subtraction and lingering"
    " threat detection."
)

# Use Streamlit's built-in native camera input (bypasses WebRTC server blocks completely!)
camera_image = st.camera_input("Capture or Stream Live Camera Frame")

# Initialize background subtractor in session state so it remembers history across frames
if "bg_subtractor" not in st.session_state:
  st.session_state.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
      history=300, varThreshold=30, detectShadows=True
  )
  st.session_state.person_start_time = None

if camera_image is not None:
  # Convert uploaded camera image buffer to OpenCV array
  bytes_data = camera_image.getvalue()
  np_arr = np.frombuffer(bytes_data, np.unint8 if hasattr(np, "unint8") else np.uint8)
  frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

  if frame is not None:
    # Process frame
    fg_mask = st.session_state.bg_subtractor.apply(frame)
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
    target_duration = 30.0

    if motion_detected:
      if st.session_state.person_start_time is None:
        st.session_state.person_start_time = current_time

      elapsed = current_time - st.session_state.person_start_time
      time_left = max(0, int(target_duration - elapsed))

      if best_box is not None:
        x, y, w, h = best_box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

      if elapsed >= target_duration:
        cv2.putText(
            frame,
            "🚨 ALARM: LINGERING THREAT (>30s)! 🚨",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            3,
        )
        st.error("🚨 CRITICAL ALARM: 30-Second Lingering Threat Detected!")
      else:
        st.warning(
            f"⚠️ Monitoring Target... Time left until alarm: {time_left}s"
        )
        cv2.putText(
            frame,
            f"Monitoring... Time left: {time_left}s",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
        )
    else:
      st.session_state.person_start_time = None
      st.info("Status: Waiting for target movement...")
      cv2.putText(
          frame,
          "Status: Waiting for target...",
          (20, 50),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.6,
          (0, 255, 0),
          2,
      )

    # Convert BGR back to RGB for clean Streamlit display
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    st.image(
        frame_rgb,
        channels="RGB",
        caption="Live Processed Frame (Threat Analysis Active)",
    )
