import mediapipe
import cv2
import pyautogui
from numba import jit, cuda
import math
import mouse
from concurrent.futures import ThreadPoolExecutor
import speech_recognition as sr
import re
import keyboard
import threading
import time
import AppOpener

mpHands = mediapipe.solutions.hands
captureHands = mediapipe.solutions.hands.Hands(static_image_mode=False, max_num_hands=1,  model_complexity=0, min_detection_confidence=0.9, min_tracking_confidence=0.9)
drawingOptions = mediapipe.solutions.drawing_utils
screenWidth, screenHeight = pyautogui.size()
camera = cv2.VideoCapture(0)

# Global Variables

imageHeight = 480
imageWidth = 640

holdActive = False
currentTime = 0

currentMode = "freeHandMode"

prevTime = {
    "leftClick": 0,
    "rightClick": 0,
    "leftHold": 0,
    "modeChange": 0
}

coordinates = {
    "index": {"x": 0,"y": 0},
    "indexKnuckle": {"x": 0,"y": 0},
    "thumb": {"x": 0,"y": 0},
    "middle": {"x": 0,"y": 0},
    "middleKnuckle": {"x": 0,"y": 0},
    "ring": {"x": 0,"y": 0},
    "ringKnuckle": {"x": 0,"y": 0},
    "wrist": {"x": 0,"y": 0},
    "pinky": {"x": 0,"y": 0}
}

modeHandler = {
    "modeSelector": False,
    "mouseMode": False,
    "clickMode": False,
    "scrollMode": False,
    "dragMode": False,
    "freeHandMode": True,
    "voiceMode": False,
    "exit": False
}

mousex = mousey = 0

# Methods related to debouncing


def updateCurrentTime():
    global currentTime
    currentTime = time.time()


# Methods related to storing and updating landmarks


def calculateAndStoreLandmarks(oneHandLandmark):
    global coordinates
    
    coordinates["index"]["x"] = int(oneHandLandmark[8].x * imageWidth)
    coordinates["index"]["y"] = int(oneHandLandmark[8].y * imageHeight)
    
    coordinates["indexKnuckle"]["x"] = int(oneHandLandmark[5].x * imageWidth)
    coordinates["indexKnuckle"]["y"] = int(oneHandLandmark[5].y * imageHeight)
    
    coordinates["thumb"]["x"] = int(oneHandLandmark[4].x * imageWidth)
    coordinates["thumb"]["y"] = int(oneHandLandmark[4].y * imageHeight)
    
    coordinates["middle"]["x"] = int(oneHandLandmark[12].x * imageWidth)
    coordinates["middle"]["y"] = int(oneHandLandmark[12].y * imageHeight)
    
    coordinates["middleKnuckle"]["x"] = int(oneHandLandmark[9].x * imageWidth)
    coordinates["middleKnuckle"]["y"] = int(oneHandLandmark[9].y * imageHeight)
    
    coordinates["ring"]["x"] = int(oneHandLandmark[16].x * imageWidth)
    coordinates["ring"]["y"] = int(oneHandLandmark[16].y * imageHeight)
    
    coordinates["ringKnuckle"]["x"] = int(oneHandLandmark[13].x * imageWidth)
    coordinates["ringKnuckle"]["y"] = int(oneHandLandmark[13].y * imageHeight)
    
    coordinates["pinky"]["x"] = int(oneHandLandmark[20].x * imageWidth)
    coordinates["pinky"]["y"] = int(oneHandLandmark[20].y * imageHeight)
    
    coordinates["wrist"]["x"] = int(oneHandLandmark[0].x * imageWidth)
    
def calculateDistance(landmarkA, landmarkB):
    x1 = coordinates[landmarkA]["x"]
    x2 = coordinates[landmarkB]["x"]
    y1 = coordinates[landmarkA]["y"]
    y2 = coordinates[landmarkB]["y"]
    return abs(math.sqrt((x2 - x1)**2 + (y2 - y1)**2))


# Methods related to Setting Modes


def displayModeOnImage(image):
    global currentMode
    cv2.putText(image, currentMode, (460, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
    
def supremeHandler(finger1: str, finger2: str, distance: int, modes: list, booleans=[True, False]):
    global currentMode
    global currentTime
    if calculateDistance(finger1, finger2) < distance and currentTime - prevTime["modeChange"] > 1:
        modeHandler[modes[0]] = booleans[0]
        modeHandler[modes[1]] = booleans[1]
        currentMode = modes[0]
        prevTime["modeChange"] = time.time()
        
def updateModeHandler(mode1="", mode2=""):
    global currentMode
    global currentTime
    if modeHandler["freeHandMode"]:
        supremeHandler("thumb", "pinky", 30, ["modeSelector", currentMode])
    if modeHandler["modeSelector"]:
        supremeHandler("thumb", "index", 30, ["mouseMode", currentMode])
        supremeHandler("thumb", "middle", 30, ["voiceMode", currentMode])
    if modeHandler["mouseMode"]:
        supremeHandler("thumb", "index", 30, ["clickMode", currentMode])
        supremeHandler("thumb", "middle", 30, ["scrollMode", currentMode])
        supremeHandler("thumb", "ring", 30, ["dragMode", currentMode])    

def exit():
    global currentMode
    global currentTime
    if currentTime - prevTime["modeChange"] < 1:
        return
    if (currentMode == "clickMode" or currentMode == "scrollMode" or currentMode == "dragMode") and calculateDistance("thumb", "pinky") < 30:
        modeHandler["mouseMode"] = True
        modeHandler[currentMode] = False
        currentMode = "mouseMode"
        prevTime["modeChange"] = currentTime
        print(calculateDistance("thumb", "pinky"))
        return
    if currentMode == "mouseMode" and calculateDistance("thumb", "pinky") < 30:
        modeHandler["modeSelector"] = True
        modeHandler[currentMode] = False
        currentMode = "modeSelector"
        prevTime["modeChange"] = currentTime
        return
    if currentMode == "modeSelector" and calculateDistance("thumb", "pinky") < 30:
        modeHandler["freeHandMode"] = True
        modeHandler[currentMode] = False
        currentMode = "freeHandMode"
        prevTime["modeChange"] = currentTime
        return
    if currentMode == "freeHandMode" and calculateDistance("thumb", "pinky") < 30:
        modeHandler["exit"] = True
        modeHandler[currentMode] = False
        currentMode = "exit"
        prevTime["modeChange"] = currentTime
        
# Methods related to mouse

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
    indexX = coordinates["index"]["x"]
    indexY = coordinates["index"]["y"]
    mousex = int(screenWidth / (450) * indexX * 1)
    mousey = int(screenHeight / (300) * indexY * 1)
    mousex, mousey = validateMousePosition(mousex, mousey)
    mouse.move(mousex, mousey, absolute=True)
    
def scrollUp():
    dist = calculateDistance("thumb", "index")
    if dist < 20:
        mouse.wheel(3)
        print("scrolling up")
        
def scrollDown():
    if calculateDistance("thumb", "middle") < 20:
        mouse.wheel(-3)
        print("scrolling down")

def click():
    global currentTime
    if currentTime - prevTime["leftClick"] > 1 and calculateDistance("thumb", "middle") < 30:
        mouse.click()
        prevTime["leftClick"] = currentTime
        print("clicked")
        
def rightClick():

    global currentTime
    if currentTime - prevTime["rightClick"] > 1 and calculateDistance("thumb", "ring") < 30:
        mouse.right_click()
        prevTime["rightClick"] = currentTime
        print("right clicked")

def drag():
    global holdActive
    global currentTime 
    if currentTime - prevTime["leftHold"] > 1 and holdActive == False and calculateDistance("thumb", "middle") < 30 and currentTime - prevTime["leftHold"] > 1:
        mouse.press()
        holdActive = True
        prevTime["leftHold"] = currentTime
        print("mouse hold")
    elif currentTime - prevTime["leftHold"] > 1 and holdActive == True and calculateDistance("thumb", "ring") < 30 and currentTime - prevTime["leftHold"] > 1:
        mouse.release()
        holdActive = False
        prevTime["leftHold"] = currentTime
        print("mouse release")


# Methods related to voice commands

    
def type_text(text):
    keyboard.write(text)

def press_key(key):
    threading.Thread(target=keyboard.press_and_release, args=(key,)).start()

def hold_key(key):
    keyboard.press(key)

def release_key(key):
    keyboard.release(key)

def sendCommands(command):
    keyboard.send(command)

def voiceCommandMode():
    global currentMode
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    # Use the default microphone device so it's less brittle across systems
    try:
        with sr.Microphone() as mic:
            # Calibrate once for ambient noise to improve subsequent recognition
            recognizer.adjust_for_ambient_noise(mic, duration=1)
            print("Voice mode active. Say 'exit' to leave.")
            # Loop while voice mode is enabled; the caller toggles this flag
            while modeHandler.get("voiceMode", False):
                try:
                    print("Listening for a command...")
                    # timeout: how long to wait for phrase to start; phrase_time_limit: max phrase length
                    audio = recognizer.listen(mic, timeout=5, phrase_time_limit=8)
                    command = recognizer.recognize_google(audio).lower()
                    print(f"Recognized command: {command}")
                    # Split phrase into subcommands by 'and', 'then', or commas
                    parts = re.split(r"\s+(?:and|then)\s+|\s*,\s*", command)
                    last_opened_was_browser = False
                    for part in parts:
                        sub = part.strip()
                        if not sub:
                            continue
                        # Application open/close
                        if sub.startswith("open "):
                            application = sub.split("open", 1)[1].strip()
                            AppOpener.open(application, match_closest=True)
                            # if a browser was opened, remember so a following 'type' can go to URL
                            last_opened_was_browser = application.lower() in ("brave", "chrome", "firefox", "edge", "msedge", "opera")
                            if last_opened_was_browser:
                                time.sleep(1)
                        elif sub.startswith("close "):
                            application = sub.split("close", 1)[1].strip()
                            AppOpener.close(application, match_closest=True)
                            last_opened_was_browser = False
                        # Keyboard actions
                        elif sub.startswith("type "):
                            text_to_type = sub.split("type", 1)[1].strip()
                            if last_opened_was_browser and "." not in text_to_type:
                                # convert short site name to url
                                url = text_to_type.replace(" ", "")
                                if not url.startswith("www."):
                                    url = "www." + url
                                if "." not in url:
                                    url = url + ".com"
                                type_text(url)
                                press_key('enter')
                                last_opened_was_browser = False
                            else:
                                type_text(text_to_type)
                        elif sub.startswith("press "):
                            key_to_press = sub.split("press", 1)[1].strip()
                            press_key(key_to_press.replace(" ", "+"))
                        elif sub.startswith("hold "):
                            key_to_hold = sub.split("hold", 1)[1].strip()
                            hold_key(key_to_hold.replace(" ", "+"))
                        elif sub.startswith("release "):
                            key_to_release = sub.split("release", 1)[1].strip()
                            release_key(key_to_release.replace(" ", "+"))
                        elif sub == "delete":
                            sendCommands("backspace")
                        elif sub == "delete word":
                            sendCommands("ctrl+backspace")
                        elif sub == "delete line":
                            sendCommands("home, ctrl+shift+end, backspace")
                        elif sub == "delete everything":
                            sendCommands("ctrl+a, backspace")
                        elif sub == "copy line":
                            sendCommands("home, ctrl+shift+end, ctrl+c")
                        elif sub == "copy word":
                            sendCommands("ctrl+shift+left, ctrl+c")
                        elif sub == "copy everything":
                            sendCommands("ctrl+a, ctrl+c")
                        elif sub == "paste":
                            sendCommands("ctrl+v")
                        elif sub == "exit":
                            print("Exiting voice mode.")
                            modeHandler["voiceMode"] = False
                            modeHandler["modeSelector"] = True
                            currentMode = "modeSelector"
                            break
                        else:
                            print(f"Unrecognized subcommand: '{sub}'")
                        # small pause to allow spawned threads to run
                        time.sleep(0.2)
                except sr.WaitTimeoutError:
                    # No speech detected within timeout — continue listening
                    print("Listening timed out; retrying...")
                    continue
                except sr.UnknownValueError:
                    print("Speech Recognition could not understand audio.")
                except sr.RequestError as e:
                    print(f"Speech API request failed: {e}")
                except KeyboardInterrupt:
                    print("Voice mode interrupted by user.")
                    break
    except Exception as e:
        print("Voice mode initialization failed:", e)
    

# rectangle size in image = 230 x 300

# Main function

@jit(target_backend='cuda')
def capture():    
    while True:
        _, image = camera.read()
        if image is None:
            break
        image = cv2.flip(image, 1)
        cv2.rectangle(image, (0, 0), (450, 300), (255, 0, 0), 1)
        cv2.rectangle(image, (450, 0), (640, 50), (0, 255, 0), -1)
        displayModeOnImage(image)
        rgbImage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        outputHands = captureHands.process(rgbImage)
        allHands = outputHands.multi_hand_landmarks
        updateCurrentTime()
        if allHands:
            for hand in allHands:
                drawingOptions.draw_landmarks(image, hand, mpHands.HAND_CONNECTIONS)
                oneHandLandmark = hand.landmark
                calculateAndStoreLandmarks(oneHandLandmark)
                updateModeHandler()
                if modeHandler["clickMode"]:
                    if coordinates["index"]["x"] <= 450 and coordinates["index"]["y"] <= 300:
                        moveMouse()
                    click()
                    rightClick()
                elif modeHandler["scrollMode"]:
                    scrollUp()
                    scrollDown()
                    updateModeHandler("scroll", "cursor")
                elif modeHandler["dragMode"]:
                    if coordinates["index"]["x"] <= 450 and coordinates["index"]["y"] <= 300:
                        moveMouse()
                    drag()
                elif modeHandler["voiceMode"]:
                    voiceCommandMode()
                exit()
        if modeHandler["exit"]:
            break
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

'''
Free hand mode 
    Mode selector
        Mouse mode
            Click mode
            Scroll mode
            Drag mode
            exit
        voice mode
            exit
        exit
    exit
exit
'''