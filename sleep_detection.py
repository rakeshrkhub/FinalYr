
serialAlarmSent = 0
# import the necessary packages
from scipy.spatial import distance as dist
from imutils import face_utils
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2
import threading
from playsound import playsound
import os
import threading
import serial



import serial.tools.list_ports
ports = serial.tools.list_ports.comports()

for port, desc, hwid in sorted(ports):
    #print("{}: {} [{}]".format(port, desc, hwid))
    print("{}: {}".format(port, desc))
            
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--source", required=True,
    help = "video source [cam] for Camera/[vid] for video")
    
ap.add_argument("-p", "--port", required=True,
    help = "com port of arduino")

args = vars(ap.parse_args())

vidsrc = args['source']
port = args['port']







baud = 9600
serialPort = serial.Serial(port, baud, timeout=1)
# open the serial port
if serialPort.isOpen():
    print(serialPort.name + ' is open...')


serialPort.write("WAKEUP_DETECTED\n")

if vidsrc == "vid":
    print("source is video")
else:
    print("source is camera")








def alarmSound():
    global serialAlarmSent
    if serialAlarmSent == 0:
        serialPort.write("SLEEP_DETECTED\n")
        serialAlarmSent = 1
    path_of_files = "assets/"
    alarm_sound_path=(path_of_files+"alarms.mp3")
    playsound(alarm_sound_path)
    """thread worker function"""
    print 'Alarm Sound Thread ended.'
    
    
    
    
soundThread = threading.Thread(target=alarmSound)



ALARM_WAIT_TIME = 3

EYE_AR_THRESH = 0.25
EYE_BLINK_FRAMES = 2
EYE_STAGE1_FRAMES = 10
EYE_STAGE2_FRAMES = 17
EYE_STAGE3_FRAMES = 24

MOUTH_AR_THRESH = 0.7
YAWN_FRAMES = 9

# initialize the frame counters and the total number of eye closes at different stages
COUNTER = 0
BLINK = 0
STAGE1 = 0
STAGE2 = 0
STAGE3 = 0

COUNTER2 = 0
YAWN = 0
YAWN_TIME = 0

    

def eye_aspect_ratio(eye):
    # compute the euclidean distances between the two sets of vertical eye landmarks (x, y)-coordinates
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # compute the euclidean distance between the horizontal eye landmark (x, y)-coordinates
    C = dist.euclidean(eye[0], eye[3])

    # compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)

    return ear

def mouth_aspect_ratio(mouth):
    # compute the euclidean distances between the two sets of vertical eye landmarks (x, y)-coordinates
    A = dist.euclidean(mouth[2], mouth[10])
    B = dist.euclidean(mouth[4], mouth[8])

    # compute the euclidean distance between the horizontal mouth landmark (x, y)-coordinates
    C = dist.euclidean(mouth[0], mouth[6])

    # compute the mouth aspect ratio
    mar = (A + B) / (2.0 * C)

    return mar


 


    

# initialize dlib's face detector and then create the facial landmark predictor
print("[INFO] loading facial landmark predictor...")
# detector = dlib.get_frontal_face_detector()
detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml") #(args["cascade"])
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat") #(args["shape_predictor"])

# grab the indexes of the facial landmarks for the left and right eye, respectively
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# mouth indexes
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]

# start the video stream thread
print("[INFO] camera sensor warming up...")


vs = None
if vidsrc == 'vid':
    vs = cv2.VideoCapture("WIN_20200430_19_00_56_Pro.mp4")
else:
    vs = cv2.VideoCapture(0)


#vs = WebcamVideoStream(src=0).start()
#vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)


fps = []
p2_time_count = 0 
p2_last_timestamp = 0
p2_current_timestamp = 0
p2_close_second_counter = 0







while True:
    # grab the frame from the threaded video file stream, resize it, and convert it to grayscale channels
    
    #print 'soundThread.isAlive()', soundThread.isAlive()
    t = time.time()
    ret, frame = vs.read()
    #frame = vs.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # detect faces in the grayscale frame
    rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
        minNeighbors=5, minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE)

    # detect faces in the grayscale frame
    #rects = detector(gray, 0)

    # loop over the face detections
    for (x, y, w, h) in rects:
        
        rect = dlib.rectangle(int(x), int(y), int(x+w), int(y+h))
        
        # determine the facial landmarks for the face region, then
        # convert the facial landmark (x, y)-coordinates to a NumPy array
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        # extract the left and right eye coordinates, then use the coordinates to compute the eye aspect ratio for both eyes
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)

        mouth = shape[mStart:mEnd]
        mar = mouth_aspect_ratio(mouth)

        # average the eye aspect ratio together for both eyes
        ear = (leftEAR + rightEAR) / 2.0

        # compute the convex hull for the left and right eye, then visualize each of the eyes
        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        mouthHull = cv2.convexHull(mouth)
        cv2.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)
        print(p2_close_second_counter)
        # check to see if the eye aspect ratio is below the blink threshold, and if so, increment the blink frame counter
        if ear < EYE_AR_THRESH:
            p2_current_timestamp = int(round(time.time() * 1000))
            if p2_current_timestamp > p2_last_timestamp+1000 :
                if p2_close_second_counter < ALARM_WAIT_TIME:
                    p2_close_second_counter+=1
                p2_last_timestamp = p2_current_timestamp
                if p2_close_second_counter > ALARM_WAIT_TIME-1:
                    if not  soundThread.isAlive():
                        soundThread = threading.Thread(target=alarmSound)
                        soundThread.start()
                        
                    print("Sleep detect!")
                    print("ALARM ON")
                    
                
            
            COUNTER += 1
           
        # otherwise, the eye aspect ratio is not below the blink threshold
        else:
            
            p2_current_timestamp = int(round(time.time() * 1000))
            if p2_current_timestamp > p2_last_timestamp+1000 and p2_close_second_counter > 0 :
                p2_close_second_counter -=1
            
            if p2_close_second_counter == 0:
                 print("Weak up detect!")
                 print("ALARM OFF")
                 global serialAlarmSent
                 if serialAlarmSent == 1:
                    serialPort.write("WAKEUP_DETECTED\n")
                    serialAlarmSent = 0
               
               
                        
                        
                        
            # if the eyes were closed for a sufficient number of then increment the total number of blinks
            if EYE_BLINK_FRAMES <= COUNTER < EYE_STAGE1_FRAMES:
                BLINK += 1
                
               
                
            elif EYE_STAGE1_FRAMES <= COUNTER < EYE_STAGE2_FRAMES:
                
                STAGE1 += 1
                print("Stage1:")#initially was 3
                
                
                
            elif EYE_STAGE2_FRAMES <= COUNTER < EYE_STAGE3_FRAMES:
                STAGE2 += 1
                print("Stage2:")
                
                
            elif COUNTER >= EYE_STAGE3_FRAMES:
                STAGE3 += 1
                print("Stage3:")
                    

            # reset the eye frame counter
            COUNTER = 0

        if mar > MOUTH_AR_THRESH:
            COUNTER2 += 1

        else:
            if COUNTER2 >= YAWN_FRAMES:
                YAWN += 1
                t = time.time()
                if t-YAWN_TIME < 30:
                    print("Stage2: Yawn ")
                elif t-YAWN_TIME < 60:
                    print("Stage1: Yawn ")
                YAWN_TIME = time.time()

            COUNTER2 = 0

        cv2.putText(frame, "Blinks: {}".format(BLINK), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.putText(frame, "Yawns: {}".format(YAWN), (10, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, "MAR: {:.2f}".format(mar), (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    
    
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    
    fps.append(time.time() - t)
 
    if key == ord("q"):
        break

print("FPS:", len(fps)/sum(fps))

# do a bit of cleanup
cv2.destroyAllWindows()
# vs.release()
bb.destroy()
vs.stop()
