import sys
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QImage, QFont, QColor, QPalette

class MOSAIC_POPUP_WINDOW(QWidget):
    """
    PURPOSE

    Popup windows to complete the computer vision mosaic task. 
    Each side of the object can be captured, then an openCV algorithm will stitch them together.
    """
    def __init__(self, Object1):
        QWidget.__init__(self) 
        # LOAD UI FILE
        uic.loadUi('mosaicPopup.ui',self)
        # KEEPS POPUP ON TOP OF MAIN PROGRAM
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        # FIND SCREEN SIZE
        self.sizeObject = QDesktopWidget().screenGeometry(-1)
        self.screenHeight = self.sizeObject.height()
        self.screenWidth = self.sizeObject.width()

        self.data = Object1
        # ADD IMAGE CAPTURE BUTTONS
        self.addWidgets()
        self.show()

    def addWidgets(self):
        """
        PURPOSE

        Adds the image view and capture button for each side of the object.

        INPUT

        NONE

        RETURNS

        NONE
        """
        defaultView = QPixmap('..../graphics/blank.png')
        # ADD CAMERA VIEW AND CAPTURE BUTTON FOR EACH SIDE OF THE UNDERWATER OBJECT
        for index in range(5):
            button = QPushButton("Capture {}".format(index + 1))
            image = QLabel()
            image.setPixmap(defaultView.scaledToHeight(0.1 * self.screenHeight))
            # ADD TO GRID LAYOUT
            self.mosaic_grid_layout.addWidget(image, index, 0)
            self.mosaic_grid_layout.addWidget(button, index, 1)
            button.clicked.connect(lambda _, index = index, buttonObject = button, imageObject = image: self.captureImage(index, buttonObject, imageObject))

        self.mosaic_grid_layout.setColumnStretch(3,1)
        self.mosaic_result.setPixmap(defaultView.scaledToHeight(0.5 * self.screenHeight))

    def captureImage(self, index, buttonObject, imageObject):
        #cameraFrame = QPixmap.fromImage(self.data.primaryCameraImage).scaledToHeight(200)
        #imageObject.setPixmap(cameraFrame)
        
        channel = 0

        # INITIATE PRIMARY CAMERA
        cameraFeed = VideoCapture(channel, CAP_DSHOW)
        cameraFeed.set(CAP_PROP_FRAME_WIDTH, 1280)
        cameraFeed.set(CAP_PROP_FRAME_HEIGHT, 720)
        
        # CAPTURE FRAME
        ret, frame = cameraFeed.read()
    
        # IF FRAME IS SUCCESSFULLY CAPTURED            
        if ret:
            # CONVERT TO RGB COLOUR
            cameraFrame = cvtColor(frame, COLOR_BGR2RGB)
            # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
            height, width, _ = cameraFrame.shape
            # CONVERT TO QIMAGE
            cameraFrame = QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QImage.Format_RGB888)
            # CONVERT TO PIXMAP
            cameraFrame = QPixmap.fromImage(cameraFrame).scaledToHeight(0.1 * self.screenHeight)
            # VIEW IMAGE
            imageObject.setPixmap(cameraFrame)

def guiInitiate(): 
    """
    PURPOSE

    Launches program and selects font.

    INPUTS

    NONE

    RETURNS

    NONE
    """
    # CREATE QAPPLICATION INSTANCE (PASS SYS.ARGV TO ALLOW COMMAND LINE ARGUMENTS)
    app = QApplication(sys.argv)
    app.setFont(QFont("Bahnschrift Light", 10))
    app.setStyle("Fusion")
    MOSAIC_POPUP_WINDOW(app)
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()