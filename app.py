import os
import logging
import absl.logging
import cv2
import mediapipe as mp
import time
import firebase_admin
from firebase_admin import credentials, db

# Suppress TensorFlow and MediaPipe warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger("mediapipe").setLevel(logging.ERROR)
absl.logging.set_verbosity(absl.logging.ERROR)

# Initialize Firebase with error handling
try:
    cred = credentials.Certificate("gesture.json")  # Replace with your Firebase key path
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://hmi1-99e38-default-rtdb.asia-southeast1.firebasedatabase.app/'  # Replace with your Firebase database URL
    })
    firebase_ready = True
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    firebase_ready = False

# Initialize MediaPipe Hand Detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

ESP32_CAM_URL = "http://192.168.97.151/stream"

# Attempt to open the ESP32 Camera Stream
cap = cv2.VideoCapture(ESP32_CAM_URL)
if not cap.isOpened():
    print("Error: Could not open ESP32 Camera Stream.")
    exit()

# Variables for Gesture Recognition
previous_finger_count = -1
stable_frame_count = 0  # Counter to filter rapid changes
stable_threshold = 5  # Number of frames required for stable detection
previous_gesture = None  # Track last detected gesture

# Gesture Mapping
gestures = {
    1: "Water",
    2: "Food",
    3: "Medicine",
    4: "Sanitation",
    5: "Emergency"
}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame. Retrying...")
        time.sleep(0.1)  # Prevent CPU overuse
        continue

    # Convert to RGB for MediaPipe Processing
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    finger_count = 0  # Default finger count
    detected_gesture = "No gesture"  # Default gesture

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get Hand Landmark Positions
            fingers = []
            h, w, _ = frame.shape
            for lm in hand_landmarks.landmark:
                cx, cy = int(lm.x * w), int(lm.y * h)
                fingers.append((cx, cy))

            # Ensure there are enough landmarks
            if len(fingers) < 21:
                continue

            # Thumb Detection (Check x-coordinates)
            if fingers[4][0] > fingers[3][0]:  # Thumb extended
                finger_count += 1

            # Other Fingers (Check y-coordinates)
            if fingers[8][1] < fingers[6][1]:  # Index Finger
                finger_count += 1
            if fingers[12][1] < fingers[10][1]:  # Middle Finger
                finger_count += 1
            if fingers[16][1] < fingers[14][1]:  # Ring Finger
                finger_count += 1
            if fingers[20][1] < fingers[18][1]:  # Pinky Finger
                finger_count += 1

        detected_gesture = gestures.get(finger_count, "NO gesture")  # Map gesture

    # Gesture Stability Check
    if finger_count == previous_finger_count:
        stable_frame_count += 1
    else:
        stable_frame_count = 0

    if stable_frame_count >= stable_threshold:
        # Only update Firebase when gesture changes
        if firebase_ready and detected_gesture != previous_gesture:
            db.reference("detected_gesture").set(detected_gesture)
            print(f"Updated Firebase: {detected_gesture}")

        stable_frame_count = 0  # Reset after sending data
        previous_gesture = detected_gesture  # Track last gesture

    # Update Previous Finger Count
    previous_finger_count = finger_count

    # Display Finger Count & Gesture
    cv2.putText(frame, detected_gesture, (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
    cv2.putText(frame, str(finger_count), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

    # Show Output
    cv2.imshow('Hand Gesture Recognition', frame)

    # Quit on 'q' Key Press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
