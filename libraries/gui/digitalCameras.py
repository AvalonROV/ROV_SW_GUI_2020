from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QLineEdit, QSpinBox, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import QIcon

class DIGITAL_CAMERAS(QObject):
    """
    PURPOSE

    Contains the functions to control the digital camera feeds.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM
    cameraEnableSignal = pyqtSignal(bool, int)
    cameraResolutionSignal = pyqtSignal(int, int, int)
    cameraEditSignal = pyqtSignal()
    cameraChangeAddress = pyqtSignal(int, str)

    # DATABASE
    feedQuantity = 4
    quantity = 0 
    labelList = []
    addressList = []
    defaultCameras = [0, 0, 0, 0]
    defaultMenus = []
    selectedCameras = [0, 0, 0, 0]
    selectedMenus = []
    resolutions = [[1920, 1080], [1600, 900], [1280, 720], [1024, 576], [640, 360], [256, 144]]
    resolutionMenus = []
    selectedResolutions = [4, 4, 4, 4]
    feedStatus = []

    def __init__(self, *, controlLayout = None, configLayout = None):
        """
        PURPOSE

        Class constructor.
        Calls setup functions.

        INPUT

        - controlLayout = layout widget located on the control panel tab to add widgets to.
        - controlLayout = layout widget located on the configuration tab to add widgets to.

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

        Adds specific number of digital cameras to the GUI.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        cameraNumber = self.quantity

        self.cameraNumber.setValue(cameraNumber)

        self.selectedCameras = self.defaultCameras.copy()
    
        # ADD DESIRED NUMBER OF CAMERAS
        for i in range(cameraNumber):
            self.addCamera()

        # SET DEFAULT CAMERAS
        self.updateDefaultMenus()
        self.updateSelectedMenus()

        # SET THE DEFAULT CAMERA ADDRESSES
        self.setCameraAddresses()

        # SET CAMERA FEED RESOLUTIONS
        self.updateResolutionMenus()
        for i, res in enumerate(self.selectedResolutions):
            self.changeResolution(res, i)
        
    def addCamera(self):
        """
        PURPOSE
        
        Adds a single digital camera to the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.addConfigCamera()

    def removeCamera(self):
        """
        PURPOSE
        
        Removes a single digital camera from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.removeConfigCamera()

    def setCameraAddresses(self):
        """
        PURPOSE

        Sets the source address of each digital camera.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for i, camera in enumerate(self.selectedCameras):
            try:
                # NONE SELECTED
                if camera == 0:
                    address = ""
                else:
                    address = self.addressList[camera - 1]
                
                # EMIT SIGNAL TO MAIN PROGRAM TO CHANGE CAMERA ADDRESS
                self.cameraChangeAddress.emit(i, address)
            except:
                pass

    def addressConverter(self, address):
        """
        PURPOSE

        Converts string to int for the USB cameras.

        INPUT

        - address = string of the camera feed source address.

        RETURNS

        - cameraAddress = int source address for USB camera, string source address for RTSP camera.
        """
        # USB CAMERA
        try:
            cameraAddress = int(address)
        # RTSP CAMERA
        except:
            cameraAddress = address

        return cameraAddress

    def reset(self):
        """
        PURPOSE

        Resets the digital camera configuration to default settings.

        INPUT

        NONE
    
        RETURNS

        NONE
        """
        for i in range(self.quantity):
            self.removeCamera()
        
        self.feedQuantity = 4
        self.quantity = 0 
        self.labelList = []
        self.addressList = []
        self.defaultCameras = [0, 0, 0, 0]
        self.selectedCameras = [0, 0, 0, 0]
        self.resolutions = [[1920, 1080], [1600, 900], [1280, 720], [1024, 576], [640, 360], [256, 144]]
        self.selectedResolutions = [4, 4, 4, 4]

        # UPDATE WIDGETS
        self.cameraNumber.setValue(self.quantity)
        self.updateDefaultMenus()
        self.updateSelectedMenus()

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
        parentLayout = QFormLayout()
        parentLayout.setLabelAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label1 = QLabel("Enable/Disable")
        label2 = QLabel("Resolution")
        label2.setAlignment(Qt.AlignCenter)
        parentLayout.addRow(label1, label2)

        # PRIMARY AND SECONDARY CAMERA ICONS FOR EACH BUTTON
        texts = ["1st", "2nd-1", "2nd-2", "2nd-3"]

        for feed, text in enumerate(texts):
            # ENABLE/DISABLE BUTTON
            button = QPushButton()
            button.setCheckable(True)
            button.setChecked(True)
            button.setText(text)
            button.setIcon(QIcon("./graphics/white_camera.png"))
            button.setIconSize(QSize(15,15))

            self.feedStatus.append(True)

            # CHANGE RESOLUTION MENU
            menu = QComboBox()
            formattedRes = [str(item[0]) + "x" + str(item[1]) for item in self.resolutions]
            menu.addItems(formattedRes)
            self.resolutionMenus.append(menu)

            # GET FRAME RESOLUTION FROM CONFIG FILE
            index = self.selectedResolutions[feed]

            menu.setCurrentIndex(index)

            # LINK WIDGETS
            button.clicked.connect(lambda state, feed = feed: self.toggleCameraFeed(state, feed))
            menu.activated.connect(lambda index, feed = feed: self.changeResolution(index, feed))

            # ADD BUTTON AND MENU TO FORM LAYOUT
            parentLayout.addRow(button, menu)

        # ADD TO GUI
        self.controlLayout.setLayout(parentLayout)

    def toggleCameraFeed(self, status, feed):
        """
        PURPOSE

        Emits signal to main program to enable/disable a camera feed.

        INPUT

        - status = state of the button.
        - feed = the camera feed to toggle (1,2,3,4).

        RETURNS

        NONE
        """
        self.feedStatus[feed] = status 
        self.cameraEnableSignal.emit(status, feed)

    def toggleAllFeeds(self, feedStatus):
        """
        PURPOSE

        Enables/disables all camera feeds when the user switches between control panel and configutaion tab.

        INPUT

        - state = True to turn on, False to turn off.

        RETURNS

        NONE
        """
        # DISABLE ALL FEEDS
        if feedStatus == False:
            for i, state in enumerate(self.feedStatus):
                self.cameraEnableSignal.emit(False, i)

        # ENABLE FEEDS THAT WERE PREVIOUSLY ENABLED
        if feedStatus == True:
            for i, state in enumerate(self.feedStatus):
                self.cameraEnableSignal.emit(state, i)
        
    def changeResolution(self, menuIndex, feed):
        """
        PURPOSE

        User selects camera feed display resolution from drop down menu.

        INPUT

        - menuIndex = the index of the menu item selected.
        - feed = the camera feed being modified.

        RETURNS

        NONE
        """
        self.selectedResolutions[feed] = menuIndex
        width = self.resolutions[menuIndex][0]
        height = self.resolutions[menuIndex][1]

        self.cameraResolutionSignal.emit(feed, width, height)

    def updateResolutionMenus(self):
        """
        PURPOSE

        Updates the resolutions menus with the correct indices.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for i, menu in enumerate(self.resolutionMenus):
            menu.setCurrentIndex(self.selectedResolutions[i])
        
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

    def updateSelectedMenus(self):
        """
        PURPOSE

        Refreshes the selected digital camera menus.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # UPDATE MAIN PROGRAM 
        self.cameraEditSignal.emit()
        
    #########################
    ### CONFIGURATION TAB ###
    #########################
    def setupConfigLayout(self):
        """
        PURPOSE

        Builts a layout on the configuration tab to add widgets to.

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
        for i in range(self.feedQuantity):
            label = QLabel("Default Feed {}".format(i))
            defaultMenu = QComboBox()
            self.defaultMenus.append(defaultMenu)
            defaultMenu.activated.connect(lambda index, camera = i: self.changeDefaultCameras(index, camera))
            settingsLayout.addRow(label, defaultMenu)

        # LAYOUT TO SHOW CAMERA SETTINGS
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

        Sets the number of digital cameras based on the user entered value in the configuration tab.

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

        Adds a single digital camera to the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # THE INDEX OF THE NEXT CAMERA
        nextCamera = self.configForm.rowCount()

        # GET LABEL AND ADDRESS FROM CONFIG FILE
        try:
            label = self.labelList[nextCamera]
            address = self.addressList[nextCamera]

        # OTHERWISE, SET DEFAULT LABEL AND ADDRESS
        except:
            label = "Camera {}".format(nextCamera + 1)
            self.labelList.append(label)

            address = ""
            self.addressList.append(address)

        # CREATE WIDGETS TO CHANGE CAMERA LABEL AND ADDRESS
        cameraNumber = QLabel("Camera {}".format(nextCamera + 1))
        cameraLabel = QLineEdit(label)
        label1 = QLabel("Name")
        cameraAddress = QLineEdit(address)
        label2 = QLabel("Address")

        # PLACE WIDGETS INSIDE LAYOUT
        layout1 = QVBoxLayout()
        layout1.addWidget(cameraNumber)
        layout2 = QFormLayout()
        layout2.addRow(label1, cameraLabel)
        layout2.addRow(label2, cameraAddress)

        # ADD LAYOUTS TO FRAMES (TO ALLOW STYLING)
        frame1 = QFrame()
        frame1.setObjectName("digital-camera-frame")
        frame1.setLayout(layout1)
        frame2 = QFrame()
        frame2.setObjectName("settings-frame")
        frame2.setLayout(layout2)

        # ADD TO CONFIGURATION TAB
        self.configForm.addRow(frame1, frame2)

        # UPDATE MENUS
        self.updateDefaultMenus()
        self.updateSelectedMenus()

        # LINK WIDGETS
        cameraLabel.textEdited.connect(lambda text, camera = nextCamera: self.changeCameraName(text, camera))
        cameraAddress.editingFinished.connect(lambda lineEditObject = cameraAddress, camera = nextCamera: self.changeCameraAddress(lineEditObject, camera))

    def removeConfigCamera(self):
        """
        PURPOSE

        Removes a single digital camera from the configuration tab.

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
        del self.addressList[cameraNumber]

        # UPDATE MENUS
        self.updateDefaultMenus()
        self.updateSelectedMenus()

    def changeDefaultCameras(self, index, camera):
        """
        PURPOSE

        Changes the default cameras to be displayed on each digital camera feed.

        INPUT

        - index = menu index selected.
        - camera = the camera feed being modified (0,1,2).

        RETURN

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

        Changes the label of a digital camera.

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

    def changeCameraAddress(self, lineEditObject, camera):
        """
        PURPOSE

        Change the source address for a camera feed.

        INPUT

        - lineEditObject = pointer to the line edit widget.
        - camera = the camera which is having its address is being changed.

        RETURNS

        NONE
        """
        address = lineEditObject.text()

        if address == None:
            address = ""

        for index, item in enumerate(self.addressList):
            if item == address:
                self.addressList[index] = ""
        
        self.addressList[camera] = address

        self.updateAddressLabels()

        # APPLY ADDRESS CHANGE
        self.setCameraAddresses()

    def updateAddressLabels(self):
        """
        PURPOSE

        Updates the digital camera label text fields.

        INPUT

        NONE

        OUTPUT

        NONE
        """
        quantity = self.configForm.rowCount()

        for i in range(quantity):
            layout = self.configForm.itemAt((i * 2) + 1).widget()
            layout = layout.layout()
            widget = layout.itemAt(3).widget()
            widget.setText(self.addressList[i])

    def updateDefaultMenus(self):
        """
        PURPOSE

        Refreshes the default digital camera menus.

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