import sys
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect, QOpenGLWidget)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QImage, QFont, QColor, QPalette

class VIEW(QWidget):
    def __init__(self):
        super(VIEW, self).__init__()
        self.setWindowTitle("Camera Capture View")
        layout = QGridLayout()
        self.view1 = QLabel("Camera View 1")
        self.view2 = QLabel("Camera View 2")
        self.view3 = QLabel("Camera View 3")
        layout.addWidget(self.view1, 0, 0)
        layout.addWidget(self.view2, 0, 1)
        layout.addWidget(self.view3, 0, 2)
        self.setLayout(layout)
        # INITIATE CAMERA
        camThread = CAMERA_CAPTURE(0, 1, 2)
        camThread.cameraNewFrameSignal1.connect(self.updateCameraFeed1)
        camThread.cameraNewFrameSignal2.connect(self.updateCameraFeed2)
        camThread.cameraNewFrameSignal3.connect(self.updateCameraFeed3)
        camThread.start()
        self.show()
        
    @pyqtSlot(QPixmap)
    def updateCameraFeed1(self, frame):
        """
        PURPOSE

        Refreshes camera feed with a new frame.

        INPUT

        - frame = QPixmap containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        pixmap = frame.scaledToHeight(800)
        self.view1.setPixmap(pixmap)

    @pyqtSlot(QPixmap)
    def updateCameraFeed2(self, frame):
        """
        PURPOSE

        Refreshes camera feed with a new frame.

        INPUT

        - frame = QPixmap containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        pixmap = frame.scaledToHeight(800)
        self.view2.setPixmap(pixmap)

    @pyqtSlot(QPixmap)
    def updateCameraFeed3(self, frame):
        """
        PURPOSE

        Refreshes camera feed with a new frame.

        INPUT

        - frame = QPixmap containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        pixmap = frame.scaledToHeight(800)
        self.view3.setPixmap(pixmap)

    
class CAMERA_CAPTURE(QThread):
    # CREATE SIGNAL
    cameraNewFrameSignal1 = pyqtSignal(QPixmap)
    cameraNewFrameSignal2 = pyqtSignal(QPixmap)
    cameraNewFrameSignal3 = pyqtSignal(QPixmap)

    def __init__(self, channel1, channel2, channel3):
        QThread.__init__(self)
        # CAMERA FEED SOURCE
        self.channel1 = channel1
        self.channel2 = channel2
        self.channel3 = channel3
    
    def run(self):
        # INITIATE CAMERA
        cameraFeed1 = VideoCapture(self.channel1, CAP_DSHOW)
        cameraFeed1.set(CAP_PROP_FRAME_WIDTH, 1024)
        cameraFeed1.set(CAP_PROP_FRAME_HEIGHT, 576)

        cameraFeed2 = VideoCapture(self.channel2, CAP_DSHOW)
        cameraFeed2.set(CAP_PROP_FRAME_WIDTH, 1024)
        cameraFeed2.set(CAP_PROP_FRAME_HEIGHT, 576)

        cameraFeed3 = VideoCapture(self.channel3, CAP_DSHOW)
        cameraFeed3.set(CAP_PROP_FRAME_WIDTH, 1024)
        cameraFeed3.set(CAP_PROP_FRAME_HEIGHT, 576)

        cameras = [cameraFeed1, cameraFeed2, cameraFeed3]
        signals = [self.cameraNewFrameSignal1, self.cameraNewFrameSignal2, self.cameraNewFrameSignal3]
    
        while True: 

            for index, camera in enumerate(cameras):

                # CAPTURE FRAME
                status, frame = camera.read()
            
                # IF FRAME IS CAPTURED            
                if status:
                    # CONVERT TO RGB COLOUR
                    cameraFrame = cvtColor(frame, COLOR_BGR2RGB)
                    # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
                    height, width, _ = cameraFrame.shape
                    # GENERATE QIMAGE
                    cameraFrame = QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QImage.Format_RGB888)
                    # CONVERT TO PIXMAP
                    cameraFrame = QPixmap.fromImage(cameraFrame)
                    # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                    signals[index].emit(cameraFrame)
                
                else:
                    signals[index].emit(QPixmap("graphics/no_signal.png"))
            
            #QThread.msleep(round(1000/24))

    def exit(self):
        print("EXIT")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VIEW()
    sys.exit(app.exec_())