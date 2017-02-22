import numpy as np
import cv2
from networktables import NetworkTables
import math


# Constants
CAMERA_PORT = 0
FOCAL_LENGTH = 571.4
IMAGE_WIDTH = 640  # Pixel width
IMAGE_HEIGHT = 360  # Pixel height
HORIZ_FIELD_OF_VIEW = 55.67  # Horizontal FOV of Microsoft LifeCam HD3000, when using 320*180
HORIZ_DEGS_PER_PIXEL = HORIZ_FIELD_OF_VIEW / IMAGE_WIDTH

VERT_FIELD_OF_VIEW = 30  # Vertical FOV of the LifeCam, when using 320*180

TARGET_HEIGHT = 127  # Height of the target in mm

# Define threshold values (H, S, V)
THRESH_MIN = np.array([50, 50, 0], np.uint8)
THRESH_MAX = np.array([80, 255, 255], np.uint8)


# Converts to HSV, then filters the image so only green remains.
def threshold():
    # Convert to HSV format
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Return pixels within the threshold range
    return cv2.inRange(hsv_img, THRESH_MIN, THRESH_MAX)


#  Find all contours in image
def find_contours():
    # Find contours
    blurred = cv2.medianBlur(threshed, 5)
    edge = cv2.Canny(blurred, 100, 200)
    contours, hierarchy = cv2.findContours(edge, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_NONE)
    return contours


# Define contours around the largest target found
def find_gear_target1(contours):
    # Select largest contour
    area1 = 0  # Largest area
    for c in contours:
        area = cv2.contourArea(c)
        if area > area1:
            area1 = area
            contour1 = c

    try:
        return contour1
    except UnboundLocalError:
        pass


#  Define contours around the second largest target found
def find_gear_target2(contours):
    # Select second-largest contour
    area1 = 0  # Largest area
    area2 = 0  # Second-largest area
    for c in contours:
        area = cv2.contourArea(c)
        if area > area1:
            area1 = area
        elif area > area2:
            area2 = area
            contour2 = c

    try:
        return contour2
    except UnboundLocalError:
        pass


# Try to draw the largest contour over the original image, unless there is no contour
def draw_contours(contour1, contour2):
    try:
        cv2.drawContours(img, contour1, -1, (0, 0, 255), thickness=3)
        cv2.drawContours(img, contour2, -1, (0, 0, 255), thickness=3)
    except UnboundLocalError:
        pass


# Find x and y coordinate of target
def find_coordinates(target_contour):
    # Find the bounding rectangle around the given contour, then return its x & y values, unless there is no contour
    try:
        rect = cv2.boundingRect(target_contour)

        # 0 = x
        # 1 = y
        # 2 = w
        # 3 = h

        x = rect[0] + (rect[2] / 2)
        y = rect[1] + (rect[3] / 2)
        height = rect[3]
        # print("find_coord: x: "+str(x)+" y : "+str(y))

        cv2.circle(img, (x, y), 5, 100, thickness=3)
    except cv2.error:
        x = -1
        y = -1
        height = -1

    return x, height


# Find angle to the target
def find_angle(x1, x2):
    image_x_centre = IMAGE_WIDTH / 2

    angle1 = (x1 - image_x_centre) * HORIZ_DEGS_PER_PIXEL  # Approx method TODO: Find focal length for other method
    angle2 = (x2 - image_x_centre) * HORIZ_DEGS_PER_PIXEL
    # angle2 = angle1
    # angle = math.atan((x_target - image_centre) / FOCAL_LENGTH)  # Formula based on 254's presentation

    avg_angle = (angle1 + angle2) / 2
    return avg_angle


# Find distance to the target
def find_distance(target1_height, target2_height):
    # TARGET_HEIGHT is the height in mm, target_height is the height in px
    distance1 = (TARGET_HEIGHT * IMAGE_HEIGHT / (2 * target1_height * math.tan(math.radians(VERT_FIELD_OF_VIEW)) / 2))
    distance2 = (TARGET_HEIGHT * IMAGE_HEIGHT / (2 * target2_height * math.tan(HORIZ_FIELD_OF_VIEW) / 2))
    # distance2 = distance1
    avg_distance = (distance1 + distance2) / 2
    return avg_distance


# Called when 'request' changes
def handle_request(table, key, value, isNew):
    print("Request Received")
    if key == 'request' and value is True:
            table.putNumber('targetAngle', targetAngle)  # x & y are not actually angle & distance yet
            table.putNumber('targetDistance', targetDistance)
            table.putBoolean('request', False)


NetworkTables.initialize(server='10.59.85.2')
table = NetworkTables.getTable("vision")
table.addTableListener(handle_request)

cap = cv2.VideoCapture(CAMERA_PORT)  # Start video capture with camera
cap.set(3, IMAGE_WIDTH)
cap.set(4, IMAGE_HEIGHT)

while True:
    retval, img = cap.read()  # Read image

    threshed = threshold()  # Remove non-green pixels
    contours = find_contours()  # Find contours in the image

    target1 = find_gear_target1(contours)  # Find the largest contour
    target2 = find_gear_target2(contours)  # Find the second-largest contour

    draw_contours(target1, target2)  # Draw contours onto img

    x1, height1 = find_coordinates(target1)
    x2, height2 = find_coordinates(target2)

    targetAngle = find_angle(x1, x2)
    # print(targetAngle)
    # print("x1: " + str(x1) + "  x2: " + str(x2) + "  targetA: " + str(targetAngle))

    targetDistance = find_distance(height1, height2)

    print("H: "+str(height1)+" W: "+str(x1*2) + " targetD: "+str(targetDistance) + " Angle : " + str(targetAngle))
    
    # Display original image, which has the contour and x, y drawn onto it
    cv2.imshow("Video Capture", img)
    cv2.imshow("Threshold", threshed)
    cv2.waitKey(100)

    # Refresh networktables
    table = NetworkTables.getTable('vision')


