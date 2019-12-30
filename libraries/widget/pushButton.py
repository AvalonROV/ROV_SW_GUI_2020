import sys
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimeLine
from PyQt5.QtWidgets import (QGroupBox, QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QImage, QFont, QColor, QPalette, QPainter

class VIEW(QWidget):
    def __init__(self , parent = None):
        super(VIEW, self).__init__()    
        self.setupGui()
    
    def setupGui(self):   
        self.resize(800,600)
        self.setWindowTitle('Custom Button')
        layout = QHBoxLayout()
        button = PUSH_BUTTON("Test Button")
        button.setFixedHeight(50)
        layout.addWidget(button)
        self.setLayout(layout)
        self.show()

class PUSH_BUTTON(QPushButton):
    def __init__(self, initialText):
        QPushButton.__init__(self)
        self.setText(initialText)
        #self.setStyleSheet("border-radius: 3px")
                                
    def setButtonStyle(self, state):
        # ON STYLE
        if state:
            pass


        # OFF STYLE
        else:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = VIEW()
    sys.exit(app.exec_())