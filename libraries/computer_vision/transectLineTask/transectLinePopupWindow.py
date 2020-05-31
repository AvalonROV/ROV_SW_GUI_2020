import sys
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from PyQt5.QtCore import QSize, Qt, pyqtSlot, pyqtSignal, pyqtBoundSignal
from PyQt5.QtWidgets import (QWidget, QApplication, QGridLayout, QPushButton, QLineEdit, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage, QFont

from libraries.computer_vision.transectLineTask.transectLineAlgorithm_v1 import TRANSECT_LINE_TASK

class TRANSECT_LINE_POPUP_WINDOW(QWidget):
    """
    PURPOSE

    Popup windows to complete the computer vision transect line task. 
    """
    # SIGNAL TO SEND DATA BACK TO MAIN PROGRAM
    transmitData = pyqtSignal()

    def __init__(self, viewWidget, cameraFeed):
        """
        PURPOSE

        Constructor for the transect line popup window.

        INPUT

        - viewWidget = the widget to diplay the widget on.
        - cameraFeed = the camera capture object to send the processing algorithm to.

        RETURNS

        NONE
        """
        QWidget.__init__(self) 
       
        # INITIATE ALGORITHM
        self.transectLineTask = TRANSECT_LINE_TASK()

        # LINK ALGORITHM DATA SIGNAL TO SLOT
        self.transectLineTask.transmitData.connect(self.dataReceived)

        # CAMERA THREAD TO SEND ALGORITHM TO
        self.cameraFeed = cameraFeed

        # START TASK BUTTON
        initiateButton = QPushButton("Start")
        initiateButton.setCheckable(True)
        initiateButton.clicked.connect(lambda status, buttonObject = initiateButton: self.taskStart(status, buttonObject))

        self.steeringData = QLineEdit()

        self.layout = QGridLayout()
        self.layout.addWidget(initiateButton,0,0)
        self.layout.addWidget(self.steeringData,1,0)
        
        viewWidget.setLayout(self.layout)

    def taskStart(self, status, buttonObject):
        """
        PURPOSE

        Starts the machine vision processing algorithm.

        INPUT

        - status = state of the start button.
        - buttonObject = points to the button widget.

        RETURNS

        NONE
        """
        if status:
            self.cameraFeed.processImage(self.transectLineTask)

        else:
            self.cameraFeed.stopProcessing()

    @pyqtSlot(str)
    def dataReceived(self, data):
        """
        PURPOSE

        Receives data from the processing algorithm.
        This data can be displayed on the GUI and further processed to control ROV functions.

        INPUT

        - data = the data received by the processing algorithm.

        RETURNS

        NONE
        """
        self.steeringData.setText(data)

        
