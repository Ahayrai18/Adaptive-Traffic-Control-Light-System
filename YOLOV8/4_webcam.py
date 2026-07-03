from ultralytics import YOLO
import cv2

def find_cameras(max_cam=10):

    indices = []

    for i in range(max_cam):

        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

        if cap.isOpened():

            ret, frame = cap.read()

            if ret:
                indices.append(i)

        cap.release()

    return indices

# Load trained model
model = YOLO(
    r"C:\Users\Kiki Salikil\Downloads\capstone-cuda\runs\detect\runs\car_color_detector-3\weights\best.pt"
)

# Open 4 cameras
camera_indices = find_cameras()

# buang kamera pertama
camera_indices = [idx for idx in camera_indices if idx != 0]

cams = [
    cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    for idx in camera_indices[:4]
]

# Set resolution to reduce GPU load
for cam in cams:
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    processed_frames = []

    for i, cam in enumerate(cams):
        ret, frame = cam.read()

        if not ret:
            # Blank image if camera unavailable
            frame = 255 * cv2.UMat(480, 640, cv2.CV_8UC3).get()
            cv2.putText(
                frame,
                f"Camera {i} Offline",
                (50, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
        else:
            # YOLO Detection
            results = model(frame, conf=0.5, verbose=False)

            # Draw boxes
            frame = results[0].plot()

            # Camera label
            cv2.putText(
                frame,
                f"Camera {i}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        processed_frames.append(frame)

    # Resize all frames to same size
    resized = [
        cv2.resize(frame, (640, 480))
        for frame in processed_frames
    ]

    # 2x2 Grid
    top = cv2.hconcat([resized[0], resized[1]])
    bottom = cv2.hconcat([resized[2], resized[3]])
    grid = cv2.vconcat([top, bottom])

    cv2.imshow("4 Camera Car Detection", grid)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
for cam in cams:
    cam.release()

cv2.destroyAllWindows()