from ultralytics import YOLO
import cv2

# Load trained model
model = YOLO("C:/Users/Kiki Salikil/Downloads/capstone-cuda/runs/detect/runs/car_color_detector-3/weights/best.pt")

# Open webcam (0 = default webcam)
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Cannot open webcam")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Run inference
    results = model(frame, conf=0.5)

    # Draw bounding boxes
    annotated_frame = results[0].plot()

    cv2.imshow("Car Color Detection", annotated_frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()