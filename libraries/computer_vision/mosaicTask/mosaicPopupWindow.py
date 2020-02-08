import sys
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt
from PyQt5.QtWidgets import (QScrollArea, QWidget, QLabel, QApplication, QGridLayout, QPushButton, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QFont

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
    images = [None] * 5

    def __init__(self, viewWidget):
        QWidget.__init__(self) 
        self.mainLayout = QGridLayout()
        self.scroll = QScrollArea()
        # self.scroll.setStyleSheet("""QScrollArea { background: transparent;
        #                             background: transparent; }
        #                             background: 0; }""")
        self.mainLayout.addWidget(self.scroll)
        self.layout = QGridLayout()
        self.scroll.setLayout(self.layout)
        # ADD IMAGE CAPTURE BUTTONS
        self.addWidgets()
        viewWidget.setLayout(self.mainLayout)

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
            self.images[index] = defaultView
            button = QPushButton("Capture {}".format(index + 1))
            image = QLabel()
            image.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored))
            image.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            image.setPixmap(defaultView.scaledToHeight(200))
            # ADD TO GRID LAYOUT
            self.layout.addWidget(image, (index * 2), 0)
            self.layout.addWidget(button, (index * 2) + 1, 0)
            button.clicked.connect(lambda state, index = index, buttonObject = button, imageObject = image: self.captureImage(index, buttonObject, imageObject))

        computeButton = QPushButton("Compute Mosaic")
        computeButton.setFixedHeight(80)
        computeButton.setStyleSheet('background-color: #0D47A1; color: white; font-weight: bold;')
        self.layout.addWidget(computeButton, 10, 0)
        computeButton.clicked.connect(self.computeMosaic)

    def captureImage(self, index, buttonObject, imageObject):        
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
            camSize = [imageObject.size().width(),imageObject.size().height()]
            cameraFrame = QPixmap.fromImage(cameraFrame)
            # SAVE PIXMAP
            self.images[index] = cameraFrame
            cameraFrame = cameraFrame.scaled(camSize[0]*0.99, camSize[1]*0.99, Qt.KeepAspectRatio)
            # VIEW IMAGE
            imageObject.setPixmap(cameraFrame)

    def computeMosaic(self):
        self.mosaicResult = MOSAIC_RESULT(self.images[0])

    def imageResizeEvent(self):
        for image in range(5):
            widget = self.layout.itemAt(image*2).widget()
            cameraPixmap = self.images[image]
            widgetSize = [widget.size().width(), widget.height()]
            adjustedImage = cameraPixmap.scaled(widgetSize[0], widgetSize[1], Qt.KeepAspectRatio)
            widget.setPixmap(adjustedImage)

class MOSAIC_RESULT(QWidget):
    def __init__(self, image):
        QWidget.__init__(self)
        imageShow = QLabel("Mosaic Result")
        imageShow.setPixmap(image.scaledToHeight(1000, Qt.SmoothTransformation))
        mainLayout = QGridLayout()
        mainLayout.addWidget(imageShow)
        self.setLayout(mainLayout)
        self.show() 

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