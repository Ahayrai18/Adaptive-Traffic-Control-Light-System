import cv2

for i in range(10):

    print(f"\nTesting Camera {i}")

    cap = cv2.VideoCapture(i)

    if cap.isOpened():

        ret, frame = cap.read()

        if ret:
            print("SUCCESS")
            print(frame.shape)

        else:
            print("OPENED BUT NO FRAME")

    else:
        print("FAILED")

    cap.release()