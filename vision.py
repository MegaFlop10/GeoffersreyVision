import numpy as np
import cv2
from networktables import NetworkTables
import math


# Constants
FOCAL_LENGTH = 939.965898323  # Focal length of the Microsoft LifeCam HD3000
IMAGE_WIDTH = 1280  # Pixel width of the Microsoft LifeCam HD3000 (Apparently)

# Define threshold values (H, S, V)
THRESH_MIN = np.array([50, 50, 0], np.uint8)
THRESH_MAX = np.array([80, 255, 255], np.uint8)


# Converts to HSV, then filters the image so only green remains.
def threshold():
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
    largest_area = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area > largest_area:
            largest_area = area
            largest_contour = c

    # Try to draw the largest contour over the original image, unless there is no contour
    try:
        cv2.drawContours(img, largest_contour, -1, (0, 0, 255), thickness=3)
        return largest_contour
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
    image_centre = IMAGE_WIDTH / 2
    angle = math.atan((x_target - image_centre) / FOCAL_LENGTH)  # Formula based on 254's presentation
    return angle


# Called when 'request' changes
def handle_request(table, key, value, isNew):
    print("Request Received")
    if key == 'request' and value is True:
            table.putNumber('targetAngle', targetAngle)  # x & y are not actually angle & distance yet
            table.putNumber('targetDistance', y)
            table.putBoolean('request', False)


NetworkTables.initialize(server='roboRIO-9985-frc.local')  # TODO: Set to static IP addresses
table = NetworkTables.getTable("vision")
table.addTableListener(handle_request)

# Start video capture with camera 0
cap = cv2.VideoCapture(0)
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
    targetAngle = find_angle(x)
    
    # Display original image, which has the contour and x, y drawn onto it
    cv2.imshow("Video Capture", img)
    cv2.waitKey(1)

    table = NetworkTables.getTable('vision')
