import mediapipe
import cv2
import pyautogui
from numba import jit, cuda

mpHands = mediapipe.solutions.hands
captureHands = mediapipe.solutions.hands.Hands()
drawingOptions = mediapipe.solutions.drawing_utils
screenWidth, screenHeight = pyautogui.size()
x1 = x2 = y1 = y2 = 0
xScroll = yScroll = 0
camera = cv2.VideoCapture(0)

@jit(target_backend='cuda')
def capture():
    while True:
        _, image = camera.read()
        if image is None:
            print("No camera found")
            break
        image = cv2.flip(image, 1)
        imageHeight, imageWidth, _ = image.shape
        rgbImage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        outputHands = captureHands.process(rgbImage)
        allHands = outputHands.multi_hand_landmarks
        if allHands:
            for hand in allHands:
                drawingOptions.draw_landmarks(image, hand)
                oneHandLandmark = hand.landmark
                for id, lm in enumerate(oneHandLandmark):
                    x = int(lm.x * imageWidth)
                    y = int(lm.y * imageHeight)
                    if id == 8:
                        mousex = int(screenWidth / imageWidth * x * 2)
                        mousey = int(screenHeight / imageHeight * y * 2)
                        if mousex <= 1:
                            mousex = 0
                        if mousey <= 1:
                            mousey = 0
                        if mousex >= 1920:
                            mousex = 1915
                        if mousey >= 1080:
                            mousey = 1075
                        pyautogui.moveTo(mousex, mousey)
                    if id == 4:
                        y1 = y
                    if id == 12:
                        x2 = x
                        y2 = y
                        print("id 12 x2 ->", x2 )
                        print("id 12 y2 ->", y2)
                    if id == 16:
                        yScroll = y
                        xScroll = x
                        print("id 16 x2 ->", xScroll)
                        print("id 16 y2 ->", yScroll)
            distForScroll = (yScroll - y2)
            if distForScroll == 0:
                pyautogui.scroll(10)
            dist = y1 - y2
            if dist < 40:
                pyautogui.click()
        cv2.imshow("cam", image)
        key = cv2.waitKey(1)
        if key == 27:
            break
    camera.release()
    cv2.destroyAllWindows()                     

try:
    capture()              
except Exception as e:
    print("error is ->", e)                                                                                                                                                                                                                                                           