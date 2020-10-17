import sys, os

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimeLine
from PyQt5.QtWidgets import (QSpacerItem, QMessageBox, QInputDialog, QSplashScreen, QProgressBar, QScrollArea, QGroupBox, QHBoxLayout, QFrame, QWidget, QStyleFactory, QMainWindow, 
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
    saveProfileSignal = pyqtSignal(str)

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
        self.setWindowTitle("Profile Selector")
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
        self.resize(600,400)

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
        parentLayout.setSpacing(30)

        # LOGO
        logoLayout = QVBoxLayout()
        logo = QLabel()
        logo.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        avalonPixmap = QPixmap('graphics/thumbnail.png')
        avalonPixmap = avalonPixmap.scaledToWidth(200, Qt.SmoothTransformation)
        logo.setPixmap(avalonPixmap)
        label = QLabel("ROV\nCONTROL\nPROGRAM")
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label.setStyleSheet("font: 20pt;")
        author = QLabel("Developed by:\nBenjamin Griffiths")
        logoLayout.addWidget(logo)
        logoLayout.addWidget(label)
        logoLayout.addWidget(author)

        # PROFILE SELECTION
        container = QGroupBox()
        layout = QVBoxLayout()
        title = QLabel("Select pilot profile:")
        title.setStyleSheet("font: 20pt;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(title)
        layout.addWidget(scroll)
        addProfileButton = QPushButton("Add New")
        addProfileButton.setObjectName("blue-button")
        layout.addWidget(addProfileButton)
        
        # SETUP SCROLL AREA
        scrollWidget = QWidget()
        scroll.setWidget(scrollWidget)
        
        # LAYOUT INSIDE SCROLL WIDGET
        scrollLayout = QVBoxLayout()
        scrollWidget.setLayout(scrollLayout)

        # LAYOUT FOR PROFILE BUTTONS
        self.profileLayout = QVBoxLayout()

        # SPACER TO PUSH ALL BUTTON TO TOP OF SCROLL WIDGET
        vSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        scrollLayout.addLayout(self.profileLayout)
        scrollLayout.addItem(vSpacer)
        
        container.setLayout(layout)

        # ADD WIDGETS TO GRID LAYOUT
        parentLayout.addLayout(logoLayout)
        parentLayout.addWidget(container)

        self.setLayout(parentLayout)

        # LINK WIDGETS
        addProfileButton.clicked.connect(self.addNewProfile)

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
        renameButton.setObjectName("green-button")
        # MAKE BUTTON CIRCULAR
        renameButton.setFixedSize(renameButton.sizeHint().height(), renameButton.sizeHint().height())
        renameButton.setIcon(QIcon("./graphics/rename-icon.png"))
        renameButton.setIconSize(QSize(20,20))
        
        # DELETE PROFILE
        deleteButton = QPushButton()
        deleteButton.setObjectName("red-button")
        # MAKE BUTTON CIRCULAR
        deleteButton.setFixedSize(deleteButton.sizeHint().height(), deleteButton.sizeHint().height())
        deleteButton.setIcon(QIcon("./graphics/delete-icon.png"))
        deleteButton.setIconSize(QSize(20,20))

        layout.addWidget(profileButton)
        layout.addWidget(renameButton)
        layout.addWidget(deleteButton)

        # LINK WIDGETS
        profileButton.clicked.connect(lambda state, directory = directory: self.loadProfile(directory))
        renameButton.clicked.connect(lambda state, directory = directory: self.renameProfile(directory))
        deleteButton.clicked.connect(lambda state, directory = directory: self.deleteProfile(directory))

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

    def addNewProfile(self):
        """
        PURPOSE

        Lets user create a new pilot profile.
        A dialog box appears for the user to enter the profile name.

        INPUT

        NONE

        RETURNS

        NONE
        """
        renameDialog = QInputDialog()
        newName, state = renameDialog.getText(self, "Rename Profile", "Enter new profile name:")

        # CHANGE FILE NAME
        if state:
            if os.path.exists("./config/" + newName + ".xml"):

                deleteMsg = QMessageBox()
                result = deleteMsg.question(self,"Profile Overwrite", "This profile name already exists, would you like to overwrite it?", deleteMsg.Yes | deleteMsg.No)

                # OVERWRITE FILE
                if result == QMessageBox.Yes:
                    self.saveProfileSignal.emit("./config/" + newName + ".xml")

                # TRY AGAIN
                else:
                    self.addNewProfile()

            else:
                self.saveProfileSignal.emit("./config/" + newName + ".xml")

            self.findProfiles()
                
    def renameProfile(self, directoryToRename):
        """
        PURPOSE
        
        Lets user rename a certain pilot profile.
        Message box launches for user to enter new file name.

        INPUT

        - directoryToRename = the directory of the configuration XML file to rename.

        RETURNS

        NONE
        """
        renameDialog = QInputDialog()
        newName, state = renameDialog.getText(self, "Rename Profile", "Enter new profile name:")

        # CHANGE FILE NAME
        if state:
            if os.path.exists("./config/" + directoryToRename):
                os.rename("./config/" + directoryToRename, "./config/" + newName + ".xml")

            self.findProfiles()

    def deleteProfile(self, directoryToDelete):
        """
        PURPOSE

        Lets the user delete a profile.
        A Message box launches to check if the user wants to proceed or not.

        INPUT

        - directoryToDelete = the directory of the configuration XML file to delete.

        RETURNS

        NONE
        """
        deleteMsg = QMessageBox()
        result = deleteMsg.question(self,"Delete Profile", "Are you sure you want to delete this user profile?", deleteMsg.Yes | deleteMsg.No)

        # DELETE FILE
        if result == QMessageBox.Yes:
            if os.path.exists("./config/" + directoryToDelete):
                os.remove("./config/" + directoryToDelete)

            self.findProfiles()

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