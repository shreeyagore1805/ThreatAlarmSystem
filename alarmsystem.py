import os
import time
import cv2
import numpy as np

try:
  import winsound

  has_winsound = True
except ImportError:
  has_winsound = False


def play_alarm():
  """Starts playing the custom alarm loop asynchronously."""
  audio_path = "alarm.wav"
  if os.path.exists(audio_path):
    winsound.PlaySound(
        audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
    )
  else:
    # Fallback if wav is missing
    winsound.Beep(2500, 1000)


def stop_alarm():
  """Stops the alarm sound."""
  if has_winsound:
    winsound.PlaySound(None, winsound.SND_ASYNC)


def main():
  cap = cv2.VideoCapture(0)
  if not cap.isOpened():
    print("Error: Could not open webcam.")
    return

  bg_subtractor = cv2.createBackgroundSubtractorMOG2(
      history=300, varThreshold=30, detectShadows=True
  )

  print("--- SMART AUTO-RESET THREAT ALARM (V7) ---")
  print("System active. Monitoring for 30s linger, auto-stops 10s after clear.")

  person_present_start_time = None
  empty_screen_start_time = None

  alarm_is_playing = False
  TARGET_DURATION = 10.0  # 30 seconds lingering threshold
  RESET_DURATION = 10.0  # 10 seconds empty screen cutoff

  while True:
    ret, frame = cap.read()
    if not ret:
      break

    fg_mask = bg_subtractor.apply(frame)
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
      # Reset the empty screen timer since someone is still there
      empty_screen_start_time = None

      if person_present_start_time is None:
        person_present_start_time = current_time

      elapsed = current_time - person_present_start_time
      time_left = max(0, int(TARGET_DURATION - elapsed))

      if best_box is not None:
        x, y, w, h = best_box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

      # Check if 30 seconds of lingering reached
      if elapsed >= TARGET_DURATION:
        cv2.putText(
            frame,
            "🚨 ALARM: LINGERING THREAT (>30s)! 🚨",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            3,
        )
        if not alarm_is_playing:
          play_alarm()
          alarm_is_playing = True
      else:
        cv2.putText(
            frame,
            f"Monitoring Target... Time left: {time_left}s",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )
    else:
      # --- SCREEN IS EMPTY (NO MOTION) ---
      person_present_start_time = None  # Reset timer for current person

      if alarm_is_playing:
        # If alarm is currently going off, track how long the screen has been empty
        if empty_screen_start_time is None:
          empty_screen_start_time = current_time

        empty_elapsed = current_time - empty_screen_start_time
        empty_time_left = max(0, int(RESET_DURATION - empty_elapsed))

        cv2.putText(
            frame,
            f"🚨 THREAT FLED! Stopping alarm in: {empty_time_left}s",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

        # If empty for 10 full seconds, shut off alarm and fully reset system
        if empty_elapsed >= RESET_DURATION:
          stop_alarm()
          alarm_is_playing = False
          empty_screen_start_time = None
          print(
              "\n[INFO] Area clear for 10s. Alarm stopped, system re-armed."
          )
      else:
        cv2.putText(
            frame,
            "Status: Waiting for target...",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    cv2.imshow("Pacing & Lingering Threat Alarm", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
      stop_alarm()
      break

  cap.release()
  cv2.destroyAllWindows()


if __name__ == "__main__":
  main()