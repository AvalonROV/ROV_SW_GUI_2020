#########################
######## IMPORTS ########
#########################

# PYQT5 MODULES
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimeLine
from PyQt5.QtWidgets import (QSplashScreen, QProgressBar, QGroupBox, QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QVBoxLayout, QLabel, QSlider, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QFont, QColor, QPalette, QPainter

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
import time
import numpy as np
import subprocess

# CUSTOM LIBRARIES
from avalonComms import ROV
from libraries.configuration_file. configurationFile import READ_CONFIG_FILE, WRITE_CONFIG_FILE
from libraries.controller.xboxController import CONTROLLER
from libraries.serial.rovComms import ROV_SERIAL
from libraries.computer_vision.mosaicTask.mosaicPopupWindow import MOSAIC_POPUP_WINDOW
from libraries.computer_vision.transectLineTask.transectLinePopupWindow import TRANSECT_LINE_POPUP_WINDOW
from libraries.computer_vision.transectLineTask.transectLineAlgorithm import TRANSECT_LINE_TASK
from libraries.camera.cameraCapture import CAMERA_CAPTURE
from libraries.animation.slideAnimation import SLIDE_ANIMATION
from libraries.simulation.rovModel import ROV_SIMULATION

class UI(QMainWindow):
    """
    PURPOSE

    Handles everything to do with the GUI.
    """
    # INITIAL SETUP
    def __init__(self, app):
        """
        PURPOSE

        Initialises objects, loads GUI and runs initial setup functions.

        INPUT

        - app = QApplication object (required to allow theme changing).

        RETURNS

        NONE
        """
        super(UI,self).__init__()
        # LOAD UI FILE
        uic.loadUi('gui.ui',self)

        # APP OBJECT TO ALLOW THEME CHANGING
        self.app = app

        # PROGRAM CLOSE EVENT
        self.app.aboutToQuit.connect(self.programExit)

        # INITIATE OBJECTS
        self.data = DATABASE()
        self.rov = ROV()
        self.controller = CONTROLLER()
        self.comms = ROV_SERIAL()
        self.control = CONTROL_PANEL(self, self.data, self.rov, self.controller, self.comms)
        self.config = CONFIG(self, self.data, self.control, self.rov, self.controller, self.comms)
        self.toolbar = TOOLBAR(self, self.data)

        # TELL ROV_SERIAL LIBRARY WHICH UI FUNCTION TO CALL IF COMMS FAILS
        self.comms.uiSerialFunction.connect(self.control.serialFailEvent)
        
        # FIND SCREEN SIZE
        self.data.sizeObject = QDesktopWidget().screenGeometry(-1)
        self.data.screenHeight = self.data.sizeObject.height()
        self.data.screenWidth = self.data.sizeObject.width()

        # SET DEFAULT WIDGET SIZE
        self.con_panel_functions_widget.resize(self.data.screenWidth/3,self.con_panel_functions_widget.height())

        # INITIATE CAMERA FEEDS
        self.initiateCameraFeed()

        # LOAD SETTINGS FROM CONFIG FILE
        self.configSetup()

        # LINK GUI BUTTONS TO FUNCTIONS
        self.linkControlPanelWidgets()
        self.linkConfigWidgets()
        self.linkToolbarWidgets()

        # INITIALISE WIDGETS FOR THE MACHINE VISION TASKS AND ADD THEM TO THE GUI
        self.control.initialiseVisionWidgets()
        
        # RESIZE GUI PIXMAPS WHEN WINDOW IS RESIZED
        self.resizeEvent(QResizeEvent(self.size(), QSize()))

        # INITIAL STARTUP MESSAGE
        self.printTerminal("Welcome to the Avalon ROV control interface.")
        self.printTerminal("Click 'Help' on the taskbar to access the user manual.")
        self.printTerminal("Connect to the ROV and CONTROLLER to get started.")
    
        # INITIALISE UI
        self.showMaximized()

    ##################################
    ## CONFIGURATION FILE FUNCTIONS ##
    ##################################
    def configSetup(self):
        """
        PURPOSE

        Read the configuration file and configures the programs thruster, actuator, sensor, camera and controller settings.
        If no configuration file is found, the program will open with default settings. 

        INPUT

        NONE

        RETURNS

        NONE
        """
        # READ CONFIGURATION FILE
        self.readConfigFile()

        # APPLY SETTINGS TO GUI
        self.programSetup()

    def readConfigFile(self):
        """
        PURPOSE

        Reads the XML configuration file and stores the data in the DATABASE class.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # PARSE CONFIGURATION FILE
        configFile = READ_CONFIG_FILE(self.data.fileName)
        configFileStatus = configFile.parseFile()

        if configFileStatus:
            self.printTerminal('Configuration file found.')
    
            # READ THEME SETTINGS
            self.data.programTheme = configFile.readTheme()
            
            # READ THRUSTER SETTINGS
            self.data.thrusterPosition, self.data.thrusterReverseList = configFile.readThruster() 
            
            # READ ACTUATOR SETTINGS
            self.data.actuatorNumber, self.data.actuatorLabelList = configFile.readActuator()

            # READ KEYBINDING SETTINGS
            self.data.keyBindings = configFile.readKeyBinding()
            
            # READ SENSOR SETTINGS
            self.data.sensorNumber, self.data.sensorSelectedType = configFile.readSensor()

            # READ ANALOG CAMERA SETTINGS
            self.data.analogCameraNumber, self.data.analogCameraLabelList, self.data.analogDefaultCameraList = configFile.readAnalogCamera()

            # READ DIGITAL CAMERA SETTINGS
            self.data.digitalCameraNumber, self.data.digitalCameraLabelList, self.data.digitalCameraAddressList, self.data.digitalDefaultCameraList = configFile.readDigitalCamera()

        else:
            self.printTerminal('Configuration file not found.')

    def programSetup(self):
        """
        PURPOSE

        Applies the configuration settings to the GUI.

        INPUT

        NONE

        RETURNS

        NONE
        """    
        # SETUP THEME
        self.changeTheme(self.data.programTheme)

        # SETUP THRUSTERS
        self.config.setupThrusters()

        # SETUP KEYBINDINGS
        self.config.setupKeybindings()

        # UPDATE GUI WITH ACTUATOR DATA
        self.config.setupActuators()  
        
        # UPDATE GUI WITH SENSOR DATA
        self.config.setupSensors()
        
        # UPDATE GUI WITH ANALOG CAMERA DATA
        self.config.setupAnalogCamera() 
        
        # UPDATE GUI WITH DIGITAL CAMERA DATA
        self.config.setupDigitalCameras()

    #### FIX THIS ASAP ####
    def resetConfig(self, resetStatus):
        """
        PURPOSE

        Resets the program to default settings (nothing configured).
        
        INPUT

        - resetStatus = true when called via the 'Reset Configuration' button (so that the number of thruster automatically resets).

        RETURNS

        NONE
        """
        ###############################
        ### RESET THRUSTER SETTINGS ###
        ###############################
        for i in reversed(range(self.config_thruster_form.rowCount())): 
            self.config_thruster_form.removeRow(i)

        self.data.thrusterPosition = ['None'] * 8
        self.data.thrusterReverseList = [False] * 8

        # RETURN NUMBER OF THRUSTERS TO 8 IF RESET BUTTON IS PRESSED
        if resetStatus == True:
            self.config.setupThrusters(self.data.thrusterNumber, 
                                            self.config_thruster_form,
                                            self.data.thrusterPosition,
                                            self.data.thrusterPositionList,
                                            self.data.thrusterReverseList)

        ###############################
        ### RESET ACTUATOR SETTINGS ###
        ###############################
        self.data.actuatorLabelList = []
        # DELETE PREVIOUS ACTUATORS FROM GUI
        for number in range(self.data.actuatorNumber):
            # REMOVE ACTUATORS FROM CONFIG TAB
            self.config_actuator_form.removeRow(1) 
            # REMOVE ACTUATORS FROM CONTROL PANEL TAB
            self.control_panel_actuators.removeRow(0)
        self.config_actuators_number.setValue(0)
        self.data.actuatorNumber = 0

        ###############################
        #### RESET SENSOR SETTINGS ####
        ###############################
        self.data.sensorSelectedType = []
        # DELETE PREVIOUS SENSORS FROM GUI
        for i in reversed(range(self.control_panel_sensors.rowCount())): 
            self.control_panel_sensors.removeRow(i)
        for i in reversed(range(1, self.config_sensor_form.rowCount())): 
            self.config_sensor_form.removeRow(i)
            pass
        
        self.config_sensors_number.setValue(0)
        self.data.sensorNumber = 0

        ###############################
        #### RESET CAMERA SETTINGS ####
        ###############################
        # ANALOG
        self.data.analogDefaultCameraList = [0] * 4
        self.data.analogCameraList = []
        self.config_analog_cameras_number.setValue(0)
        self.config_analog_cameras_number.clear()
        self.config_camera_2_list.clear()
        self.config_camera_3_list.clear()
        self.config_camera_4_list.clear()
        # DIGITAL
        self.data.digitalCameraLabels = ['Camera 1', 'Camera 2', 'Camera 3']
        self.data.digitalDefaultCameraList = [0, 0, 0]
        self.data.digitalSelectedCameraList = [0, 1, 2]
        self.config.setupDigitalCameras()

        ###############################
        ## RESET KEYBINDING SETTINGS ##
        ###############################
        numberDelete = len(self.data.keyBindings)
        for index in range(numberDelete):
            self.config.removeKeyBinding(numberDelete - index - 1)

        # RE-ADD DEFAULT KEY BINDING TO SWITCH ROV ORIENTATION IF RESET BUTTON IS PRESSED
        if resetStatus == True:
            self.config.addKeyBinding("Switch Orientation", False)
            self.config.addKeyBinding("Change Sensitivity", False)
            self.config.addKeyBinding("Yaw Right", False)
            self.config.addKeyBinding("Yaw Left", False)
            self.config.addKeyBinding("Yaw Sensitivity", False)
        
    #################################
    ##### GUI LINKING FUNCTIONS #####
    #################################
    def linkControlPanelWidgets(self):
        """
        PURPOSE

        Links widgets in the control panel tab to their respective functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CHANGE GUI VIEW BUTTONS
        self.change_gui_control.clicked.connect(lambda state, view = 0: self.changeView(view))
        self.applyGlow(self.change_gui_control, "#0D47A1", 10)
        self.change_gui_control.setStyleSheet(self.data.blueButtonClicked)

        self.change_gui_config.clicked.connect(lambda statem, view = 1: self.changeView(view))
        self.applyGlow(self.change_gui_config, "#0D47A1", 10)
        self.change_gui_config.setStyleSheet(self.data.blueButtonDefault)

        # TAB CHANGE SLIDE ANIMATION
        self.animation = SLIDE_ANIMATION(self.gui_view_widget)
        self.animation.setSpeed(500)
        self.animation.setDirection(Qt.Vertical)

        # SPITTER
        self.control_panel_splitter.splitterMoved.connect(self.splitterEvent)

        # ROV CONNECT BUTTON
        self.control_rov_connect.clicked.connect(lambda buttonState = self.control_rov_connect: self.control.rovSerialConnection(buttonState))
        self.applyGlow(self.control_rov_connect, "#0D47A1", 10)
        self.control_rov_connect.setFixedHeight(self.control_rov_connect.geometry().height() * 1.5)
        self.control_rov_connect.setStyleSheet(self.data.blueButtonDefault)
        
        # CONTROLLER CONNECT BUTTON
        self.control_controller_connect.clicked.connect(self.control.controllerConnect)
        self.applyGlow(self.control_controller_connect, "#0D47A1", 10)
        self.control_controller_connect.setFixedHeight(self.control_controller_connect.geometry().height() * 1.5)
        self.control_controller_connect.setStyleSheet(self.data.blueButtonDefault)
        
        # SWITCH CONTROL DIRECTION BUTTON
        if self.data.programTheme:
            self.control_switch_direction.setIcon(QIcon('graphics/switch_direction_white.png'))
        else:
            self.control_switch_direction.setIcon(QIcon('graphics/switch_direction_black.png'))
        self.control_switch_direction.clicked.connect(self.control.switchControlDirection)
        self.control_switch_direction.setFixedHeight(self.control_switch_direction.geometry().height() * 1.5)
        self.control_switch_direction.setIconSize(QSize(50,50))
        self.applyGlow(self.control_switch_direction, "#679e37", 10)
        self.control_switch_direction_forward.setStyleSheet(self.data.greenText)
        
        # TIMER CONTROL BUTTONS
        self.control_timer_start.clicked.connect(self.control.toggleTimer)
        self.control_timer_start.setStyleSheet(self.data.buttonGreen)
        self.control_timer_reset.clicked.connect(self.control.resetTimer)
        self.control_timer.setNumDigits(11)
        self.control_timer.display('00:00:00:00')
        self.control_timer.setMinimumHeight(48)
        
        # MACHINE VISION TASK BUTTONS
        self.control_vision_mosaic.clicked.connect(self.control.popupMosaicTask)
        self.control_vision_shape_detection.clicked.connect(self.control.popupShapeDetectionTask)
        self.control_vision_transect_line.clicked.connect(self.control.popupTransectLineTask)
        self.control_vision_coral_health.clicked.connect(self.control.popupCoralHealthTask)

        # CAMERA ENABLE CHECKBOX
        self.camera_1_enable.setChecked(True)
        self.camera_2_enable.setChecked(True)
        self.camera_3_enable.setChecked(True)
        self.camera_1_enable.toggled.connect(lambda state, camera = 0: self.toggleCameraFeed(state, camera))
        self.camera_2_enable.toggled.connect(lambda state, camera = 1: self.toggleCameraFeed(state, camera))
        self.camera_3_enable.toggled.connect(lambda state, camera = 2: self.toggleCameraFeed(state, camera))

        # CONTROLLER SENSITIVITY SETTINGS
        self.control_sensitivity_slider.valueChanged.connect(self.control.changeSensitivity)
        self.control.changeSensitivity(2)

        # CONTROLLER SENSITIVITY SETTINGS
        self.yaw_sensitivity_slider.valueChanged.connect(self.control.changeYawSensitivity)
        self.control.changeYawSensitivity(2)

        # LINK EACH DEFAULT CAMERA DROP DOWN MENU TO THE SAME SLOT, PASSING CAMERA ID AS 1,2,3,4 ETC.
        self.control_camera_1_list.activated.connect(lambda index, camera = 0: self.control.changeAnalogCameraFeed(index, camera))
        self.control_camera_2_list.activated.connect(lambda index, camera = 1: self.control.changeAnalogCameraFeed(index, camera))
        self.control_camera_3_list.activated.connect(lambda index, camera = 2: self.control.changeAnalogCameraFeed(index, camera))
        self.control_camera_4_list.activated.connect(lambda index, camera = 3: self.control.changeAnalogCameraFeed(index, camera))

        # LINK EACH DIGITAL CAMERA DROP DOWN MENU TO THE SAME SLOT, PASSING CAMERA ID AS 1,2,3,4 ETC.
        self.camera_feed_1_menu.activated.connect(lambda index, camera = 0: self.changeCameraFeedMenu(index, camera))
        self.camera_feed_2_menu.activated.connect(lambda index, camera = 1: self.changeCameraFeedMenu(index, camera))
        self.camera_feed_3_menu.activated.connect(lambda index, camera = 2: self.changeCameraFeedMenu(index, camera))

        # CAMERA FEED CLICK EVENT
        self.camera_feed_1.mousePressEvent = lambda event, cameraFeed = 0: self.changeCameraFeed(event, cameraFeed)
        self.camera_feed_2.mousePressEvent = lambda event, cameraFeed = 1: self.changeCameraFeed(event, cameraFeed)
        self.camera_feed_3.mousePressEvent = lambda event, cameraFeed = 2: self.changeCameraFeed(event, cameraFeed)

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
        self.config_rov_connect.clicked.connect(lambda buttonState = self.config_rov_connect: self.control.rovSerialConnection(buttonState))
        self.applyGlow(self.config_rov_connect, "#0D47A1", 10)
        self.config_rov_connect.setFixedHeight(self.config_rov_connect.geometry().height() * 1.5)
        self.config_rov_connect.setStyleSheet(self.data.blueButtonDefault)
        
        # CONTROLLER CONNECT BUTTON
        self.config_controller_connect.clicked.connect(self.control.controllerConnect)
        self.applyGlow(self.config_controller_connect, "#0D47A1", 10)
        self.config_controller_connect.setFixedHeight(self.config_controller_connect.geometry().height() * 1.5)
        self.config_controller_connect.setStyleSheet(self.data.blueButtonDefault)
            
        self.config_com_port_list.activated.connect(self.config.changeComPort) 
        self.config_find_com_ports.clicked.connect(self.config.refreshComPorts)   
        self.config_sensors_number.editingFinished.connect(self.config.changeSensorsNumber)
        self.config_analog_cameras_number.editingFinished.connect(self.config.changeAnalogCamerasNumber)
        self.config_digital_cameras_number.editingFinished.connect(self.config.changeDigitalCamerasNumber)
        self.config_actuators_number.editingFinished.connect(self.config.changeActuatorsNumber)

        # DIGITAL DEFAULT CAMERA FEEDS
        self.config_digital_default_1.activated.connect(lambda index, camera = 0: self.config.changeDigitalDefault(index, camera))
        self.config_digital_default_2.activated.connect(lambda index, camera = 1: self.config.changeDigitalDefault(index, camera))
        self.config_digital_default_3.activated.connect(lambda index, camera = 2: self.config.changeDigitalDefault(index, camera))

        # LINK EACH DEFAULT CAMERA DROP DOWN MENU TO THE SAME SLOT, PASSING THE CAMERA ID AS 1,2,3,4 ETC.
        self.config_analog_default_1.activated.connect(lambda index, camera = 0: self.config.changeAnalogDefaultCameras(index, camera))
        self.config_analog_default_2.activated.connect(lambda index, camera = 1: self.config.changeAnalogDefaultCameras(index, camera))
        self.config_analog_default_3.activated.connect(lambda index, camera = 2: self.config.changeAnalogDefaultCameras(index, camera))
        self.config_analog_default_4.activated.connect(lambda index, camera = 3: self.config.changeAnalogDefaultCameras(index, camera))

        # CREATE INDICATORS FOR CONTROLLER VALUES
        self.controller.setupControllerValuesDisplay(self.config_controller_form)

        # ADD OPENGL ROV SIMULATION
        rovModel = ROV_SIMULATION()
        self.config_simulation_graph.addWidget(rovModel)

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
        self.toolbar_save_settings.triggered.connect(self.toolbar.saveSettings)
        self.toolbar_open_documentation.triggered.connect(self.toolbar.openDocumentation)
        self.toolbar_open_github.triggered.connect(self.toolbar.openGitHub)
        self.toolbar_toggle_theme.triggered.connect(self.toolbar.toggleTheme)

    #############################
    ### CAMERA FEED FUNCTIONS ###
    #############################
    def initiateCameraFeed(self):
        """
        PURPOSE

        Starts each camera feed in a new thread.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.cameraFeeds = [self.camera_feed_1, self.camera_feed_2, self.camera_feed_3]

        # INITIATE CAMERAS IN QTHREADS
        
        # PRIMARY CAMERA        
        self.camThread1 = CAMERA_CAPTURE()
        self.camThread1.cameraNewFrameSignal.connect(self.updateCamera1Feed)
        self.camThread1.start()
        
        # SECONDARY CAMERA 1
        self.camThread2 = CAMERA_CAPTURE()
        self.camThread2.cameraNewFrameSignal.connect(self.updateCamera2Feed)
        self.camThread2.start()
        
        # SECONDARY CAMERA 2
        self.camThread3 = CAMERA_CAPTURE()
        self.camThread3.cameraNewFrameSignal.connect(self.updateCamera3Feed)
        self.camThread3.start()

    def toggleCameraFeed(self, status, feed):
        """
        PURPOSE

        Turns specific camera feed off.

        INPUT

        - status = True to turn ON, False to turn OFF.
        - feed = the camera to be toggled (1,2,3).

        RETURNS

        NONE
        """
        if feed == 0:
            if status:
                self.camThread1.feedBegin()
                self.camThread1.start()
            else:
                self.camThread1.feedStop()
                
        if feed == 1:
            if status:
                self.camThread2.feedBegin()
                self.camThread2.start()
            else:
                self.camThread2.feedStop()

        if feed == 2:
            if status:
                self.camThread3.feedBegin()
                self.camThread3.start()
            else:
                self.camThread3.feedStop()

    @pyqtSlot(QPixmap)
    def updateCamera1Feed(self, frame):
        """
        PURPOSE

        Refreshes camera feed 1 with a new frame.

        INPUT

        - frame = QImage containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        pixmap = frame.scaled(self.cameraFeeds[0].size().width(), self.cameraFeeds[0].size().height(), Qt.KeepAspectRatio)
        self.cameraFeeds[0].setPixmap(pixmap)

    @pyqtSlot(QPixmap)
    def updateCamera2Feed(self, frame):
        """
        PURPOSE

        Refreshes camera feed 2 with a new frame.

        INPUT

        - frame = QImage containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        pixmap = frame.scaled(self.cameraFeeds[1].size().width(), self.cameraFeeds[1].size().height(), Qt.KeepAspectRatio)
        self.cameraFeeds[1].setPixmap(pixmap)

    @pyqtSlot(QPixmap)
    def updateCamera3Feed(self, frame):
        """
        PURPOSE

        Refreshes camera feed 3 with a new frame.

        INPUT

        - frame = QImage containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        pixmap = frame.scaled(self.cameraFeeds[2].size().width(), self.cameraFeeds[2].size().height(), Qt.KeepAspectRatio)
        self.cameraFeeds[2].setPixmap(pixmap)

    def changeCameraFeed(self, event, cameraFeed):
        """
        PURPOSE

        Changes which camera is shown in the main camera feed. When a secondary camera feed is clicked, it is swapped with the current primary camera feed.

        INPUT

        - event = Mouse click event.
        - cameraFeed = Camera feed that has been clicked on (1,2,3).

        RETURNS

        NONE
        """
        if cameraFeed == 0:
            pass

        if cameraFeed == 1:
            self.cameraFeeds[0], self.cameraFeeds[1] = self.cameraFeeds[1], self.cameraFeeds[0]
              
        if cameraFeed == 2:
            self.cameraFeeds[0], self.cameraFeeds[2] = self.cameraFeeds[2], self.cameraFeeds[0]

    def changeCameraFeedMenu(self, index, cameraFeed):
        """
        PURPOSE

        Changes the camera feed from the menu options.

        INPUTS

        - index = menu index of the camera selected.
        - cameraFeed = the camera feed that is being modified.
        """
        # NOT YET IMPLEMENTED
        pass

    #############################
    ###### THEME FUNCTIONS ######
    #############################
    def changeTheme(self, theme):
        """
        PURPOSE

        Change the program theme between light and dark.

        INPUT

        - theme = True for dark theme, False for light theme.

        RETURNS 

        NONE
        """
        # APPLY DARK THEME
        if theme:

            # LOAD AVALON LOGO
            self.setLogo(True)

            # APPLY CUSTOM STYLESHEETS
            self.setStyleSheets(True)
        
            # CREATE QPALETTE
            darkPalette = QPalette()
            darkPalette.setColor(QPalette.Window, QColor("#161616"))        # MAIN WINDOW BACKGROUND COLOR
            darkPalette.setColor(QPalette.WindowText, QColor("#fafafa"))    # TEXT COLOR
            darkPalette.setColor(QPalette.Base,QColor("#323232"))           # TEXT ENTRY BACKGROUND COLOR
            darkPalette.setColor(QPalette.Text,QColor("#fafafa"))           # TEXT ENTRY COLOR
            darkPalette.setColor(QPalette.Button,QColor("#353535"))         # BUTTON COLOR
            darkPalette.setColor(QPalette.ButtonText,QColor("#fafafa"))     # BUTTON TEXT COLOR       

            # MODIFY GROUP BOXES
            self.changeGroupBoxColor()
            
            # APPLY CUSTOM COLOR PALETTE
            self.app.setPalette(darkPalette)
            
        # APPLY DEFAULT THEME
        else:
            # LOAD AVALON LOGO
            self.setLogo(False)

            # APPLY CUSTOM STYLESHEETS
            self.setStyleSheets(False)

            # CREATE QPALETTE
            lightPalette = self.app.style().standardPalette()
            
            self.app.setPalette(lightPalette)

    def setStyleSheets(self, theme):
        """
        PURPOSE

        Sets the widget stylesheets for either the light or dark theme.

        INPUT

        - theme = True for dark theme, False for light theme.

        RETURNS

        NONE
        """
        # DARK THEME
        if theme:
            self.data.greenText = 'color: #679e37'
            self.data.redText = 'color: #c62828'
            self.data.disabledText = 'color: rgba(0,0,0,40%);'
            self.data.actuatorGreen = 'color: white; background-color: #679e37; border-radius: 20px'
            self.data.actuatorRed = 'color: white; background-color: #c62828; border-radius: 20px'
            self.data.buttonGreen = 'color: black; background-color: #679e37;'
            self.data.buttonRed = 'color: black; background-color: #c62828;'
            self.data.blueButtonClicked = 'background-color: #0D47A1; color: white; font-weight: bold;'
            self.data.blueButtonDefault = 'color: white; font-weight: bold;'

        # LIGHT THEME
        else:
            self.data.greenText = 'color: #679e37'
            self.data.redText = 'color: #c62828'
            self.data.disabledText = 'color: rgba(0,0,0,25%);'
            self.data.actuatorGreen = 'background-color: #679e37'
            self.data.actuatorRed = 'background-color: #c62828'
            self.data.buttonGreen = 'color: black; background-color: #679e37;'
            self.data.buttonRed = 'color: black; background-color: #c62828;'
            self.data.blueButtonClicked = 'background-color: #0D47A1; color: white; font-weight: bold;'
            self.data.blueButtonDefault = 'color: #0D47A1; font-weight: bold;'

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
            avalonPixmap = QPixmap('graphics/logo_white.png')
            avalonPixmap = avalonPixmap.scaledToWidth(250, Qt.SmoothTransformation)
            self.avalon_logo.setPixmap(avalonPixmap)

        # LIGHT THEME
        else:
            self.avalon_logo.clear()
            avalonPixmap = QPixmap('graphics/logo.png')
            avalonPixmap = avalonPixmap.scaledToWidth(250, Qt.SmoothTransformation)
            self.avalon_logo.setPixmap(avalonPixmap)

    ###########################
    ##### OTHER FUNCTIONS #####
    ###########################
    def changeView(self, view):
        """
        PURPOSE

        Switches between the 'Control Panel' tab and the 'Configuration' tab within the program. 
        The camera feeds are disabled whilst the program is in the 'Configuration' tab.

        INPUT

        - view = the page to transition to. 0 = Control Panel, 1 = Configuration.

        RETURNS

        NONE
        """
        if self.animation.animationComplete:
            # TRANSITION TO CONTROL PANEL TAB
            if view == 0:
                self.animation.screenPrevious()
                self.change_gui_control.setStyleSheet(self.data.blueButtonClicked)
                self.change_gui_config.setStyleSheet(self.data.blueButtonDefault)

                # RESTART CAMERA FEEDS
                if self.camera_1_enable.isChecked():
                    self.camThread1.feedBegin()
                    self.camThread1.start()
                if self.camera_2_enable.isChecked():
                    self.camThread2.feedBegin()
                    self.camThread2.start()
                if self.camera_3_enable.isChecked():
                    self.camThread3.feedBegin()
                    self.camThread3.start()

            # TRANSITION TO CONFIGURATION TAB
            if view == 1:
                # TURN OFF CAMERA FEEDS
                self.camThread1.feedStop()
                self.camThread2.feedStop()
                self.camThread3.feedStop()

                self.animation.screenNext()
                self.change_gui_control.setStyleSheet(self.data.blueButtonDefault)
                self.change_gui_config.setStyleSheet(self.data.blueButtonClicked)

    def applyGlow(self, widget, color, blurRadius):
        """
        PURPOSE

        Applies a coloured underglow effect to a widget.

        INPUT

        - widget = pointer to the widget to apply the glow to.
        - color = color to apply to the glow (HEX format)
        - blueRadius = radius of the glow.

        RETURNS

        NONE
        """
        shadowEffect = QGraphicsDropShadowEffect()
        shadowEffect.setBlurRadius(blurRadius)
        shadowEffect.setColor(QColor(color))
        shadowEffect.setXOffset(0)
        shadowEffect.setYOffset(0)
        # APPLY GLOW TO WIDGET
        widget.setGraphicsEffect(shadowEffect)

    def changeGroupBoxColor(self):
        """
        PURPOSE

        Modifies the style of every group box in the program for the dark teme, by adding a corner radius and changing the colour.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.gui_view_widget.setStyleSheet("""QGroupBox {
                                            background-color: #212121;
                                            border-radius: 20px;
                                            font-size: 12pt;
                                            margin-top: 1.2em;
                                            padding-top: 10px;
                                            padding-bottom: 10px;
                                            padding-left: 10px;
                                            padding-right: 10px;
                                            }
                                            """)

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

    def resizeEvent(self, event):
        """
        PURPOSE

        Function is called whenever the programs window size is changed.

        INPUT

        - event = QResizeEvent event.

        RETURNS

        NONE
        """
        self.changePixmapSize()
        QMainWindow.resizeEvent(self, event)

    def splitterEvent(self):
        """
        PURPOSE

        Function is called whenever the control panel splitter is activated.

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

    Handles everything that happens on the Control Panel tab.
    """
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3, Object4, Object5):
        """
        PURPOSE

        Initialises objects.

        INPUT

        - Object1 = 'UI' class
        - Object2 = 'DATABASE' class
        - Object3 = 'ROV' class
        - Object4 = 'CONTROLLER' class
        - Object5 = 'ROV_SERIAL' class

        RETURNS

        NONE
        """
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2
        self.rov = Object3
        self.controller = Object4
        self.comms = Object5

        #self.comms = None

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
        
        # FIND ALL AVAILABLE COM PORTS
        self.ui.printTerminal('Searching for available COM ports...')
        
        availableComPorts, rovComPort, identity = self.comms.findComPorts(self.ui.config_com_port_list, 115200, self.data.rovID)
        self.data.rovComPort = rovComPort
        
        self.ui.printTerminal("{} available COM ports found.".format(len(availableComPorts)))
        self.ui.printTerminal('Device Identity: {}'.format(identity))
        
        # ATTEMPT CONNECTION TO ROV COM PORT
        status, message = self.comms.serialConnect(rovComPort, 115200)
        self.ui.printTerminal(message)

        # IF CONNECTION IS SUCCESSFUL
        if status == True:
            # MODIFY BUTTON STYLE
            self.ui.control_rov_connect.setText('DISCONNECT')
            self.ui.config_rov_connect.setText('DISCONNECT')
            self.ui.control_rov_connect.setStyleSheet(self.data.blueButtonClicked)
            self.ui.config_rov_connect.setStyleSheet(self.data.blueButtonClicked)

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
        self.ui.control_rov_connect.setStyleSheet(self.data.blueButtonDefault)
        self.ui.config_rov_connect.setStyleSheet(self.data.blueButtonDefault)
        
        # CLOSE COM PORT
        if self.comms.commsStatus:
            self.ui.printTerminal("Disconnected from {}".format(self.data.rovComPort))
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
    def controllerConnect(self):
        """
        PURPOSE

        Initialises communication with the XBOX controller.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.controllerConnectButtonStatus == False:
            
            # DISABLE CONTROLLER CONNECT BUTTONS
            self.ui.control_controller_connect.setEnabled(False)
            self.ui.config_controller_connect.setEnabled(False)

            # INITIATE COMMUNICATION WITH THE CONTROLLER
            connectionStatus, controllerNumber, message = self.controller.findController("Controller (Xbox One For Windows)")
            self.ui.printTerminal(message)
            
            if connectionStatus == True:
                # START READING CONTROLLER INPUTS IN A TIMED THREAD, RETURN VALUES TO PROCESSING FUNCTIONS
                self.controller.startControllerEventLoop(controllerNumber, self.processButtons, self.processJoysticks)
                
                # UPDATE BUTTON STYLE
                self.data.controllerConnectButtonStatus = True
                self.ui.control_controller_connect.setText('DISCONNECT')
                self.ui.config_controller_connect.setText('DISCONNECT')
                self.ui.control_controller_connect.setStyleSheet(self.data.blueButtonClicked)
                self.ui.config_controller_connect.setStyleSheet(self.data.blueButtonClicked)

            # ENABLE CONTROLLER CONNECT BUTTONS
            self.ui.control_controller_connect.setEnabled(True)
            self.ui.config_controller_connect.setEnabled(True)

        else:
            self.data.controllerConnectButtonStatus = False
            self.ui.control_controller_connect.setText('CONNECT')
            self.ui.config_controller_connect.setText('CONNECT')
            self.ui.control_controller_connect.setStyleSheet(self.data.blueButtonDefault)  
            self.ui.config_controller_connect.setStyleSheet(self.data.blueButtonDefault)
            # STOP UPDATING CONTROLLER VALUES  
            self.controller.stopControllerEventLoop()
            # UNINITIALISE JOYSTICK MODULE
            quit()

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
        self.data.buttonStates = buttonStates

        # CYCLE THROUGH EACH BUTTON
        for index, button in enumerate(buttonStates):
            
            # FIND THE NAME OF THE BUTTON IN QUESTION ('A', 'B', 'X', 'Y' ETC.)
            whichButton = self.data.controllerButtons[index]
            
            # FIND WHICH ROV CONTROL USES THAT KEYBINDING
            try:
                whichControl = self.data.keyBindings.index(whichButton)
                buttonExists = True
            except:
                buttonExists = False

            # IF BUTTON IS PRESSED
            if button == 1:
                # IF KEYBINDING EXISTS AND HAS PREVIOUSLY BEEN RELEASED
                if buttonExists == True and self.data.controllerButtonReleased[index] == True:
                    # PREVENT ACTUATOR BEING TOGGLED AGAIN UNTILL BUTTON IS RELEASED
                    self.data.controllerButtonReleased[index] = False
                    
                    # IF ROV CONTROL ORIENTATION IS BEING TOGGLED (SPECIAL CASE)
                    if whichControl == 0:
                        self.switchControlDirection()

                    # IF ROV CONTROLLER SENSITIVITY IS BEING CHANGED (SPECIAL CASE)
                    if whichControl == 1:
                        currentValue = self.ui.control_sensitivity_slider.value()
                        if currentValue < 3:
                            self.changeSensitivity(currentValue + 1)
                        else:
                            self.changeSensitivity(1)

                    # IF ROV YAW IS ACTIVATED (SPECIAL CASE)
                    # RIGHT YAW
                    if whichControl == 2:
                        self.data.yawButtonStates[0] = 1                    
                    # LEFT YAW
                    if whichControl == 3:
                        self.data.yawButtonStates[1] = 1

                    # IF ROV YAW SENSITIVITY IS BEING CHANGED (SPECIAL CASE)
                    if whichControl == 4:
                        currentValue = self.ui.yaw_sensitivity_slider.value()
                        if currentValue < 3:
                            self.changeYawSensitivity(currentValue + 1)
                        else:
                            self.changeYawSensitivity(1)
                    
                    # IF ROV ACTUATOR IS BEING TOGGLED
                    else: 
                        whichActuator = whichControl - 5
                        # FIND POINTER TO THE BUTTON WIDGET CORRESPONDING TO THE ACTUATOR
                        widgetPosition = (whichActuator * 2) + 1
                        widget = self.ui.control_panel_actuators.itemAt(widgetPosition).widget()
                        # TOGGLES ACTUATORS AND CHANGES APPEARANCE OF GUI BUTTON
                        self.changeActuators(whichActuator, widget)

            # WAIT FOR BUTTON TO BE RELEASED
            else:
                self.data.controllerButtonReleased[index] = True

                #IF ROV YAW IS DE-ACTIVATED (SPECIAL CASE)
                if buttonExists == True:
                    #RIGHT YAW
                    if whichControl == 2:
                        self.data.yawButtonStates[0] = 0
                    # LEFT YAW
                    if whichControl == 3:
                        self.data.yawButtonStates[1] = 0
        
    def processJoysticks(self, joystickValues):
        """
        PURPOSE

        Calculates the required speed of each thruster on the ROV to move a certain direction.

        INPUT
        
        - joystickValues = an array containing the filtered values of all the joysticks (-1 -> 1).

        RETURNS
        
        NONE
        """
        filteredThrusterSpeeds = [0] * self.data.thrusterNumber

        # CHECK IF YAW BUTTONS HAVE BEEN PRESSED
        yawDirection, yawActive = self.checkYaw()
        
        if joystickValues != self.data.joystickValues or yawActive == True:

            controllerSensitivity = self.data.controllerSensitivity
            yawSensitivity = self.data.yawSensitivity
            
            # APPLY THE THRUST VECTORING ALGORITHM
            filteredThrusterSpeeds = self.thrustVectorAlgorithm(joystickValues, yawDirection, controllerSensitivity, yawSensitivity)
        
            # SEND THRUSTER SPEEDS TO ROV
            self.changeThrusters(filteredThrusterSpeeds)
        
        # SAVE VALUES TO BE COMPARED IN THE NEXT CYCLE
        self.data.joystickValues = joystickValues
        self.data.yawButtonStatesPrevious = self.data.yawButtonStates.copy()
        
    def checkYaw(self):
        """
        PURPOSE

        Checks if the yaw buttons are pressed.

        INPUT

        NONE

        RETURNS

        - yawDirection = 1 for right yaw, -1 for left yaw, 0 for neutral
        - yawActive = True is the yaw has been activated or deactivated since previous controller update.

        """
        # YAW DIRECTION FROM BUTTONS
        if self.data.yawButtonStates[0] != self.data.yawButtonStates[1]:
            yawActive = True
            # RIGHT YAW
            if self.data.yawButtonStates[0] == 1:
                yawDirection = 1
            # LEFT YAW
            elif self.data.yawButtonStates[1] == 1:
                yawDirection = -1
            # NEUTRAL YAW
            else:
                yawDirection = 0
        else:
            yawDirection = 0
            # CHECK IF YAW HAS CHANGED FROM PREVIOUS STATE
            if self.data.yawButtonStatesPrevious != self.data.yawButtonStates:
                yawActive = True
            else:
                yawActive = False

        return yawDirection, yawActive

    def thrustVectorAlgorithm(self, joystickValues, yawDirection, controllerSensitivity, yawSensitivity):
        """
        PURPOSE 

        Calculate the required speed of each thruster to achieve a desired movement.

        INPUT

        - joystickValues = array containing the values of the controllers joysticks.
        - yawDirection = 1 for right yaw, -1 for left yaw, 0 for neutral.
        - controllerSensitivity = the sensitivity of the controller (0 -> 1)
        - yawSensitivity = the sensitivity of the yaw control (0 -> 1)

        RETURNS

        - filteredThrusterSpeeds = array containing the required speed of each thruster (001 -> 999)
        """
        # DECOMPOSE JOYSTICKS INTO MOTION AXIS
        right_left = joystickValues[0]
        forward_backward = -joystickValues[1]
        up_down = -joystickValues[2]
        pitch = joystickValues[3]
        roll = joystickValues[4]
        yaw = yawDirection * yawSensitivity

        # CALCULATE CONTRIBUTION TO MOTION FROM EACH THRUSTER
        speed_A = right_left + forward_backward - up_down - pitch - roll + yaw
        speed_B = - right_left + forward_backward - up_down - pitch + roll - yaw
        speed_C = - right_left - forward_backward - up_down + pitch + roll + yaw
        speed_D = right_left - forward_backward - up_down + pitch - roll - yaw
        speed_E = right_left + forward_backward + up_down + pitch + roll + yaw
        speed_F = - right_left + forward_backward + up_down + pitch - roll - yaw
        speed_G = - right_left - forward_backward + up_down - pitch - roll + yaw
        speed_H = right_left - forward_backward + up_down - pitch + roll - yaw

        filteredThrusterSpeeds = [speed_A, speed_B, speed_C, speed_D, speed_E, speed_F, speed_G, speed_H]
        
        # FIND THRUSTER WITH HIGHEST SPEED AND PEAK JOYSTICK VALUE
        maxSpeed = max((abs(speed) for speed in filteredThrusterSpeeds))
        maxJoystick = max((abs(position) for position in joystickValues))

        # SET FIXED SPEED FOR YAW CONTROL
        if yaw != 0 and maxJoystick == 0:
            maxJoystick = 0.5

        # NORMALISE ALL THRUSTER SPEEDS W.R.T THE FASTEST THRUSTER AND THE MAXIMUM JOYSTICK POSITION (MAX = 1)
        for i in range(len(filteredThrusterSpeeds)):
            if maxSpeed > 0:
                normalisedSpeed = controllerSensitivity * maxJoystick / maxSpeed
                filteredThrusterSpeeds[i] = round(normalisedSpeed * filteredThrusterSpeeds[i], 3)

        # CONVERT -1 -> 1 TO 1 -> 999 FOR ARDUINO MICROSECONDS SERVO SIGNAL
        for i in range(len(filteredThrusterSpeeds)):
            filteredThrusterSpeeds[i] = int(500 + filteredThrusterSpeeds[i]*499)
        
        return filteredThrusterSpeeds

    ###########################
    ## ROV CONTROL FUNCTIONS ##
    ###########################
    def changeActuators(self, actuator, buttonObject):
        """
        PURPOSE

        Sends commmand to ROV when an actuator has been toggled.
        Changes the appearance of the actuator button.

        INPUT

        - actuator = the actuator being toggled.
        - buttonObject = pointer to the actuator button widget.

        RETURNS

        NONE
        """
        if self.data.actuatorStates[actuator] == False:
            buttonObject.setText(self.data.actuatorLabelList[actuator][2])
            buttonObject.setStyleSheet(self.data.actuatorRed)
            self.data.actuatorStates[actuator] = True

        elif self.data.actuatorStates[actuator] == True:
            buttonObject.setText(self.data.actuatorLabelList[actuator][1])
            buttonObject.setStyleSheet(self.data.actuatorGreen)
            self.data.actuatorStates[actuator] = False

        # SEND COMMAND TO ROV
        self.comms.setActuators(self.data.actuatorStates)

    def changeThrusters(self, thrusterSpeeds, testStatus = False):
        """
        PURPOSE

        Prepares and sends desired thruster speeds to the communication library.

        INPUT

        - thrusterSpeed = array containing the desired speed of each thruster. (1 - 999).

        RETURNS

        NONE
        """
        # REVERSE THE DIRECTION OF THRUSTERS WHERE NECCESSARY
        tempThrusterSpeeds = thrusterSpeeds.copy()
        
        for i, speed in enumerate(tempThrusterSpeeds):
            if self.data.thrusterReverseList[i] == True:
                tempThrusterSpeeds[i] = 1000 - speed

        # IF THRUSTER ARE BEING INDIVIDUALLY TESTED
        if testStatus:
            # SEND COMMAND TO ROV
            self.comms.setThrusters(tempThrusterSpeeds)

        else:
            # MAPS THRUSTERS TO CORRECT ROV POSITION
            mappedThrusterSpeeds = [500] * 8

            for index, position in enumerate(self.data.thrusterPositionList):
                if position != "None":
                    try:
                        # FIND WHICH THRUSTER BELONGS TO THIS ROV POSITION
                        thrusterIndex = self.data.thrusterPosition.index(position)

                        # SET SPEED TO CORRECT THRUSTER
                        mappedThrusterSpeeds[thrusterIndex] = tempThrusterSpeeds[index - 1]
                    except:
                        pass
        
            # SEND COMMAND TO ROV
            #print(mappedThrusterSpeeds)
            self.comms.setThrusters(mappedThrusterSpeeds)

    def switchControlDirection(self):
        """
        PURPOSE

        Changes the control orientation of the ROV, to allow easy maneuvering in reverse.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.rovControlDirection == True:
            self.data.rovControlDirection = False
            self.ui.control_switch_direction_forward.setStyleSheet("")
            self.ui.control_switch_direction_reverse.setStyleSheet(self.data.greenText)
        else:
            self.data.rovControlDirection = True
            self.ui.control_switch_direction_forward.setStyleSheet(self.data.greenText)
            self.ui.control_switch_direction_reverse.setStyleSheet("")

    def changeSensitivity(self, sensitivity):
        """
        PURPOSE

        Selects the desired controller throttle sensitivity to control the ROV.
        Pilot can select between LOW, NORMAL and HIGH.

        INPUT

        - sensitivity = desired sensitivity of the controller (0 = LOW, 1 = NORMAL, 2 = HIGH).

        RETURNS

        NONE
        """
        # LOW SENSITIVITY
        if sensitivity == 1:
            self.data.controllerSensitivity = 1/3
            self.ui.control_sensitivity_slider.setValue(1)
            self.ui.control_sensitivity_low.setStyleSheet(self.data.greenText)
            self.ui.control_sensitivity_medium.setStyleSheet("")
            self.ui.control_sensitivity_high.setStyleSheet("")

        # NORMAL SENSITIVITY
        if sensitivity == 2:
            self.data.controllerSensitivity = 2/3
            self.ui.control_sensitivity_slider.setValue(2)
            self.ui.control_sensitivity_low.setStyleSheet("")
            self.ui.control_sensitivity_medium.setStyleSheet(self.data.greenText)
            self.ui.control_sensitivity_high.setStyleSheet("")

        # HIGH SENSITIVITY
        if sensitivity == 3:
            self.data.controllerSensitivity = 1
            self.ui.control_sensitivity_slider.setValue(3)
            self.ui.control_sensitivity_low.setStyleSheet("")
            self.ui.control_sensitivity_medium.setStyleSheet("")
            self.ui.control_sensitivity_high.setStyleSheet(self.data.greenText)

    def changeYawSensitivity(self, sensitivity):
        """
        PURPOSE

        Selects the desired yaw sensitivity to control the ROV.
        Pilot can select between LOW, NORMAL and HIGH.

        INPUT

        - sensitivity = desired sensitivity of the yaw control (0 = LOW, 1 = NORMAL, 2 = HIGH).

        RETURNS

        NONE
        """
        if sensitivity == 1:
            self.data.yawSensitivity = 1/3
            self.ui.yaw_sensitivity_slider.setValue(1)
            self.ui.yaw_sensitivity_low.setStyleSheet(self.data.greenText)
            self.ui.yaw_sensitivity_medium.setStyleSheet("")
            self.ui.yaw_sensitivity_high.setStyleSheet("")

        if sensitivity == 2:
            self.data.yawSensitivity = 2/3
            self.ui.yaw_sensitivity_slider.setValue(2)
            self.ui.yaw_sensitivity_low.setStyleSheet("")
            self.ui.yaw_sensitivity_medium.setStyleSheet(self.data.greenText)
            self.ui.yaw_sensitivity_high.setStyleSheet("")

        if sensitivity == 3:
            self.data.yawSensitivity = 1
            self.ui.yaw_sensitivity_slider.setValue(3)
            self.ui.yaw_sensitivity_low.setStyleSheet("")
            self.ui.yaw_sensitivity_medium.setStyleSheet("")
            self.ui.yaw_sensitivity_high.setStyleSheet(self.data.greenText)

    ###########################
    ##### TIMER FUNCTIONS #####
    ###########################
    def readSystemTime(self):
        """
        PURPOSE

        Reads the system time in a new thread and calculates the number of seconds elapsed since the timer was started.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CALCULATE SECONDS ELAPSED SINCE TIMER STARTED 
        currentTime = datetime.now()
        currentSeconds = (currentTime - self.startTime).total_seconds() + self.data.timerMem
        self.updateTimer(currentSeconds)
    
        # READ SYSTEM TIME EVERY 1 SECOND (TO REDUCE CPU USAGE)
        thread = Timer(0.5,self.readSystemTime)
        thread.daemon = True                            
        thread.start()
        
        # STOP THREAD IF STOP BUTTON CLICKED
        if self.data.timerEnabled == False:
            thread.cancel()
            self.data.timerMem = currentSeconds

    def toggleTimer(self):
        """
        PURPOSE

        Starts/Stops the timer.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.timerEnabled == False:
            self.data.timerEnabled = True
            self.ui.control_timer_start.setText('Stop')
            self.ui.control_timer_start.setStyleSheet(self.data.buttonRed)
            self.startTime = datetime.now()
            # START TIMER
            self.readSystemTime()
        else:
            self.data.timerEnabled = False
            self.ui.control_timer_start.setText('Start')
            self.ui.control_timer_start.setStyleSheet(self.data.buttonGreen)

    def resetTimer(self):
        """
        PURPOSE

        Resets the timer back to zero if the timer is stopped.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.timerEnabled == False:
            self.data.timerMem = 0
            self.updateTimer(0)

    def updateTimer(self, currentSeconds):
        """
        PURPOSE

        Converts seconds into DD:HH:MM:SS format and updates the timer widget on the GUI.

        INPUT

        - currentSeconds = the number of seconds since the timer was started.

        RETURNS

        NONE
        """
        # CONVERT SECONDS TO DD:HH:MM:SS
        minutes, seconds = divmod(currentSeconds,60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        # DISPLAY TIME SINCE MEASUREMENT START
        self.ui.control_timer.display('%02d:%02d:%02d:%02d' % (days, hours, minutes, seconds))

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
            for sensor, reading in enumerate(sensorReadings):
                if sensor < self.data.sensorNumber:
                    # FIND INDEX OF SENSOR TEXTBOX WIDGET
                    widgetIndex = (sensor * 2) + 1
                    textWidget = self.ui.control_panel_sensors.itemAt(widgetIndex).widget()
                    textWidget.setText(str(reading))

    def changeAnalogCameraFeed(self, index, camera):
        """
        PURPOSE

        Changes which analog camera is displayed on the camera feed.

        INPUT

        - index = the menu index selected.
        - camera = the feed number to display the camera on (0 -> 3).

        RETURNS

        NONE
        """
        self.data.analogSelectedCameraList[camera] = index

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

        self.mosaicPopup = MOSAIC_POPUP_WINDOW(self.ui.scroll_mosaic_task)
        self.transectLinePopup = TRANSECT_LINE_POPUP_WINDOW(self.ui.group_box_transect_task)

        self.transectLineTask = TRANSECT_LINE_TASK()

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
        
        for i in range(len(self.data.visionTaskStatus)):
            button = layout.itemAtPosition(i, 1).widget()
            if i == index:
                if status:
                    button.setText("Stop")
                    button.setStyleSheet(self.data.blueButtonClicked)
                else:
                    button.setText("Start")
                    button.setStyleSheet("")

            else:
                button.setText("Start")
                button.setStyleSheet("")
                self.data.visionTaskStatus[i] = False

    def popupMosaicTask(self):
        """
        PURPOSE

        Displays the widget for the Mosaic vision task.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.animation.animationComplete:
            if self.data.visionTaskStatus[0] == False:
                # OPEN WIDGET
                self.data.visionTaskStatus[0] = True
                self.changeVisionButtons(0, True)
                self.animation.jumpTo(1)
                
            else:
                #CLOSE WIDGET
                self.data.visionTaskStatus[0] = False
                self.changeVisionButtons(0, False)
                self.animation.jumpTo(0)
            
    def popupShapeDetectionTask(self):
        """
        PURPOSE

        Displays the widget for the Mosaic vision task.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.animation.animationComplete:
            if self.data.visionTaskStatus[1] == False:
                # OPEN WIDGET
                self.data.visionTaskStatus[1] = True
                self.changeVisionButtons(1, True)
                self.animation.jumpTo(2)
                
            else:
                # CLOSE WIDGET
                self.data.visionTaskStatus[1] = False
                self.changeVisionButtons(1, False)
                self.animation.jumpTo(0)
            
    def popupTransectLineTask(self):
        """
        PURPOSE

        Displays the widget for the Mosaic vision task.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.animation.animationComplete:
            if self.data.visionTaskStatus[2] == False:
                # OPEN WIDGET
                self.data.visionTaskStatus[2] = True
                self.changeVisionButtons(2, True)
                self.animation.jumpTo(3)

                self.ui.camThread1.processImage(self.transectLineTask)
                
            else:
                # CLOSE WIDGET
                self.data.visionTaskStatus[2] = False
                self.changeVisionButtons(2, False)
                self.animation.jumpTo(0)

                self.ui.camThread1.stopProcessing()

    def popupCoralHealthTask(self):
        """
        PURPOSE

        Displays the widget for the Mosaic vision task.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.animation.animationComplete:
            if self.data.visionTaskStatus[3] == False:
                # OPEN WIDGET
                self.data.visionTaskStatus[3] = True
                self.changeVisionButtons(3, True)
                self.animation.jumpTo(4)
                
            else:
                # CLOSE WIDGET
                self.data.visionTaskStatus[3] = False
                self.changeVisionButtons(3, False)
                self.animation.jumpTo(0)

class CONFIG():
    """
    PURPOSE

    Handles everything that happens on the Configuration tab.
    """
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3, Object4, Object5, Object6):
        """
        PURPOSE

        Constructor for Configuration tab object.

        INPUT

        - Object1 = 'UI' class
        - Object2 = 'DATABASE' class
        - Object3 = 'CONTROL_PANEL' class
        - Object4 = 'ROV' clsss
        - Object5 = 'CONTROLLER' class
        - Object6 = 'ROV_SERIAL' class

        RETURNS

        NONE
        """
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2
        self.control = Object3
        self.rov = Object4
        self.controller = Object5
        self.comms = Object6

    ##########################
    ##### COMMS SETTINGS #####
    ##########################
    def changeComPort(self, index):
        """
        PURPOSE

        Allows user to manually select the COM port to connect to without performing an identity check.

        INPUT

        - index = the menu index selected.

        RETURNS

        NONE
        """
        ### FEATURE NOT YET IMPLEMENTED ###
        pass

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

    #########################
    ### THRUSTER SETTINGS ###
    #########################
    def setupThrusters(self):
        """
        PURPOSE

        Adds specific number of thrusters to the GUI configration tab, with a ROV location menu, reverse checkbox and a test button.

        INPUT

        - thrusterNumber = the number of thrusters to add.
        - thrusterLayout = the form layout widget to add the widgets to.
        - thrusterPosition = array containing the ROV position of each thruster.
        - thrusterPositionList = array containing all the possible ROV thruster locations.
        - thrusterReverse = array containing the direction of each thruster.

        RETURNS

        NONE 
        """
        # NUMBER OF THRUSTERS TO ADD
        thrusterNumber = self.data.thrusterNumber

        for i in range(thrusterNumber):
            self.addThruster(self.ui.config_thruster_form,
                                self.data.thrusterPosition,
                                self.data.thrusterPositionList,
                                self.data.thrusterReverseList)
            
    def addThruster(self, thrusterLayout, thrusterPosition, thrusterPositionList, thrusterReverse):
        """
        PURPOSE

        Adds a single thruster to the configuration tab.

        INPUT

        - thrusterLayout = the form layout widget to add the widgets to.
        - thrusterPosition = array containing the ROV position of each thruster.
        - thrusterPositionList = array containing all the possible ROV thruster locations.
        - thrusterReverse = array containing the direction of each thruster.

        RETURNS

        NONE
        """
        # INDEX OF THE NEXT THRUSTER
        thrusterNumber = thrusterLayout.rowCount()

        # CREATE THRUSTER NUMBER LABEL
        thrusterLabel = QLabel("Thruster {}".format(thrusterNumber + 1))
        thrusterLabel.setStyleSheet("font-weight: bold;")
        thrusterLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # CREATE ROV LOCATION DROP DOWN MENU AND ADD ITEMS
        thrusterLocation = QComboBox()
        thrusterLocation.addItems(thrusterPositionList)           
        thrusterLocation.setCurrentIndex(thrusterPositionList.index(thrusterPosition[thrusterNumber]))
        # CREATE THRUSTER REVERSE CHECKBOX
        thrusterReverseCheck = QCheckBox()
        thrusterReverseCheck.setChecked(thrusterReverse[thrusterNumber])
        # CREATE THRUSTER TEST BUTTON
        thrusterTest = QPushButton("Test")
        
        # CREATE GRID LAYOUT
        layout = QGridLayout()
        label1 = QLabel('ROV Location')
        label1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label1,0,0)
        layout.addWidget(thrusterLocation,0,1)
        label2 = QLabel('Reversed')
        label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label2,1,0)
        layout.addWidget(thrusterReverseCheck,1,1)
        layout.addWidget(thrusterTest,2,1)

        # ADD TO CONFIG TAB FORM LAYOUT
        thrusterLayout.addRow(thrusterLabel, layout)

        # LINK EACH THRUSTER CONFIGURATION TO SAME SLOT, PASSING THE MENU INDEX, THRUSTER SELECTED, AND WHICH SETTING HAS BEEN CHANGED (POSITION, REVERSE, TEST, CONFIG)
        thrusterLocation.activated.connect(lambda index, thruster = thrusterNumber: self.thrusterPosition(index, thruster)) 
        thrusterReverseCheck.toggled.connect(lambda state, thruster = thrusterNumber, controlObject = thrusterReverseCheck: self.thrusterReverse(thruster, controlObject))
        thrusterTest.pressed.connect(lambda state = True, thruster = thrusterNumber, controlObject = thrusterTest: self.thrusterTest(state, thruster, controlObject))
        thrusterTest.released.connect(lambda state = False, thruster = thrusterNumber, controlObject = thrusterTest: self.thrusterTest(state, thruster, controlObject))

    def thrusterPosition(self, index, thruster):
        """
        PURPOSE

        Stores thruster settings such as ROV position, reverse state and sends command to ROV to test thruster.

        INPUT

        - index = menu index of the ROV location selected.
        - thruster = the thruster being modified.
        - setting = the thruster setting that has been modified (0 = position, 1 = reverse state, 2 = test).
        - controlObject = pointer to the combobox/checkbox/button object.

        RETURNS

        NONE
        """
        self.data.thrusterPosition[thruster] = self.data.thrusterPositionList[index]

        # PREVENT MULTIPLE THRUSTERS PER ROV LOCATION
        for i, item in enumerate(self.data.thrusterPosition):
            if item == self.data.thrusterPosition[thruster] and i != thruster:
                # SET BINDING TO NONE
                self.data.thrusterPosition[i] = self.data.thrusterPositionList[0]
                # FIND BINDING MENU WIDGET
                layout = self.ui.config_thruster_form.itemAt((2 * i) + 1).layout()
                widget = layout.itemAt(1).widget()
                # SET TO NONE
                widget.setCurrentIndex(0)

    def thrusterReverse(self, thruster, checkboxObject):
        """
        PURPOSE

        Switches direction of the thruster.

        INPUT

        - thruster = the thruster being reversed (0,1,2 etc).
        - checkboxObject = pointed to the reverse checkbox belonging to the thruster.

        RETURNS

        NONE
        """
        self.data.thrusterReverseList[thruster] = checkboxObject.isChecked()

    def thrusterTest(self, state, thruster, buttonObject):
        """
        PURPOSE

        Allows each thruster to be individually turned on at a low speed.
        This lets the pilot known where each thruster is on the ROV and which direction they spin.

        INPUT

        - state = state of the 'test' button (True or False).
        - thruster = the thruster being tested (0,1,2 etc).
        - buttonObject = pointer to the 'test' button widget.

        RETURNS

        NONE
        """
        testSpeed = 550

        if state:
            buttonObject.setStyleSheet(self.data.blueButtonClicked)
            # SET ALL THRUSTER SPEEDS TO ZERO
            speeds = [500] * self.data.thrusterNumber
            # SET DESIRED THRUSTER TO TEST SPEED
            speeds[thruster] = testSpeed
            self.control.changeThrusters(speeds, True)
            
        else:
            # SET ALL THRUSTER SPEEDS TO ZERO
            speeds = [500] * self.data.thrusterNumber
            self.control.changeThrusters(speeds, True)
            buttonObject.setStyleSheet("")
            
    #########################
    ### ACTUATOR SETTINGS ###
    #########################
    def setupActuators(self):
        """
        PURPOSE

        Adds specific number of actuators to the GUI configration tab, with textfields to modify the name and off/on state labels.

        INPUT

        NONE

        RETURNS

        NONE
        """
        actuatorNumber = self.data.actuatorNumber

        self.ui.config_actuators_number.setValue(actuatorNumber)

        for i in range(actuatorNumber):
            self.addActuator()
        
    def changeActuatorsNumber(self):
        """
        PURPOSE

        Sets the number of actuators based on the user entered value in the configuration tab.

        INPUT

        NONE

        RETURN

        NONE
        """
        newNumber = self.ui.config_actuators_number.value()
        oldNumber = self.ui.config_actuator_form.rowCount()

        self.data.actuatorNumber = newNumber

        delta = newNumber - oldNumber

        # ADD ACTUATORS
        if delta > 0:
            for i in range(delta):
                self.addActuator()

        # REMOVE ACTUATORS
        if delta < 0:
            for i in range(-delta):
                self.removeActuator()

    def addActuator(self):
        """
        PURPOSE

        Add a single actuators to the program.

        INPUT

        NONE

        RETURNS

        NONE
        """   
        # THE INDEX OF THE NEXT ACTUATOR
        nextActuator = self.ui.config_actuator_form.rowCount()

        # TRY TO SET LABELS FROM CONFIG FILE
        try:
            labelList = self.data.actuatorLabelList[nextActuator]

        # OTHERWISE, SET DEFAULT LABELS
        except:
            labelList = []
            labelList.append('Actuator {}'.format(nextActuator + 1))
            labelList.append('OFF')
            labelList.append('ON')
            self.data.actuatorLabelList.append(labelList)

        # STORE ACTUATOR STATE
        self.data.actuatorStates.append(False)

        # CREATE WIDGETS ON CONFIG TAB
        actuatorNumber = QLabel("Actuator {}".format(nextActuator + 1))
        actuatorNumber.setStyleSheet("font-weight: bold;")
        actuatorNumber.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        actuatorLabel = QLineEdit(labelList[0])
        state1 = QLineEdit(labelList[1])
        state2 = QLineEdit(labelList[2])
        
        # CREATE WIDGETS ON CONTROL PANEL TAB
        actuatorName = QLabel(labelList[0])
        actuatorName.setFixedHeight(50)
        actuatorToggle = QPushButton(labelList[1])
        actuatorToggle.setFixedHeight(50)
        actuatorToggle.setStyleSheet(self.data.actuatorGreen)
        
        # CREATE CONFIG TAB ACTUATORS LAYOUT
        actuatorLayout = QGridLayout()
        label1 = QLabel('Actuator Name')
        label1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        actuatorLayout.addWidget(label1,0,0)
        actuatorLayout.addWidget(actuatorLabel,0,1)
        label2 = QLabel('Default State')
        label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        actuatorLayout.addWidget(label2,1,0)
        actuatorLayout.addWidget(state1,1,1)
        label3 = QLabel('Actuated State')
        label3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        actuatorLayout.addWidget(label3,2,0)
        actuatorLayout.addWidget(state2,2,1)

        # ADD TO CONFIGURATION TAB
        self.ui.config_actuator_form.addRow(actuatorNumber, actuatorLayout)
        
        # ADD TO CONTROL PANEL TAB
        self.ui.control_panel_actuators.addRow(actuatorName, actuatorToggle)

        # LINK CONFIG ACTUATOR TEXT FIELDS TO SLOT - PASS OBJECT, ACTUATOR NUMBER AND WHICH TEXT FIELD HAS BEEN EDITED
        actuatorLabel.textChanged.connect(lambda text, actuator = nextActuator, label = 0, controlObject = actuatorName: self.changeActuatorType(text, actuator, label, controlObject))
        state1.textChanged.connect(lambda text, actuator = nextActuator, label = 1, controlObject = actuatorToggle: self.changeActuatorType(text, actuator, label, controlObject))
        state2.textChanged.connect(lambda text, actuator = nextActuator, label = 2, controlObject = actuatorToggle: self.changeActuatorType(text, actuator, label, controlObject))
        
        # LINK CONTROL PANEL ACTUATOR BUTTONS TO SLOT - PASS ACTUATOR NUMBER
        actuatorToggle.clicked.connect(lambda state, actuator = nextActuator, buttonObject = actuatorToggle: self.control.changeActuators(actuator, buttonObject))

        # CREATE KEYBINDING FOR ACTUATOR
        label = "Actuator {}".format(nextActuator + 1)
        self.addKeyBinding(label)

    def removeActuator(self):
        """
        PURPOSE

        Remove a single actuator from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REMOVE ACTUATOR FROM CONFIGURATION TAB
        actuatorNumber = self.ui.config_actuator_form.rowCount() - 1
        self.ui.config_actuator_form.removeRow(actuatorNumber) 
        
        # REMOVE ACTUATOR FROM CONTROL PANEL TAB
        actuatorNumber = self.ui.control_panel_actuators.rowCount() - 1
        self.ui.control_panel_actuators.removeRow(actuatorNumber)

        # REMOVE ACTUATOR STATE DATA
        del self.data.actuatorLabelList[actuatorNumber]
        del self.data.actuatorStates[actuatorNumber]

        # REMOVE KEYBINDING FROM CONFIGURATION TAB
        self.removeKeyBinding()

    def changeActuatorType(self, text, actuator, label, controlObject):
        """
        PURPOSE

        Changes the name label and button text on the actuator buttons.

        INPUT

        - text = the text entered by the user.
        - actuator = the actuator being modified.
        - label = the label being modified (0 = name, 1 = default state, 2 = actuated state).
        - controlObject = pointer to the object that is being modified.

        RETURNS

        NONE
        """
        # STORE NEW LABEL
        self.data.actuatorLabelList[actuator][label] = text

        # IF NAME IS CHANGED
        if label == 0:
            # CHANGE LABEL ON CONTROL PANEL
            controlObject.setText(text)

        # IF DEFAULT STATE IS CHANGED
        if label == 1:
            # CHANGE LABEL ON CONTROL PANEL
            if self.data.actuatorStates[actuator] == False:
                controlObject.setText(text)                

        # IF ACTUATED STATE IS CHANGED
        if label == 2:
            # CHANGE LABEL ON CONTROL PANEL
            if self.data.actuatorStates[actuator] == True:
                controlObject.setText(text)  

    #########################
    #### SENSOR SETTINGS ####
    #########################
    def setupSensors(self):
        """
        PURPOSE

        Adds specific number of sensors to the GUI.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        sensorNumber = self.data.sensorNumber

        self.ui.config_sensors_number.setValue(sensorNumber)

        for i in range(sensorNumber):
            self.addSensor()

    def changeSensorsNumber(self):
        """
        PURPOSE

        Sets the number of seneors based on the user entered value in the configuration tab.

        INPUT

        NONE

        RETURN

        NONE
        """
        newNumber = self.ui.config_sensors_number.value()
        oldNumber = self.ui.config_sensor_form.rowCount()

        self.data.sensorNumber = newNumber

        delta = newNumber - oldNumber

        # ADD SENSOR
        if delta > 0:
            for i in range(delta):
                self.addSensor()

        # REMOVE SENSOR
        if delta < 0:
            for i in range(-delta):
                self.removeSensor()

    def addSensor(self):
        """
        PURPOSE

        Adds a single sensor to the program.

        INPUT

        NONE

        RETURN

        NONE
        """
        # THE INDEX OF THE NEXT SENSOR
        nextSensor = self.ui.config_sensor_form.rowCount()

        # TRY TO SET SENSOR TYPE FROM CONFIG FILE
        try:
            selectedType = self.data.sensorSelectedType[nextSensor]
        
        # OTHERWISE, SET DEFAULT AS NONE
        except:
            selectedType = 0
            self.data.sensorSelectedType.append(selectedType)
        
        # CREATE SENSOR TYPE DROP DOWN MENU AND ADD ITEMS
        sensorType = QComboBox()
        sensorType.addItems(self.data.sensorTypeList)

        sensorType.setCurrentIndex(selectedType)
        
        # CREATE SENSOR READINGS TEXT BOX
        sensorView = QLineEdit()
        sensorView.setReadOnly(True)
        sensorView.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        
        # CREATE SENSOR LABEL
        typeLabel = self.data.sensorTypeList[selectedType]
        sensorLabel = QLabel(typeLabel)
        
        # CREATE FORM LAYOUT
        layout = QFormLayout()
        layout.addRow(QLabel("Type"), sensorType)
        
        # ADD TO CONFIG TAB
        label = "Sensor {}".format(nextSensor + 1)
        self.ui.config_sensor_form.addRow(QLabel(label), layout)
        
        # ADD TO CONTROL PANEL TAB
        self.ui.control_panel_sensors.addRow(sensorLabel, sensorView)
        
        # LINK DROP DOWN MENU TO SLOT - PASS SENSOR NUMBER AND MENU INDEX SELECTED
        sensorType.activated.connect(lambda index, 
                                            sensor = nextSensor, 
                                            labelObject = sensorLabel: 
                                            self.changeSensorType(index, sensor, labelObject))

    def removeSensor(self):
        """
        PURPOSE

        Removes a single sensor from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REMOVE SENSORS FROM CONFIG TAB
        sensorNumber = self.ui.config_sensor_form.rowCount() - 1
        self.ui.config_sensor_form.removeRow(sensorNumber) 
        
        # REMOVE SENSORS FROM CONTROL PANEL TAB
        sensorNumber = self.ui.config_sensor_form.rowCount() - 1
        self.ui.control_panel_sensors.removeRow(sensorNumber) 
        
        # REMOVE SENSOR DATA
        del self.data.sensorSelectedType[sensorNumber]
                
    def changeSensorType(self, index, sensor, labelObject):
        """
        PURPOSE

        Changes the type and label of a sensor.

        INPUT

        - index = menu index of the sensor type selected.
        - sensor = the sensor being modified.
        - labelObject = the sensor label object.

        RETURNS

        NONE
        """
        labelObject.setText(self.data.sensorTypeList[index])
        self.data.sensorSelectedType[sensor] = index

    ############################
    ## ANALOG CAMERA SETTINGS ##
    ############################
    def setupAnalogCamera(self):
        """
        PURPOSE

        Apply the analog camera settings from the configuration file.

        INPUT

        NONE

        RETURNS

        NONE
        """
        cameraNumber = self.data.analogCameraNumber

        self.ui.config_analog_cameras_number.setValue(cameraNumber)

        for i in range(cameraNumber):
            self.addAnalogCamera()

    def changeAnalogCamerasNumber(self):
        """
        PURPOSE

        Sets the number of analog cameras based on the user entered value in the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        newNumber = self.ui.config_analog_cameras_number.value()
        oldNumber = self.ui.config_analog_cameras.rowCount()

        self.data.analogCameraNumber = newNumber

        delta = newNumber - oldNumber

        # ADD CAMERA
        if delta > 0:
            for i in range(delta):
                self.addAnalogCamera()

        # REMOVE CAMERA
        if delta < 0:
            for i in range(-delta):
                self.removeAnalogCamera()

    def addAnalogCamera(self):
        """
        PURPOSE

        Adds a single analog camera to the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # THE INDEX OF THE NEXT CAMERA
        nextCamera = self.ui.config_analog_cameras.rowCount()

        # TRY TO SET LABEL FROM CONFIG FILE
        try:
            label = self.data.analogCameraLabelList[nextCamera]

        # OTHERWISE, SET DEFAULT LABEL
        except:
            label = "Camera {}".format(nextCamera + 1)
            self.data.analogCameraLabelList.append(label)

        cameraNumber = QLabel("Camera {}".format(nextCamera + 1))
        cameraLabel = QLineEdit(label)

        # ADD TO CONFIGURATION TAB
        self.ui.config_analog_cameras.addRow(cameraNumber, cameraLabel)

        # UPDATE MENUS
        self.updateAnalogMenus(self.data.analogCameraLabelList, self.data.analogDefaultCameraList)

        cameraLabel.textChanged.connect(lambda text, camera = nextCamera: self.changeAnalogCameraName(text, camera))

    def removeAnalogCamera(self):
        """
        PURPOSE

        Removes a single analog camera from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

    def changeAnalogDefaultCameras(self, index, camera):
        """
        PURPOSE

        Changes which four cameras are shown on the feed upon program startup.

        INPUT

        - index = menu index of the camera selected.
        - camera = the camera feed being modified.

        RETURNS

        NONE
        """
        self.data.analogDefaultCameraList[camera] = index  

    def changeAnalogCameraName(self, text, camera):
        """
        PURPOSE

        Changes the label of an analog camera.

        INPUT

        - text = the new label.
        - camera = the camera the label belong to.

        RETURNS

        NONE
        """
        self.data.analogCameraLabelList[camera] = text

        # UPDATE MENUS
        self.updateAnalogMenus(self.data.analogCameraLabelList, self.data.analogDefaultCameraList)

    def updateAnalogMenus(self, labelList, defaultCameras):
        """
        PURPOSE

        Updates the item on the analog camera default feed menus.

        MENU

        - labelList = array containing the items to add to the menu.
        - defaultCamera = array containing the default camera for each feed.

        RETURNS

        NONE
        """
        # CLEAR CONFIGURATION TAB MENUS
        self.ui.config_analog_default_1.clear()
        self.ui.config_analog_default_2.clear()
        self.ui.config_analog_default_3.clear()
        self.ui.config_analog_default_4.clear()

        # CLEAR CONTROL PANEL TAB MENUS
        self.ui.control_camera_1_list.clear()
        self.ui.control_camera_2_list.clear()
        self.ui.control_camera_3_list.clear()
        self.ui.control_camera_4_list.clear()

        # UPDATE CONFIGURATION TAB MENUS
        self.ui.config_analog_default_1.addItems(labelList)
        self.ui.config_analog_default_1.setCurrentIndex(defaultCameras[0])
        self.ui.config_analog_default_2.addItems(labelList)
        self.ui.config_analog_default_2.setCurrentIndex(defaultCameras[1])
        self.ui.config_analog_default_3.addItems(labelList)
        self.ui.config_analog_default_3.setCurrentIndex(defaultCameras[2])
        self.ui.config_analog_default_4.addItems(labelList)
        self.ui.config_analog_default_4.setCurrentIndex(defaultCameras[3])
        
        # UPDATE CONTROL PANEL MENUS
        self.ui.control_camera_1_list.addItems(labelList)
        self.ui.control_camera_1_list.setCurrentIndex(defaultCameras[0])
        self.ui.control_camera_2_list.addItems(labelList)
        self.ui.control_camera_2_list.setCurrentIndex(defaultCameras[1])
        self.ui.control_camera_3_list.addItems(labelList)
        self.ui.control_camera_3_list.setCurrentIndex(defaultCameras[2])
        self.ui.control_camera_4_list.addItems(labelList)
        self.ui.control_camera_4_list.setCurrentIndex(defaultCameras[3])

    #############################
    ## DIGITAL CAMERA SETTINGS ##
    #############################
    def setupDigitalCameras(self):
        """
        PURPOSE

        Apply the digital camera settings from the configuration file.

        INPUT

        NONE

        RETURNS

        NONE
        """
        cameraNumber = self.data.digitalCameraNumber

        self.ui.config_digital_cameras_number.setValue(cameraNumber)

        for i in range(cameraNumber):
            self.addDigitalCamera()

        self.setDigitalCameraAddress()

    def setDigitalCameraAddress(self):
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
            default1 = self.data.digitalDefaultCameraList[0]
            # NONE SELECTED
            if default1 == 0:
                address1 = ""
            else:
                address1 = self.data.digitalCameraAddressList[default1 - 1]
                address1 = self.addressConverter(address1)
            self.ui.camThread1.changeSource(address1)
        except:
            pass

        # FEED 2
        try:
            default2 = self.data.digitalDefaultCameraList[1]
            # NONE SELECTED
            if default2 == 0:
                address2 = ""
            else:
                address2 = self.data.digitalCameraAddressList[default2 - 1]
                address2 = self.addressConverter(address2)
            self.ui.camThread2.changeSource(address2)
        except:
            pass

        # FEED 3
        try:
            default3 = self.data.digitalDefaultCameraList[2]
            # NONE SELECTED
            if default3 == 0:
                address3 = ""
            else:
                address3 = self.data.digitalCameraAddressList[default3 - 1]
                address3 = self.addressConverter(address3)
            self.ui.camThread3.changeSource(address3)
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

    def changeDigitalCamerasNumber(self):
        """
        PURPOSE

        Sets the number of digital cameras based on the user entered value in the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        newNumber = self.ui.config_digital_cameras_number.value()
        oldNumber = self.ui.config_digital_cameras.rowCount()

        self.data.digitalCameraNumber = newNumber

        delta = newNumber - oldNumber

        # ADD CAMERA
        if delta > 0:
            for i in range(delta):
                self.addDigitalCamera()

        # REMOVE CAMERA
        if delta < 0:
            for i in range(-delta):
                self.removeDigitalCamera()

    def addDigitalCamera(self):
        """
        PURPOSE

        Adds a single digital camera to the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # THE INDEX OF THE NEXT CAMERA
        nextCamera = self.ui.config_digital_cameras.rowCount()

        # TRY TO SET LABEL FROM CONFIG FILE
        try:
            label = self.data.digitalCameraLabelList[nextCamera]
            address = self.data.digitalCameraAddressList[nextCamera]

        # OTHERWISE, SET DEFAULT LABEL AND ADDRESS
        except:
            label = "Camera {}".format(nextCamera + 1)
            self.data.digitalCameraLabelList.append(label)

            address = ""
            self.data.digitalCameraAddressList.append(address)

        cameraNumber = QLabel("Camera {}".format(nextCamera + 1))
        cameraNumber.setStyleSheet("font-weight: bold;")
        cameraNumber.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # CREATE CONFIGURATION TAB WIDGETS
        layout = QGridLayout()
        cameraLabel = QLineEdit(label)
        cameraAddress = QLineEdit(address)
        layout.addWidget(QLabel("Name"),0,0)
        layout.addWidget(cameraLabel,0,1)
        layout.addWidget(QLabel("Address"),1,0)
        layout.addWidget(cameraAddress)

        # ADD TO CONFIGURATION TAB
        self.ui.config_digital_cameras.addRow(cameraNumber, layout)

        # UPDATE MENUS
        self.updateDigitalMenus(self.data.digitalCameraLabelList, self.data.digitalDefaultCameraList)

        cameraLabel.textChanged.connect(lambda text, camera = nextCamera: self.changeDigitalCameraName(text, camera))
        cameraAddress.textChanged.connect(lambda text, camera = nextCamera: self.changeDigitalCameraAddress(text, camera))

    def removeDigitalCamera(self):
        """
        PURPOSE

        Remove a single digital camera from the program.

        INPUT
        
        NONE

        RETURN

        NONE
        """
        pass

    def changeDigitalDefault(self, index, camera):
        """
        PURPOSE

        Changes the default digital camera to be displayed on each digital camera feed.

        INPUT

        - index = menu index selected.
        - camera = the camera feed being modified  (0,1,2)

        RETURN

        NONE
        """
        self.data.digitalDefaultCameraList[camera] = index

    def changeDigitalCameraName(self, text, camera):
        """
        PURPOSE

        Changes the label of a digital camera.

        INPUT

        - text = the name entered by the user.
        - camera = the camera to apply the label to (0,1,2).

        RETURNS

        NONE
        """
        self.data.digitalCameraLabelList[camera] = text

    def changeDigitalCameraAddress(self, text, camera):
        """
        PURPOSE

        Change the source address for a camera feed.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.data.digitalCameraAddressList[camera] = text

    def updateDigitalMenus(self, labelList, defaultCameras):
        """
        PURPOSE

        Updates the digital camera drop down menus from the control panel and configuration tab.

        INPUT

        - items = array containing the camera items to display on the drop down menus.
        - defaultIndex = array containing the menu indices for the default selected camera.

        RETURNS

        NONE
        """
        # UPDATE CONFIGURATION TAB MENUS
        self.ui.config_digital_default_1.clear()
        self.ui.config_digital_default_1.addItem("None")
        self.ui.config_digital_default_1.addItems(labelList)
        self.ui.config_digital_default_1.setCurrentIndex(defaultCameras[0])
        self.ui.config_digital_default_2.clear()
        self.ui.config_digital_default_2.addItem("None")
        self.ui.config_digital_default_2.addItems(labelList)
        self.ui.config_digital_default_2.setCurrentIndex(defaultCameras[1])
        self.ui.config_digital_default_3.clear()
        self.ui.config_digital_default_3.addItem("None")
        self.ui.config_digital_default_3.addItems(labelList)
        self.ui.config_digital_default_3.setCurrentIndex(defaultCameras[2])

    #########################
    # KEY BINDING FUNCTIONS #
    #########################
    def setupKeybindings(self):
        """
        PURPOSE

        Adds the default keybindings.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.addKeyBinding("Switch Orientation")
        self.addKeyBinding("Change Sensitivity")
        self.addKeyBinding("Yaw Right")
        self.addKeyBinding("Yaw Left")
        self.addKeyBinding("Yaw Sensitivity")

    def addKeyBinding(self, label):
        """
        PURPOSE

        Adds a single keybinding configurator for a specific ROV control.

        INPUT

        label = the name of the ROV control.

        RETURNS

        NONE
        """
        bindingNumber = self.ui.config_keybindings_form.rowCount()

        # TRY TO SET KEYBDING FROM CONFIGURATION FILE
        try:
            binding = self.data.keyBindings[bindingNumber]

        # OTHERWISE, SET DEFAULT BINDING TO NONE
        except:
            binding = "None"
            self.data.keyBindings.append(binding)
        
        # CREATE CONFIGURATION TAB WIDGETS
        keybindingLabel = QLabel(label)
        keybindingLabel.setStyleSheet("font-weight: bold;")
        keybindingLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        currentBinding = QComboBox()
        currentBinding.addItems(self.data.availableKeyBindings)
        
        # SET KEYBINDING
        bindingIndex = self.data.availableKeyBindings.index(binding)
        currentBinding.setCurrentIndex(bindingIndex)

        # --- FIND WAY TO DISABLE SCROLLING THROUGH BINDINGS --- #
        currentBinding.setFocusPolicy(Qt.StrongFocus)
        
        setBinding = QPushButton('Auto Binding')

        # CREATE CONFIG TAB KEYBINDINGS LAYOUT
        keybindingLayout = QGridLayout()
        keybindingLayout.addWidget(currentBinding,0,0)
        keybindingLayout.addWidget(setBinding,1,0)

        # ADD TO CONFIG TAB KEYBINDINGS FORM
        self.ui.config_keybindings_form.addRow(keybindingLabel, keybindingLayout)
        
        # LINK KEYBINDING WIDGETS TO SLOT - PASS LAYOUT INDEX NUMBER, THE OBJECT, AND AN INDENTIFIER
        currentBinding.activated.connect(lambda binding, index = bindingNumber: self.setKeyBindings(binding, index))
        
        setBinding.clicked.connect(lambda bindingFound = False, 
                                            binding = None, 
                                            index = bindingNumber, 
                                            buttonObject = setBinding, 
                                            menuObject = currentBinding: 
                                            self.autoKeyBinding(bindingFound, binding, index, buttonObject, menuObject))

    def removeKeyBinding(self):
        """
        PURPOSE

        Removes a single keybinding from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        bindingNumber = self.ui.config_keybindings_form.rowCount()
        
        # REMOVE ACTUATOR KEYBINDING FROM CONFIGURATION TAB
        self.ui.config_keybindings_form.removeRow(bindingNumber - 1)

        # REMOVE KEYBINDING DATA
        del self.data.keyBindings[bindingNumber - 1]

    def setKeyBindings(self, binding, index):
        """
        PURPOSE

        Sets the keybinding for a specific control on the ROV. 
        The keybinding can be selected from a menu, or detected by pressing a button on the controller.

        INPUT
         
        - binding = menu index selected.
        - index = the ROV control having its key binding changed.

        RETURNS 

        NONE
        """
        self.data.keyBindings[index] = self.data.availableKeyBindings[binding]

        keyBinding = self.data.keyBindings[index]

        # PREVENT BINDING BEING ASSOCIATED WITH MULTIPLE CONTROLS
        for i, item in enumerate(self.data.keyBindings):
            # CHECK IF BINDING ALREADY EXISTS
            if i != index:
                if item == keyBinding and item != 'None':
                    # SET BINDING TO NONE
                    self.data.keyBindings[i] = 'None'
                    # FIND BINDING MENU WIDGET
                    layout = self.ui.config_keybindings_form.itemAt((2 * i) + 1).layout()
                    widget = layout.itemAt(0).widget()
                    # SET SELECTED MENU ITEM TO NONE
                    widget.setCurrentIndex(0)

    def autoKeyBinding(self, bindingFound, binding, index, buttonObject, menuObject):
        """
        PURPOSE

        Initiates a thread that waits for a button to be pressed. 
        When a key binding has been found, the key binding is set.

        INPUT

        - bindingFound = True if a key binding has been found.
        - binding = the index in the array of button states that has been changed.
        - index = which key binding is being changed.
        - buttonObject = pointer to the button widget.
        - menuObject = pointer to the keybinding menu widget.

        RETURNS

        NONE
        """
        if bindingFound == False:
            # CHANGE BUTTON STYLE
            buttonObject.setStyleSheet(self.data.blueButtonClicked)

            # DISABLE ALL AUTOBINDING BUTTONS UNTIL BINDING HAS BEEN FOUND
            for item in range(self.ui.config_keybindings_form.rowCount()):
                layout = self.ui.config_keybindings_form.itemAt((2 * item) + 1).layout()
                widget = layout.itemAt(1).widget()
                widget.setEnabled(False)
            
            # INITIATE SEARCH FOR PRESSED BUTTON
            startTime = datetime.now()
            self.findKeyBinding(index, buttonObject, menuObject, startTime)
        
        else:
            # SET KEY BINDING
            self.setKeyBindings(binding + 1, index)
            menuObject.setCurrentIndex(binding + 1)
            # REVERT BUTTON STYLE
            buttonObject.setStyleSheet('')

            # ENABLE ALL AUTOBINDING BUTTONS
            for item in range(self.ui.config_keybindings_form.rowCount()):
                layout = self.ui.config_keybindings_form.itemAt((2 * item) + 1).layout()
                widget = layout.itemAt(1).widget()
                widget.setEnabled(True)

    def findKeyBinding(self, index, buttonObject, menuObject, startTime):
        """
        PURPOSE

        Looks at the button states in a seperate thread and detects which button has been pressed on the controller.

        INPUT

        - index = which key binding is being changed.
        - buttonObject = pointer to the auto binding button widget.
        - menuObject = pointer to the key bindings menu widget.
        - startTime = the system time when the search for a pressed button begins (used for a timeout).
        
        RETURNS

        NONE
        """
        buttonStates = self.data.buttonStates

        # FIND WHICH BUTTON HAS BEEN PRESSED
        for i in range(len(buttonStates)):
            if buttonStates[i] == 1:
                keyBinding = i
                # SET THE KEY BINDING
                self.autoKeyBinding(True, keyBinding, index, buttonObject, menuObject)
                # EXIT THREAD
                exit()

        # 5 SECOND TIMEOUT
        elapsedTime = (datetime.now() - startTime).total_seconds()
        if elapsedTime > 3:
            self.autoKeyBinding(True, menuObject.currentIndex() - 1, index, buttonObject, menuObject)
            exit()
        
        # FIND BUTTON CHANGES AT A RATE OF 60FPS TO REDUCE CPU USAGE
        thread = Timer(1/60, lambda index = index, buttonObject = buttonObject, menuObject = menuObject: self.findKeyBinding(index, buttonObject, menuObject, startTime))
        thread.daemon = True                            
        thread.start()

class TOOLBAR():
    """
    PURPOSE

    Handles everything that happens on the toolbar.
    """
    def __init__(self, Object1, Object2):
        """
        PURPOSE

        Constructor for toolbar object.

        INPUT

        - Object1 = UI class object.
        - Object2 = DATABASE class object
        """
        self.ui = Object1
        self.data = Object2

    def saveSettings(self):
        """
        PURPOSE

        Saves the current program configuration.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        # WRITE CURRENT PROGRAM CONFIGURATION TO XML FILE.
        self.writeConfigFile()

        self.ui.printTerminal("Current program configuration saved to {}.".format(self.data.fileName))

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
        self.ui.resetConfig(True)

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
        configFile = WRITE_CONFIG_FILE(self.data.fileName)
        configFile.createFile()

        # SAVE THEME SETTINGS
        configFile.saveTheme(self.data.programTheme)

        # SAVE THRUSTER SETTINGS
        configFile.saveThruster(self.data.thrusterPosition, self.data.thrusterReverseList)

        # SAVE ACTUATOR SETTINGS
        configFile.saveActuator(self.data.actuatorNumber, self.data.actuatorLabelList)

        # SAVE SENSOR SETTINGS
        configFile.saveSensor(self.data.sensorNumber, self.data.sensorSelectedType)

        # SAVE ANALOG CAMERA SETTINGS
        configFile.saveAnalogCamera(self.data.analogCameraNumber, self.data.analogCameraLabelList, self.data.analogDefaultCameraList)

        # SAVE DIGITAL CAMERA SETTINGS
        configFile.saveDigitalCamera(self.data.digitalCameraNumber, self.data.digitalCameraLabelList, self.data.digitalCameraAddressList, self.data.digitalDefaultCameraList)
        
        # SAVE KEYBINDING SETTINGS
        configFile.saveKeybinding(self.data.keyBindings)

        # WRITE SETTINGS TO XML FILE
        configFile.writeFile()

    def loadSettings(self):
        """
        PURPOSE

        Opens a window that allows user to select a configuration xml file to set up the program.

        INPUTS

        NONE

        RETURNS 

        NONE
        """
        # USER CHOOSES SEQUENCE FILE
        self.data.fileName, _ = QFileDialog.getOpenFileName(self.ui, 'Open File','./','XML File (*.xml)')
        if self.data.fileName != '':
            self.ui.printTerminal("Loading {} configuration file".format(self.data.fileName))
            self.ui.configSetup()
        else:
            # SET BACK TO DEFAULT NAME IF USER DOES NOT SELECT A FILE
            self.data.fileName = 'config/config.xml'

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

        Opens up doxygen html interface to view detailed code documentation

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
        if self.data.programTheme == False:
            self.data.programTheme = True
            self.ui.changeTheme(True)

        else:
            self.data.programTheme = False
            self.ui.changeTheme(False)

        self.restartProgram()

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
        # CLOSE CAMERA FEEDS
        self.ui.programExit()
        subprocess.Popen(['python', 'main.py'])
        sys.exit(0)
            
class DATABASE():
    """
    PURPOSE

    Stores all the variables and lists to be accessed anywhere in the program.
    """
    ###############################
    ######## CONTROL PANEL ########
    ###############################
    programTheme = False                    # FALSE = LIGHT THEME, TRUE = DARK THEME
    comPorts = []                           # LIST OF AVAILABLE COM PORTS
    rovID = "AVALONROV"                     # IDENTITY RESPONSE REQUIRED FROM COM PORT TO CONNECT
    rovComPort = None                       # ACTUAL COM PORT OF THE ROV
    controllerConnectButtonStatus = False   # TRUE WHEN CONNECTION TO CONTROLLER IS SUCCESSFUL

    actuatorStates = []                     # STORES STATE OF EACH ACTUATOR

    visionTaskStatus = [False] * 4          # STORES THE ON/OFF STATUS OF EACH TASK
    
    # STYLESHEETS USED FOR BUTTONS AND TEXT ETC.
    greenText = ""
    redText = ""
    disabledText = ""
    actuatorGreen = ""
    actuatorRed = ""
    buttonGreen = ""
    buttonRed = ""
    blueButtonClicked = ""
    blueButtonDefault = ""

    rovControlDirection = True       # ROV CONTROL ORIENTATION (TRUE = FORWARD, FALSE = REVERSE)
    controllerSensitivity = 2/3      # 1/3, 2/3 or 3/3 controller sensitivity
    yawSensitivity = 2/3             # 1/3, 2/3 or 3/3 yaw sensitivity

    timerEnabled = False             # TIMER START/STOP BUTTON
    timerNew = True                  # FALSE IF TIMER IS STARTED AGAIN AFTER BEING PAUSED
    timerMem = 0                     # TIME WHEN THE TIMER IS PAUSED

    ###############################
    ######## CONFIGURATION ########
    ###############################
    fileName = '.\config\config.xml' # DEFAULT CONFIG FILE NAME

    # THRUSTER SETTINGS
    thrusterNumber = 8
    thrusterPositionList = ['None', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    thrusterPosition = ['None'] * 8
    thrusterReverseList = [False] * 8
    yawButtonStates = [0,0]
    yawButtonStatesPrevious = [0,0]

    # SENSOR SETTINGS
    sensorNumber = 0
    sensorTypeList = ['None','Temperature (°C)','Depth (m)', 'Yaw (°)', 'Pitch (°)', 'Roll (°)']
    sensorSelectedType = []
    
    # ACTUATOR SETTINGS
    actuatorNumber = 0
    actuatorLabelList = []        # LABELS (NAME, DEFAULT STATE, ACTUATED STATE)

    # ANALOG CAMERA SETTINGS
    analogCameraNumber = 0 
    analogCameraLabelList = []                  # LIST OF AVAILABLE CAMERAS
    analogDefaultCameraList = [0 ,1 ,2 ,3]      # DEFAULT CAMERAS TO SHOW ON STARTUP
    analogSelectedCameraList = [0 ,1 ,2 ,3]     # SELECTED CAMERAS TO SHOW ON EACH FEED
    analogCameraViewList = [None] * 4       # STORES THE SELECTED EXTERNAL CAMERA FEEDS
    
    # DIGITAL CAMERA SETTINGS
    digitalCameraNumber = 3 
    digitalCameraLabelList = []
    digitalCameraAddressList = []
    digitalDefaultCameraList = [0, 0, 0]
    digitalSelectedCameraList = [0, 1, 2]

    # KEY BINDING CONFIGURATION SETTINGS
    
    # KEY BINDING LIST FOR DROP DOWN MENU
    availableKeyBindings = ['None','A','B','X','Y','LB','RB','SELECT','START','LS','RS','LEFT','RIGHT','DOWN','UP']
    
    # THE ORDER THAT BUTTONS APPEAR IN THE BUTTON STATES ARRAY
    controllerButtons = ['A','B','X','Y','LB','RB','SELECT','START','LS','RS','LEFT','RIGHT','DOWN','UP']
    
    controllerButtonReleased = [True] * 14    # USED FOR DEBOUNCING CONTROLLER BUTTONS
    
    keyBindings = []    # STORES SELECTED BINDINGS
    
    buttonStates = []   # STORES CONTROLLER BUTTON STATES
    joystickValues = [] # STORES CONTROLLER JOYSTICK STATES

    ###############################
    ############ OTHER ############
    ###############################
    screenHeight = 0
    screenWidth = 0

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

    # PROGRAM BOOT SPLASH SCREEN
    splash_pix = QPixmap('graphics/splash_screen.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()   

    # SET PROGRAM STYLE
    app.setFont(QFont("Bahnschrift Light", 10))
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