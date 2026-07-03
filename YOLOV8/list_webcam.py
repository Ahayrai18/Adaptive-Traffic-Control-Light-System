import cv2

for i in range(10):
    cap = cv2.VideoCapture(i)

    if cap.isOpened():
        print(f"Camera {i} detected")
        cap.release()