from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QLineEdit, QSpinBox, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot

class ANALOG_CAMERAS(QObject):
    """
    PURPOSE

    Contains all the functions to control which analogue cameras are displayed through the DVR, and subsequently to the RTSP stream.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM

    # DATABASE
    quantity = 0 
    labelList = []                  
    defaultCameras = [1 ,2 ,3 ,4]
    defaultMenus = []
    selectedCameras = [1 ,2 ,3 ,4]
    selectedMenus = []

    def __init__(self, *, controlLayout = None, configLayout = None):
        """
        PURPOSE

        Class constructor.
        Calls layout setup functions.

        INPUT

        - controlLayout = layout widget located on the control panel tab to add widgets to.
        - controlLayout = layout widget located on the configuration tab to add widgets to.
        - style = pointer to the style library to access stylesheets.

        RETURNS

        NONE
        """
        QObject.__init__(self)
        
        # CREATE THRUSTER WIDGETS ON THE CONTROL PANEL AND CONFIGURATION TABS
        self.controlLayout = controlLayout
        self.configLayout = configLayout

        # INITIAL LAYOUT SETUP
        if configLayout != None and controlLayout != None:
            self.setupConfigLayout()
            self.setupControlLayout()

    def setup(self):
        """
        PURPOSE

        Adds specific number of sensors to the GUI.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        cameraNumber = self.quantity

        self.cameraNumber.setValue(cameraNumber)

        # ADD DESIRED NUMBER OF CAMERAS
        for i in range(cameraNumber):
            self.addCamera()

        # SET DEFAULT CAMERAS
        self.updateDefaultMenus()
        self.updateSelectedMenus()

    def addCamera(self):
        """
        PURPOSE

        Adds a single analogue camera to the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.addConfigCamera()

    def removeCamera(self):
        """
        PURPOSE

        Removes a single analogue camera from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.removeConfigCamera()

    def reset(self):
        """
        PURPOSE

        Resets the analog cameras to default configuration.

        INPUT

        NONE
    
        RETURNS

        NONE
        """
        for i in range(self.quantity):
            self.removeCamera()

        self.quantity = 0 
        self.labelList = []                  
        self.defaultCameras = [0 ,1 ,2 ,3]  
        self.selectedCameras = [0 ,1 ,2 ,3]

    #########################
    ### CONTROL PANEL TAB ###
    #########################
    def setupControlLayout(self):
        """
        PURPOSE

        Builds a layout on the control panel tab to add widgets to.

        INPUT

        NONE

        RETURNS

        NONE
        """
        parentLayout = QGridLayout()
        
        # CAMERA FEED MENUS
        for i in range(4):
            label = QLabel("Feed {}".format(i + 1))
            label.setAlignment(Qt.AlignCenter)
            menu = QComboBox()
            self.selectedMenus.append(menu)
            menu.activated.connect(lambda index, camera = i: self.changeSelectedCameras(index, camera))

            # ADD LABEL AND MENU TO VERTICAL LAYOUT
            layout = QVBoxLayout()
            layout.addWidget(label)
            layout.addWidget(menu)

            # ADD CAMERA TO 2x4 GRID ARRANGEMENT
            parentLayout.addLayout(layout, (0 if i < 2 else 1), (i if i < 2 else i - 2))

        # ADD TO GUI
        self.controlLayout.setLayout(parentLayout)

    def changeSelectedCameras(self, index, camera):
        """
        PURPOSE

        Changes the current camera feed to display.

        INPUT

        - index = menu index of the camera selected.
        - camera = the camera feed being modified.

        RETURNS

        NONE
        """
        self.selectedCameras[camera] = index

        # CHECK FOR DUPLICATES
        for i, cameraFeed in enumerate(self.selectedCameras):
            if cameraFeed == index and i != camera:
                self.selectedCameras[i] = 0
                self.updateSelectedMenus()

    def updateSelectedMenus(self):
        """
        PURPOSE
        
        Refreshes the drop down menus for the selected analogue cameras.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for i, menu in enumerate(self.selectedMenus):
            menu.clear()
            menu.addItem("None")
            menu.addItems(self.labelList)
            menu.setCurrentIndex(self.selectedCameras[i])

    #########################
    ### CONFIGURATION TAB ###
    #########################
    def setupConfigLayout(self):
        """
        PURPOSE

        Builds a layout on the configuation tab to add widgets to.

        INPUT

        NONE

        RETURNS

        NONE
        """
        parentLayout = QVBoxLayout()
        
        # WIDGETS TO CHANGE CAMERA SETTINGS
        settingsLayout = QFormLayout()
        self.cameraNumber = QSpinBox()
        self.cameraNumber.setMaximum(10)
        settingsLayout.addRow(QLabel("Quantity"), self.cameraNumber)
        
        # DEFAULT CAMERA FEED MENUS
        for i in range(4):
            label = QLabel("Default Feed {}".format(i))
            defaultMenu = QComboBox()
            self.defaultMenus.append(defaultMenu)
            defaultMenu.activated.connect(lambda index, camera = i: self.changeDefaultCameras(index, camera))
            settingsLayout.addRow(label, defaultMenu)

        # LAYOUT TO SHOW EACH CAMERAS SETTINGS
        self.configForm = QFormLayout()

        # SPACER TO PUSH ALL WIDGETS UP
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ADD CHILDREN TO PARENT LAYOUT
        parentLayout.addLayout(settingsLayout)
        parentLayout.addLayout(self.configForm)
        parentLayout.addItem(spacer)
        
        # LINK WIDGETS
        self.cameraNumber.editingFinished.connect(self.changeCamerasNumber)
        
        # ADD TO GUI
        self.configLayout.setLayout(parentLayout)
    
    def changeCamerasNumber(self):
        """
        PURPOSE

        Sets the number of analog cameras.

        INPUT

        NONE

        RETURNS

        NONE
        """
        newNumber = self.cameraNumber.value()
        oldNumber = self.configForm.rowCount()

        self.quantity = newNumber

        delta = newNumber - oldNumber

        # ADD CAMERA
        if delta > 0:
            for i in range(delta):
                self.addCamera()

        # REMOVE CAMERA
        if delta < 0:
            for i in range(-delta):
                self.removeCamera()

    def addConfigCamera(self):
        """
        PURPOSE

        Adds a single analog camera to the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # THE INDEX OF THE NEXT CAMERA
        nextCamera = self.configForm.rowCount()

        # TRY TO SET LABEL FROM CONFIG FILE
        try:
            label = self.labelList[nextCamera]

        # OTHERWISE, SET DEFAULT LABEL
        except:
            label = "Camera {}".format(nextCamera + 1)
            self.labelList.append(label)

        cameraNumber = QLabel("Camera {}".format(nextCamera + 1))
        cameraLabel = QLineEdit(label)

        # PLACE WIDGETS INSIDE LAYOUT
        layout1 = QVBoxLayout()
        layout1.addWidget(cameraNumber)
        layout2 = QVBoxLayout()
        layout2.addWidget(cameraLabel)

        # ADD LAYOUTS TO FRAMES (TO ALLOW STYLING)
        frame1 = QFrame()
        frame1.setObjectName("analog-camera-frame")
        frame1.setLayout(layout1)
        frame2 = QFrame()
        frame2.setObjectName("settings-frame")
        frame2.setLayout(layout2)

        # ADD TO CONFIGURATION TAB
        self.configForm.addRow(frame1, frame2)

        # UPDATE MENUS
        self.updateDefaultMenus()
        self.updateSelectedMenus()

        cameraLabel.textChanged.connect(lambda text, camera = nextCamera: self.changeCameraName(text, camera))

    def removeConfigCamera(self):
        """
        PURPOSE

        Removes a single analog camera from the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REMOVE CAMERA FROM CONFIG TAB
        cameraNumber = self.configForm.rowCount() - 1
        self.configForm.removeRow(cameraNumber) 
        
        # REMOVE CAMERA DATA
        del self.labelList[cameraNumber]

        # UPDATE MENUS
        self.updateDefaultMenus()
        self.updateSelectedMenus()

    def changeDefaultCameras(self, index, camera):
        """
        PURPOSE

        Changes which four cameras are shown on the feed upon program startup.

        INPUT

        - index = menu index of the camera selected.
        - camera = the camera feed being modified.

        RETURNS

        NONE
        """
        self.defaultCameras[camera] = index 

        # CHECK FOR DUPLICATES
        for i, cameraFeed in enumerate(self.defaultCameras):
            if cameraFeed == index and i != camera:
                self.defaultCameras[i] = 0
                self.updateDefaultMenus()

    def changeCameraName(self, text, camera):
        """
        PURPOSE

        Changes the label of an analog camera.

        INPUT

        - text = the new label.
        - camera = the camera the label belong to.

        RETURNS

        NONE
        """
        self.labelList[camera] = text

        # UPDATE MENUS
        self.updateDefaultMenus() 
        self.updateSelectedMenus()

    def updateDefaultMenus(self):
        """
        PURPOSE

        Refreshes the analogue camera default menus.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for i, menu in enumerate(self.defaultMenus):
            menu.clear()
            menu.addItem("None")
            menu.addItems(self.labelList)
            menu.setCurrentIndex(self.defaultCameras[i])