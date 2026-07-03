import cv2
import pickle
import cvzone
import numpy as np
import time

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate("")
firebase_admin.initialize_app(cred, {''})
ref = db.reference('')

cap = cv2.VideoCapture('street_video.mp4')


with open('streetPos', 'rb') as f:
    posList = pickle.load(f)

# width, height = 130, 52
#width, height = 107, 48
# width, height = 190, 110
width, height = 200,90
horisantalPos = 2
count = []

# FPS calculation variables
fps_counter = 0
fps_start_time = time.time()
fps = 0

def trafficdensity(imgPro):
    spaceCounter = 0
    i = 0
    horizantalTrafficJam = 0
    verticalTrafficJam = 0
    count.clear()
    for pos in posList:
        x, y = pos
        if i < horisantalPos:
            imgCrop = imgPro[y:y + height, x:x + width]
        else:
            imgCrop = imgPro[y:y + width, x:x + height]
        #cv2.imshow(str(x * y), imgCrop)
        #count[i] = cv2.countNonZero(imgCrop)
        count.append(cv2.countNonZero(imgCrop))
        # cv2.imshow(str(i+1), imgCrop)
        if count[i] < 600:
            color = (0, 255, 0)
            thickness = 5
            spaceCounter += 1
        else:
            color = (0, 0, 255)
            thickness = 2
        if i < horisantalPos:
            cv2.rectangle(img, pos,(pos[0] + width, pos[1] + height), color, thickness)
            cvzone.putTextRect(img, str(count[i]), (x, y + height - 3), scale=1,
                               thickness=2, offset=0, colorR=color)
            horizantalTrafficJam += count[i]
        else:
            cv2.rectangle(img, pos,  (pos[0] + height, pos[1] + width), color, thickness)
            cvzone.putTextRect(img, str(count[i]), (x, y + width - 3), scale=1,
                               thickness=2, offset=0, colorR=color)
            verticalTrafficJam += count[i]
        i += 1
    print(count)
    ref.set(count)

while True:
    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    success, img = cap.read()
    
    # FPS calculation
    fps_counter += 1
    if fps_counter >= 30:  # Calculate FPS every 30 frames
        fps_end_time = time.time()
        fps = fps_counter / (fps_end_time - fps_start_time)
        fps_counter = 0
        fps_start_time = time.time()
    
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    
    # Use simple threshold instead of adaptive to reduce noise
    _, imgThreshold = cv2.threshold(imgBlur, 60, 255, cv2.THRESH_BINARY_INV)
    
    # Remove noise with opening operation first
    kernel = np.ones((3, 3), np.uint8)
    imgOpen = cv2.morphologyEx(imgThreshold, cv2.MORPH_OPEN, kernel, iterations=2)
    
    # Fill the cars completely with larger kernel and more iterations
    kernel_large = np.ones((7, 7), np.uint8)
    imgDilate = cv2.dilate(imgOpen, kernel_large, iterations=4)
    imgClose = cv2.morphologyEx(imgDilate, cv2.MORPH_CLOSE, kernel_large, iterations=3)
    
    # Final cleanup to remove remaining small noise
    imgFinal = cv2.morphologyEx(imgClose, cv2.MORPH_OPEN, kernel, iterations=1)
    
    trafficdensity(imgFinal)
    
    # Display FPS on the image
    # cvzone.putTextRect(img, f'FPS: {fps:.1f}', (10, 30), scale=2,
    #                    thickness=3, offset=10, colorR=(0, 255, 255), colorT=(0, 0, 0))
    
    cv2.imshow("Said Albardawil", img)
    # cv2.imshow("ImageBlur", imgBlur)
    # cv2.imshow("ImageThres", imgFinal)
    
    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()