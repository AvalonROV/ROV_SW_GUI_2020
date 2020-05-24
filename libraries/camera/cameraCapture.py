import sys
import time
from datetime import datetime
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW, CAP_FFMPEG, CAP_PROP_BUFFERSIZE
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect, QOpenGLWidget)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QImage, QFont, QColor, QPalette

class VIEW(QWidget):
    def __init__(self, app):
        super(VIEW, self).__init__()

        self.app = app 
        # PROGRAM CLOSE EVENT
        self.app.aboutToQuit.connect(self.programExit)

        self.setWindowTitle("Camera Capture View")
        layout = QGridLayout()
        self.view = QLabel("Camera View")
        self.view.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        changeButton = QPushButton("CHANGE CAMERA")
        changeButton.clicked.connect(self.changeCameraFeed)
        layout.addWidget(self.view, 0, 0)
        layout.addWidget(changeButton, 1, 0)
        self.setLayout(layout)

        self.address1 = 0
        self.address2 = "rtsp://192.168.0.100/user=admin&password=&channel=1&stream=0.sdp?"

        # INITIATE CAMERA
        self.camThread = CAMERA_CAPTURE()
        self.camThread.cameraNewFrameSignal.connect(self.updateCameraFeed)
        self.camThread.start()
        
        self.currentAddress = self.address1
        self.camThread.changeSource(self.currentAddress)
     
        self.show()
        
    def changeCameraFeed(self):
        if self.currentAddress == self.address1:
            self.currentAddress = self.address2
            self.camThread.changeSource(self.currentAddress)

        else:
            self.currentAddress = self.address1
            self.camThread.changeSource(self.currentAddress)

    def programExit(self):
        self.camThread.feedStop()
        time.sleep(1)

    @pyqtSlot(QPixmap)
    def updateCameraFeed(self, frame):
        """
        PURPOSE

        Refreshes camera feed with a new frame.

        INPUT

        - frame = QPixmap containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        pixmap = frame.scaledToHeight(800)
        self.view.setPixmap(pixmap)
    
class CAMERA_CAPTURE(QThread):
    """
    PURPOSE

    Contains all the functions to setup and read from RTSP and USB cameras.
    """
    # CREATE SIGNAL
    cameraNewFrameSignal = pyqtSignal(QPixmap, int)

    def __init__(self, address = "", identifier = 0):
        """
        PURPOSE

        Class constructor.
        Defines the default camera settings.

        INPUT

        address = address of the camera feed.
        identifier = the number of the camera (0, 1, 2)
        """
        QThread.__init__(self)
        self.address = address
        self.identifier = identifier
        self.cameraFeed = None
        self.runFeed = True
        self.task = None
        self.width = 1920      
        self.height = 1080
    
    def run(self):
        """
        PURPOSE

        Main loop that captures camera frames and displays them on the GUI.

        INPUT

        NONE

        RETURNS

        NONE
        """
        elapsedTime = 0
        previousTime = datetime.now()
        defaultImage = QPixmap("graphics/no_signal.png")

        # ATTEMPT TO CONNECT TO CAMERA EVERY 0.5 SECONDS
        while self.runFeed:
            # INITIATE CAMERA
            self.initiateCamera()

            if self.initiateStatus:
                self.cameraFeed.set(CAP_PROP_FRAME_WIDTH, self.width)
                self.cameraFeed.set(CAP_PROP_FRAME_HEIGHT, self.height)

            while self.runFeed and self.initiateStatus:
                
                # ~30 FPS CAPTURE RATE
                if elapsedTime > 1/30:
                    try:
                        # CAPTURE FRAME
                        self.cameraFeed.grab()
                        status, frame = self.cameraFeed.read()

                        # IF FRAME IS CAPTURED            
                        if status:
                            previousTime = datetime.now()
                            
                            # RUN IMAGE THROUGH VISION PROCESSING ALGORITHM
                            if self.task != None:
                                frame = self.task.runAlgorithm(frame)

                            # CONVERT TO PIXMAP
                            cameraFrame = self.convertFrame(frame)
                            
                            # SEND FRAME BACK TO MAIN PROGRAM
                            self.cameraNewFrameSignal.emit(cameraFrame, self.identifier)

                        else:
                            # DEFAULT IMAGE
                            self.cameraNewFrameSignal.emit(defaultImage, self.identifier)
                            break
                    
                    except:
                        pass

                elapsedTime = (datetime.now() - previousTime).total_seconds()

            QThread.msleep(500)

            self.cameraNewFrameSignal.emit(defaultImage, self.identifier)
            
        try:
            self.cameraFeed.release()
        except:
            pass

    def initiateCamera(self):
        """
        PURPOSE

        Attempts to initiate camera.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.initiateStatus = False

        if self.address != "":

            # CHECK IF ADDRESS IS INTEGER OR STRING
            addressType = isinstance(self.address, str)

            # RTSP CAMERA
            if addressType:
                try:
                    self.cameraFeed = VideoCapture(self.address, CAP_FFMPEG)
                    self.cameraFeed.set(CAP_PROP_BUFFERSIZE, 3)
                    self.initiateStatus = True
                except:
                    self.initiateStatus = False

            # USB CAMERA
            else:
                try:
                    self.cameraFeed = VideoCapture(self.address, CAP_DSHOW)
                    
                    self.cameraFeed.set(CAP_PROP_BUFFERSIZE, 3)
                    self.initiateStatus = True
                except:
                    self.initiateStatus = False

    def convertFrame(self, frame):
        """
        PURPOSE

        Converts the cv2 image into a pixmap.

        INPUT

        - frame = the image captured by cv2.

        RETURNS

        - cameraFrame = the converted pixmap image.
        """
        # CONVERT TO RGB COLOUR
        cameraFrame = cvtColor(frame, COLOR_BGR2RGB)
        # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
        height, width, _ = cameraFrame.shape
        # GENERATE QIMAGE
        cameraFrame = QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QImage.Format_RGB888)
        # CONVERT TO PIXMAP
        cameraFrame = QPixmap.fromImage(cameraFrame)

        return cameraFrame

    def changeResolution(self, width, height):
        """
        PURPOSE

        Changes the capture resolution of the camera frames.

        INPUT

        - width = width of the frame in pixels.
        - height = height of the frame in pixels.

        RETURNS

        NONE
        """
        self.width = width
        self.height = height

        # SET RESOLUTION IF CAMERA FEED IS INITIALISED
        try:
            self.cameraFeed.set(CAP_PROP_FRAME_WIDTH, self.width)
            self.cameraFeed.set(CAP_PROP_FRAME_HEIGHT, self.height)
        except:
            pass

    def changeSource(self, address):
        """
        PURPOSE

        Changes the address of the camera source.

        INPUT

        - address = the source, either an integer for USB cameras, or a RTSP link for IP cameras.

        RETURNS

        NONE
        """
        if address != self.address:
            self.address = address
            self.initiateStatus = False
        
            try:
                # DISCONNECT FROM CAMERA
                self.cameraFeed.release()
            except:
                pass

    def feedStop(self):
        """
        PURPOSE

        Stops the camera thread.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.runFeed = False

    def feedBegin(self):
        """
        PURPOSE

        Re-starts the camera thread.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.runFeed = True

    def processImage(self, task):
        """
        PURPOSE

        Defines which processing algorithm to run the camera feed through.

        INPUT

        - task = the class object of the processing algorithm

        RETURNS

        NONE
        """
        self.task = task

    def stopProcessing(self):
        """
        PURPOSE

        Stops the camera feed from being processed.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.task = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VIEW(app)
    sys.exit(app.exec_())