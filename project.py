import mediapipe
import cv2
import pyautogui
from numba import jit, cuda
import math
import mouse
from concurrent.futures import ThreadPoolExecutor
import speech_recognition as sr
import keyboard
import threading
import time


mpHands = mediapipe.solutions.hands
captureHands = mediapipe.solutions.hands.Hands(static_image_mode=False, max_num_hands=1,  model_complexity=0, min_detection_confidence=0.85, min_tracking_confidence=0.8)
drawingOptions = mediapipe.solutions.drawing_utils
screenWidth, screenHeight = pyautogui.size()
camera = cv2.VideoCapture(0)

imageHeight = 480
imageWidth = 640

indexX = indexY = 0
indexKnuckleX = indexKnuckleY = 0
thumbX = thumbY = 0
middleX = middleY = 0
ringX = ringY = 0
wristX = wristY = 0

mousex = mousey = 0

def calculateAndStoreLandmarks(oneHandLandmark):
    global indexX
    global indexY
    global indexKnuckleX
    global indexKnuckleY
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
    
    indexKnuckleX = int(oneHandLandmark[5].x * imageWidth)
    indexKnuckleY = int(oneHandLandmark[5].y * imageHeight)
    
    thumbX = int(oneHandLandmark[4].x * imageWidth)
    thumbY = int(oneHandLandmark[4].y * imageHeight)
    
    middleX = int(oneHandLandmark[12].x * imageWidth)
    middleY = int(oneHandLandmark[12].y * imageHeight)
    
    ringX = int(oneHandLandmark[16].x * imageWidth)
    ringY = int(oneHandLandmark[16].y * imageHeight)
    
    wristX = int(oneHandLandmark[0].x * imageWidth)
    wristY = int(oneHandLandmark[0].y * imageHeight)
    
def type_text(text):
    keyboard.write(text)

def press_key(key):
    threading.Thread(target=keyboard.press_and_release, args=(key,)).start()

def hold_key(key):
    keyboard.press(key)

def release_key(key):
    keyboard.release(key)

def voiceCommandMode():
    recognizer = sr.Recognizer()

    while True:
        try:
            with sr.Microphone(device_index=1) as mic:
                print("Listening for a command...")
                recognizer.adjust_for_ambient_noise(mic, duration=0.2)
                audio = recognizer.listen(mic)

            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")

            if "type" in command:
                text_to_type = command.split("type", 1)[1].strip()
                type_text(text_to_type)

            elif "press" in command:
                key_to_press = command.split("press", 1)[1].strip()
                press_key(key_to_press.replace(" ", "+"))

            elif "hold" in command:
                key_to_hold = command.split("hold", 1)[1].strip()
                hold_key(key_to_hold.replace(" ", "+"))

            elif "release" in command:
                key_to_release = command.split("release", 1)[1].strip()
                release_key(key_to_release.replace(" ", "+"))

            elif "exit" in command:
                print("Exiting the program.")
                break

            else:
                print("Invalid command. Please try again.")

            # Sleep to allow the separate thread to run
            time.sleep(1)

        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio.")
        except KeyboardInterrupt:
            print("Program interrupted by user.")
            break    
    

def calculateDistance(x1, x2, y1, y2):
    return abs(math.sqrt((x2 - x1)**2 + (y2 - y1)**2))
    
     
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

# rectangle size in image = 230 x 300

def moveMouse():
    global mousex
    global mousey
    mousex = int(screenWidth / (450) * indexX * 1)
    mousey = int(screenHeight / (300) * indexY * 1)
    mousex, mousey = validateMousePosition(mousex, mousey)
    # pyautogui.moveTo(mousex, mousey)
    mouse.move(mousex, mousey, absolute=True)

def scrollUp():
    if calculateDistance(wristX, middleX, wristY, middleY) < 50:
        pyautogui.scroll(100)
        
def scrollDown():
    if calculateDistance(wristX, ringX, wristY, ringY) < 50:
        pyautogui.scroll(-100)

def click():
    if calculateDistance(indexKnuckleX, thumbX, indexKnuckleY, thumbY) < 15:
        pyautogui.click()

def drag():
    if calculateDistance(middleX, indexX, middleY, indexY) < 10:
        pyautogui.mouseDown()
    if calculateDistance(middleX, indexX, middleY, indexY):
        pyautogui.mouseUp()

@jit(target_backend='cuda')
def capture():    
    while True:
        _, image = camera.read()
        if image is None:
            break
        # image = cv2.resize(image, (640, 360), interpolation=cv2.INTER_LINEAR)
        image = cv2.flip(image, 1)
        cv2.rectangle(image, (0, 0), (450, 300), (255, 0, 0), 1)
        rgbImage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        outputHands = captureHands.process(rgbImage)
        allHands = outputHands.multi_hand_landmarks
        if allHands:
            for hand in allHands:
                drawingOptions.draw_landmarks(image, hand)
                oneHandLandmark = hand.landmark
                calculateAndStoreLandmarks(oneHandLandmark)
                if indexX <= 450 and indexY <= 300:
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