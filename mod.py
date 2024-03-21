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
import AppOpener

mpHands = mediapipe.solutions.hands
captureHands = mediapipe.solutions.hands.Hands(static_image_mode=False, max_num_hands=1,  model_complexity=0, min_detection_confidence=0.9, min_tracking_confidence=0.9)
drawingOptions = mediapipe.solutions.drawing_utils
screenWidth, screenHeight = pyautogui.size()
camera = cv2.VideoCapture(0)

imageHeight = 480
imageWidth = 640

holdActive = False
currentTime = 0

prevTime = {
    "leftClick": 0,
    "rightClick": 0,
    "leftHold": 0,
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
    "cursorMode": False,
    "freeHandMode": False,
    "voiceMode": True,
    "scrollMode": False
}

mousex = mousey = 0

# click -> thumb to index knuckle
# right click -> middle to thumb
# scroll up
# scroll down
# drag
# drag release


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
    recognizer = sr.Recognizer()

    while True:
        try:
            with sr.Microphone(device_index=1) as mic:
                print("Listening for a command...")
                recognizer.adjust_for_ambient_noise(mic, duration=0.2)
                audio = recognizer.listen(mic)

            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")
            
            # Only keyboard commands
            
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
                
            # Commands related to copy/paste
            
            elif "copy line" in command:
                sendCommands("home, ctrl+shift+end, ctrl+c")
                
            elif "copy word" in command:
                sendCommands("ctrl+shift+left, ctrl+c")
            
            elif "copy everything" in command:
                sendCommands("ctrl+a, ctrl+c") 
                
            elif "paste" in command:
                sendCommands("ctrl+v")
            
            elif "delete" == command:
                sendCommands("backspace")    
            
            elif "delete word" in command:
                sendCommands("ctrl+backspace")
                
            elif "delete line" in command:
                sendCommands("home, ctrl+shift+end, backspace")
                
            elif "delete everything" in command:
                sendCommands("ctrl+a, backspace")
                
            # Commands related to Applications
            
            elif "open" in command:
                application = command.split("open", 1)[1].strip()
                AppOpener.open(application, match_closest=True)
                
            elif "close" in command:
                application = command.split("open", 1)[1].strip()
                AppOpener.close(application, match_closest=True)

            # Exit

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
    

def calculateDistance(landmarkA, landmarkB):
    x1 = coordinates[landmarkA]["x"]
    x2 = coordinates[landmarkB]["x"]
    y1 = coordinates[landmarkA]["y"]
    y2 = coordinates[landmarkB]["y"]
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
    if currentTime - prevTime["leftClick"] > 1 and calculateDistance("indexKnuckle", "thumb") < 30:
        mouse.click()
        prevTime["leftClick"] = currentTime
        print("clicked")
        

def rightClick():
    global currentTime
    if currentTime - prevTime["rightClick"] > 1 and calculateDistance("middle", "thumb") < 30:
        mouse.right_click()
        prevTime["rightClick"] = currentTime
        print("right clicked")

def drag():
    global holdActive
    global currentTime 
    if currentTime - prevTime["leftHold"] > 1 and holdActive == False and calculateDistance("ring", "thumb") < 30:
        mouse.press()
        holdActive = True
        print("mouse hold")
    elif currentTime - prevTime["leftHold"] > 1 and holdActive == True and calculateDistance("middle", "ring") < 30:
        mouse.release()
        holdActive = False
        print("mouse release")
    
def updateModeHandler(mode1="", mode2=""):
    if calculateDistance("index", "indexKnuckle") < 15 and calculateDistance("middle", "middleKnuckle") < 15 and calculateDistance("ring", "ringKnuckle") < 15 and calculateDistance("thumb", "indexKnuckle") > 75:
        modeHandler["freeHandMode"] = False
        modeHandler["cursorMode"] = True
    elif calculateDistance("thumb", "pinky") > 250:
        modeHandler["cursorMode"] = False
        modeHandler["scrollMode"] = True
    elif mode1 == "scroll" and mode2 == "cursor" and calculateDistance("thumb", "ring") < 20:
        modeHandler["cursorMode"] = True
        modeHandler["scrollMode"] = False
    # if calculateDistance("ring", "thumb") < 15:
    #     modeHandler["cursorMode"] = False
    #     modeHandler["voiceMode"] = True
        
def displayModeOnImage(image):
    text = ""
    if modeHandler["cursorMode"]:
        text = "Cursor Mode"
    elif modeHandler["freeHandMode"]:
        text = "Free Hand Mode"
    elif modeHandler["voiceMode"]:
        text = "Voice Commands Mode"
    elif modeHandler["scrollMode"]:
        text = "Scroll Mode"
    cv2.putText(image, text, (460, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
        
    
def updateCurrentTime():
    global currentTime
    currentTime = time.time()

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
                if modeHandler["cursorMode"]:
                    if coordinates["index"]["x"] <= 450 and coordinates["index"]["y"] <= 300:
                        moveMouse()
                    click()
                    rightClick()
                    drag()
                # elif modeHandler["scrollMode"]:
                #     scrollUp()
                #     scrollDown()
                #     updateModeHandler("scroll", "cursor")
                elif modeHandler["voiceMode"]:
                    voiceCommandMode()
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