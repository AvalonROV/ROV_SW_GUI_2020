import sys
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt
from PyQt5.QtWidgets import (QSpacerItem, QScrollArea, QWidget, QLabel, QApplication, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QSizePolicy)
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
    imageWidgets = []

    def __init__(self, controlLayout = None):
        QWidget.__init__(self) 

        self.controlLayout = controlLayout

        if controlLayout != None:
            self.setupControlLayout()

    def setupControlLayout(self):
        """
        PURPOSE

        Add a label to paint pixmaps to, and a button for each side of the mosaic.

        INPUT

        NONE

        RETURNS

        NONE
        """
        parentLayout = QVBoxLayout()

        for index in range(5):
            childLayout = self.addWidgets(index)
            parentLayout.addLayout(childLayout)

        # ADD FINAL BUTTON TO COMPUTE MOSAIC
        computeButton = QPushButton("Compute Mosaic")
        computeButton.setObjectName("blue-button")
        computeButton.setFixedHeight(int(computeButton.sizeHint().height() * 1.5))
        parentLayout.addWidget(computeButton)

        self.controlLayout.setLayout(parentLayout)

        # LINK WIDGETS
        computeButton.clicked.connect(self.computeMosaic)

        # CORRECT IMAGE SIZE
        self.imageResizeEvent()

    def addWidgets(self, index):
        """
        PURPOSE

        Creates an image view and capture button, and add them to a layout.

        INPUT

        - index = the side of the mosaic (0,1,2,3 etc.)

        RETURNS

        - layout = A layout containing all the widgets for that specific side.
        """
        defaultView = QPixmap('graphics/blank.png')
        self.images[index] = defaultView

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 30)

        # CREATE LABEL, IMAGE VIEW AND CAPTURE BUTTON
        label = QLabel("Side {}".format(index + 1))
        imageView = QLabel()
        imageView.setPixmap(defaultView)
        imageView.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding))
        imageView.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.imageWidgets.append(imageView)
        buttonLayout = QHBoxLayout()
        capture = QPushButton("Capture")
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttonLayout.addWidget(capture)
        buttonLayout.addItem(spacer)
        layout.addWidget(label)
        layout.addWidget(imageView, 1)
        layout.addLayout(buttonLayout)

        # LINK WIDGETS
        #button.clicked.connect(lambda state, index = index: self.captureImage(index))        

        return layout

    def computeMosaic(self):
        """
        PURPOSE

        Displays the processed image in a new window.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.mosaicResult = MOSAIC_RESULT(self.images[0])

    def imageResizeEvent(self):
        """
        PURPOSE

        Dynamically resizes each pixmap during a resize event.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for index, image in enumerate(self.imageWidgets):
            cameraPixmap = self.images[index]
            widgetSize = [image.size().width(), image.size().height()]
            adjustedImage = cameraPixmap.scaledToWidth(widgetSize[0])
            image.setPixmap(adjustedImage)

class MOSAIC_RESULT(QWidget):
    """
    PURPOSE

    External window that displays the processed iamge.
    """
    def __init__(self, image):
        """
        PURPOSE

        Class constructor.
        Creates layout and displays image.

        INPUT

        - image = the pixmap to display.

        RETURNS

        NONE
        """
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