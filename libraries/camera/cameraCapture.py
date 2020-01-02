import sys
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QImage, QFont, QColor, QPalette

class VIEW(QWidget):
    def __init__(self):
        super(VIEW, self).__init__()
        self.setWindowTitle("Camera Capture View")
        layout = QGridLayout()
        self.view = QLabel("Camera View")
        layout.addWidget(self.view, 0, 0)
        self.setLayout(layout)
        # INITIATE CAMERA
        camThread = CAMERA_CAPTURE(0)
        camThread.cameraNewFrameSignal.connect(self.updateCameraFeed)
        camThread.start()
        self.show()
        
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
        pixmap = frame.scaledToHeight(600)
        self.view.setPixmap(pixmap)
    
class CAMERA_CAPTURE(QThread):
    # CREATE SIGNAL
    cameraNewFrameSignal = pyqtSignal(QPixmap)

    def __init__(self, channel):
        QThread.__init__(self)
        # CAMERA FEED SOURCE
        self.channel = channel
    
    def run(self):
        # INITIATE CAMERA
        cameraFeed = VideoCapture(self.channel, CAP_DSHOW)
        cameraFeed.set(CAP_PROP_FRAME_WIDTH, 1920)
        cameraFeed.set(CAP_PROP_FRAME_HEIGHT, 1080)

        while True:    
            # CAPTURE FRAME
            status, frame = cameraFeed.read()
        
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
                self.cameraNewFrameSignal.emit(cameraFrame)
            
            else:
                self.cameraNewFrameSignal.emit(QImage("graphics/no_signal.png"))

    def exit(self):
        print("EXIT")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VIEW()
    sys.exit(app.exec_())