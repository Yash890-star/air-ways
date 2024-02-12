import mediapipe
import cv2
import pyautogui
from numba import jit, cuda


mpHands = mediapipe.solutions.hands
captureHands = mediapipe.solutions.hands.Hands(static_image_mode=False)
drawingOptions = mediapipe.solutions.drawing_utils
screenWidth, screenHeight = pyautogui.size()
camera = cv2.VideoCapture(0)

imageHeight = 480
imageWidth = 640

indexX = indexY = 0
thumbX = thumbY = 0
middleX = middleY = 0
ringX = ringY = 0
wristX = wristY = 0

mousex = mousey = 0

def cameraNotFound(image):
     if image is None:
         return True
     
def isInsideRectangle(x, y, rect):
    xStart, yStart, xEnd, yEnd = rect
    return x >= xStart and y >= yStart and y < yEnd

def calculateAndStoreLandmarks(oneHandLandmark):
    global indexX
    global indexY
    global thumbX
    global thumbY
    global middleX
    global middleY
    global ringX
    global ringY
    global wristX
    global wristY
    
    indexX = int(oneHandLandmark[8].x * imageWidth)
    indexY = int(oneHandLandmark[8].y * imageHeight)
    
    thumbX = int(oneHandLandmark[4].x * imageWidth)
    thumbY = int(oneHandLandmark[4].y * imageHeight)
    
    middleY = int(oneHandLandmark[12].x * imageWidth)
    middleY = int(oneHandLandmark[12].y * imageHeight)
    
    ringX = int(oneHandLandmark[16].x * imageWidth)
    ringY = int(oneHandLandmark[16].y * imageHeight)
    
    wristX = int(oneHandLandmark[0].x * imageWidth)
    wristY = int(oneHandLandmark[0].y * imageHeight)
    
     
def validateMousePosition(mousex, mousey):
    if mousex <= 1:
        mousex = 5
    if mousey <= 1:
        mousey = 5
    if mousex >= 1920:
        mousex = 1915
    if mousey >= 1080:
        mousey = 1075
    return (mousex, mousey)

def moveMouse():
    global mousex
    global mousey
    mousex = int(screenWidth / imageWidth * indexX * 1)
    mousey = int(screenHeight / imageHeight * indexY * 1)
    mousex, mousey = validateMousePosition(mousex, mousey)
    pyautogui.moveTo(mousex, mousey)

def scrollUp():
    if wristY - middleY < 50:
        pyautogui.scroll(100)
        
def scrollDown():
    if wristY - ringY < 50:
        pyautogui.scroll(-100)

def click():
    if middleX - thumbX < 15:
        pyautogui.click()

def drag():
    if middleX - indexX < 15:
        pyautogui.mouseDown()
    if middleX - indexX > 15:
        pyautogui.mouseUp()

@jit(target_backend='cuda')
def capture():    
    while True:
        _, image = camera.read()
        if cameraNotFound(image):
            break
        image = cv2.flip(image, 1)
        rgbImage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        outputHands = captureHands.process(rgbImage)
        allHands = outputHands.multi_hand_landmarks
        if allHands:
            for hand in allHands:
                drawingOptions.draw_landmarks(image, hand)
                oneHandLandmark = hand.landmark
                calculateAndStoreLandmarks(oneHandLandmark)
                moveMouse()
                scrollUp()
                scrollDown()
                click()
                drag()
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