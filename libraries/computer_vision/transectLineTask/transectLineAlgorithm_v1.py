#import cv2
from cv2 import CAP_DSHOW, cvtColor, COLOR_BGR2HSV, inRange, Canny, fillPoly, bitwise_and, HoughLinesP, line, addWeighted, VideoCapture, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, waitKey, flip, imshow
import numpy as np
import math
import sys
import time

from PyQt5.QtCore import pyqtSignal, QObject

class TRANSECT_LINE_TASK(QObject):
    """
    PURPOSE
    
    Performs the image processing for the transect line task.
    """

    transmitData = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)

    def runAlgorithm(self, frame):
        """
        PURPOSE

        Processes and returns the camera frame.
        Transmits required data to main program.

        INPUT

        - frame = camera frame to process.

        RETURNS

        NONE
        """
        edges = self.detect_edges(frame)
        
        roi = self.region_of_interest(edges)
        
        line_segments = self.detect_line_segments(roi)
        
        edges_2 = self.detect_red_edges(frame)
        
        roi_2 = self.region_of_interest(edges_2)
        
        line_segments_2 = self.detect_line_segments(roi_2)
        
        lane_lines = self.average_slope_intercept(frame, line_segments)
        
        lane_lines_image = self.display_lines(frame, lane_lines)
        
        steering_angle = self.get_steering_angle(frame, lane_lines)
        
        heading_image = self.display_heading_line(lane_lines_image, steering_angle)

        # CALCULATE STEERING DATA
        deviation = steering_angle - 90

        data = ""

        if deviation < 10 and deviation > -10:
            data = "NEUTRAL"

        elif deviation > 5:
            data = "RIGHT"

        elif deviation < -5:
            data = "LEFT"

        # SEND DATA BACK TO PROGRAM
        self.sendData(data)

        return heading_image

    def sendData(self, data):
        """
        PURPOSE

        Sends required data back to main program.

        INPUT

        - data = the data to send.

        RETURNS

        NONE
        """
        self.transmitData.emit(data)
    
    ###########################
    ### ALGORITHM FUNCTIONS ###
    ###########################

    def detect_edges(self, frame):
        # filter for blue lane lines
        hsv = cvtColor(frame, COLOR_BGR2HSV)
        lower_blue = np.array([30, 40, 0], dtype="uint8")
        upper_blue = np.array([150, 255, 255], dtype="uint8")
        # blue color mask
        mask_blue = inRange(hsv, lower_blue, upper_blue)
        # detect edges
        edges = Canny(mask_blue, 200, 400)

        return edges

    def detect_red_edges(self, frame):
        hsv = cvtColor(frame, COLOR_BGR2HSV)
        # filter for red lines
        lower_red = np.array([0, 120, 70])
        upper_red = np.array([10, 255, 255])
        # red mask
        mask_red = inRange(hsv, lower_red, upper_red)
        edges_red = Canny(mask_red, 50, 100)
        return edges_red

    def region_of_interest(self, edges):
        height, width = edges.shape  # extract the height and width of the edges frame
        mask = np.zeros_like(edges)  # make an empty matrix with same dimensions of the edges frame

        # only focus lower half of the screen
        # specify the coordinates of 4 points (lower left, upper left, upper right, lower right)
        polygon = np.array([[
            (0, height),
            (0, height / 2),
            (width, height / 2),
            (width, height),
        ]], np.int32)

        fillPoly(mask, polygon, 255)  # fill the polygon with blue color

        cropped_edges = bitwise_and(edges, mask)
        # imshow("roi",cropped_edges)  take the edged frame as parameter and draws a polygon with 4 preset points

        return cropped_edges

    def detect_line_segments(self, cropped_edges):
        rho = 1  # the the distance precision in pixels
        theta = np.pi / 180  # angular precision in radians
        min_threshold = 10  # minimum vote it should get for it to be considered as a line

        line_segments = HoughLinesP(cropped_edges, rho, theta, min_threshold,
                                        np.array([]), minLineLength=5, maxLineGap=150)

        return line_segments

    def average_slope_intercept(self, frame, line_segments):
        lane_lines = []

        if line_segments is None or len(line_segments) == 2:
            print("Go up")
            return lane_lines

        height, width, _ = frame.shape
        left_fit = []
        right_fit = []

        boundary = 1 / 3
        left_region_boundary = width * (1 - boundary)
        right_region_boundary = width * boundary

        for line_segment in line_segments:
            for x1, y1, x2, y2 in line_segment:
                if x1 == x2:
                    print("skipping vertical lines (slope = infinity")
                    continue

                fit = np.polyfit((x1, x2), (y1, y2), 1)
                slope = (y2 - y1) / (x2 - x1)
                intercept = y1 - (slope * x1)

                if slope < 0:
                    if x1 < left_region_boundary and x2 < left_region_boundary:
                        left_fit.append((slope, intercept))
                else:
                    if x1 > right_region_boundary and x2 > right_region_boundary:
                        right_fit.append((slope, intercept))

        left_fit_average = np.average(left_fit, axis=0)
        if len(left_fit) > 0:
            lane_lines.append(self.make_points(frame, left_fit_average))

        right_fit_average = np.average(right_fit, axis=0)
        if len(right_fit) > 0:
            lane_lines.append(self.make_points(frame, right_fit_average))

        return lane_lines

    def make_points(self, frame, line):
        height, width, _ = frame.shape

        slope, intercept = line

        y1 = height  # bottom of the frame
        y2 = int(y1 / 2)  # make points from middle of the frame down

        if slope == 0:  # slope = 0 which means y1 = y2 (horizontal line)
            slope = 0.1

        x1 = int((y1 - intercept) / slope)
        x2 = int((y2 - intercept) / slope)

        return [[x1, y1, x2, y2]]
   
    def display_lines(self, frame, lines, line_color=(0, 255, 0), line_width=6):
        line_image = np.zeros_like(frame)

        if lines is not None:
            for line1 in lines:
                for x1, y1, x2, y2 in line1:
                    line(line_image, (x1, y1), (x2, y2), line_color, line_width)

        line_image = addWeighted(frame, 0.8, line_image, 1, 1)

        return line_image

    def display_heading_line(self, frame, steering_angle, line_color=(0, 0, 255), line_width=5):
        heading_image = np.zeros_like(frame)
        height, width, _ = frame.shape

        steering_angle_radian = steering_angle / 180.0 * math.pi

        x1 = int(width / 2)
        y1 = height
        x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
        y2 = int(height / 2)

        line(heading_image, (x1, y1), (x2, y2), line_color, line_width)
        # combine two images but with giving each one a weight
        heading_image = addWeighted(frame, 0.8, heading_image, 1, 1)

        return heading_image

    def get_steering_angle(self, frame, lane_lines):
        """
        PURPOSE

        blah blah blah

        INPUT

        blah blah blah

        RETURNS

        blah blah blah
        """

        height, width, _ = frame.shape

        if len(lane_lines) == 2:  # if two lane lines are detected
            _, _, left_x2, _ = lane_lines[0][0]  # extract left x2 from lane_lines array
            _, _, right_x2, _ = lane_lines[1][0]  # extract right x2 from lane_lines array
            mid = int(width / 2)
            x_offset = (left_x2 + right_x2) / 2 - mid
            y_offset = int(height / 2)

        elif len(lane_lines) == 1:  # if only one line is detected
            x1, _, x2, _ = lane_lines[0][0]
            x_offset = x2 - x1
            y_offset = int(height / 2)

        elif len(lane_lines) == 0:  # if only no line is detected
            x_offset = 0
            y_offset = int(height / 2)

        angle_to_mid_radian = math.atan(x_offset / y_offset)
        angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / math.pi)
        steering_angle = angle_to_mid_deg + 90

        return steering_angle