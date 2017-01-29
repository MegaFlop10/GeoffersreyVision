import numpy as np
import cv2
from networktables import NetworkTables
import math


# Constants
CAMERA_PORT = 0
# FOCAL_LENGTH = 571.4
IMAGE_WIDTH = 640  # Pixel width
IMAGE_HEIGHT = 480  # Pixel height
FIELD_OF_VIEW = 62.8  # Horizontal FOV
DEGREES_PER_PIXEL = FIELD_OF_VIEW / IMAGE_WIDTH
CAMERA_HEIGHT = 30  # Height of camera from centre of target

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
    image_x_centre = IMAGE_WIDTH / 2
    angle = (x_target - image_x_centre) * DEGREES_PER_PIXEL  # Approx method  TODO: Find focal length for other method
    # angle = math.atan((x_target - image_centre) / FOCAL_LENGTH)  # Formula based on 254's presentation
    return angle


# Find distance to the target
def find_distance(y_target):
    image_y_centre = IMAGE_HEIGHT / 2
    vertAngle = 90 - ((y_target-image_y_centre) * DEGREES_PER_PIXEL)
    distance = (math.sin(vertAngle)/math.cos(vertAngle)) * CAMERA_HEIGHT
    return distance


# Called when 'request' changes
def handle_request(table, key, value, isNew):
    print("Request Received")
    if key == 'request' and value is True:
            table.putNumber('targetAngle', targetAngle)  # x & y are not actually angle & distance yet
            table.putNumber('targetDistance', targetDistance)
            table.putBoolean('request', False)


NetworkTables.initialize(server='roboRIO-9985-frc.local')  # TODO: Set to static IP addresses
table = NetworkTables.getTable("vision")
table.addTableListener(handle_request)

cap = cv2.VideoCapture(CAMERA_PORT)  # Start video capture with camera

while True:
    retval, img = cap.read()  # Read image

    threshed = threshold()  # Remove non-green pixels
    target = find_target()  # Find the largest contour
    x, y = find_coordinates(target)  # Find its coordinates
    targetAngle = find_angle(x)  # Find angle of target
    targetDistance = find_distance(y)
    
    # Display original image, which has the contour and x, y drawn onto it
    cv2.imshow("Video Capture", img)
    cv2.waitKey(1)

    # Refresh networktables
    table = NetworkTables.getTable('vision')
