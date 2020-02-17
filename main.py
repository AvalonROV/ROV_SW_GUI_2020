#########################
######## IMPORTS ########
#########################

# PYQT5 MODULES
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimeLine
from PyQt5.QtWidgets import (QSplashScreen, QProgressBar, QGroupBox, QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QLabel, QSlider, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QFont, QColor, QPalette, QPainter

# ADDITIONAL MODULES
import sys, os
from threading import Thread, Timer
from datetime import datetime
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
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
from libraries.controller.xboxController import CONTROLLER
from libraries.computer_vision.mosaicTask.mosaicPopupWindow import MOSAIC_POPUP_WINDOW
from libraries.computer_vision.transectLineTask.transectLinePopupWindow import TRANSECT_LINE_POPUP_WINDOW
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
        self.control = CONTROL_PANEL(self, self.data, self.rov, self.controller)
        self.config = CONFIG(self, self.data, self.control, self.rov, self.controller)
        self.toolbar = TOOLBAR(self, self.data)
        
        # FIND SCREEN SIZE
        self.data.sizeObject = QDesktopWidget().screenGeometry(-1)
        self.data.screenHeight = self.data.sizeObject.height()
        self.data.screenWidth = self.data.sizeObject.width()

        # SET DEFAULT WIDGET SIZE
        self.con_panel_functions_widget.resize(self.data.screenWidth/3,self.con_panel_functions_widget.height())

        # LOAD SETTINGS FROM CONFIG FILE
        self.configSetup()

        # LINK GUI BUTTONS TO FUNCTIONS
        self.linkControlPanelWidgets()
        self.linkConfigWidgets()
        self.linkToolbarWidgets()

        # INITIATE CAMERA FEEDS
        self.initiateCameraFeed()

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

        Calls function to read the configuration file and configures the programs thruster, actuator, sensor, camera and controller settings.
        If no configuration file is found, the program will open with default settings. 

        INPUT

        NONE

        RETURNS

        NONE
        """
        # GET CONFIGURATION SETTINGS FROM CONFIG FILE
        (configFileStatus,
            self.data.programTheme,
            self.data.configThrusterPosition,
            self.data.configThrusterReverse, 
            self.data.configActuatorLabelList,
            self.data.configSensorSelectedType,
            self.data.configDefaultCameraList,
            self.data.configDigitalCameraLabels,
            self.data.configDigitalDefaultCameraList,
            self.data.configKeyBindings) = self.readConfigFile(self.data.fileName, 
                                                                self.data.programTheme,
                                                                self.data.configThrusterPosition,
                                                                self.data.configThrusterReverse, 
                                                                self.data.configActuatorLabelList,
                                                                self.data.configSensorSelectedType,
                                                                self.data.configDefaultCameraList,
                                                                self.data.configDigitalCameraLabels,
                                                                self.data.configDigitalDefaultCameraList,
                                                                self.data.configKeyBindings)       
        
        #############################
        ### APPLY SETTINGS TO GUI ###
        #############################

        # APPLY THEME
        self.changeTheme(self.data.programTheme)

        if configFileStatus == False:
            self.printTerminal('Configuration file not found.')
            # ADD DEFAULT KEYBINDINGS IF NO CONFIG FILE EXISTS (SET TO NONE BINDING AS DEFAULT)
            self.config.addKeyBinding("Switch Orientation", False)
            self.config.addKeyBinding("Change Sensitivity", False)
            self.config.addKeyBinding("Yaw Right", False)
            self.config.addKeyBinding("Yaw Left", False)
            self.config.addKeyBinding("Yaw Sensitivity", False)
            
        else:
            self.printTerminal('Configuration file settings applied.')
            # ADD DEFAULT KEY BINDINGS (SETS TO BINDINGS FOUND IN CONFIG FILE)
            self.config.addKeyBinding("Switch Orientation", True)
            self.config.addKeyBinding("Change Sensitivity", True)
            self.config.addKeyBinding("Yaw Right", True)
            self.config.addKeyBinding("Yaw Left", True)
            self.config.addKeyBinding("Yaw Sensitivity", True)

        # UPDATE GUI WITH THRUSTER DATA
        self.config.setThrustersNumber(self.data.configThrusterNumber, 
                                        self.config_thruster_form,
                                        self.data.configThrusterPosition,
                                        self.data.configThrusterPositionList,
                                        self.data.configThrusterReverse)
        # UPDATE GUI WITH ACTUATOR DATA
        self.config.setActuatorsNumber(True)  
        # UPDATE GUI WITH SENSOR DATA
        self.config.setSensorsNumber(True) 
        # UPDATE GUI WITH ANALOG CAMERA DATA
        self.config.setCamerasNumber() 
        # UPDATE GUI WITH DIGITAL CAMERA DATA
        self.config.setupDigitalCameras()

    def readConfigFile(self, fileName,
                        theme, 
                        thrusterPosition, 
                        thrusterReverse, 
                        actuatorLabelList, 
                        sensorSelectedType, 
                        defaultCameraList, 
                        digitalCameraLabels,
                        defaultDigitalCameras,
                        keyBindings):
        """
        PURPOSE

        Reads a specified .xml configuration file that contains all the programs desired settings.

        INPUT

        - fileName = directory of the configuration file.
        - thrusterPosition = array for the default thruster positions on the ROV.
        - thrusterReverse = array for the default direction of the thrusters.
        - actuatorLabelList = array for the default name, off and on state labels for the actuators.
        - sensorSelectedType = array for the default sensor types.
        - defaultCameraList = array for the default selection of cameras on the four feeds.
        - keyBindings = array for the default controller keybindings for the actuators.

        RETURNS

        - thrusterPosition = modified array for the thruster positions on the ROV.
        - thrusterReverse = modified array for the default direction of the thrusters.
        - actuatorLabelList = modified array for the default name, off and on state labels for the actuators.
        - sensorSelectedType = modified array for the default sensor types.
        - defaultCameraList = modified array for the default selection of cameras on the four feeds.
        - keyBindings = modified array for the default controller keybindings for the actuators.
        """
        # TRY TO FIND THE FILE SPECIFIED
        try:
            configFile = parse(fileName)
            configFileStatus = True
        except:
            configFileStatus = False

        # IF CONFIGURATION FILE IS FOUND
        if configFileStatus == True:
            
            # FACTORY RESET GUI CONFIGURATION
            self.resetConfig(False)

            root = configFile.getroot()

            for child in root:

                ##############################
                #### READ THEME SETTINGS #####
                ##############################
                if child.tag == 'theme':
                    theme = True if child.text == "dark" else False

                ##############################
                ### READ THRUSTER SETTINGS ###
                ##############################
                if child.tag == 'thrusters':
                    for index, thruster in enumerate(child):
                        thrusterPosition[index] = thruster.find("location").text
                        thrusterReverse[index] = True if thruster.find("reversed").text == 'True' else False
       
                ##############################
                ### READ ACTUATOR SETTINGS ###
                ##############################
                if child.tag == 'actuators':
                    for index1, actuator in enumerate(child):
                        # SET NUMBER OF ACTUATORS
                        if actuator.tag == 'quantity':
                            self.config_actuators_number.setValue(int(actuator.text))
                        # SET ACTUATOR LABELS
                        else:
                            actuatorLabelList.append([])
                            actuatorLabelList[index1 - 1].append('')
                            actuatorLabelList[index1 - 1].append('')
                            actuatorLabelList[index1 - 1].append('')

                            for index2, label in enumerate(actuator):
                                actuatorLabelList[index1 - 1][index2] = label.text

                ##############################
                #### READ SENSOR SETTINGS ####
                ##############################
                if child.tag == 'sensors':
                    for index, sensor in enumerate(child):
                        # SET NUMBER OF SENSORS AND SENSOR TYPE
                        if sensor.tag == 'quantity':
                            self.config_sensors_number.setValue(int(sensor.text))
                        else:
                            sensorSelectedType.append(0)
                            for sensorType in sensor:
                                sensorSelectedType[index - 1] = int(sensorType.text)
                    
                ##############################
                #### READ CAMERA SETTINGS ####
                ##############################
                if child.tag == 'cameras':
                    for cameraType in child: 
                        # ANALOG CAMERAS
                        if cameraType.tag == 'analog':
                            for index, camera in enumerate(cameraType):
                                # SET NUMBER OF SENSORS AND SENSOR TYPE
                                if camera.tag == 'quantity':
                                    self.config_cameras_number.setValue(int(camera.text))
                                else:
                                    defaultCameraList[index - 1] = int(camera.text)

                        # DIGITAL CAMERAS
                        if cameraType.tag == 'digital':                            
                            for attr in cameraType:
                                # SET NUMBER OF SENSORS AND SENSOR TYPE
                                if attr.tag == 'labels':                                    
                                    for index, item in enumerate(attr):                        
                                        digitalCameraLabels[index] = str(item.text)   
                                if attr.tag == 'defaultfeeds':
                                    for index, item in enumerate(attr):                        
                                        defaultDigitalCameras[index] = int(item.text)
                                    
                ##############################
                ## READ KEYBINDING SETTINGS ##
                ##############################
                if child.tag == 'keybindings':
                    for control in child:
                        keyBindings.append(self.data.configKeyBindingsList.index(control.text))     

        #############################
        ### RETURN EXTRACTED DATA ###
        #############################
        return (configFileStatus,
                theme,
                thrusterPosition,
                thrusterReverse, 
                actuatorLabelList,
                sensorSelectedType,
                defaultCameraList,
                digitalCameraLabels,
                defaultDigitalCameras,
                keyBindings)

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

        self.data.configThrusterPosition = ['None'] * 8
        self.data.configThrusterReverse = [False] * 8

        # RETURN NUMBER OF THRUSTERS TO 8 IF RESET BUTTON IS PRESSED
        if resetStatus == True:
            self.config.setThrustersNumber(self.data.configThrusterNumber, 
                                            self.config_thruster_form,
                                            self.data.configThrusterPosition,
                                            self.data.configThrusterPositionList,
                                            self.data.configThrusterReverse)

        ###############################
        ### RESET ACTUATOR SETTINGS ###
        ###############################
        self.data.configActuatorLabelList = []
        # DELETE PREVIOUS ACTUATORS FROM GUI
        for number in range(self.data.configActuatorNumber):
            # REMOVE ACTUATORS FROM CONFIG TAB
            self.config_actuator_form.removeRow(1) 
            # REMOVE ACTUATORS FROM CONTROL PANEL TAB
            self.control_panel_actuators.removeRow(0)
        self.config_actuators_number.setValue(0)
        self.data.configActuatorNumber = 0

        ###############################
        #### RESET SENSOR SETTINGS ####
        ###############################
        self.data.controlSensorLabelObjects = []
        self.data.configSensorSelectedType = []
        # DELETE PREVIOUS SENSORS FROM GUI
        for i in reversed(range(self.control_panel_sensors.rowCount())): 
            self.control_panel_sensors.removeRow(i)
        for i in reversed(range(1, self.config_sensor_form.rowCount())): 
            self.config_sensor_form.removeRow(i)
            pass
        
        self.config_sensors_number.setValue(0)
        self.data.configSensorNumber = 0

        ###############################
        #### RESET CAMERA SETTINGS ####
        ###############################
        # ANALOG
        self.data.configDefaultCameraList = [0] * 4
        self.data.configCameraList = []
        self.config_cameras_number.setValue(0)
        self.config_camera_1_list.clear()
        self.config_camera_2_list.clear()
        self.config_camera_3_list.clear()
        self.config_camera_4_list.clear()
        # DIGITAL
        self.data.configDigitalCameraLabels = ['Camera 1', 'Camera 2', 'Camera 3']
        self.data.configDigitalDefaultCameraList = [0, 1, 2]
        self.data.configDigitalSelectedList = [0, 1, 2]
        self.config.setupDigitalCameras()

        ###############################
        ## RESET KEYBINDING SETTINGS ##
        ###############################
        numberDelete = len(self.data.configKeyBindings)
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
        self.control_rov_connect.clicked.connect(self.control.rovConnect)
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
        self.control_camera_1_list.activated.connect(lambda index, camera = 0: self.control.changeExternalCameraFeed(index, camera))
        self.control_camera_2_list.activated.connect(lambda index, camera = 1: self.control.changeExternalCameraFeed(index, camera))
        self.control_camera_3_list.activated.connect(lambda index, camera = 2: self.control.changeExternalCameraFeed(index, camera))
        self.control_camera_4_list.activated.connect(lambda index, camera = 3: self.control.changeExternalCameraFeed(index, camera))

        # LINK EACH DIGITAL CAMERA DROP DOWN MENU TO THE SAME SLOT, PASSING CAMERA ID AS 1,2,3,4 ETC.
        self.camera_feed_1_menu.activated.connect(lambda index, camera = 0: self.changeCameraFeedMenu(index, camera))
        self.camera_feed_2_menu.activated.connect(lambda index, camera = 1: self.changeCameraFeedMenu(index, camera))
        self.camera_feed_3_menu.activated.connect(lambda index, camera = 2: self.changeCameraFeedMenu(index, camera))
        self.camera_feed_1_menu.addItems(self.data.configDigitalCameraLabels)
        self.camera_feed_2_menu.addItems(self.data.configDigitalCameraLabels)
        self.camera_feed_3_menu.addItems(self.data.configDigitalCameraLabels)

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
        self.config_rov_connect.clicked.connect(self.control.rovConnect)
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
        self.config_sensors_number.editingFinished.connect(lambda: self.config.setSensorsNumber(False))
        self.config_cameras_number.editingFinished.connect(self.config.setCamerasNumber)
        self.config_actuators_number.editingFinished.connect(lambda: self.config.setActuatorsNumber(False))

        # DIGITAL CAMERA CHANGE NAME
        self.config_digital_name_1.textChanged.connect(lambda text, camera = 0: self.config.changeDigitalCameraName(text, camera))
        self.config_digital_name_2.textChanged.connect(lambda text, camera = 1: self.config.changeDigitalCameraName(text, camera))
        self.config_digital_name_3.textChanged.connect(lambda text, camera = 2: self.config.changeDigitalCameraName(text, camera))

        # DIGITAL DEFAULT CAMERA FEEDS
        self.config_digital_list_1.activated.connect(lambda index, camera = 0: self.config.changeDigitalDefault(index, camera))
        self.config_digital_list_2.activated.connect(lambda index, camera = 1: self.config.changeDigitalDefault(index, camera))
        self.config_digital_list_3.activated.connect(lambda index, camera = 2: self.config.changeDigitalDefault(index, camera))

        # CREATE INDICATORS FOR CONTROLLER VALUES
        self.controller.setupControllerValuesDisplay(self.config_controller_form)

        # LINK EACH DEFAULT CAMERA DROP DOWN MANU TO THE SAME SLOT, PASSING THE CAMERA ID AS 1,2,3,4 ETC.
        self.config_camera_1_list.activated.connect(lambda index, camera = 0: self.config.changeDefaultCameras(index, camera))
        self.config_camera_2_list.activated.connect(lambda index, camera = 1: self.config.changeDefaultCameras(index, camera))
        self.config_camera_3_list.activated.connect(lambda index, camera = 2: self.config.changeDefaultCameras(index, camera))
        self.config_camera_4_list.activated.connect(lambda index, camera = 3: self.config.changeDefaultCameras(index, camera))

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
        self.camThread1 = CAMERA_CAPTURE(0)
        self.camThread1.cameraNewFrameSignal.connect(self.updateCamera1Feed)
        self.camThread1.start()
        
        # SECONDARY CAMERA 1
        self.camThread2 = CAMERA_CAPTURE(1)
        self.camThread2.cameraNewFrameSignal.connect(self.updateCamera2Feed)
        self.camThread2.start()
        
        # SECONDARY CAMERA 2
        self.camThread3 = CAMERA_CAPTURE(2)
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
            # AVALON LOGO
            self.avalon_logo.clear()
            avalonPixmap = QPixmap('graphics/logo_white.png')
            avalonPixmap = avalonPixmap.scaledToWidth(250, Qt.SmoothTransformation)
            self.avalon_logo.setPixmap(avalonPixmap)

            # DARK THEME STYLE SHEETS
            self.data.greenText = 'color: #679e37'
            self.data.redText = 'color: #c62828'
            self.data.disabledText = 'color: rgba(0,0,0,40%);'
            self.data.actuatorGreen = 'color: white; background-color: #679e37; border-radius: 20px'
            self.data.actuatorRed = 'color: white; background-color: #c62828; border-radius: 20px'
            self.data.buttonGreen = 'color: black; background-color: #679e37;'
            self.data.buttonRed = 'color: blackl; background-color: #c62828;'
            self.data.blueButtonClicked = 'background-color: #0D47A1; color: white; font-weight: bold;'
            self.data.blueButtonDefault = 'color: white; font-weight: bold;'

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
            # AVALON LOGO
            self.avalon_logo.clear()
            avalonPixmap = QPixmap('graphics/logo.png')
            avalonPixmap = avalonPixmap.scaledToWidth(250, Qt.SmoothTransformation)
            self.avalon_logo.setPixmap(avalonPixmap)

            # LIGHT THEME STYLE SHEETS
            self.data.greenText = 'color: #679e37'
            self.data.redText = 'color: #c62828'
            self.data.disabledText = 'color: rgba(0,0,0,25%);'
            self.data.actuatorGreen = 'background-color: #679e37'
            self.data.actuatorRed = 'background-color: #c62828'
            self.data.blueButtonClicked = 'background-color: #0D47A1; color: white; font-weight: bold;'
            self.data.blueButtonDefault = 'color: #0D47A1; font-weight: bold;'

            self.app.setPalette(self.app.style().standardPalette())

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
    def __init__(self, Object1, Object2, Object3, Object4):
        """
        PURPOSE

        Initialises objects.

        INPUT

        - Object1 = 'UI' class
        - Object2 = 'DATABASE' class
        - Object3 = 'ROV' clsss
        - Object4 = 'CONTROLLER' class

        RETURNS

        NONE
        """
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2
        self.rov = Object3
        self.controller = Object4

        self.comms = None

    def rovConnect(self):
        """
        PURPOSE

        Initialises serial communication with the ROV and starts sensor reading requests.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.rovConnectButtonStatus == False:

            self.ui.control_rov_connect.setEnabled(False)
            self.ui.config_rov_connect.setEnabled(False)
            
            # FIND ALL AVAILABLE COM PORTS
            self.ui.printTerminal('Searching for available COM ports...')
            availableComPorts, rovComPort, identity = self.findComPorts(self.ui.config_com_port_list, self.data.rovCommsStatus, 115200, self.data.rovID)
            self.data.rovComPort = rovComPort
            self.ui.printTerminal("{} available COM ports found.".format(len(availableComPorts)))
            self.ui.printTerminal('Device Identity: {}'.format(identity))
            
            # ATTEMPT CONNECTION TO ROV COM PORT
            status, message = self.serialConnect(rovComPort, 115200)
            self.ui.printTerminal(message)

            # IF CONNECTION IS SUCCESSFUL
            if status == True:
                self.data.rovConnectButtonStatus = True
                # MODIFY BUTTON STYLE
                self.ui.control_rov_connect.setText('DISCONNECT')
                self.ui.config_rov_connect.setText('DISCONNECT')
                self.ui.control_rov_connect.setStyleSheet(self.data.blueButtonClicked)
                self.ui.config_rov_connect.setStyleSheet(self.data.blueButtonClicked)
                self.data.rovCommsStatus = True
                # CALL INITIAL ROV FUNCTIONS
                self.startupProcedure()

            self.ui.control_rov_connect.setEnabled(True)
            self.ui.config_rov_connect.setEnabled(True)      

        else:
            self.armThrusters()
            self.data.rovConnectButtonStatus = False
            self.ui.control_rov_connect.setText('CONNECT')
            self.ui.config_rov_connect.setText('CONNECT')
            self.ui.control_rov_connect.setStyleSheet(self.data.blueButtonDefault)
            self.ui.config_rov_connect.setStyleSheet(self.data.blueButtonDefault)
            # CLOSE COM PORT
            if self.data.rovCommsStatus:
                self.ui.printTerminal("Disconnected from {}".format(self.data.rovComPort))
                self.comms.close()
                self.rov.disconnect()
            self.data.rovCommsStatus = False

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
        self.data.configButtonStates = buttonStates

        # CYCLE THROUGH EACH BUTTON
        for index, button in enumerate(buttonStates):
            
            # FIND THE NAME OF THE BUTTON IN QUESTION ('A', 'B', 'X', 'Y' ETC.)
            whichButton = self.data.configControllerButtons[index]
            # FIND THE BUTTONS INDEX ON THE KEYBINDINGS DROP DOWN MENU
            whichMenuIndex = self.data.configKeyBindingsList.index(whichButton)
            # FIND WHICH ROV CONTROL USES THAT KEYBINDING
            try:
                whichControl = self.data.configKeyBindings.index(whichMenuIndex)
                buttonExists = True
            except:
                buttonExists = False

            # IF BUTTON IS PRESSED
            if button == 1:
                # IF KEYBINDING EXISTS AND HAS PREVIOUSLY BEEN RELEASED
                if buttonExists == True and self.data.configControllerButtonReleased[index] == True:
                    # PREVENT ACTUATOR BEING TOGGLED AGAIN UNTILL BUTTON IS RELEASED
                    self.data.configControllerButtonReleased[index] = False
                    
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
                self.data.configControllerButtonReleased[index] = True

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
        filteredThrusterSpeeds = [0] * self.data.configThrusterNumber

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
        
        if joystickValues != self.data.configJoystickValues or yawActive == True:
            # DECOMPOSE JOYSTICKS INTO MOTION AXIS
            right_left = joystickValues[0]
            forward_backward = -joystickValues[1]
            up_down = -joystickValues[2]
            pitch = joystickValues[3]
            roll = joystickValues[4]
            yaw = yawDirection * self.data.yawSensitivity

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
            
            # CONTROLLER SENSITIVITY SCALING FACTOR
            controllerSensitivity = self.data.controllerSensitivity 

            # NORMALISE ALL THRUSTER SPEEDS W.R.T THE FASTEST THRUSTER AND THE MAXIMUM JOYSTICK POSITION (MAX = 1)
            for i in range(len(filteredThrusterSpeeds)):
                if maxSpeed > 0:
                    filteredThrusterSpeeds[i] = round(controllerSensitivity * maxJoystick * filteredThrusterSpeeds[i] / maxSpeed, 3)

            # CONVERT -1 -> 1 TO 1 -> 999 FOR ARDUINO MICROSECONDS SERVO SIGNAL
            for i in range(len(filteredThrusterSpeeds)):
                filteredThrusterSpeeds[i] = int(500 + filteredThrusterSpeeds[i]*499)

            self.changeThrusters(filteredThrusterSpeeds)
        
        # SAVE VALUES TO BE COMPARED IN THE NEXT CYCLE
        self.data.configJoystickValues = joystickValues
        self.data.yawButtonStatesPrevious = self.data.yawButtonStates.copy()
        
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
        if self.data.controlActuatorStates[actuator] == False:
            buttonObject.setText(self.data.configActuatorLabelList[actuator][2])
            buttonObject.setStyleSheet(self.data.actuatorRed)
            self.data.controlActuatorStates[actuator] = True

        elif self.data.controlActuatorStates[actuator] == True:
            buttonObject.setText(self.data.configActuatorLabelList[actuator][1])
            buttonObject.setStyleSheet(self.data.actuatorGreen)
            self.data.controlActuatorStates[actuator] = False

        # SEND COMMAND TO ROV
        self.setActuators(self.data.controlActuatorStates)

    def changeThrusters(self, thrusterSpeeds):
        """
        PURPOSE

        Prepares and sends desired thruster speeds to the communication library.

        INPUT

        - thrusterSpeed = array containing the desired speed of each thruster. (1 - 999).

        RETURNS

        NONE
        """
        tempThrusterSpeeds = thrusterSpeeds.copy()

        # REVERSE THE DIRECTION OF THRUSTERS WHERE NECCESSARY
        for i, speed in enumerate(tempThrusterSpeeds):
            if self.data.configThrusterReverse[i] == True:
                tempThrusterSpeeds[i] = 1000 - speed
        
        # SEND COMMAND TO ROV
        self.setThrusters(tempThrusterSpeeds)

    def switchControlDirection(self):
        """
        PURPOSE

        Changes the control orientation of the ROV, to allow easy maneuvering in reverse.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.controlControlDirection == True:
            self.data.controlControlDirection = False
            self.ui.control_switch_direction_forward.setStyleSheet("")
            self.ui.control_switch_direction_reverse.setStyleSheet(self.data.greenText)
        else:
            self.data.controlControlDirection = True
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
        currentSeconds = (currentTime - self.startTime).total_seconds() + self.data.controlTimerMem
        self.updateTimer(currentSeconds)
    
        # READ SYSTEM TIME EVERY 1 SECOND (TO REDUCE CPU USAGE)
        thread = Timer(0.5,self.readSystemTime)
        thread.daemon = True                            
        thread.start()
        
        # STOP THREAD IF STOP BUTTON CLICKED
        if self.data.controlTimerEnabled == False:
            thread.cancel()
            self.data.controlTimerMem = currentSeconds

    def toggleTimer(self):
        """
        PURPOSE

        Starts/Stops the timer.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.controlTimerEnabled == False:
            self.data.controlTimerEnabled = True
            self.ui.control_timer_start.setText('Stop')
            self.ui.control_timer_start.setStyleSheet(self.data.buttonRed)
            self.startTime = datetime.now()
            # START TIMER
            self.readSystemTime()
        else:
            self.data.controlTimerEnabled = False
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
        if self.data.controlTimerEnabled == False:
            self.data.controlTimerMem = 0
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
        self.armThrusters()

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
        if self.data.rovCommsStatus == False:
            self.timer.stop()
        
        else:
            # REQEST SINGLE READING
            sensorReadings = self.getSensors()

            # UPDATE GUI
            for sensor, reading in enumerate(sensorReadings):
                if sensor < self.data.configSensorNumber:
                    # FIND INDEX OF SENSOR TEXTBOX WIDGET
                    widgetIndex = (sensor * 2) + 1
                    textWidget = self.ui.control_panel_sensors.itemAt(widgetIndex).widget()
                    textWidget.setText(str(reading))

    def changeExternalCameraFeed(self, camera, display):
        """
        PURPOSE

        Changes which analog camera is displayed on the camera feed.

        INPUT

        - camera = the camera number to be displayed.
        - display = the screen quadrant to display the camera feed on.

        RETURNS

        NONE
        """
        # CAMERA VARIABLE REPRESENTS THE MENU INDEX SELECTED
        # INDEX VARIABLE REPRESENTS WHICH CAMERA FEED IS BEING MODIFIED (0,1,2,3)
        
        # STORE WHICH CAMERA HAS BEEN SELECTED FOR EACH FEED
        self.data.controlCameraViewList[display] = camera

    ##############################
    #### SERIAL LIBRARY MOCKS ####
    ##############################
    def serialConnect(self, rovComPort, baudRate):
        """
        PURPOSE

        Attempts to initialise a serial communication interface with a desired COM port.

        INPUT

        - rovComPort = the COM port of the ROV.
        - baudRate = the baud rate of the serial interface.

        RETURNS

        NONE
        """
        status = False
        if rovComPort != None:
            try:
                self.comms = serial.Serial(rovComPort, baudRate, timeout = 1)
                message = "Connection to ROV successful."
                status = True
            except:
                message = "Failed to connect to {}.".format(rovComPort)
        else:
            message = "Failed to recognise device identity."

        return status, message

    def findComPorts(self, menuObject, commsStatus, baudRate, rovIdentity):
        """
        PURPOSE

        Find all available COM ports and adds them to drop down menu.

        INPUT

        - menuObject = pointer to the drop down menu to display the available COM ports.
        - commsStatus = current ROV communication status (True/False).
        - baudRate = baud rate of the serial interface.
        - rovIdentity = string containing the required device identity to connect to the ROV.

        RETURNS

        - availableComPorts = list of all the available COM ports.
        - rovComPort = the COM port that belongs to the ROV.
        - identity = the devices response from an identity request.
        """
        # DISCONNECTED FROM CURRENT COM PORT IF ALREADY CONNECTED
        if commsStatus == True:
            self.rovConnect()

        # CREATE LIST OF ALL POSSIBLE COM PORTS
        ports = ['COM%s' % (i + 1) for i in range(256)] 

        # CLEAR CURRENT MENU LIST
        menuObject.clear()

        identity = ""
        rovComPort = None
        availableComPorts = []
        
        # CHECK WHICH COM PORTS ARE AVAILABLE
        for port in ports:
            try:
                comms = serial.Serial(port, baudRate, timeout = 1)
                
                # ADD AVAILABLE COM PORT TO MENU LIST
                availableComPorts.append(port)
                menuObject.addItem(port)
                
                # REQUEST IDENTITY FROM COM PORT
                self.data.rovCommsStatus = True
                identity = self.getIdentity(comms, self.data.rovID)
                comms.close()
                self.data.rovCommsStatus = False
                
                # FIND WHICH COM PORT IS THE ROV
                if identity == rovIdentity:
                    rovComPort = port
                    break
                    
            # SKIP COM PORT IF UNAVAILABLE
            except (OSError, serial.SerialException):
                pass

        return availableComPorts, rovComPort, identity

    def getIdentity(self, serialInterface, identity):
        """
        PURPOSE

        Request identity from a defined COM port.

        INPUT

        - serialInterface = pointer to the serial interface object.
        - identity = the desired identity response from the device connected to the COM port.

        RETURNS

        - identity = the devices response.
        """
        identity = ""
        startTime = datetime.now()
        elapsedTime = 0
        # REPEATIDELY REQUEST IDENTIFICATION FROM DEVICE FOR UP TO 3 SECONDS
        while (identity == "") and (elapsedTime < 3):
            self.serialSend("?I", serialInterface)
            identity = self.serialReceive(serialInterface)
            elapsedTime = (datetime.now() - startTime).total_seconds()

        return identity        

    def setActuators(self, actuatorStates):
        """
        PURPOSE

        Generates command to send to ROV with the desired actuator states.

        INPUT

        - actuatorStates = array containing the desired state of each actuator.

        RETURNS

        NONE
        """
        # COMMAND INITIALISATION  
        transmitActuatorStates = '?RA'
        # ADD ACTUATOR STATES ONTO THE END OF STRING
        for state in actuatorStates:
            # CONVERT TRUE/FALSE TO '1'/'0'
            transmitActuatorStates += ('1' if state == True else '0')
        self.serialSend(transmitActuatorStates, self.comms)

    def setThrusters(self, thrusterSpeeds):
        """
        PURPOSE

        Generates command to send to ROV with the desired thruster speeds.

        INPUT

        - thrusterSpeeds = array containing the desired speed of each thruster.

        RETURNS

        NONE
        """
        # COMMAND INITIALISATION  
        transmitThrusterSpeeds = '?RT'
        # ADD ACTUATOR STATES ONTO THE END OF STRING
        for speed in thrusterSpeeds:
            # CONVERT TO 'xxx' format (PAD EMPTY SPACES WITH ZEROS)
            transmitThrusterSpeeds += ('{0:03d}'.format(speed))

        self.serialSend(transmitThrusterSpeeds, self.comms)

    def armThrusters(self):
        """
        PURPOSE

        Sends command to ROV to arm the thruster ESCs.

        INPUT

        NONE

        RETURN

        NONE
        """
        # COMMAND INITIALISATION  
        transmitArmThrusters = '?RX'
        self.serialSend(transmitArmThrusters, self.comms) 

    def getSensors(self):
        """
        PURPOSE

        Send request to ROV to get sensor readings and return them.
        
        INPUT

        NONE

        RETURNS

        - results = array containing the sensor readings.
        """
        # REQUEST SENSOR READINGS
        command = "?RS"
        self.serialSend(command, self.comms)
        # READ RESPONSE INTO AN ARRAY
        results = self.serialReceive(self.comms).split(",")

        return results

    def serialSend(self, command, serialInterface):
        """
        PURPOSE

        Sends a string down the serial interface to the ROV.

        INPUT

        - command = the command to send.
        - serialInterface = pointer to the serial interface object..

        RETURNS

        NONE
        """
        if self.data.rovCommsStatus:
            try:
                serialInterface.write((command + '\n').encode('ascii'))
            except:
                self.ui.printTerminal("Failed to send command.")
                self.rovConnect()

    def serialReceive(self, serialInterface):
        """
        PURPOSE

        Waits for data until a newline character is received.

        INPUT

        - serialInterface = pointer to the serial interface object.

        RETURNS

        NONE
        """
        received = ""
        try:
            received = serialInterface.readline().decode('ascii').strip()
        except:
            self.ui.printTerminal("Failed to receive data.")
            self.rovConnect()
            
        return(received)

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
        
        for i in range(len(self.data.controlVisionTaskStatus)):
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
                self.data.controlVisionTaskStatus[i] = False

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
            if self.data.controlVisionTaskStatus[0] == False:
                # OPEN WIDGET
                self.data.controlVisionTaskStatus[0] = True
                self.changeVisionButtons(0, True)
                self.animation.jumpTo(1)
                
            else:
                #CLOSE WIDGET
                self.data.controlVisionTaskStatus[0] = False
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
            if self.data.controlVisionTaskStatus[1] == False:
                # OPEN WIDGET
                self.data.controlVisionTaskStatus[1] = True
                self.changeVisionButtons(1, True)
                self.animation.jumpTo(2)
                
            else:
                # CLOSE WIDGET
                self.data.controlVisionTaskStatus[1] = False
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
            if self.data.controlVisionTaskStatus[2] == False:
                # OPEN WIDGET
                self.data.controlVisionTaskStatus[2] = True
                self.changeVisionButtons(2, True)
                self.animation.jumpTo(3)
                
            else:
                # CLOSE WIDGET
                self.data.controlVisionTaskStatus[2] = False
                self.changeVisionButtons(2, False)
                self.animation.jumpTo(0)

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
            if self.data.controlVisionTaskStatus[3] == False:
                # OPEN WIDGET
                self.data.controlVisionTaskStatus[3] = True
                self.changeVisionButtons(3, True)
                self.animation.jumpTo(4)
                
            else:
                # CLOSE WIDGET
                self.data.controlVisionTaskStatus[3] = False
                self.changeVisionButtons(3, False)
                self.animation.jumpTo(0)

class CONFIG():
    """
    PURPOSE

    Handles everything that happens on the Configuration tab.
    """
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3, Object4, Object5):
        """
        PURPOSE

        Constructor for Configuration tab object.

        INPUT

        - Object1 = 'UI' class
        - Object2 = 'DATABASE' class
        - Object3 = 'CONTROL_PANEL' class
        - Object4 = 'ROV' clsss
        - Object5 = 'CONTROLLER' class

        RETURNS

        NONE
        """
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2
        self.control = Object3
        self.rov = Object4
        self.controller = Object5

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
        availableComPorts, rovComPort, identity = self.control.findComPorts(self.ui.config_com_port_list, self.data.rovCommsStatus, 115200, 'AVALONROV')
        self.ui.printTerminal("{} available COM ports found.".format(len(availableComPorts))) 

    #########################
    ### THRUSTER SETTINGS ###
    #########################
    def setThrustersNumber(self, thrusterNumber, thrusterLayout, thrusterPosition, thrusterPositionList, thrusterReverse):
        """
        PURPOSE

        Adds specific number of thrusters to the GUI configration tab, with a ROV location menu, reverse checkbox and a test button.

        INPUT

        - thrusterNumber = the number of thrusters to add.
        - thrusterLayout = the form layout widget to add the widgets to.
        - thrusterPosition = array containing the ROV position of each thruster.
        - thusterPosition = array containing all the possible ROV thruster locaitons.
        - thrusterReverse = array containing the direction of each thruster.

        RETURNS

        NONE 
        """
        for thruster in range(thrusterNumber):
            # CREATE THRUSTER NUMBER LABEL
            thrusterLabel = QLabel("Thruster {}".format(thruster + 1))
            thrusterLabel.setStyleSheet("font-weight: bold;")
            thrusterLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # CREATE ROV LOCATION DROP DOWN MENU AND ADD ITEMS
            thrusterLocation = QComboBox()
            thrusterLocation.addItems(thrusterPositionList)           
            thrusterLocation.setCurrentIndex(thrusterPositionList.index(thrusterPosition[thruster]))
            # CREATE THRUSTER REVERSE CHECKBOX
            thrusterReverseCheck = QCheckBox()
            thrusterReverseCheck.setChecked(thrusterReverse[thruster])
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
            thrusterLocation.activated.connect(lambda index, thruster = thruster: self.thrusterPosition(index, thruster)) 
            thrusterReverseCheck.toggled.connect(lambda state, thruster = thruster, controlObject = thrusterReverseCheck: self.thrusterReverse(thruster, controlObject))
            thrusterTest.pressed.connect(lambda state = True, thruster = thruster, controlObject = thrusterTest: self.thrusterTest(state, thruster, controlObject))
            thrusterTest.released.connect(lambda state = False, thruster = thruster, controlObject = thrusterTest: self.thrusterTest(state, thruster, controlObject))

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
        self.data.configThrusterPosition[thruster] = self.data.configThrusterPositionList[index]

        # PREVENT MULTIPLE THRUSTERS PER ROV LOCATION
        for i, item in enumerate(self.data.configThrusterPosition):
            if item == self.data.configThrusterPosition[thruster] and i != thruster:
                # SET BINDING TO NONE
                self.data.configThrusterPosition[i] = self.data.configThrusterPositionList[0]
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
        self.data.configThrusterReverse[thruster] = checkboxObject.isChecked()

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
            speeds = [500] * self.data.configThrusterNumber
            # SET DESIRED THRUSTER TO TEST SPEED
            speeds[thruster] = testSpeed
            self.control.changeThrusters(speeds)
            
        else:
            # SET ALL THRUSTER SPEEDS TO ZERO
            speeds = [500] * self.data.configThrusterNumber
            self.control.changeThrusters(speeds)
            buttonObject.setStyleSheet("")
            
    #########################
    ### ACTUATOR SETTINGS ###
    #########################
    def setActuatorsNumber(self, configStatus):
        """
        PURPOSE

        Adds specific number of actuators to the GUI configration tab, with textfields to modify the name and off/on state labels.

        INPUT

        - configStatus = true if function is called by the configSetup function.

        RETURNS

        NONE
        """
        oldNumber = self.data.configActuatorNumber
        newNumber = self.ui.config_actuators_number.value()
        self.data.configActuatorNumber = newNumber
    
        # ADD ACTUATORS IF NEW NUMBER IS HIGHER
        if newNumber > oldNumber:
            # CALCULATE NUMBER OF ACTUATORS TO ADD ON TOP OF CURRENT NUMBER
            delta = newNumber - oldNumber
            for number in range(delta):
                
                # DEFAULT VALUES WHEN NO CONFIG FILE IS FOUND
                if configStatus == False:
                    # CREATE 2-DIMENSIONAL ARRAY TO STORE NAME, DEFAULT AND ACTUATED LABELS FOR EACH ACTUATOR
                    self.data.configActuatorLabelList.append([])
                    self.data.configActuatorLabelList[oldNumber + number].append('Actuator {}'.format(oldNumber + number + 1))
                    self.data.configActuatorLabelList[oldNumber + number].append('OFF')
                    self.data.configActuatorLabelList[oldNumber + number].append('ON')

                # CREATE ARRAY TO STORE DEFAULT ACTUATOR STATES
                self.data.controlActuatorStates.append(False)

                # CREATE CONFIG TAB ACTUATOR WIDGETS
                actuatorNumber = QLabel("Actuator {}".format((oldNumber + number + 1)))
                actuatorNumber.setStyleSheet("font-weight: bold;")
                actuatorNumber.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                actuatorLabel = QLineEdit(self.data.configActuatorLabelList[oldNumber + number][0])
                state1 = QLineEdit(self.data.configActuatorLabelList[oldNumber + number][1])
                state2 = QLineEdit(self.data.configActuatorLabelList[oldNumber + number][2])
                
                # CREATE CONTROL PANEL TAB ACTUATOR WIDGETS
                actuatorToggle = QPushButton(self.data.configActuatorLabelList[oldNumber + number][1])
                actuatorToggle.setFixedHeight(50)
                actuatorName = QLabel(self.data.configActuatorLabelList[oldNumber + number][0])
                actuatorName.setFixedHeight(50)

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

                # SET DEFAULT STYLE SHEET
                actuatorToggle.setStyleSheet(self.data.actuatorGreen)

                # ADD TO CONFIG TAB ACTUATORS FORM
                self.ui.config_actuator_form.addRow(actuatorNumber, actuatorLayout)
                # ADD TO CONTROL PANEL TAB ACTUATORS FORM
                self.ui.control_panel_actuators.addRow(actuatorName, actuatorToggle)

                # LINK CONFIG ACTUATOR TEXT FIELDS TO SLOT - PASS OBJECT, ACTUATOR NUMBER AND WHICH TEXT FIELD HAS BEEN EDITED
                actuatorLabel.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 0, controlObject = actuatorName: self.changeActuatorType(text, actuator, label, controlObject))
                state1.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 1, controlObject = actuatorToggle: self.changeActuatorType(text, actuator, label, controlObject))
                state2.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 2, controlObject = actuatorToggle: self.changeActuatorType(text, actuator, label, controlObject))
                # LINK CONTROL PANEL ACTUATOR BUTTONS TO SLOT - PASS ACTUATOR NUMBER
                actuatorToggle.clicked.connect(lambda state, actuator = (oldNumber + number), buttonObject = actuatorToggle: self.control.changeActuators(actuator, buttonObject))

                # CREATE KEYBINDING FOR ACTUATOR
                self.addKeyBinding("Actuator {}".format((oldNumber + number + 1)), configStatus)

        # REMOVE ACTUATORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF ACTUATORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                # REMOVE ACTUATORS FROM CONFIG TAB
                totalRows = self.ui.config_actuator_form.rowCount()
                self.ui.config_actuator_form.removeRow(totalRows - 1) 
                
                # REMOVE ACTUATORS FROM CONTROL PANEL TAB
                totalRows = self.ui.control_panel_actuators.rowCount()
                self.ui.control_panel_actuators.removeRow(totalRows - 1)

                # REMOVE KEYBINDINGS FROM CONFIG TAB
                totalBindings = self.ui.config_keybindings_form.rowCount()
                self.removeKeyBinding(totalBindings - 1)

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
        self.data.configActuatorLabelList[actuator][label] = text

        # IF NAME IS CHANGED
        if label == 0:
            # CHANGE LABEL ON CONTROL PANEL
            controlObject.setText(text)

        # IF DEFAULT STATE IS CHANGED
        if label == 1:
            # CHANGE LABEL ON CONTROL PANEL
            if self.data.controlActuatorStates[actuator] == False:
                controlObject.setText(text)                

        # IF ACTUATED STATE IS CHANGED
        if label == 2:
            # CHANGE LABEL ON CONTROL PANEL
            if self.data.controlActuatorStates[actuator] == True:
                controlObject.setText(text)  

    #########################
    #### SENSOR SETTINGS ####
    #########################
    def setSensorsNumber(self, configStatus):
        """
        PURPOSE

        Adds specific number of sensors to the GUI configration tab, with a drop down menu containing the sensor types.

        INPUT

        - configStatus = True if function is called by the configSetup function.

        RETURNS

        NONE
        """
        oldNumber = self.data.configSensorNumber
        newNumber = self.ui.config_sensors_number.value()
        self.data.configSensorNumber = newNumber

        # ADD SENSORS IF NEW NUMBER IS HIGHER
        if newNumber > oldNumber:
            
            # CALCULATE NUMBER OF SENSORS TO ADD ON TOP OF CURRENT NUMBER
            delta = newNumber - oldNumber
            
            for number in range(delta):
                # CREATE SENSOR TYPE STORAGE ARRAY IF NO CONFIG FILE IS FOUND
                if configStatus == False:
                    self.data.configSensorSelectedType.append(0)
                
                # CREATE SENSOR TYPE DROP DOWN MENU AND ADD ITEMS
                sensorType = QComboBox()
                sensorType.addItems(self.data.configSensorTypeList)
                sensorType.setCurrentIndex(self.data.configSensorSelectedType[oldNumber + number])
                
                # CREATE SENSOR READINGS TEXT BOX
                sensorView = QLineEdit()
                sensorView.setReadOnly(True)
                sensorView.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                
                # CREATE SENSOR LABEL
                sensorLabel = QLabel(self.data.configSensorTypeList[self.data.configSensorSelectedType[oldNumber + number]])
                
                # CREATE FORM LAYOUT
                layout = QFormLayout()
                layout.addRow(QLabel("Type"), sensorType)
                
                # ADD TO CONFIG TAB
                self.ui.config_sensor_form.addRow(QLabel("Sensor {}".format((oldNumber + number + 1))), layout)
                
                # ADD TO CONTROL PANEL TAB
                self.ui.control_panel_sensors.addRow(sensorLabel, sensorView)
                
                # LINK DROP DOWN MENU TO SLOT - PASS SENSOR NUMBER AND MENU INDEX SELECTED
                sensorType.activated.connect(lambda index, 
                                                    sensor = (oldNumber + number + 1), 
                                                    sensorSelected = sensorLabel: 
                                                    self.changeSensorType(index, sensor, sensorSelected))

        # REMOVE SENSORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF SENSORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                # REMOVE SENSORS FROM CONFIG TAB
                totalRows = self.ui.config_sensor_form.rowCount()
                self.ui.config_sensor_form.removeRow(totalRows - 1) 
                
                # REMOVE SENSORS FROM CONTROL PANEL TAB
                totalRows = self.ui.config_sensor_form.rowCount()
                self.ui.control_panel_sensors.removeRow(totalRows - 1) 
                del self.data.configSensorSelectedType[oldNumber - number - 1]
                      
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
        labelObject.setText(self.data.configSensorTypeList[index])
        self.data.configSensorSelectedType[sensor - 1] = index

    #########################
    #### CAMERA SETTINGS ####
    #########################
    def setCamerasNumber(self):
        """
        PURPOSE

        Adds specific number of cameras to drop down menu for each analog camera feed.

        INPUT

        - configStatus = true if function is called by the configSetup function.

        RETURNS

        NONE
        """
        newNumber = self.ui.config_cameras_number.value()
        self.data.configCameraNumber = newNumber
        # ERASE LIST
        del self.data.configCameraList[:]

        # CLEAR MENU OPTIONS
        self.ui.control_camera_1_list.clear()
        self.ui.control_camera_2_list.clear()
        self.ui.control_camera_3_list.clear()
        self.ui.control_camera_4_list.clear()
        self.ui.config_camera_1_list.clear()
        self.ui.config_camera_2_list.clear()
        self.ui.config_camera_3_list.clear()
        self.ui.config_camera_4_list.clear()
        
        self.data.configCameraList.append('None')
        # ADD CAMERAS TO LIST
        for number in range(self.data.configCameraNumber):
            self.data.configCameraList.append('Camera {}'.format(number + 1))
        # ADD LIST TO EACH DROP DOWN MENU

        # CONTROL PANEL
        self.ui.control_camera_1_list.addItems(self.data.configCameraList)
        self.ui.control_camera_1_list.setCurrentIndex(self.data.configDefaultCameraList[0])
        self.ui.control_camera_2_list.addItems(self.data.configCameraList)
        self.ui.control_camera_2_list.setCurrentIndex(self.data.configDefaultCameraList[1])
        self.ui.control_camera_3_list.addItems(self.data.configCameraList)
        self.ui.control_camera_3_list.setCurrentIndex(self.data.configDefaultCameraList[2])
        self.ui.control_camera_4_list.addItems(self.data.configCameraList)
        self.ui.control_camera_4_list.setCurrentIndex(self.data.configDefaultCameraList[3])

        # CONFIGURATION
        self.ui.config_camera_1_list.addItems(self.data.configCameraList)
        self.ui.config_camera_1_list.setCurrentIndex(self.data.configDefaultCameraList[0])
        self.ui.config_camera_2_list.addItems(self.data.configCameraList)
        self.ui.config_camera_2_list.setCurrentIndex(self.data.configDefaultCameraList[1])
        self.ui.config_camera_3_list.addItems(self.data.configCameraList)
        self.ui.config_camera_3_list.setCurrentIndex(self.data.configDefaultCameraList[2])
        self.ui.config_camera_4_list.addItems(self.data.configCameraList)
        self.ui.config_camera_4_list.setCurrentIndex(self.data.configDefaultCameraList[3])

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
        # CAMERA VARIABLE REPRESENTS WHICH CAMERA FEED IS BEING MODIFIED (0,1,2,3)
        # INDEX VARIABLE REPRESENTS THE MENU INDEX SELECTED
        self.data.configDefaultCameraList[camera] = index  
        self.data.controlCameraViewList[camera] = index
        if camera == 0:
            self.ui.control_camera_1_list.setCurrentIndex(self.data.configDefaultCameraList[0])  
        if camera == 1:
            self.ui.control_camera_2_list.setCurrentIndex(self.data.configDefaultCameraList[1]) 
        if camera == 2:
            self.ui.control_camera_3_list.setCurrentIndex(self.data.configDefaultCameraList[2]) 
        if camera == 3:
            self.ui.control_camera_4_list.setCurrentIndex(self.data.configDefaultCameraList[3]) 
  
    def setupDigitalCameras(self):
        """
        PURPOSE

        Apply configuration settings for the digital camera feeds.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # UPDATE CAMERA NAME TEXT BOXES
        self.ui.config_digital_name_1.setText(self.data.configDigitalCameraLabels[0])
        self.ui.config_digital_name_2.setText(self.data.configDigitalCameraLabels[1])
        self.ui.config_digital_name_3.setText(self.data.configDigitalCameraLabels[2])

        # REFRESH DROP DOWN MENUS
        self.updateDigitalCameraMenus(self.data.configDigitalCameraLabels, 
                                        self.data.configDigitalDefaultCameraList,
                                        self.data.configDigitalSelectedList)

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
        self.data.configDigitalDefaultCameraList[camera] = index

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
        # CHANGE CAMERA NAME LABEL
        self.data.configDigitalCameraLabels[camera] = text
        # REFRESH DROP DOWN MENUS
        self.updateDigitalCameraMenus(self.data.configDigitalCameraLabels, 
                                        self.data.configDigitalDefaultCameraList,
                                        self.data.configDigitalSelectedList)

    def updateDigitalCameraMenus(self, items, defaultIndex, currentIndex):
        """
        PURPOSE

        Updates the digital camera drop down menus from the control panel and configuration tab.

        INPUT

        - items = array containing the camera items to display on the drop down menus.
        - defaultIndex = array containing the menu indices for the default selected camera.
        - currentIndex = array containing the menu indices for the current selected camera.

        RETURNS

        NONE
        """
        # REFRESH DROP DOWN MENUS
        self.ui.config_digital_list_1.clear()
        self.ui.config_digital_list_1.addItems(items)
        self.ui.config_digital_list_1.setCurrentIndex(items.index(items[defaultIndex[0]]))
        self.ui.config_digital_list_2.clear()
        self.ui.config_digital_list_2.addItems(items)
        self.ui.config_digital_list_2.setCurrentIndex(items.index(items[defaultIndex[1]]))
        self.ui.config_digital_list_3.clear()
        self.ui.config_digital_list_3.addItems(items)
        self.ui.config_digital_list_3.setCurrentIndex(items.index(items[defaultIndex[2]]))

        self.ui.camera_feed_1_menu.clear()
        self.ui.camera_feed_1_menu.addItems(items)
        self.ui.camera_feed_1_menu.setCurrentIndex(items.index(items[currentIndex[0]]))
        self.ui.camera_feed_2_menu.clear()
        self.ui.camera_feed_2_menu.addItems(items)
        self.ui.camera_feed_2_menu.setCurrentIndex(items.index(items[currentIndex[1]]))
        self.ui.camera_feed_3_menu.clear()
        self.ui.camera_feed_3_menu.addItems(items)
        self.ui.camera_feed_3_menu.setCurrentIndex(items.index(items[currentIndex[2]]))

    #########################
    # KEY BINDING FUNCTIONS #
    #########################
    def addKeyBinding(self, label, configStatus):
        """
        PURPOSE

        Adds a keybinding configurator for a specific ROV control.

        INPUT

        label = the name of the ROV control.
        configStatus = True if a config file exists.

        RETURNS

        NONE
        """
        # SET DEFAULT KEY BINDING IF NO CONFIG FILE IS FOUND
        if configStatus == False:
            self.data.configKeyBindings.append(0)

        # FIND INDEX OF NEW KEY BINDING ON THE KEYBINDINGS TAB
        index = int(self.ui.config_keybindings_form.count() / 2)

        # CREATE CONFIG TAB KEYBINDING WIDGETS
        keybindingLabel = QLabel(label)
        keybindingLabel.setStyleSheet("font-weight: bold;")
        keybindingLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        currentBinding = QComboBox()
        currentBinding.addItems(self.data.configKeyBindingsList)
        currentBinding.setCurrentIndex(self.data.configKeyBindings[index])

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
        currentBinding.activated.connect(lambda binding, index = index: self.setKeyBindings(binding, index))
        setBinding.clicked.connect(lambda bindingFound = False, 
                                            binding = None, index = index, 
                                            buttonObject = setBinding, 
                                            menuObject = currentBinding: 
                                            self.autoKeyBinding(bindingFound, binding, index, buttonObject, menuObject))

    def removeKeyBinding(self, index):
        """
        PURPOSE

        Deletes a specific keybinding

        INPUT

        index = position of the keybinding configurator in the keybinding group box to delete.

        RETURNS

        NONE
        """
        # REMOVE ACTUATOR KEYBINDINGS FROM CONFIG TAB
        self.ui.config_keybindings_form.removeRow(index)
        del self.data.configKeyBindings[index]

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
        self.data.configKeyBindings[index] = binding

        # PREVENT BINDING BEING ASSOCIATED WITH MULTIPLE CONTROLS
        for i, item in enumerate(self.data.configKeyBindings):
            # CHECK IF BINDING ALREADY EXISTS
            if i != index:
                if item == binding and item != 0:
                    # SET BINDING TO NONE
                    self.data.configKeyBindings[i] = 0
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
        buttonStates = self.data.configButtonStates

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
        self.writeConfig(self.data.programTheme,
                            self.data.configThrusterPosition,
                            self.data.configThrusterReverse, 
                            self.data.configActuatorLabelList,
                            self.data.configActuatorNumber,
                            self.data.configSensorSelectedType,
                            self.data.configSensorNumber,
                            self.data.configDefaultCameraList,
                            self.data.configCameraNumber,
                            self.data.configDigitalCameraLabels,
                            self.data.configDigitalDefaultCameraList,
                            self.data.configKeyBindings,
                            self.data.configKeyBindingsList)

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

    def writeConfig(self, theme,
                        thrusterPosition, 
                        thrusterReverse, 
                        actuatorLabelList,
                        actuatorNumber, 
                        sensorSelectedType,
                        sensorNumber, 
                        defaultCameraList,
                        cameraNumber,
                        digitalCameraLabels,
                        defaultDigitalList,
                        keyBindings,
                        keyBindingsList):
        """
        PURPOSE

        Writes current program configuration to Config.xml file.

        INPUT

        - thrusterPosition = array containing the thruster positions on the ROV.
        - thrusterReverse = array containing the direction of the thrusters.
        - actuatorLabelList = array containing the name, off and on state labels for the actuators.
        - actuatorNumber = the number of actuators.
        - sensorSelectedType = array containing the sensor types.
        - sensorNumber = the number of sensors.
        - defaultCameraList = array containing the selection of cameras on the four feeds.
        - cameraNuber = the number of analog cameras.
        - keyBindings = array containing the controller keybindings for the actuators.
        - keyBindingsList = array containing the name of each button on the controller.

        RETURNS

        NONE
        """
        root = Element("root")

        SubElement(root, "theme").text = "dark" if theme else "light"
        
        ###################################
        ### CONFIGURATION FOR THRUSTERS ###
        ###################################
        thrusters = SubElement(root, "thrusters")
        for index in range(8):
            thruster = SubElement(thrusters, "thruster{}".format(index))
            SubElement(thruster, "location").text = thrusterPosition[index]
            SubElement(thruster, "reversed").text = "True" if thrusterReverse[index] else "False"
        
        ###################################
        ### CONFIGURATION FOR ACTUATORS ###
        ###################################
        actuators = SubElement(root, "actuators")
        SubElement(actuators, "quantity").text = str(actuatorNumber)
        
        for index in range(self.data.configActuatorNumber):
            actuator = SubElement(actuators, "actuator{}".format(index))
            SubElement(actuator, "nameLabel").text = actuatorLabelList[index][0]
            SubElement(actuator, "offLabel").text = actuatorLabelList[index][1]
            SubElement(actuator, "onLabel").text = actuatorLabelList[index][2]

        ###################################
        #### CONFIGURATION FOR SENSORS ####
        ###################################
        sensors = SubElement(root, "sensors")
        SubElement(sensors, "quantity").text = str(sensorNumber)
        
        for index in range(sensorNumber):
            sensor = SubElement(sensors, "sensor{}".format(index))
            SubElement(sensor, "type").text = str(sensorSelectedType[index])

        ###################################
        #### CONFIGURATION FOR CAMERAS ####
        ###################################
        cameras = SubElement(root, "cameras")
        analog = SubElement(cameras, "analog")
        digital = SubElement(cameras, "digital")

        # ANALOG CAMERAS
        SubElement(analog, "quantity").text = str(cameraNumber)
        for index in range(4):
            SubElement(analog, "defaultfeed{}".format(index)).text = str(defaultCameraList[index])

        digitalLabels = SubElement(digital, "labels")
        for index in range(3):
            SubElement(digitalLabels, "camera{}".format(index + 1)).text = str(digitalCameraLabels[index])

        defaultFeeds = SubElement(digital, "defaultfeeds")
        for index in range(3):
            SubElement(defaultFeeds, "feed{}".format(index + 1)).text = str(defaultDigitalList[index])
        
        ###################################
        ## CONFIGURATION FOR KEYBINDINGS ##
        ###################################
        keybindings = SubElement(root, "keybindings")

        # KEYBINDING TO SWITCH ROV CONTROL ORIENTATION
        SubElement(keybindings, "switch_control_direction".format(index)).text = str(keyBindingsList[keyBindings[0]])

        # KEYBINDING TO CHANGE CONTROLLER SENSITIVITY
        SubElement(keybindings, "controller_sensitivity".format(index)).text = str(keyBindingsList[keyBindings[1]])

        # KEYBINDING TO YAW RIGHT
        SubElement(keybindings, "right_yaw".format(index)).text = str(keyBindingsList[keyBindings[2]])
        
        # KEYBINDING TO YAW LEFT
        SubElement(keybindings, "right_left".format(index)).text = str(keyBindingsList[keyBindings[3]])

        # KEYBINDING TO YAW SENSITIVITY
        SubElement(keybindings, "yaw_sensitivity".format(index)).text = str(keyBindingsList[keyBindings[4]])
        
        # KEYBINDINGS TO ACTUATE EACH ACTUATOR
        for index in range(actuatorNumber):
            SubElement(keybindings, "actuator{}".format(index)).text = str(keyBindingsList[keyBindings[index + 5]])

        # SAVE TO XML FILE                                                           
        tree = ElementTree(root)
        tree.write(self.data.fileName,encoding='utf-8', xml_declaration=True)

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
    rovConnectButtonStatus = False          # TRUE WHEN CONNECT BUTTONS IS PRESSED
    rovCommsStatus = False                  # TRUE WHEN CONNECTION TO COM PORT IS SUCCESSFUL
    controllerConnectButtonStatus = False   # TRUE WHEN CONNECTION TO CONTROLLER IS SUCCESSFUL

    controlActuatorStates = []              # STORES STATE OF EACH ACTUATOR
    controlSensorValues = []                # STORES RECIEVED SENSORS VALUES
    controlSensorLabelObjects = []          # STORES SENSOR LABEL OBJECTS

    controlCameraViewList = [None] * 4      # STORES THE SELECTED EXTERNAL CAMERA FEEDS

    controlVisionTaskStatus = [False] * 4   # STORES THE ON/OFF STATUS OF EACH TASK
    
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

    controlControlDirection = True          # ROV CONTROL ORIENTATION (TRUE = FORWARD, FALSE = REVERSE)
    controllerSensitivity = 2/3             # 1/3, 2/3 or 3/3 controller sensitivity
    yawSensitivity = 2/3                    # 1/3, 2/3 or 3/3 yaw sensitivity

    controlTimerEnabled = False             # TIMER START/STOP BUTTON
    controlTimerNew = True                  # FALSE IF TIMER IS STARTED AGAIN AFTER BEING PAUSED
    controlTimerMem = 0                     # TIME WHEN THE TIMER IS PAUSED

    controlMosaicTaskStatus = False         # TRUE IF STARTED
    controlShapeDetectionTaskStatus = False # TRUE IF STARTED

    ###############################
    ######## CONFIGURATION ########
    ###############################
    fileName = 'config/config.xml' # DEFAULT CONFIG FILE NAME

    # THRUSTER CONFIGURATION SETTINGS
    configThrusterNumber = 8
    configThrusterPositionList = ['None', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    configThrusterPosition = ['None'] * 8
    configThrusterReverse = [False] * 8
    yawButtonStates = [0,0]
    yawButtonStatesPrevious = [0,0]

    # SENSOR CONFIGURATION SETTINGS
    configSensorNumber = 0
    configSensorTypeList = ['None','Temperature (°C)','Depth (m)', 'Yaw (°)', 'Pitch (°)', 'Roll (°)']
    configSensorSelectedType = []
    
    # ACTUATOR CONFIGURATION SETTINGS
    configActuatorNumber = 0
    configActuatorLabelList = []    # LABELS (NAME, DEFAULT STATE, ACTUATED STATE)

    # EXTERNAL CAMERA CONFIGURATION SETTINGS
    # ANALOG
    configCameraNumber = 0 
    configCameraList = []   # LIST OF AVAILABLE CAMERAS
    configDefaultCameraList = [0] * 4   # DEFAULT CAMERAS TO SHOW ON STARTUP
    # DIGITAL
    configDigitalCameraLabels = ['Camera 1', 'Camera 2', 'Camera 3']
    configDigitalDefaultCameraList = [0, 1, 2]
    configDigitalSelectedList = [0, 1, 2]

    # KEY BINDING CONFIGURATION SETTINGS
    # KEY BINDING LIST FOR DROP DOWN MENU
    configKeyBindingsList = ['None','A','B','X','Y','LB','RB','SELECT','START','LS','RS','LEFT','RIGHT','DOWN','UP']
    # THE ORDER THAT BUTTONS APPEAR IN THE BUTTON STATES ARRAY
    configControllerButtons = ['A','B','X','Y','LB','RB','SELECT','START','LS','RS','LEFT','RIGHT','DOWN','UP']
    configControllerButtonReleased = [True] * 14    # USED FOR DEBOUNCING CONTROLLER BUTTONS
    configKeyBindings = []  # STORES SELECTED BINDINGS
    
    configButtonStates = [] # STORES CONTROLLER BUTTON STATES
    configJoystickValues = [] # STORES CONTROLLER JOYSTICK STATES

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