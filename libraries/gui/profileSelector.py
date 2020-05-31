import sys, os

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimeLine
from PyQt5.QtWidgets import (QSplashScreen, QProgressBar, QScrollArea, QGroupBox, QHBoxLayout, QFrame, QWidget, QStyleFactory, QMainWindow, 
                                QApplication, QComboBox, QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QVBoxLayout, QLabel, QSlider, 
                                QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, QFileDialog, QGraphicsDropShadowEffect, QShortcut)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QKeyEvent, QKeySequence, QIcon, QFont, QColor, QPalette, QPainter

class PROFILE_SELECTOR(QWidget):
    """
    PURPOSE

    A popup window that lets the user select a pilot profile.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM
    loadProfileSignal = pyqtSignal(str)

    def __init__(self):
        """
        PURPOSE

        Class constructor.

        INPUT

        NONE

        RETURNS

        NONE
        """
        QWidget.__init__(self)
        self.setupLayout()

    def showPopup(self):
        """
        PURPOSE

        Launches the popup window.

        INPUT

        NONE

        OUTPUT

        NONE
        """
        # FIND ALL AVAILABLE PROFILES AND ADD TO LIST
        self.findProfiles()
        
        # LAUNCH WINDOW
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.show()
        self.resize(600,300)

    def setupLayout(self):
        """
        PURPOSE

        Creates widgets for the popup window.

        INPUT

        NONE

        RETURNS

        NONE
        """
        parentLayout = QHBoxLayout()

        # LOGO
        logo = QLabel()
        avalonPixmap = QPixmap('graphics/thumbnail.png')
        avalonPixmap = avalonPixmap.scaledToWidth(200, Qt.SmoothTransformation)
        logo.setPixmap(avalonPixmap)

        # PROFILE SELECTION
        layout = QVBoxLayout()
        title = QLabel("Select pilot profile:")
        title.setStyleSheet("font: 20pt;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(title)
        layout.addWidget(scroll)
        
        scrollWidget = QWidget()
        self.profileLayout = QVBoxLayout()
        scrollWidget.setLayout(self.profileLayout)
        scroll.setWidget(scrollWidget)

        # ADD NEW PROFILE
        addProfileButton = QPushButton("Add New")
        layout.addWidget(addProfileButton)

        # ADD WIDGETS TO GRID LAYOUT
        parentLayout.addWidget(logo)
        parentLayout.addLayout(layout)

        self.setLayout(parentLayout)

    def findProfiles(self):
        """
        PURPOSE

        Searches config directory for all available XML files.
        A button for each profile is added to the list.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CLEAR CURRENT LIST
        self.clearList()

        profileDirectory = []
        profileName = []

        for file in os.listdir("./config"):
            profileDirectory.append(file)

            # REMOVE FILE EXTENSION FROM FILE NAME
            nameSplit = os.path.splitext(file)
            name = nameSplit[0]
            profileName.append(name)

            profileButtons = self.createProfileButton(file, name)
            self.profileLayout.addLayout(profileButtons)

    def clearList(self):
        """
        PURPOSE

        Clears all the pilot profiles from the list.
        """
        while self.profileLayout.count() > 0:
            childLayout = self.profileLayout.takeAt(0)
            
            # CLEAR ALL WIDGETS IN LAYOUT
            while childLayout.count() > 0:
                widget = childLayout.takeAt(0)
                widget.widget().deleteLater()

            childLayout.layout().deleteLater()

    def createProfileButton(self, directory, name):
        """
        PURPOSE

        Create a button that opens a specific configuration XML file.

        INPUT

        - directory = directory of the XML configuration file.
        - name = name of the file (file name with extension removed).

        RETURNS

        NONE
        """
        layout = QHBoxLayout()
        profileButton = QPushButton(name)

        # RENAME PROFILE
        renameButton = QPushButton()
        renameButton.setObjectName("rename-button")
        renameButton.setFixedSize(30, 30)
        renameButton.setIcon(QIcon("./graphics/rename-icon.png"))
        renameButton.setIconSize(QSize(20,20))
        
        
        # DELETE PROFILE
        deleteButton = QPushButton()
        deleteButton.setObjectName("delete-button")
        deleteButton.setFixedSize(30, 30)
        deleteButton.setIcon(QIcon("./graphics/delete-icon.png"))
        deleteButton.setIconSize(QSize(20,20))

        layout.addWidget(profileButton)
        layout.addWidget(renameButton)
        layout.addWidget(deleteButton)

        # LINK WIDGETS
        profileButton.clicked.connect(lambda state, directory = directory: self.loadProfile(directory))

        return layout

    def loadProfile(self, directory):
        """
        PURPOSE

        Send signal to main program to load a specific profile.

        INPUT

        - directory = directory of the selected XML configuration file.

        RETURNS

        NONE
        """
        self.loadProfileSignal.emit(directory)
        self.closeWindow()

    def closeWindow(self):
        """
        PURPOSE

        Terminates the popup window once a profile has been selected.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.close()

def guiInitiate(): 
    # CREATE QAPPLICATION INSTANCE (PASS SYS.ARGV TO ALLOW COMMAND LINE ARGUMENTS)
    app = QApplication(sys.argv)

    # SET PROGRAM STYLE
    app.setFont(QFont("Bahnschrift Regular", 10))
    app.setStyle("Fusion")
    
    # INITIATE MAIN GUI OBJECT
    program = PROFILE_SELECTOR(app)
    program.setWindowTitle("Profile Selector")
    
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()

