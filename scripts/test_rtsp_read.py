import cv2
import time

cap = cv2.VideoCapture('rtsp://localhost:8554/test')
if not cap.isOpened():
    print("НЕ ОТКРЫЛОСЬ")
else:
    for i in range(50):
        ret, frame = cap.read()
        if not ret:
            print(f"кадр {i}: не получен")
        else:
            print(f"кадр {i}: получен, shape={frame.shape}")
        time.sleep(0.2)
cap.release()