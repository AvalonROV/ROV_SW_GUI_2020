#########################
######## IMPORTS ########
#########################

try:
    # PYQT5 MODULES
    from PyQt5 import uic
    from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimeLine
    from PyQt5.QtWidgets import (QSplashScreen, QProgressBar, QScrollArea, QGroupBox, QHBoxLayout, QFrame, QWidget, QStyleFactory, QMainWindow, 
                                QApplication, QComboBox, QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QVBoxLayout, QLabel, QSlider, 
                                QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, QFileDialog, QGraphicsDropShadowEffect, QShortcut)
    from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QKeyEvent, QKeySequence, QIcon, QFont, QColor, QPalette, QPainter

    # ADDITIONAL MODULES
    import sys, os
    from threading import Thread, Timer
    from datetime import datetime
    from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW, CAP_FFMPEG
    from xml.etree.ElementTree import parse, Element, SubElement, ElementTree
    from subprocess import call
    from webbrowser import open
    from pygame import init
    from pygame.joystick import quit, Joystick, get_count
    from pygame.event import Event, get
    import serial
    from math import ceil
    import time
    import subprocess
except:
    sys.exit("\n###################################################################################################"
                "\nSome libraries are missing! Run the 'install_libraries.bat' file to install the required libraries."
                "\n###################################################################################################")

# CUSTOM LIBRARIES
from libraries.configuration_file.configurationFile import READ_CONFIG_FILE, WRITE_CONFIG_FILE
from libraries.serial.rovComms import ROV_SERIAL
from libraries.controller.xboxController import CONTROLLER
from libraries.computer_vision.mosaicTask.mosaicPopupWindow import MOSAIC_POPUP_WINDOW
from libraries.computer_vision.transectLineTask.transectLinePopupWindow import TRANSECT_LINE_POPUP_WINDOW
from libraries.computer_vision.transectLineTask.transectLineAlgorithm_v1 import TRANSECT_LINE_TASK
from libraries.camera.cameraCapture import CAMERA_CAPTURE
from libraries.animation.slideAnimation import SLIDE_ANIMATION
from libraries.visual.visualEffects import STYLE
from libraries.gui.profileSelector import PROFILE_SELECTOR
from libraries.gui.timerWidget import TIMER
from libraries.gui.thrusters import THRUSTERS
from libraries.gui.actuators import ACTUATORS
from libraries.gui.analogCameras import ANALOG_CAMERAS
from libraries.gui.digitalCameras import DIGITAL_CAMERAS
from libraries.gui.keybindings import KEYBINDINGS
from libraries.gui.controllerDisplay import CONTROLLER_DISPLAY
from libraries.gui.sensors import SENSORS

class UI(QMainWindow):
    """
    PURPOSE

    Contains functions to initiate the GUI, link the widgets and connect all the signals/slots from external libraries together.
    """
    # DATABASE
    fileName = ""
    cameraFeeds = []
    cameraThreadList = []
    visionTaskStatus = [False] * 4

    # INITIAL SETUP
    def __init__(self, app):
        """
        PURPOSE

        Class constructor.
        Loads GUI, call functions to initiate all the libraries and connects the signal/slots together.


        INPUT

        - app = QApplication object (required to allow theme changing).

        RETURNS

        NONE
        """
        super(UI,self).__init__()
        
        # LOAD UI FILE
        uic.loadUi('gui.ui',self)

        # APPLICATION OBJECT TO ALLOW THEME CHANGING
        self.app = app

        # INITIATE ALL OBJECTS AND LIBRARIES
        self.initiateObjects()

        # CONNECT LIBRARY SIGNALS TO SLOTS
        self.connectSignals()

        # LINK SIGNALS TO SLOTS
        self.linkControlPanelWidgets()
        self.linkConfigWidgets()
        self.linkToolbarWidgets()

        # LOAD DEFAULT PROGRAM CONFIGURATION
        self.configSetup()

        # SET DEFAULT SCALING
        self.setupDefaultScaling()

        # LINK KEYBOARD SHORTCUTS
        self.setKeyShortcuts()

        # INITIAL STARTUP MESSAGE
        self.printTerminal("Welcome to the Avalon ROV control interface.")
        self.printTerminal("Click 'Help' on the taskbar to access the user manual.")
        self.printTerminal("Connect to the ROV and CONTROLLER to get started.")
    
        # LAUNCH GUI
        self.showFullScreen()

        # LAUNCH PILOT PROFILE SELECTOR
        self.profileSelector.showPopup()     

    def initiateObjects(self):
        """
        PURPOSE

        Instantiates all the external library modules.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # OPEN PILOT PROFILE SELECTOR WINDOW
        self.profileSelector = PROFILE_SELECTOR()

        # INITIATE SERIAL COMMUNICATION LIBRARY
        self.comms = ROV_SERIAL()

        # INITIATE XBOX CONTROLLER LIBRARY
        self.controller = CONTROLLER()

        self.control = CONTROL_PANEL(self, self.controller, self.comms)
        self.config = CONFIG(self, self.control, self.controller, self.comms)
        self.toolbar = TOOLBAR(self)

        # INITIATE SLIDE ANIMATION FOR TAB CHANGE
        self.animation = SLIDE_ANIMATION(self.gui_view_widget)
        self.animation.setSpeed(500)
        self.animation.setDirection(Qt.Vertical)

        # INITIATE CAMERA FEED LIBRARY
        self.initiateCameraFeed()

        # STYLESHEET LIBRARY AND STYLING FUNCTIONS
        self.style = STYLE()

        # INITIATE VISION TASKS
        self.control.initialiseVisionWidgets()

        # INITIATE TIMER
        self.timer = TIMER(controlLayout = self.timer_control)

        # INITIATE THRUSTERS
        self.thrusters = THRUSTERS(controlLayout = self.orientation_control, configLayout = self.thruster_config)

        # INITIATE ACTUATORS
        self.actuators = ACTUATORS(controlLayout = self.actuator_control, configLayout = self.actuator_config)

        # INITIATE ANALOG CAMERAS
        self.analogCameras = ANALOG_CAMERAS(controlLayout = self.analog_camera_control, configLayout = self.analog_camera_config)

        # INITIATE DIGITAL CAMERAS
        self.digitalCameras = DIGITAL_CAMERAS(controlLayout = self.digital_camera_control, configLayout = self.digital_camera_config)

        # INITIATE KEYBINDINGS
        self.keybindings = KEYBINDINGS(configLayout = self.keybinding_config)

        # INITIATE CONTROLLER INPUT DISPLAY
        self.controllerDisplay = CONTROLLER_DISPLAY(configLayout = self.controller_display_config, controlLayout = self.controller_control)

        # INITIATE SENSORS
        self.sensors = SENSORS(controlLayout = self.sensor_control, configLayout = self.sensor_config)

    def connectSignals(self):
        """
        PURPOSE

        Connect all the signals from modules to slots in the main program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # PILOT PROFILE SELECTED SIGNAL
        self.profileSelector.loadProfileSignal.connect(self.pilotProfileSelected)
        self.profileSelector.saveProfileSignal.connect(self.addNewProfile)

        # PROGRAM CLOSE SIGNAL
        self.app.aboutToQuit.connect(self.programExit)

        # WINDOW RESIZE EVENT
        self.resizeEvent(QResizeEvent(self.size(), QSize()))

        # KEYBINDING GET BUTTON STATES SIGNAL
        self.keybindings.getButtonStates.connect(self.config.returnButtonStates)

        # DIGITAL CAMERA CHANGE ADDRESS/LABEL SIGNALS
        self.digitalCameras.cameraEnableSignal.connect(self.toggleCameraFeed)
        self.digitalCameras.cameraResolutionSignal.connect(self.changeCameraResolution)
        self.digitalCameras.cameraEditSignal.connect(self.updateCameraMenus)
        self.digitalCameras.cameraChangeAddress.connect(self.changeCameraAddress)

        # THRUSTER TEST/SET SPEED SIGNALS
        self.thrusters.thrusterTestSignal.connect(self.control.changeThrusters)
        self.thrusters.thrusterSpeedsSignal.connect(self.control.changeThrusters)

        # ADD/REMOVE/TOGGLE ACTUATOR SIGNALS
        self.actuators.addKeybinding.connect(lambda label: self.keybindings.addBinding(label))
        self.actuators.removeKeybinding.connect(self.keybindings.removeBinding)
        self.actuators.toggleActuatorSignal.connect(self.control.changeActuators)

        # CONTROLLER VALUES SIGNAL
        self.controller.processInputSignal.connect(self.control.processControllerInput)

        # COMMS FAIL SIGNAL
        self.comms.uiSerialFunction.connect(self.control.serialFailEvent)

    ###############################
    ### CONFIGURATION FUNCTIONS ###
    ###############################
    @pyqtSlot(str)
    def pilotProfileSelected(self, directory):
        """
        PURPOSE

        Called when a pilot profile is selected from the popup window.
        Sets the directory of the configuration file to load.
        Loads to configuration file.

        INPUT

        - directory = directory of the XML configuration file.

        RETURNS

        NONE
        """
        self.fileName = "./config/" + directory

        # LOAD SETTINGS FROM CONFIG FILE
        self.resetConfig()
        self.configSetup()

    @pyqtSlot(str)
    def addNewProfile(self, directory):
        """
        PURPOSE

        Called by the pilot profile selector window when the user wants to add a new pilot profile.
        The default program configuration is saved.

        INPUT

        - directory = the directory of the the new pilot profile.

        RETURNS

        NONE
        """
        self.writeDefaultConfigFile(directory)

    def configSetup(self):
        """
        PURPOSE

        Reads the configuration file and configures the programs thruster, actuator, sensor, camera and controller settings.
        If no configuration file is found, the program will open with default settings. 

        INPUT

        NONE

        RETURNS

        NONE
        """
        # READ PROGRAM SETTINGS FROM CONFIGURATION FILE
        self.readConfigFile()

        # APPLY SETTINGS TO GUI
        self.programSetup()

    def readConfigFile(self):
        """
        PURPOSE

        Reads the XML configuration file and stores the data in their respective modules.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # PARSE CONFIGURATION FILE
        configFile = READ_CONFIG_FILE(self.fileName)
        configFileStatus = configFile.parseFile()

        if configFileStatus:
            self.printTerminal('Configuration file found.')
            
            # READ THEME SETTINGS
            self.style.theme = configFile.readTheme()
            
            # READ THRUSTER SETTINGS
            self.thrusters.rovPositions, self.thrusters.reverseStates = configFile.readThruster() 
            
            # READ ACTUATOR SETTINGS
            self.actuators.quantity, self.actuators.labelList = configFile.readActuator()

            # READ ANALOG CAMERA SETTINGS
            self.analogCameras.quantity, self.analogCameras.labelList, self.analogCameras.defaultCameras = configFile.readAnalogCamera()

            # READ DIGITAL CAMERA SETTINGS
            self.digitalCameras.quantity, self.digitalCameras.labelList, self.digitalCameras.addressList, self.digitalCameras.defaultCameras, self.digitalCameras.selectedResolutions = configFile.readDigitalCamera()
            
            # READ KEYBINDING SETTINGS
            self.keybindings.bindings = configFile.readKeyBinding()

            # READ SENSOR SETTINGS
            self.sensors.quantity, self.sensors.selectedTypes = configFile.readSensor()

        else:
            self.printTerminal('Configuration file not found.')

    def writeConfigFile(self):
        """
        PURPOSE

        Write the program settings to an XML file.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CREATE ROOT
        configFile = WRITE_CONFIG_FILE(self.fileName)
        configFile.createFile()

        # SAVE THEME SETTINGS
        configFile.saveTheme(self.style.theme)

        # SAVE THRUSTER SETTINGS
        configFile.saveThruster(self.thrusters.rovPositions, self.thrusters.reverseStates)

        # SAVE ACTUATOR SETTINGS
        configFile.saveActuator(self.actuators.quantity, self.actuators.labelList)

        # SAVE ANALOG CAMERA SETTINGS
        configFile.saveAnalogCamera(self.analogCameras.quantity, self.analogCameras.labelList, self.analogCameras.defaultCameras)

        # SAVE DIGITAL CAMERA SETTINGS
        configFile.saveDigitalCamera(self.digitalCameras.quantity, self.digitalCameras.labelList, self.digitalCameras.addressList, self.digitalCameras.defaultCameras, self.digitalCameras.selectedResolutions)
        
        # SAVE KEYBINDING SETTINGS
        configFile.saveKeybinding(self.keybindings.bindings)

        # SAVE SENSOR SETTINGS
        configFile.saveSensor(self.sensors.quantity, self.sensors.selectedTypes)

        # WRITE SETTINGS TO XML FILE
        configFile.writeFile()

    def writeDefaultConfigFile(self, directory):
        """
        PURPOSE

        Saves a default program configuration to an XML file.

        INPUT

        - directory = the directory of the the new pilot profile.

        RETURNS

        NONE
        """
        # CREATE ROOT
        configFile = WRITE_CONFIG_FILE(directory)
        configFile.createFile()

        # SAVE THEME SETTINGS
        style = STYLE()
        configFile.saveTheme(style.theme)

        # SAVE THRUSTER SETTINGS
        thrusters = THRUSTERS()
        configFile.saveThruster(thrusters.rovPositions, thrusters.reverseStates)

        # SAVE ACTUATOR SETTINGS
        actuators = ACTUATORS()
        configFile.saveActuator(actuators.quantity, actuators.labelList)

        # SAVE ANALOG CAMERA SETTINGS
        analogCameras = ANALOG_CAMERAS()
        configFile.saveAnalogCamera(analogCameras.quantity, analogCameras.labelList, analogCameras.defaultCameras)

        # SAVE DIGITAL CAMERA SETTINGS
        digitalCameras = DIGITAL_CAMERAS()
        configFile.saveDigitalCamera(digitalCameras.quantity, digitalCameras.labelList, digitalCameras.addressList, digitalCameras.defaultCameras, digitalCameras.selectedResolutions)
        
        # SAVE KEYBINDING SETTINGS
        keybindings = KEYBINDINGS()
        configFile.saveKeybinding(keybindings.bindings)

        # SAVE SENSOR SETTINGS
        sensors = SENSORS()
        configFile.saveSensor(sensors.quantity, sensors.selectedTypes)

        # WRITE SETTINGS TO XML FILE
        configFile.writeFile()

    def programSetup(self):
        """
        PURPOSE

        Applies the configuration settings to the GUI by calling the setup() function of each module.

        INPUT

        NONE

        RETURNS

        NONE
        """    
        # SETUP THEME
        self.changeTheme(self.style.theme)

        # SETUP TIMER
        self.timer.setup()

        # SETUP THRUSTERS
        self.thrusters.setup()

        # SETUP KEYBINDINGS
        self.keybindings.setup()

        # SETUP ACTUATORS
        self.actuators.setup() 
         
        # SETUP ANALOG CAMERAS
        self.analogCameras.setup()
        
        # SETUP DIGITAL CAMERAS
        self.digitalCameras.setup()

        # SETUP CONTROLLER DISPLAY
        self.controllerDisplay.setup()

        # UPDATE GUI WITH SENSOR DATA
        self.sensors.setup()

    def resetConfig(self):
        """
        PURPOSE

        Resets the program to default settings (nothing configured).
        
        INPUT

        NONE

        RETURNS

        NONE
        """
        # CLEAR TIMER LAYOUT
        self.timer.reset()

        # RESET THRUSTER SETTINGS
        self.thrusters.reset()

        # RESET ACTUATOR SETTINGS
        self.actuators.reset()

        # RESET SENSOR SETTINGS
        self.sensors.reset()

        # RESET ANALOG CAMERA SETTINGS
        self.analogCameras.reset()

        # RESET DIGITAL CAMERA SETTINGS
        self.digitalCameras.reset()

        # RESET CONTROLLER DISPLAY
        self.controllerDisplay.reset()

        # RESET KEYBINDING SETTINGS
        self.keybindings.reset()
      
    ################################
    ### WIDGET LINKING FUNCTIONS ###
    ################################
    def linkControlPanelWidgets(self):
        """
        PURPOSE

        Links widgets in the control panel tab to their respective functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # GO TO CONTROL PANEL TAB BUTTON
        self.change_gui_control.clicked.connect(lambda state, view = 0: self.changeView(view))
        self.change_gui_control.setChecked(True)
        self.style.applyGlow(self.change_gui_control, "#0D47A1", 10)
        
        # GO TO CONFIGURATION TAB BUTTON
        self.change_gui_config.clicked.connect(lambda state, view = 1: self.changeView(view))
        self.style.applyGlow(self.change_gui_config, "#0D47A1", 10)
        
        # VERTICAL SPITTER
        self.control_panel_splitter.splitterMoved.connect(self.splitterEvent)

        # ROV CONNECT BUTTON
        self.control_rov_connect.clicked.connect(self.control.rovSerialConnection)
        self.control_rov_connect.setObjectName("large-button")
        self.style.applyGlow(self.control_rov_connect, "#0D47A1", 10)
        self.control_rov_connect.setFixedHeight(50)
        
        # CONTROLLER CONNECT BUTTON
        self.control_controller_connect.clicked.connect(self.control.controllerConnection)
        self.control_controller_connect.setObjectName("large-button")
        self.style.applyGlow(self.control_controller_connect, "#0D47A1", 10)
        self.control_controller_connect.setFixedHeight(50)
        
        # MACHINE VISION TASK BUTTONS
        self.control_vision_mosaic.clicked.connect(lambda status, task = 0: self.control.popupVisionTask(task)) 
        self.control_vision_shape_detection.clicked.connect(lambda status, task = 1: self.control.popupVisionTask(task))
        self.control_vision_transect_line.clicked.connect(lambda status, task = 2: self.control.popupVisionTask(task))
        self.control_vision_coral_health.clicked.connect(lambda status, task = 3: self.control.popupVisionTask(task))
   
        # LINK EACH DIGITAL CAMERA DROP DOWN MENU TO THE SAME SLOT, PASSING CAMERA ID AS 1,2,3,4 ETC.
        self.camera_feed_1_menu.activated.connect(lambda index, camera = 0: self.changeCameraFeedMenu(index, camera))
        self.camera_feed_2_menu.activated.connect(lambda index, camera = 1: self.changeCameraFeedMenu(index, camera))
        self.camera_feed_3_menu.activated.connect(lambda index, camera = 2: self.changeCameraFeedMenu(index, camera))
        self.camera_feed_4_menu.activated.connect(lambda index, camera = 3: self.changeCameraFeedMenu(index, camera))

        # CAMERA FEED CLICK EVENT
        self.camera_feed_1.mousePressEvent = lambda event, cameraFeed = 0: self.changeCameraFeed(event, cameraFeed)
        self.camera_feed_2.mousePressEvent = lambda event, cameraFeed = 1: self.changeCameraFeed(event, cameraFeed)
        self.camera_feed_3.mousePressEvent = lambda event, cameraFeed = 2: self.changeCameraFeed(event, cameraFeed)
        self.camera_feed_4.mousePressEvent = lambda event, cameraFeed = 3: self.changeCameraFeed(event, cameraFeed)

        # SWITCH USER BUTTON
        self.switch_user.clicked.connect(lambda: self.profileSelector.showPopup())
        self.switch_user.setIcon(QIcon("./graphics/login-icon.png"))
        self.switch_user.setIconSize(QSize(20,20))
        self.switch_user.setObjectName("rename-button")

        # PROGRAM EXIT BUTTON
        self.program_exit.clicked.connect(lambda: self.app.quit())
        self.program_exit.setObjectName("program-exit-button")
        
    def linkConfigWidgets(self):
        """
        PURPOSE

        Links widgets in the configuration tab to their respective functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # ROV CONNECT BUTTON
        self.config_rov_connect.clicked.connect(self.control.rovSerialConnection)
        self.config_rov_connect.setObjectName("large-button")
        self.style.applyGlow(self.config_rov_connect, "#0D47A1", 10)
        self.config_rov_connect.setFixedHeight(50)
        
        # CONTROLLER CONNECT BUTTON
        self.config_controller_connect.clicked.connect(self.control.controllerConnection)
        self.config_controller_connect.setObjectName("large-button")
        self.style.applyGlow(self.config_controller_connect, "#0D47A1", 10)
        self.config_controller_connect.setFixedHeight(50)
            
        # SERIAL COMMUNICATION BUTTONS
        self.config_com_port_list.activated.connect(self.config.changeComPort)
        self.config_find_com_ports.clicked.connect(self.config.refreshComPorts)   

    def linkToolbarWidgets(self):
        """
        PURPOSE

        Links widgets in the toolbar to their respective functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.toolbar_load_settings.triggered.connect(self.toolbar.loadSettings)
        self.toolbar_reset_settings.triggered.connect(self.toolbar.resetSettings)
        self.toolbar_change_pilot.triggered.connect(self.toolbar.changePilotProfile)
        self.toolbar_save_settings.triggered.connect(self.toolbar.saveSettings)
        self.toolbar_open_documentation.triggered.connect(self.toolbar.openDocumentation)
        self.toolbar_open_github.triggered.connect(self.toolbar.openGitHub)
        self.toolbar_toggle_theme.triggered.connect(self.toolbar.toggleTheme)

    ################################
    #### CAMERA FEEDS FUNCTIONS ####
    ################################
    def initiateCameraFeed(self):
        """
        PURPOSE

        Instantiates a camera feed object for each camera and starts the threads.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.cameraFeeds = [self.camera_feed_1, self.camera_feed_2, self.camera_feed_3, self.camera_feed_4]

        # INITIATE CAMERA THREADS
        feedQuantity = len(self.cameraFeeds)
        
        for i in range(feedQuantity):
            cameraThread = CAMERA_CAPTURE(identifier = i)
            
            # CONNECT SIGNAL TO SLOT
            cameraThread.cameraNewFrameSignal.connect(self.updateCameraFeed)
            
            # STORE THREAD POINTER FOR LATER USE
            self.cameraThreadList.append(cameraThread)

            # START THREAD
            cameraThread.start()

    @pyqtSlot()
    def updateCameraMenus(self):
        """
        PURPOSE

        Refreshes the digital camera feed menus on the control panel tab.
        Called when a camera feed is changed or the name is modified.

        INPUT

        NONE

        RETURNS
        """
        menuList = [self.camera_feed_1_menu, self.camera_feed_2_menu, self.camera_feed_3_menu, self.camera_feed_4_menu]

        for i, menu in enumerate(menuList):
            menu.clear()
            menu.addItem("None")
            menu.addItems(self.digitalCameras.labelList)
            menu.setCurrentIndex(self.digitalCameras.selectedCameras[i])

    @pyqtSlot(bool, int)
    def toggleCameraFeed(self, status, feed):
        """
        PURPOSE

        Turns specific camera feed off.

        INPUT

        - status = True to turn ON, False to turn OFF.
        - feed = the camera to be toggled (1,2,3,4).

        RETURNS

        NONE
        """
        if status:
            self.cameraThreadList[feed].feedBegin()
            self.cameraThreadList[feed].start()
        else:
            self.cameraThreadList[feed].feedStop()

    @pyqtSlot(int, str)
    def changeCameraAddress(self, camera, address):
        """
        PURPOSE

        Changes the source address of a specific camera.
        Called by the DIGITAL_CAMERAS module which then calls the changeSource function in the camera module.
        
        INPUT

        NONE

        - camera = the camera feed being changed.
        - addess = the new source address.

        RETURNS

        NONE
        """
        # FORMAT ADDRESS
        formattedAddress = self.digitalCameras.addressConverter(address)

        # CHECK IF THIS ADDRESS IS ALREADY IN USE
        for i, cameraThread in enumerate(self.cameraThreadList):
            address = cameraThread.address
            if address == formattedAddress and i != camera:
                # DISCONNECT FROM THAT FEED BEFORE ATTEMPTING TO CONNECT AGAIN
                # PREVENTS THREADS FIGHTING OVER CAMERA ACCESS
                cameraThread.changeSource("")

        # REINITIALISE CAMERA WITH NEW ADDRESS
        self.cameraThreadList[camera].changeSource(formattedAddress)
 
    @pyqtSlot(int, int, int)
    def changeCameraResolution(self, camera, width, height):
        """
        PURPOSE

        Calls function in camera capture library to change camera resolution.

        INPUT

        - camera = the camera feed being modified (0,1,2,3).
        - width = width of the frame in px.
        - height = height of the frame in px.

        RETURNS

        NONE
        """
        try:
            self.cameraThreadList[camera].changeResolution(width, height)
        except:
            pass

    @pyqtSlot(QPixmap, int)
    def updateCameraFeed(self, frame, identifier):
        """
        PURPOSE

        Refreshes a specific camera feed with a new frame.

        INPUT

        - frame = QImage containing the new frame captures from the camera.
        - identifier = the identification number of the camera feed (0, 1, 2 etc.)

        RETURNS

        NONE
        """
        # RESIZE PIXMAP
        pixmap = frame.scaled(self.cameraFeeds[identifier].size().width(), self.cameraFeeds[identifier].size().height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # PAINT PIXMAP ONTO LABEL
        self.cameraFeeds[identifier].setPixmap(pixmap)

    def changeCameraFeed(self, event, cameraFeed):
        """
        PURPOSE

        Changes which camera is shown in the main camera feed. When a secondary camera feed is clicked, it is swapped with the current primary camera feed.

        INPUT

        - event = Mouse click event.
        - cameraFeed = Camera feed that has been clicked on (1,2,3,4).

        RETURNS

        NONE
        """
        # SWAP MAIN FEED WITH SELECTED SECONDARY FEED
        try:
            self.digitalCameras.selectedCameras[0], self.digitalCameras.selectedCameras[cameraFeed] = self.digitalCameras.selectedCameras[cameraFeed], self.digitalCameras.selectedCameras[0]
            self.digitalCameras.setCameraAddresses()
        except:
            pass
        
        # UPDATE MENUS
        self.updateCameraMenus()

    def changeCameraFeedMenu(self, index, cameraFeed):
        """
        PURPOSE

        Changes the camera feed from the menu options.

        INPUTS

        - index = menu index of the camera selected.
        - cameraFeed = the camera feed that is being modified.
        """
        self.digitalCameras.selectedCameras[cameraFeed] = index

        # CHECK FOR DUPLICATE CAMERA FEEDS
        for i, camera in enumerate(self.digitalCameras.selectedCameras):
            if camera == index and i != cameraFeed:
                self.digitalCameras.selectedCameras[i] = 0
                self.updateCameraMenus()

        # UPDATE CAMERA FEEDS
        self.digitalCameras.setCameraAddresses()

    #############################
    ###### THEME FUNCTIONS ######
    ############################# 
    def changeTheme(self, theme = None):
        """
        PURPOSE

        Change the program theme between light and dark.

        INPUT

        - theme = True for dark theme, False for light theme.

        RETURNS 

        NONE
        """
        # TOGGLE CURRENT THEME
        if theme == None:
            self.style.theme = not self.style.theme
        else: 
            self.style.theme = theme

        # APPLY NEW APPLICATION DEFAULT COLOR PALETTE
        self.style.setPalette(self.style.theme, self.app)

        # CHANGE PROGRAM STYLESHEETS
        self.style.setStyleSheets(self.style.theme)

        # SET STYLESHEETS
        try: 
            globalStylesheets = (
                self.style.normalButton + 
                self.style.largeButton +
                self.style.actuatorButton + 
                self.style.orientationButton +
                self.style.timerStartButton +
                self.style.renameButton +
                self.style.deleteButton +
                self.style.programExitButton +
                self.style.timerLCD +
                self.style.scrollArea +
                self.style.comboBox + 
                self.style.groupBox +
                self.style.settingsFrame +
                self.style.thrusterFrame +
                self.style.actuatorFrame +
                self.style.digitalCameraFrame +
                self.style.keybindingFrame +
                self.style.labelOnOff +
                self.style.infoLabel)

            # APPLY TO MAIN PROGRAM
            self.setStyleSheet(globalStylesheets)

            # APPLY TO PROFILE SELECTOR POPUP
            self.profileSelector.setStyleSheet(globalStylesheets)
        
        except:
            pass
        
        # LOAD AVALON LOGO
        self.setLogo(self.style.theme)      

    def setLogo(self, theme):
        """
        PURPOSE

        Loads the Avalon logo for either the light or dark theme.

        INPUT

        - theme = True for dark theme, False for light theme.

        RETURNS

        NONE
        """
        # DARK THEME
        if theme:
            self.avalon_logo.clear()
            avalonPixmap = QPixmap('graphics/thumbnail.png')
            avalonPixmap = avalonPixmap.scaledToWidth(200, Qt.SmoothTransformation)
            self.avalon_logo.setPixmap(avalonPixmap)

        # LIGHT THEME
        else:
            self.avalon_logo.clear()
            avalonPixmap = QPixmap('graphics/logo.png')
            avalonPixmap = avalonPixmap.scaledToWidth(200, Qt.SmoothTransformation)
            self.avalon_logo.setPixmap(avalonPixmap)

    ###########################
    #### SCALING FUNCTIONS ####
    ###########################
    def setupDefaultScaling(self):
        """
        PURPOSE

        Sets the default proportion of the side bar on the control panel at program launch.

        INPUT

        NONE

        RETURNS

        NONE
        """
        screenWidth, screenHeight = self.getScreenSize()

        # SET DEFAULT SIDE BAR WIDTH
        self.con_panel_functions_widget.resize(1000,self.con_panel_functions_widget.height())

        # SET HEIGHT OF GROUP BOXES ON CONFIG TAB
        #self.configuration_tab.

    def getScreenSize(self):
        """
        PURPOSE

        Gets the width and height of the screen.

        INPUT

        NONE

        RETURNS

        - width = width of screen in pixels.
        - height = height of screen in pixels.
        """
        sizeObject = QDesktopWidget().screenGeometry(-1)
        screenWidth = sizeObject.width()
        screenHeight = sizeObject.height()
        
        return screenWidth, screenHeight

    def resizeEvent(self, event):
        """
        PURPOSE

        Function is called whenever the programs window size is changed.
        Calls functions to refresh the pixmaps sizes and the GUI widget proportions.

        INPUT

        - event = QResizeEvent event.

        RETURNS

        NONE
        """
        self.changePixmapSize()
        self.reorderConfigGrid()

        QMainWindow.resizeEvent(self, event)

    def splitterEvent(self):
        """
        PURPOSE

        Function is called whenever the control panel splitter is activated.
        Calls function to refresh pixmap size.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.changePixmapSize()
        
    def changePixmapSize(self): 
        """
        PURPOSE

        Dynamically scales all the pixmap objects in the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # UPDATE PIXMAP SIZE ON MOSAIC TASK POPUP WINDOW
        self.control.mosaicPopup.imageResizeEvent()

        # UPDATE SIZE OF EACH CAMERA FEED
        for camera in self.cameraFeeds:
            try:
                camSize = [camera.size().width(), camera.size().height()]
                cameraPixmap = camera.pixmap().scaled(camSize[0], camSize[1], Qt.KeepAspectRatio)
                camera.setPixmap(cameraPixmap)  
            except:
                pass

    def reorderConfigGrid(self):
        """
        PURPOSE

        Adjusts the number of rows/columns in the configuration tab depending on the window size so all the settings are clearly visible.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # GET WINDOW DIMENSIONS
        width = self.frameGeometry().width()
        height = self.frameGeometry().height()

        # FIND SCREEN SIZE
        screenWidth, screenHeight = self.getScreenSize()

        widthProportion = width/screenWidth
        
        if widthProportion < 0.4:
            objects = self.unparentGridWidgets()
            self.setNewGridOrder(objects, 3)
            self.setGridStretch()

        elif widthProportion < 0.6:
            objects = self.unparentGridWidgets()
            self.setNewGridOrder(objects, 4)
            self.setGridStretch()

        elif widthProportion < 0.8:
            objects = self.unparentGridWidgets()
            self.setNewGridOrder(objects, 5)
            self.setGridStretch()

        else:
            objects = self.unparentGridWidgets()
            self.setNewGridOrder(objects, 6)
            self.setGridStretch()

    def unparentGridWidgets(self):
        """
        PURPOSE

        Removes the group box from each grid location and stores them in an array.

        INPUT

        NONE

        RETURNS

        - objects = an array containing the children of the grid layout.
        """
        # FIND ALL GROUP BOXES IN THE GRID LAYOUT (IN ORDER FROM TOP LEFT TO BOTTOM RIGHT)
        objects = []

        rowCount = self.config_grid_layout.rowCount()
        columnCount = self.config_grid_layout.columnCount()

        for row in range(rowCount):
            for column in range(columnCount):
                item = self.config_grid_layout.itemAtPosition(row, column)

                # IF GRID LOCATION CONTAINS OBJECT
                if item != None:
                    widget = item.widget()
                    objects.append(widget)

        # UNPARENT ALL GROUP BOXES FROM GRID LAYOUT
        for groupBox in objects:
            self.config_grid_layout.removeWidget(groupBox)

        return objects

    def setNewGridOrder(self, objects, columnNumber):
        """
        PURPOSE

        Sets the number of columns in the configuration tab grid layout.

        INPUT

        - objects = array containing the pointers to the group boxes.
        - columnNumber = the new number of colomns.

        RETURNS

        NONE
        """
        # NUMBER OF GROUP BOXES TO DISPLAY IN THE GRID LAYOUT
        widgetCount = len(objects)

        newColumnCount = columnNumber
        newRowCount = ceil(widgetCount/newColumnCount)
        
        index = 0

        # ADD GROUP BOXES TO NEW GRID LOCATIONS
        for row in range(newRowCount):
            for column in range(newColumnCount):
                try:
                    self.config_grid_layout.addWidget(objects[index], row, column)
                    index += 1   
                except:
                    pass

    def setGridStretch(self):
        """
        PURPOSE

        Sets the stretch of each row and column in the grid layout to make the size of each group box equal.

        INPUT

        NONE

        RETURNS

        NONE
        """
        rowCount = self.config_grid_layout.rowCount()            
        columnCount = self.config_grid_layout.columnCount()

        # HIDE UNUSED ROWS
        for row in range(rowCount):
            self.config_grid_layout.setRowStretch(row, 0)
            for column in range(columnCount):
                item = self.config_grid_layout.itemAtPosition(row, column)

                # IF OBJECT EXISTS ON CURRENT GRID ROW
                if item != None:
                    self.config_grid_layout.setRowStretch(row, 1)
                    # SET MINIMUM ROW HEIGHT
                    self.config_grid_layout.setRowMinimumHeight(row, 800)
                
        # HIDE UNUSED COLUMNS
        for column in range(columnCount):
            self.config_grid_layout.setColumnStretch(column, 0)
            for row in range(rowCount):
                item = self.config_grid_layout.itemAtPosition(row, column)

                # IF OBJECT EXISTS ON CURRENT GRID ROW
                if item != None:
                    self.config_grid_layout.setColumnStretch(column, 1)

    ###########################
    ##### OTHER FUNCTIONS #####
    ###########################
    def changeView(self, view):
        """
        PURPOSE

        Switches between the 'Control Panel' tab and the 'Configuration' tab within the program. 
        The camera feeds are disabled whilst the program is in the 'Configuration' tab.

        INPUT

        - view = the page to transition to. (0 = Control Panel) (1 = Configuration)

        RETURNS

        NONE
        """
        if self.animation.animationComplete:
            # TRANSITION TO CONTROL PANEL TAB
            if view == 0:
                self.animation.screenPrevious()
                self.change_gui_control.setChecked(True)
                self.change_gui_config.setChecked(False)

                # RESTART CAMERA FEEDS
                self.digitalCameras.toggleAllFeeds(True)

            # TRANSITION TO CONFIGURATION TAB
            if view == 1:
                # TURN OFF CAMERA FEEDS
                self.digitalCameras.toggleAllFeeds(False)
                
                self.animation.screenNext()
                self.change_gui_control.setChecked(False)
                self.change_gui_config.setChecked(True)

        else:
            # IGNORE BUTTONS WHILE ANIMATION IS IN PROGRESS
            if view == 0:
                self.change_gui_control.setChecked(not self.change_gui_control.isChecked())
            if view == 1:
                self.change_gui_config.setChecked(not self.change_gui_config.isChecked())

    def printTerminal(self, text):
        """
        PURPOSE

        Prints text to the serial terminal on the configuration tab.

        INPUT
        
        - text = the text to display on the serial terminal

        RETURNS

        NONE
        """
        time = datetime.now().strftime("%H:%M:%S")
        string = time + " -> " + str(text)
        self.config_terminal.appendPlainText(str(string))

    def setKeyShortcuts(self):
        """
        PURPOSE

        Defines keyboard shortcuts and connect them to repective functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CTRL+S TO SAVE SETTINGS
        save = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_S), self)
        save.activated.connect(self.toolbar.saveSettings) 

        # F11 TO ENTER FULLSCREEN
        fullscreen = QShortcut(QKeySequence(Qt.Key_F11), self)
        fullscreen.activated.connect(self.showFullScreen)
 
        # ESC TO EXIT FULL SCREEN
        exitFullscreen = QShortcut(QKeySequence(Qt.Key_Escape), self)
        exitFullscreen.activated.connect(self.showMaximized)

    def programExit(self):
        """
        PURPOSE

        Called when program exits.
        Closes the camera threads to prevent them from continually running in the background.#

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CLOSE CAMERA THREADS
        self.toggleCameraFeed(False, 0)
        self.toggleCameraFeed(False, 1)
        self.toggleCameraFeed(False, 2)
        # REQUIRED TO LET THREADS CLOSE BEFORE MAIN EVENT LOOP EXITS
        time.sleep(1)

class CONTROL_PANEL():
    """
    PURPOSE

    Contains function relating to the control panel tab.
    """
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3):
        """
        PURPOSE

        Class constructor.
        Initialises objects.

        INPUT

        - Object1 = 'UI' class
        - Object2 = 'CONTROLLER' class
        - Object3 = 'ROV_SERIAL' class

        RETURNS

        NONE
        """
        # CREATE OBJECTS
        self.ui = Object1
        self.controller = Object2
        self.comms = Object3

    ############################
    ##### SERIAL FUNCTIONS #####
    ############################
    def rovSerialConnection(self, buttonState):
        """
        PURPOSE

        Determines whether to connect or disconnect from the ROV serial interface.

        INPUT

        - buttonState = the state of the button (checked or unchecked).

        RETURNS

        NONE
        """
        # CONNECT
        if buttonState:
            self.rovConnect()

        # DISCONNECT
        else:
            self.rovDisconnect()

    def rovConnect(self):
        """
        PURPOSE

        Attempts to connect to the ROV using the comms library.
        Changes the appearance of the connect buttons.
        If connection is successful, the ROV startup procedure is initiated.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # DISABLE BUTTONS TO AVOID DOUBLE CLICKS
        self.ui.control_rov_connect.setEnabled(False)
        self.ui.config_rov_connect.setEnabled(False) 

        # AUTO CONNECT ENABLED    
        if self.ui.config_auto_connect.isChecked():
            # FIND ALL AVAILABLE COM PORTS
            self.ui.printTerminal('Searching for available COM ports...')
            availableComPorts, rovComPort, identity = self.comms.findComPorts(self.ui.config_com_port_list, 115200, self.comms.rovID)
            self.comms.rovComPort = rovComPort
            self.ui.printTerminal("{} available COM ports found.".format(len(availableComPorts)))
            self.ui.printTerminal('Device Identity: {}'.format(identity))
        else:
            rovComPort = self.comms.rovComPort
        
        # ATTEMPT CONNECTION TO ROV COM PORT
        status, message = self.comms.serialConnect(rovComPort, 115200)
        self.ui.printTerminal(message)

        # IF CONNECTION IS SUCCESSFUL
        if status == True:
            # MODIFY BUTTON STYLE
            self.ui.control_rov_connect.setChecked(True)
            self.ui.control_rov_connect.setText('DISCONNECT')
            self.ui.config_rov_connect.setChecked(True)
            self.ui.config_rov_connect.setText('DISCONNECT')

            # CALL INITIAL ROV FUNCTIONS
            self.startupProcedure()
        
        # IF CONNECTION IS UNSUCCESSFUL
        else:
            self.rovDisconnect()
            
        # RE-ENABLE CONNECT BUTTONS
        self.ui.control_rov_connect.setEnabled(True)
        self.ui.config_rov_connect.setEnabled(True)

    def rovDisconnect(self):
        """
        PURPOSE

        Disconnects from the ROV using the comms library.
        Changes the appearance of the connect buttons

        INPUT

        NONE

        RETURNS

        NONE
        """
        # MODIFY BUTTON STYLE
        self.ui.control_rov_connect.setText('CONNECT')
        self.ui.control_rov_connect.setChecked(False)
        self.ui.config_rov_connect.setText('CONNECT')
        self.ui.config_rov_connect.setChecked(False)
        
        # CLOSE COM PORT
        if self.comms.commsStatus:
            self.ui.printTerminal("Disconnected from {}".format(self.ui.comms.rovComPort))
            self.comms.comms.close()
            self.comms.commsStatus = False

    def serialFailEvent(self, message):
        """
        PURPOSE

        This function is called from the comms library in the event of a communication failure.

        INPUT

        - message = string error message to show on the GUI.

        RETURNS

        NONE
        """
        self.rovDisconnect()
        self.ui.printTerminal(message)

    ############################
    ### CONTROLLER FUNCTIONS ###
    ############################
    def controllerConnection(self, buttonState):
        """
        PURPOSE

        Determines whether to connect or disconnect from the controller.

        INPUT

        - buttonState = the state of the button (checked or unchecked).

        RETURNS

        NONE
        """
        # CONNECT
        if buttonState:
            self.controllerConnect()

        # DISCONNECT
        else:
            self.controllerDisconnect()
           
    def controllerConnect(self):    
        """
        PURPOSE

        Initialises communication with the XBOX controller.

        INPUT

        NONE

        RETURNS

        NONE
        """            
        # DISABLE CONTROLLER CONNECT BUTTONS
        self.ui.control_controller_connect.setEnabled(False)
        self.ui.config_controller_connect.setEnabled(False)

        # INITIATE COMMUNICATION WITH THE CONTROLLER
        connectionStatus, controllerNumber, message = self.controller.findController("Controller (Xbox One For Windows)")
        self.ui.printTerminal(message)
        
        if connectionStatus == True:
            # START READING CONTROLLER INPUTS IN A TIMED THREAD, RETURN VALUES TO PROCESSING FUNCTIONS
            self.controller.startControllerEventLoop(controllerNumber)
            
            # UPDATE BUTTON STYLE
            self.ui.control_controller_connect.setChecked(True)
            self.ui.control_controller_connect.setText('DISCONNECT')
            self.ui.config_controller_connect.setChecked(True)
            self.ui.config_controller_connect.setText('DISCONNECT')

        else:
            self.controllerDisconnect()

        # ENABLE CONTROLLER CONNECT BUTTONS
        self.ui.control_controller_connect.setEnabled(True)
        self.ui.config_controller_connect.setEnabled(True)
            
    def controllerDisconnect(self):
        """
        PURPOSE

        Disconnects from the controller.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # MODIFY BUTTON STYLE
        self.ui.control_controller_connect.setText('CONNECT')
        self.ui.control_controller_connect.setChecked(False)
        self.ui.config_controller_connect.setText('CONNECT')
        self.ui.config_controller_connect.setChecked(False)
        
        # STOP UPDATING CONTROLLER VALUES  
        self.controller.stopControllerEventLoop()
        
        # UNINITIALISE JOYSTICK MODULE
        quit()

    def processControllerInput(self, buttonStates, joystickValues):
        """
        PURPOSE

        Processes the controller inputs to perform the desired actions.

        INPUT

        - buttonStates = array containing the state of each controller button.
        - joystickValues = array containing the value of each controller joystick.

        RETURNS

        NONE
        """
        # UPDATE CONTROLLER VALUES DISPLAY
        self.ui.controllerDisplay.updateDisplay(buttonStates, joystickValues)
        
        self.processButtons(buttonStates)
        self.processJoysticks(joystickValues)

    def processButtons(self, buttonStates):
        """
        PURPOSE
        
        Analyses the states of all the buttons.
        If a button has been pressed, the corresponding control that the button is binded to is toggled.

        INPUT

        - buttonStates = array containined the state of each button on the XBOX controller (1 or 0).

        RETURNS

        NONE
        """
        # CYCLE THROUGH EACH BUTTON
        for index, buttonState in enumerate(buttonStates):
            
            # FIND THE NAME OF THE BUTTON ('A', 'B', 'X', 'Y' ETC.)
            whichButton = self.ui.controller.buttonLabels[index]
            
            # FIND WHICH ROV CONTROL USES THAT KEYBINDING
            try:
                whichControl = self.ui.keybindings.bindings.index(whichButton)
                buttonExists = True
            except:
                buttonExists = False

            if buttonExists:
                # BUTTON PRESSED
                if buttonState == 1:
                    # IF BUTTON HAS PREVIOUSLY BEEN RELEASED
                    if self.ui.controller.buttonReleased[index]:
                        # SET BUTTON TO BE IGNORED IN UNTIL IT IS RELEASED
                        self.ui.controller.buttonReleased[index] = False
                        # CALL FUNCTION LINKED TO BINDING
                        self.callBindingFunction(whichControl, buttonState)

                # BUTTON RELEASED
                else:
                    self.ui.controller.buttonReleased[index] = True

                    # TO CALL FUNCTIONS UPON BUTTON RELEASE
                    self.callBindingFunction(whichControl, buttonState)

    def callBindingFunction(self, control, state):
        """
        PURPOSE

        Links the keybinding being activated to a function to execute.

        INPUT

        - control = the index of the keybinding being activated.
        - state = state of the button linked to the control (1 or 0)

        RETURNS

        NONE
        """
        # TOGGLE ROV CONTROL DIRECTION
        if control == 0 and state:
            self.ui.thrusters.toggleControlDirection()

        # TOGGLE JOYSTICK SENSITIVITY
        if control == 1 and state:
            currentValue = self.ui.controllerDisplay.joystickSlider.value()
            if currentValue < 3:
                self.ui.controllerDisplay.changeJoystickSensitivity(currentValue + 1)
            else:
                self.ui.controllerDisplay.changeJoystickSensitivity(1)

        # ACTIVATE/DE-ACTIVATE RIGHT YAW
        if control == 2:
            self.ui.thrusters.yawState[0] = state             
        
        # ACTIVATE/DE-ACTIVATE LEFT YAW
        if control == 3:
            self.ui.thrusters.yawState[1] = state

        # TOGGLE YAW SENSITIVITY
        if control == 4 and state:
            currentValue = self.ui.controllerDisplay.yawSlider.value()
            if currentValue < 3:
                self.ui.controllerDisplay.changeYawSensitivity(currentValue + 1)
            else:
                self.ui.controllerDisplay.changeYawSensitivity(1)
        
        # TOGGLE ACTUATOR
        elif control > 4 and state:
            # NUMBER OF NON-ACTUATOR BINDINGS
            startingIndex = len(self.ui.keybindings.bindings) - self.ui.actuators.quantity
            
            # INDEX OF ACTUATOR
            whichActuator = control - startingIndex

            self.ui.actuators.toggleActuator(whichActuator)

    def processJoysticks(self, joystickValues):
        """
        PURPOSE

        Sends the joystick values through a series of filtering algorithms to calculate the speed of each thruster.

        INPUT
        
        - joystickValues = an array containing the filtered values of all the joysticks (-1 -> 1).

        RETURNS
        
        NONE
        """
        controllerSensitivity = self.ui.controllerDisplay.joystickSensitivity
        yawSensitivity = self.ui.controllerDisplay.yawSensitivity

        # GET YAW DIRECTION
        yawDirection, _ = self.ui.thrusters.getYaw()
            
        # CONVERT JOYSTICK VALUES TO THRUSTER SPEEDS
        thrusterSpeeds = self.ui.thrusters.thrustVectorAlgorithm(joystickValues, yawDirection, controllerSensitivity, yawSensitivity)

        # FILTER THRUSTER SPEEDS AND SEND TO ROV
        self.ui.thrusters.convertThrusterSpeeds(thrusterSpeeds)

    ###########################
    ## ROV CONTROL FUNCTIONS ##
    ###########################
    def changeActuators(self, actuatorStates):
        """
        PURPOSE

        Sends commmand to ROV when an actuator has been toggled.

        INPUT

        - actuatorStates = array contaning the state of each actuator.

        RETURNS

        NONE
        """
        # SEND COMMAND TO ROV
        self.comms.setActuators(actuatorStates)

    def changeThrusters(self, thrusterSpeeds):
        """
        PURPOSE

        Send command to ROV to set the speed of each thruster.

        INPUT

        - thrusterSpeeds = array containing the desired speed of each thruster. (1 - 999).

        RETURNS

        NONE
        """
        # SEND COMMAND TO ROV
        self.comms.setThrusters(thrusterSpeeds)

    ###########################
    ##### OTHER FUNCTIONS #####
    ###########################
    def startupProcedure(self):
        """
        PURPOSE

        Calls start up function to execute once ROV serial communication is connected.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # ARM THE THRUSTER ESCs
        self.comms.armThrusters()

        # START POLLING SENSORS VALUES
        self.getSensorReadings()

    def getSensorReadings(self):
        """
        PURPOSE

        Requests sensor readings from ROV and updates GUI.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # SENSOR POLLING RATE (HZ)
        refreshRate = 10

        # START QTIMER TO REPEATEDLY UPDATE SENSORS AT THE DESIRED POLLING RATE 
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.getSensorReadings)
        self.timer.start(1000*1/refreshRate)
        
        # STOP REQUESTING SENSOR VALUES IF ROV IS DISCONNECTED
        if self.comms.commsStatus == False:
            self.timer.stop()
        
        else:
            # REQEST SINGLE READING
            sensorReadings = self.comms.getSensors()

            # UPDATE GUI
            self.ui.sensors.updateSensorReadings(sensorReadings)

    ###############################
    #### COMPUTER VISION TASKS ####
    ###############################
    def initialiseVisionWidgets(self):
        """
        PURPOSE

        Initialises widget for each machine vision task.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.animation = SLIDE_ANIMATION(self.ui.control_vision_stacked_widget)
        self.animation.setSpeed(300)

        # MOSIAC TASK
        self.mosaicPopup = MOSAIC_POPUP_WINDOW(self.ui.scroll_mosaic_task)
        
        # TRANSECT LINE TASK
        self.transectLinePopup = TRANSECT_LINE_POPUP_WINDOW(self.ui.group_box_transect_task, self.ui.cameraThreadList[0])

    def changeVisionButtons(self, index, status):
        """
        PURPOSE

        Changes the appearence of the machine vision 'Start' buttons depending which task is active.

        INPUT

        - index = position of the button in the vision tasks group box.
        - status = the current state of the task.

        RETURNS

        NONE
        """
        # GROUP BOX CONTAINING THE START BUTTONS FOR EACH VISION TASK
        layout = self.ui.group_box_tasks.layout()
        
        for i in range(len(self.ui.visionTaskStatus)):
            button = layout.itemAtPosition(i, 1).widget()
            if i == index:
                if status:
                    button.setText("Stop")
                    button.setChecked(True)
                else:
                    button.setText("Start")
                    button.setChecked(False)
            else:
                button.setText("Start")
                button.setChecked(False)
                self.ui.visionTaskStatus[i] = False

    def popupVisionTask(self, task):
        """
        PURPOSE

        Reveals popup window for specific machine vision task.

        INPUT

        - task = the index of the task being activated (0,1,2).

        RETURNS

        NONE
        """
        if self.animation.animationComplete:
            if self.ui.visionTaskStatus[task] == False:
                # OPEN WIDGET
                self.ui.visionTaskStatus[task] = True
                self.changeVisionButtons(task, True)
                self.animation.jumpTo(task + 1)
                
            else:
                # CLOSE WIDGET
                self.ui.visionTaskStatus[task] = False
                self.changeVisionButtons(task, False)
                self.animation.jumpTo(0)

        else:
            # IGNORE ANY OTHER TASK BUTTONS WHILE ANIMATION IS IN PROGRESS
            if True in self.ui.visionTaskStatus:
                activeTask = self.ui.visionTaskStatus.index(True)
                self.changeVisionButtons(activeTask, True)

    @pyqtSlot()       
    def receiveMosaicTask(self):
        """
        PURPOSE

        Processes data sent back from the mosaic algorithm.

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass
       
    @pyqtSlot()
    def receiveShapeDetectionTask(self):
        """
        PURPOSE

        Processes data sent back from the shape detection algorithm.#

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

    @pyqtSlot()
    def receiveTransectLineTask(self):
        """
        PURPOSE

        Processes data sent back from the transect line algorithm.

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

    @pyqtSlot()
    def receiveCoralHealthTask(self):
        """
        PURPOSE

        Processes data sent back from the coral health algorithm.

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

class CONFIG():
    """
    PURPOSE

    Contains functions relating to the configuration tab.
    """
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3, Object4):
        """
        PURPOSE

        Constructor for Configuration tab object.

        INPUT

        - Object1 = 'UI' class
        - Object2 = 'CONTROL_PANEL' class
        - Object3 = 'CONTROLLER' class
        - Object4 = 'ROV_SERIAL' class

        RETURNS

        NONE
        """
        # CREATE OBJECTS
        self.ui = Object1
        self.control = Object2
        self.controller = Object3
        self.comms = Object4

    ##########################
    ##### COMMS SETTINGS #####
    ##########################
    def changeComPort(self, index):
        """
        PURPOSE

        Allows user to manually select a COM port to connect to without performing an identity check.

        INPUT

        - index = the menu index selected.

        RETURNS

        NONE
        """
        # GET LIST OF AVAILABLE COM PORTS
        comPorts = [self.ui.config_com_port_list.itemText(i) for i in range(self.ui.config_com_port_list.count())] 

        self.comms.rovComPort = comPorts[index]

    def refreshComPorts(self):
        """
        PURPOSE

        Manually refreshes the available COM port list.

        INPUT

        NONE

        RETURNS

        NONE
        """
        availableComPorts, rovComPort, identity = self.comms.findComPorts(self.ui.config_com_port_list, 115200, 'AVALONROV')
        self.ui.printTerminal("{} available COM ports found.".format(len(availableComPorts))) 

    def returnButtonStates(self):
        """
        PURPOSE

        Sends the current button controller states from the controller module to the keybindings module.
        This is activated by a signal in the keybindings module during the auto binding process.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.ui.keybindings.buttonStates = self.ui.controller.buttonStates

class TOOLBAR():
    """
    PURPOSE

    Contains function relating to the toolbar.
    """
    def __init__(self, Object1):
        """
        PURPOSE

        Constructor for toolbar object.

        INPUT

        - Object1 = UI class object.

        RETURNS

        NONE
        """
        self.ui = Object1

    def saveSettings(self):
        """
        PURPOSE

        Saves the current program configuration.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        if self.ui.fileName == "":
            self.ui.fileName, _ = QFileDialog.getSaveFileName(self.ui, 'Save File','./config', 'XML File (*.xml)')
        
        if self.ui.fileName != "": 
            # WRITE CURRENT PROGRAM CONFIGURATION TO XML FILE.
            self.ui.writeConfigFile()

            self.ui.printTerminal("Current program configuration saved to {}.".format(self.ui.fileName))

    def changePilotProfile(self):
        """
        PURPOSE

        Opens a popup windows to select the pilot profile to load.

        INPUT

        NONE

        RETURNS
        
        NONE
        """
        self.ui.profileSelector.showPopup()

    def resetSettings(self):
        """
        PURPOSE

        Resets the entire program to an unconfigured state.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.ui.printTerminal("Program configuration reset.")
        self.ui.resetConfig()
        #self.ui.programSetup()

    def loadSettings(self):
        """
        PURPOSE

        Opens a dialog window that allows the user to select a configuration XML file to set up the program.

        INPUTS

        NONE

        RETURNS 

        NONE
        """
        # USER CHOOSES CONFIGURATION FILE
        self.ui.fileName, _ = QFileDialog.getOpenFileName(self.ui, 'Open File','./config','XML File (*.xml)')
        if self.ui.fileName != '':
            self.ui.printTerminal("Loading {} configuration file".format(self.ui.fileName))
            self.ui.resetConfig()
            self.ui.configSetup()
        else:
            # SET BACK TO DEFAULT NAME IF USER DOES NOT SELECT A FILE
            self.ui.fileName = 'config/config.xml'

    def openUserManual(self):
        """
        PURPOSE

        Opens user manual that demonstrates how to use the program.

        INPUT 

        NONE

        RETURNS

        NONE
        """
        pass

    def openDocumentation(self):
        """
        PURPOSE

        Opens up doxygen html interface to view detailed code documentation.

        INPUT

        NONE

        RETURNS

        NONE
        """
        call(['open_documentation.bat'])

    def openGitHub(self):
        """
        PURPOSE

        Open the Avalon ROV GitHub page.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # OPEN AVALON GITHUB PAGE IN BROWSER
        open('https://github.com/AvalonROV')

    def toggleTheme(self):
        """
        PURPOSE

        Toggles program theme between Light and Dark.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # TOGGLE THEME
        self.ui.changeTheme()
        
    def restartProgram(self):
        """
        PURPOSE

        Closes and re-opens program.
        Used to apply new theme.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        self.saveSettings()
        self.ui.programExit()

        # RUNNING AS PYTHON PROGRAM
        try:
            subprocess.Popen(['python', 'main.py'])

        # RUNNING AS EXECUTABLE
        except:
            subprocess.Popen(['main.exe'])
        
        else:
            pass

        sys.exit(0)
            
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
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QApplication(sys.argv)

    # PROGRAM BOOT SPLASH SCREEN
    splash_pix = QPixmap('graphics/splash_screen.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()

    # SET PROGRAM STYLE
    app.setFont(QFont("Bahnschrift Regular", 10))
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon('graphics/icon.ico'))
    
    # INITIATE MAIN GUI OBJECT
    program = UI(app)
    program.setWindowTitle("Avalon ROV Control Interface")
    
    splash.finish(program)
    
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()
