import cv2
import pickle
#width, height = 130, 52
#width, height = 107, 48
# width, height = 190, 110
# width, height = 260, 70

width, height = 200,90

horisantalPos=2
try:
    with open('streetPos', 'rb') as f:
        posList = pickle.load(f)
except:
    posList = []


def mouseClick(events, x, y, flags, params):
    if events == cv2.EVENT_LBUTTONDOWN:
        posList.append((x, y))


    # if events == cv2.EVENT_RBUTTONDOWN:
    #     posList.append((x, y))

    if events == cv2.EVENT_RBUTTONDOWN:
        for i, pos in enumerate(posList):
            x1, y1 = pos
            if x1 < x < x1 + width and y1 < y < y1 + height:
                posList.pop(i)

    with open('streetPos', 'wb') as f:
        pickle.dump(posList, f)


while True:
    img = cv2.imread('street_image.jpg')
    i=0
    for pos in posList:
        if i<horisantalPos:
            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), (255, 0, 255), 2)
        else:
            cv2.rectangle(img, pos, (pos[0] + height, pos[1] + width), (255, 0, 255), 2)
        i += 1


    cv2.imshow("Image", img)
    cv2.setMouseCallback("Image", mouseClick)
    key =cv2.waitKey(1)
    if key==27:
        break
