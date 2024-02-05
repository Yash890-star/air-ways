import mediapipe
import cv2
import pyautogui
from numba import jit, cuda

mpHands = mediapipe.solutions.hands
captureHands = mediapipe.solutions.hands.Hands()
drawingOptions = mediapipe.solutions.drawing_utils
screenWidth, screenHeight = pyautogui.size()
x1 = x2 = y1 = y2 = 0
camera = cv2.VideoCapture(0)

@jit(target_backend='cuda')
def capture():
    while True:
        _, image = camera.read()
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
                        pyautogui.moveTo(mousex, mousey)
                        x1 = x 
                        y1 = y
                    if id == 4:
                        x2 = x
                        y2 = y
            dist = y2 - y1
            if dist < 40:
                pyautogui.click()
        cv2.imshow("cam", image)
        key = cv2.waitKey(1)
        if key == 27:
            break
    camera.release()
    cv2.destroyAllWindows()                     

capture()                                                                                                                                                                                                                                                                         