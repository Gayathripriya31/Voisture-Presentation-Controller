import cv2
import mediapipe as mp
import pyautogui
import speech_recognition as sr
import threading
import time
import os
from datetime import datetime

# Create screenshots folder if not exists
if not os.path.exists("screenshots"):
    os.makedirs("screenshots")

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Flags and state variables
highlight_mode = False
draw_points = []

# Function to capture screenshot
def take_screenshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots/screenshot_{timestamp}.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    print(f"📸 Screenshot saved: {filename}")

# Voice Command Handler
def recognize_voice_command():
    global highlight_mode, draw_points
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    while True:
        with mic as source:
            print("🎤 Listening for voice command...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            print("Voice Command:", command)

            if "next" in command:
                pyautogui.press("right")
            elif "previous" in command or "back" in command:
                pyautogui.press("left")
            elif "start presentation" in command:
                pyautogui.press("f5")
            elif "end presentation" in command or "stop" in command:
                pyautogui.press("esc")
            elif "screenshot" in command or "take screenshot" in command:
                take_screenshot()
            elif "start highlighting" in command:
                highlight_mode = True
                print("🖍️ Highlight mode ON (Voice)")
            elif "stop highlighting" in command:
                highlight_mode = False
                print("🛑 Highlight mode OFF (Voice)")
            elif "clear highlight" in command:
                draw_points.clear()
                print("🧹 Cleared highlights (Voice)")
        except Exception as e:
            print("Voice error:", e)

# Start voice command in a separate thread
voice_thread = threading.Thread(target=recognize_voice_command)
voice_thread.daemon = True
voice_thread.start()

# Gesture recognition function
def get_finger_status(hand_landmarks):
    tip_ids = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Other fingers
    for id in range(1, 5):
        if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[tip_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

# OpenCV camera input
cap = cv2.VideoCapture(0)
print("🖐️ Smart Controller started... Show gestures or speak commands!")

last_gesture_time = time.time()

while cap.isOpened():
    success, img = cap.read()
    if not success:
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
            fingers = get_finger_status(handLms)

            current_time = time.time()

            # Toggle highlight mode with Thumb + Index
            if current_time - last_gesture_time > 1.5:
                if fingers == [1, 1, 0, 0, 0]:
                    highlight_mode = not highlight_mode
                    print(f"🖍️ Highlight mode {'ON' if highlight_mode else 'OFF'} (Gesture)")
                    last_gesture_time = current_time

                elif fingers == [0, 1, 0, 0, 0]:
                    pyautogui.press("right")
                    print("➡️ Next Slide (Gesture)")
                    last_gesture_time = current_time
                elif fingers == [0, 1, 1, 0, 0]:
                    pyautogui.press("left")
                    print("⬅️ Previous Slide (Gesture)")
                    last_gesture_time = current_time
                elif fingers == [1, 1, 1, 1, 1]:
                    pyautogui.press("f5")
                    print("▶️ Start Presentation (Gesture)")
                    last_gesture_time = current_time
                elif fingers == [0, 0, 0, 0, 0]:
                    pyautogui.press("esc")
                    print("⏹️ End Presentation (Gesture)")
                    last_gesture_time = current_time
                elif fingers == [1, 0, 0, 0, 0]:
                    take_screenshot()
                    print("📸 Screenshot (Gesture)")
                    last_gesture_time = current_time

            # Highlighting when index finger is up
            if highlight_mode and fingers[1] == 1:
                h, w, _ = img.shape
                x = int(handLms.landmark[8].x * w)
                y = int(handLms.landmark[8].y * h)
                draw_points.append((x, y))

    # Draw highlight trail
    for point in draw_points:
        cv2.circle(img, point, 10, (0, 255, 255), cv2.FILLED)

    # Press 'c' to clear highlights
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC to exit
        break
    elif key == ord('c'):
        draw_points.clear()
        print("🧹 Cleared highlights (Key)")

    cv2.imshow("Smart Presentation Controller", img)

cap.release()
cv2.destroyAllWindows()
