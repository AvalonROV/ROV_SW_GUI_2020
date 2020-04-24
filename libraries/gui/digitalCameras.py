from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QLineEdit, QSpinBox, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot

class DIGITAL_CAMERAS(QObject):
    """
    PURPOSE

    Contains the functions to control the digital camera feeds.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM
    cameraEditSignal = pyqtSignal()
    cameraChangeAddress = pyqtSignal(int, str)

    # DATABASE
    quantity = 3 
    labelList = []
    addressList = []
    defaultCameras = [0, 0, 0]
    defaultMenus = []
    selectedCameras = [0, 0, 0]
    selectedMenus = []

    def __init__(self, *, controlLayout = None, configLayout = None, style = None):
        """
        PURPOSE

        Class constructor.
        Calls setup functions.

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
        self.style = style

        # INITIAL LAYOUT SETUP
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

        # UPDATE MAIN PROGRAM 
        self.cameraEditSignal.emit()

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

        # UPDATE MAIN PROGRAM 
        self.cameraEditSignal.emit()

    def setCameraAddresses(self):
        """
        PURPOSE

        Sets the source address of each digital camera.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # FEED 1
        try:
            selected1 = self.selectedCameras[0]
            # NONE SELECTED
            if selected1 == 0:
                address1 = ""
            else:
                address1 = self.addressList[selected1 - 1]
            self.cameraChangeAddress.emit(0, address1)
        except:
            pass

        # FEED 2
        try:
            selected2 = self.selectedCameras[1]
            # NONE SELECTED
            if selected2 == 0:
                address2 = ""
            else:
                address2 = self.addressList[selected2 - 1]
            self.cameraChangeAddress.emit(1, address2)
        except:
            pass

        # FEED 3
        try:
            selected3 = self.selectedCameras[2]
            # NONE SELECTED
            if selected3 == 0:
                address3 = ""
            else:
                address3 = self.addressList[selected3 - 1]
            self.cameraChangeAddress.emit(2, address3)
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
        
        self.quantity = 3
        self.labelList = []
        self.addressList = []
        self.defaultCameras = [0, 0, 0]
        self.selectedCameras = [0, 0, 0]
    
    #########################
    ### CONTROL PANEL TAB ###
    #########################

    ### NOT IMPLEMENTED ###
    def setupControlLayout(self):
        """
        PURPOSE

        Builds a layout on the control panel tab to add widgets to.

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

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
        for i, menu in enumerate(self.selectedMenus):
            menu.clear()
            menu.addItems(self.labelList)
            menu.setCurrentIndex(self.selectedCameras[i])

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
        for i in range(3):
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
        frame1.setLayout(layout1)
        frame2 = QFrame()
        frame2.setLayout(layout2)
        
        # APPLY STYLING
        try:
            label1.setStyleSheet(self.style.infoLabel)
            label2.setStyleSheet(self.style.infoLabel)
            frame1, frame2 = self.style.setColouredFrame(frame1, frame2, self.style.digitalCameraFrame, self.style.settingsFrame)
        except:
            pass

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

        # UPDATE MAIN PROGRAM 
        self.cameraEditSignal.emit()

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

        # UPDATE MAIN PROGRAM 
        self.cameraEditSignal.emit()

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