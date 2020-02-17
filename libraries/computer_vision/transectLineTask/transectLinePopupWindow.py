import sys
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QGridLayout, QPushButton, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage, QFont

class VIEW(QWidget):
    def __init__(self):
        super(VIEW, self).__init__()
        self.setWindowTitle("Transect Line Task Popup")
        self.mosaicTask = TRANSECT_LINE_POPUP_WINDOW(self)
        self.show()

class TRANSECT_LINE_POPUP_WINDOW(QWidget):
    """
    PURPOSE

    Popup windows to complete the computer vision transect line task. 
    """
    def __init__(self, viewWidget):
        QWidget.__init__(self) 
        self.layout = QGridLayout()
        initiateButton = QPushButton("Start")
        self.layout.addWidget(initiateButton)
        viewWidget.setLayout(self.layout)

    def processImage(self, frame):
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