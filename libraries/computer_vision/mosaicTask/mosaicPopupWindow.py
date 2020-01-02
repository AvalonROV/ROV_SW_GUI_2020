import sys
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt
from PyQt5.QtWidgets import (QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QImage, QFont, QColor, QPalette

class VIEW(QWidget):
    def __init__(self):
        super(VIEW, self).__init__()
        self.setWindowTitle("Mosaic Task Popup")
        self.mosaicTask = MOSAIC_POPUP_WINDOW(self)
        self.show()

class MOSAIC_POPUP_WINDOW(QWidget):
    """
    PURPOSE

    Popup windows to complete the computer vision mosaic task. 
    Each side of the object can be captured, then an openCV algorithm will stitch them together.
    """
    def __init__(self, viewWidget):
        QWidget.__init__(self) 
        # LOAD UI FILE
        uic.loadUi('libraries/computer_vision/mosaicTask/mosaicPopup.ui',self)
        
        # ADD IMAGE CAPTURE BUTTONS
        self.addWidgets()

        layout = QGridLayout()
        layout.addWidget(self)
        viewWidget.setLayout(layout)

    def addWidgets(self):
        """
        PURPOSE

        Adds the image view and capture button for each side of the object.

        INPUT

        NONE

        RETURNS

        NONE
        """
        defaultView = QPixmap('graphics/blank.png')
        # ADD CAMERA VIEW AND CAPTURE BUTTON FOR EACH SIDE OF THE UNDERWATER OBJECT
        for index in range(5):
            button = QPushButton("Capture {}".format(index + 1))
            image = QLabel()
            image.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            image.setPixmap(defaultView.scaledToHeight(10))
            # ADD TO GRID LAYOUT
            self.mosaic_grid_layout.addWidget(image, (index * 2), 0)
            self.mosaic_grid_layout.addWidget(button, (index * 2) + 1, 0)
            button.clicked.connect(lambda _, index = index, buttonObject = button, imageObject = image: self.captureImage(index, buttonObject, imageObject))

        computeButton = QPushButton("Compute Mosaic")
        self.mosaic_grid_layout.addWidget(computeButton, 10, 0)
        computeButton.clicked.connect(self.computeMosaic)

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
            cameraFrame = QPixmap.fromImage(cameraFrame).scaledToHeight(10)
            # VIEW IMAGE
            imageObject.setPixmap(cameraFrame)

    def computeMosaic(self):
        pass

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
    ex = VIEW()
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()