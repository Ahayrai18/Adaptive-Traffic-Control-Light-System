import cv2

available_cams = []

for i in range(10):  # scan kamera 0-9

    cap = cv2.VideoCapture(i)

    if cap.isOpened():

        ret, frame = cap.read()

        if ret:
            available_cams.append(i)
            print(f"Camera {i} ditemukan")

    cap.release()

print("Daftar kamera:", available_cams)