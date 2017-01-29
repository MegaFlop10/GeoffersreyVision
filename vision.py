import numpy as np
import cv2
from networktables import NetworkTables
import time


# Converts to HSV, then filters the image so only green remains.
def threshold():
    # Define threshold values (H, S, V)
    THRESH_MIN = np.array([50, 50, 0], np.uint8)
    THRESH_MAX = np.array([80, 255, 255], np.uint8)

    # Convert to HSV format
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Return pixels within the threshold range
    return cv2.inRange(hsv_img, THRESH_MIN, THRESH_MAX)


# Define target
def find_target():
    # Find contours
    blurred = cv2.medianBlur(threshed, 5)
    edge = cv2.Canny(blurred, 100, 200)
    contours, hierarchy = cv2.findContours(edge, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_NONE)

    # Select largest contour
    largestArea = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area > largestArea:
            largestArea = area
            largestContour = c

    # Try to draw the largest contour over the original image, unless there is no contour
    try:
        cv2.drawContours(img, largestContour, -1, (0, 0, 255), thickness=3)
        return largestContour
    except UnboundLocalError:
        pass


# Find x and y coordinate of target
def find_coordinates(target_contour):
    # Find the bounding rectangle around the given contour, then return its x & y values, unless there is no contour
    try:
        rect = cv2.boundingRect(target_contour)

        x = rect[0] + (rect[2] / 2)
        y = rect[1] + (rect[3] / 2)

        cv2.circle(img, (x, y), 5, 100, thickness=3)
    except cv2.error:
        x = 0
        y = 0

    return x, y


# Find angle to the target
def find_angle(x_target):
    pass                                                                                                              


# Called when 'request' changes
def handle_request(table, key, value, isNew):
    print("Request Received")
    if (key == 'request' and value == True):
            table.putNumber('targetAngle', x) # x & y are not actually angle & distance yet
            table.putNumber('targetDistance', y)
            table.putBoolean('request',False)


NetworkTables.initialize(server='roboRIO-9985-frc.local')
table =  NetworkTables.getTable("vision")
table.addTableListener(handle_request)

# Start video capture with camera 0
cap = cv2.VideoCapture(0)
start_tick=time.time()
while True:
    # Read image
    retval, img = cap.read()

    # Remove non-green pixels
    threshed = threshold()
    # Find the largest contour
    target = find_target()
    # Find its coordinates
    x, y = find_coordinates(target)
    # Find angle of target
    

    # Display original image, which has the contour and x, y drawn onto it
    cv2.imshow("Video Capture", img)
    cv2.waitKey(1)

    table = NetworkTables.getTable('vision')
    count_tick = time.time() - start_tick
    if (count_tick > 10.0):
        print("10s passed")
        print(table.getBoolean('request'))
        
        #print(" targetAngle="+table.getNumber('targetAngle')+" targetDistance="+table.getNumber('targetDistance')+"\n")
        
        start_tick=time.time()   

    
