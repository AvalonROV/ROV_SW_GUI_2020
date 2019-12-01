from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer
from PyQt5.QtWidgets import QApplication, QComboBox, QRadioButton, QFormLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QCheckBox
from PyQt5.QtGui import QPixmap, QImage

import threading
import time
import datetime
import sys
import cv2
import serial
import xml.etree.ElementTree as xml
import numpy
import subprocess
import webbrowser
import pygame

# SERIAL LIBRARY
from avalonComms import ROV
from avalonComms import controller as CONTROLLER

class UI(QtWidgets.QMainWindow):
    """
    PURPOSE

    Handles everything to do with the GUI.
    """
    # INITIAL SETUP
    def __init__(self):
        """
        PURPOSE

        Initialises objects, loads GUI and runs initial setup functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        super(UI,self).__init__()
        # LOAD UI FILE
        uic.loadUi('gui.ui',self)

        # CREATING OBJECTS AND PASSING OBJECTS TO THEM
        self.data = DATABASE()
        self.rov = ROV()
        self.controller = CONTROLLER()
        self.control = CONTROL_PANEL(self, self.data, self.rov, self.controller)
        self.config = CONFIG(self, self.data, self.control, self.rov, self.controller)
        self.toolbar = TOOLBAR(self, self.data)
        
        # FIND SCREEN SIZE
        self.data.sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)
        self.data.screenHeight = self.data.sizeObject.height()
        self.data.screenWidth = self.data.sizeObject.width()

        # SET DEFAULT WIDGET SIZES
        self.con_panel_functions_widget.resize(self.data.screenWidth/6,self.con_panel_functions_widget.height())

        # ADD AVALON LOGO
        pixmap = QPixmap("logo.png")
        pixmap = pixmap.scaledToWidth(250)
        self.avalon_logo.setPixmap(pixmap)

        # LINK GUI BUTTONS TO METHODS
        self.linkToolbarWidgets()
        self.linkControlPanelWidgets()
        self.linkConfigWidgets()

        # INITIATE CAMERA FEEDS
        self.initiateCameraFeed()

        # SEND OUT ID REQUEST TO EACH COM PORT TO AUTOMATICALLY FIND ROV
        self.data.comPorts = self.rov.findROVs(self.data.rovID)

        # LOAD SETTING FROM CONFIG FILE
        self.configSetup()

        # RESIZE CAMERA FEEDS WHEN WINDOW IS RESIZED
        #self.resizeEvent(QtGui.QResizeEvent(self.size(), QtCore.QSize()))

        # INITIALISE UI
        self.showMaximized()

    #def resizeEvent(self, event):
        #self.data.windowSizeObject = self.size()
        #self.data.windowHeight = self.data.windowSizeObject.height()
        #self.data.windowWidth = self.data.windowSizeObject.width()

        #self.primary_camera.setFixedHeight(self.data.windowHeight*2/3)
        #QtWidgets.QMainWindow.resizeEvent(self, event)
    
    def configSetup(self):
        """
        PURPOSE

        Reads the Config.xml file and configures the programs thruster, actuator, sensor, camera and controller settings.
        If no Config.xml file is found, the program will open with default settings. 

        INPUT

        NONE

        RETURNS

        NONE
        """
        try:
            configFile = xml.parse(self.data.fileName)
            configFileStatus = True
        except:
            print('Configuration file not found')
            configFileStatus = False

        if configFileStatus == True:
            # FACTORY RESET GUI CONFIGURATION
            self.resetConfig(False)

            root = configFile.getroot()

            for child in root:
                ##############################
                ### READ THRUSTER SETTINGS ###
                ##############################
                if child.tag == 'thrusters':
                    for index, thruster in enumerate(child):
                        self.data.configThrusterPosition[index] = thruster.find("location").text
                        self.data.configThrusterReverse[index] = True if thruster.find("reversed").text == 'True' else False
       
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
                            self.data.configActuatorLabelList.append([])
                            self.data.configActuatorLabelList[index1 - 1].append('')
                            self.data.configActuatorLabelList[index1 - 1].append('')
                            self.data.configActuatorLabelList[index1 - 1].append('')

                            for index2, label in enumerate(actuator):
                                self.data.configActuatorLabelList[index1 - 1][index2] = label.text

                ##############################
                #### READ SENSOR SETTINGS ####
                ##############################
                if child.tag == 'sensors':
                    for index, sensor in enumerate(child):
                        # SET NUMBER OF SENSORS AND SENSOR TYPE
                        if sensor.tag == 'quantity':
                            self.config_sensors_number.setValue(int(sensor.text))
                        else:
                            self.data.configSensorSelectedType.append(0)
                            for sensorType in sensor:
                                self.data.configSensorSelectedType[index - 1] = int(sensorType.text)
                    
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
                                    self.data.configDefaultCameraList[index - 1] = int(camera.text)

                        # DIGITAL CAMERAS
                        if cameraType.tag == 'digital':
                            pass

                ##############################
                #### READ CONFIG SETTINGS ####
                ##############################
                if child.tag == 'keybindings':
                    for control in child:
                        self.data.configKeyBindings.append(self.data.configKeyBindingsList.index(control.text))     

            ###############################
            #### APPLY SETTINGS TO GUI ####
            ###############################
            
            # ADD KEYBINDING FOR SWITCHING CONTROL ORIENTATION
            self.config.addKeyBinding("Switch Orientation", 0, True)
            # UPDATE GUI WITH THRUSTER DATA
            self.config.setThrustersNumber(self.data.configThrusterNumber)
            # UPDATE GUI WITH ACTUATOR DATA
            self.config.setActuatorsNumber(True)  
            # UPDATE GUI WITH SENSOR DATA
            self.config.setSensorsNumber(True) 
            # UPDATE GUI WITH ANALOG CAMERA DATA
            self.config.setCamerasNumber(True)                        

    def resetConfig(self, resetStatus):
        """
        PURPOSE

        Resets the program to default settings (nothing unconfigured).
        
        INPUT

        - resetStatus = true when called via the 'Reset Configuration' button.

        RETURNS

        NONE
        """
        ###############################
        ### RESET THRUSTER SETTINGS ###
        ###############################
        for number in range(self.data.configThrusterNumber):
            # REMOVE THRUSTERS FROM CONFIG TAB
            self.config_thruster_form.removeRow(0)

        self.data.configThrusterPosition = ['None'] * 8
        self.data.configThrusterReverse = [False] * 8

        # RETURN NUMBER OF THRUSTERS TO 8 IF RESET BUTTON IS PRESSED
        if resetStatus == True:
            self.config.setThrustersNumber(self.data.configThrusterNumber)

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
        for number in range(self.data.configSensorNumber):
            # REMOVE SENSORS FROM CONFIG TAB
            self.config_sensor_form.removeRow(2) 
            # REMOVE SENSORS FROM CONTROL PANEL TAB
            self.control_panel_sensors.removeRow(0)
        self.config_sensors_number.setValue(0)
        self.data.configSensorNumber = 0

        ###############################
        #### RESET CAMERA SETTINGS ####
        ###############################
        self.data.configDefaultCameraList = [0] * 4
        self.data.configCameraList = []
        self.config_cameras_number.setValue(0)
        self.config_camera_1_list.clear()
        self.config_camera_2_list.clear()
        self.config_camera_3_list.clear()
        self.config_camera_4_list.clear()

        ###############################
        ## RESET KEYBINDING SETTINGS ##
        ###############################
        numberDelete = len(self.data.configKeyBindings)
        for index in range(numberDelete):
            self.config.removeKeyBinding(numberDelete - index - 1)

        # RE-ADD DEFAULT KEY BINDING TO SWITCH ROV ORIENTATION IF RESET BUTTON IS PRESSED
        if resetStatus == True:
            self.config.addKeyBinding("Switch Orientation", 0, False)
        
    def linkControlPanelWidgets(self):
        """
        PURPOSE

        Links widgets in the control panel tab to their respective functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.control_rov_connect.clicked.connect(self.control.rovConnect)
        self.control_rov_connect.setFixedHeight(self.control_rov_connect.geometry().height() * 1.5)
        self.control_rov_connect.setStyleSheet(self.data.defaultBlue)
        self.control_controller_connect.clicked.connect(self.control.controllerConnect)
        self.control_controller_connect.setFixedHeight(self.control_controller_connect.geometry().height() * 1.5)
        self.control_controller_connect.setStyleSheet(self.data.defaultBlue)
        self.control_switch_direction.setIcon(QtGui.QIcon('graphics/switch_direction.png'))
        self.control_switch_direction.clicked.connect(self.control.switchControlDirection)
        self.control_switch_direction.setFixedHeight(self.control_switch_direction.geometry().height() * 1.5)
        self.control_switch_direction_forward.setStyleSheet(self.data.textGreenStyle)
        self.control_switch_direction_reverse.setStyleSheet(self.data.textDisabledStyle)
        self.control_switch_direction.setIconSize(QtCore.QSize(50,50))
        self.control_timer_start.clicked.connect(self.control.toggleTimer)
        self.control_timer_start.setStyleSheet(self.data.greenStyle)
        self.control_timer_reset.clicked.connect(self.control.resetTimer)
        self.control_timer.setNumDigits(11)
        self.control_timer.display('00:00:00:00')
        self.control_timer.setMinimumHeight(48)

        # LINK EACH DEFAULT CAMERA DROP DOWN MANU TO THE SAME SLOT, PASSING THE CAMERA ID AS 1,2,3,4 ETC.
        self.control_camera_1_list.activated.connect(lambda index, camera = 0: self.control.changeExternalCameraFeed(index, camera))
        self.control_camera_2_list.activated.connect(lambda index, camera = 1: self.control.changeExternalCameraFeed(index, camera))
        self.control_camera_3_list.activated.connect(lambda index, camera = 2: self.control.changeExternalCameraFeed(index, camera))
        self.control_camera_4_list.activated.connect(lambda index, camera = 3: self.control.changeExternalCameraFeed(index, camera))

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
        self.toolbar_reset_settings.triggered.connect(lambda: self.resetConfig(True))
        self.toolbar_save_settings.triggered.connect(self.toolbar.saveSettings)
        self.toolbar_open_documentation.triggered.connect(self.toolbar.openDocumentation)
        self.toolbar_open_github.triggered.connect(self.toolbar.openGitHub)

    def linkConfigWidgets(self):
        """
        PURPOSE

        Links widgets in the configuration tab to their respective functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.config_sensors_number.editingFinished.connect(lambda: self.config.setSensorsNumber(False))
        self.config_cameras_number.editingFinished.connect(lambda: self.config.setCamerasNumber(False))
        self.config_actuators_number.editingFinished.connect(lambda: self.config.setActuatorsNumber(False))
        
        # ADD THRUSTER CONFIGURATION WIDGETS
        self.config.setThrustersNumber(self.data.configThrusterNumber)

        # CREATE KEYBINDING FOR ACTUATOR
        self.config.addKeyBinding("Switch Orientation", 0, False)

        # CREATE DISPLAY FOR CONTROLLER INPUTS
        self.config.setControllerValuesDisplay()

        # LINK EACH DEFAULT CAMERA DROP DOWN MANU TO THE SAME SLOT, PASSING THE CAMERA ID AS 1,2,3,4 ETC.
        self.config_camera_1_list.activated.connect(lambda index, camera = 0: self.config.changeDefaultCameras(index, camera))
        self.config_camera_2_list.activated.connect(lambda index, camera = 1: self.config.changeDefaultCameras(index, camera))
        self.config_camera_3_list.activated.connect(lambda index, camera = 2: self.config.changeDefaultCameras(index, camera))
        self.config_camera_4_list.activated.connect(lambda index, camera = 3: self.config.changeDefaultCameras(index, camera))

    def initiateCameraFeed(self):
        """
        PURPOSE

        Starts each camera feed in a new thread.

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass
        # INITIATE CAMERAS IN SEPERATE THREADS
        # PRIMARY CAMERA
        camThread1 = CAMERA_FEED_1(self)
        camThread1.cameraNewFrame.connect(self.updateCamera1Feed)
        camThread1.start()
        # SECONDARY CAMERA 1
        camThread2 = CAMERA_FEED_2(self)
        camThread2.cameraNewFrame.connect(self.updateCamera2Feed)
        camThread2.start()
        # SECONDARY CAMERA 2
        #camThread3 = CAMERA_FEED_3(self)
        #camThread3.cameraNewFrame.connect(self.updateCamera3Feed)
        #camThread3.start()

    @pyqtSlot(QImage)
    def updateCamera1Feed(self, frame):
        """
        PURPOSE

        Refreshes camera feed 1 with a new frame.

        INPUT

        - frame = QImage containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        # SET SIZE
        #frame = frame.scaled(self.primary_camera.size().width(), self.primary_camera.size().height(), QtCore.Qt.KeepAspectRatio)
        # DISPLAY NEW FRAME ON CAMERA FEED
        self.primary_camera.setPixmap(QPixmap.fromImage(frame))

    @pyqtSlot(QImage)
    def updateCamera2Feed(self, frame):
        """
        PURPOSE

        Refreshes camera feed 2 with a new frame.

        INPUT

        - frame = QImage containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        # DISPLAY NEW FRAME ON CAMERA FEED
        self.secondary_camera_1.setPixmap(QPixmap.fromImage(frame))

    @pyqtSlot(QImage)
    def updateCamera3Feed(self, frame):
        """
        PURPOSE

        Refreshes camera feed 3 with a new frame.

        INPUT

        - frame = QImage containing the new frame captures from the camera.

        RETURNS

        NONE
        """
        # DISPLAY NEW FRAME ON CAMERA FEED
        self.secondary_camera_2.setPixmap(QPixmap.fromImage(frame))

class CAMERA_FEED_1(QThread):
    # CREATE SIGNAL
    cameraNewFrame = pyqtSignal(QImage)

    # URL of camera stream
    channel = 0
    
    def run(self):
        # INITIATE SECONDARY 1 CAMERA
        cameraFeed = cv2.VideoCapture(self.channel)
        
        while True:
            # CAPTURE FRAME
            ret, frame = cameraFeed.read()
            # IF FRAME IS SUCCESSFULLY CAPTURED            
            if ret:
                # CONVERT TO RGB COLOUR
                cameraFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
                height, width, _ = cameraFrame.shape
                # CONVERT TO QIMAGE
                cameraFrame = QtGui.QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QtGui.QImage.Format_RGB888)
                # SET SIZE
                cameraFrame = cameraFrame.scaled(1920, 1080, QtCore.Qt.KeepAspectRatio)
                # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                self.cameraNewFrame.emit(cameraFrame)
                QThread.msleep(40)

class CAMERA_FEED_2(QThread):
    # CREATE SIGNAL
    cameraNewFrame = pyqtSignal(QImage)

    # URL of camera stream
    channel = 1 
    
    def run(self):
        # INITIATE SECONDARY 1 CAMERA
        cameraFeed = cv2.VideoCapture(self.channel)
        
        while True:
            # CAPTURE FRAME
            ret, frame = cameraFeed.read()
            # IF FRAME IS SUCCESSFULLY CAPTURED            
            if ret:
                # CONVERT TO RGB COLOUR
                cameraFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
                height, width, _ = cameraFrame.shape
                # CONVERT TO QIMAGE
                cameraFrame = QtGui.QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QtGui.QImage.Format_RGB888)
                # SET SIZE
                cameraFrame = cameraFrame.scaled(400, 400, QtCore.Qt.KeepAspectRatio)
                # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                self.cameraNewFrame.emit(cameraFrame)
                QThread.msleep(40)

class CAMERA_FEED_3(QThread):
    # CREATE SIGNAL
    cameraNewFrame = pyqtSignal(QImage)

    # URL of camera stream
    channel = 2 
    
    def run(self):
        # INITIATE SECONDARY 1 CAMERA
        cameraFeed = cv2.VideoCapture(self.channel)
        
        while True:
            # CAPTURE FRAME
            ret, frame = cameraFeed.read()
            # IF FRAME IS SUCCESSFULLY CAPTURED            
            if ret:
                # CONVERT TO RGB COLOUR
                cameraFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
                height, width, _ = cameraFrame.shape
                # CONVERT TO QIMAGE
                cameraFrame = QtGui.QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QtGui.QImage.Format_RGB888)
                # SET SIZE
                cameraFrame = cameraFrame.scaled(500, 500, QtCore.Qt.KeepAspectRatio)
                # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                self.cameraNewFrame.emit(cameraFrame)

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

    def rovConnect(self):
        """
        PURPOSE

        Initialises serial communication with the ROV and starts sensor reading requests.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.controlROVCommsStatus == False:
            self.data.controlROVCommsStatus = True
            self.ui.control_rov_connect.setText('DISCONNECT')
            self.ui.control_rov_connect.setStyleSheet(self.data.blueStyle)
            self.rov.initialiseConnection('AVALON',self.data.rovCOMPort, 115200)
            # START FETCHING SENSOR READINGS
            self.getSensorReadings()
        else:
            self.data.controlROVCommsStatus = False
            self.ui.control_rov_connect.setText('CONNECT')
            self.ui.control_rov_connect.setStyleSheet(self.data.defaultBlue)
            self.rov.disconnect()

    def controllerConnect(self):
        """
        PURPOSE

        Initialises bluetooth communication with the XBOX controller.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.controlControllerCommsStatus == False:
            self.data.controlControllerCommsStatus = True
            self.ui.control_controller_connect.setText('DISCONNECT')
            self.ui.control_controller_connect.setStyleSheet(self.data.blueStyle)
            self.controller.initialiseConnection(self.data.controllerCOMPort)
            self.initiateController()
        else:
            self.data.controlControllerCommsStatus = False
            self.ui.control_controller_connect.setText('CONNECT')
            self.ui.control_controller_connect.setStyleSheet(self.data.defaultBlue) 
            # NEED TO FIND A BETTER SOLUTION TO DISCONNECT THE XBOX CONTROLLER   
            #pygame.joystick.quit()   

    def initiateController(self):
        """
        PURPOSE

        Initiates the PyGame library and any connected controllers.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # INITIALISE PYGAME MODULE
        pygame.init()

        self.done = False

        # INITIALISE JOYSICKS
        pygame.joystick.init()

        # GET NUMBER OF JOYSTICKS CONNECTED
        joystick_count = pygame.joystick.get_count()

        if joystick_count < 1:
            print('Joystick not found')
            self.controllerConnect()
            pygame.quit()

        else:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                # GET NAME OF CONTROLLER/JOYSTICK FROM OS
                name = joystick.get_name()
            
            # ONLY ACCEPT XBOX CONTROLLER
            if name == 'Controller (Xbox One For Windows)':
                print('Connected to controller')
                # READ CONTROLLER INPUTS IN A TIMED THREAD
                self.controllerEventLoop()

    def processButtons(self, buttonStates):
        """
        PURPOSE

        Analyses the states of all the buttons.
        If a button has been pressed, the corresponding control that the button is binded to is toggled.

        INPUT

        - buttonStates = an array containing the states of all the controller buttons (0 or 1).

        RETURNS

        NONE
        """
        for index, button in enumerate(buttonStates):
            # IF BUTTON IS PRESSED
            if button == 1:
                # FIND WHICH BUTTON HAS BEEN PRESSED
                whichButton = self.data.configControllerButtons[index]
                # FIND THE INDEX ON THE KEYBINDINGS MENU THAT CORRESPONDS TO THAT BUTTON
                whichMenuIndex = self.data.configKeyBindingsList.index(whichButton)
                # FIND WHICH ACTUATOR USES THAT KEYBINDING
                try:
                    whichControl = self.data.configKeyBindings.index(whichMenuIndex)
                    buttonExists = True
                except:
                    print('Button not assigned')
                    buttonExists = False

                # IF BUTTON IS ASSIGNED IN THE PROGRAM AND HAS PREVIOUSLY BEEN RELEASED
                if buttonExists == True & self.data.configControllerButtonReleased[index] == True:
                    # PREVENT TOGGLING BEING ACTUATED AGAIN UNTIL THE BUTTON IS RELEASED
                    self.data.configControllerButtonReleased[index] = False
                    # IF ROV CONTROL ORIENTATION IS BEING TOGGLED
                    if whichControl == 0:
                        self.switchControlDirection()
                    
                    # IF ROV ACTUATOR IS BEING TOGGLED
                    else:
                        # FIND POINTER TO THE BUTTON WIDGET CORRESPONDING TO THE ACTUATOR
                        widget = self.ui.control_panel_actuators.itemAt((2*whichControl)-1).widget()
                        # TOGGLES ACTUATORS AND CHANGES APPEARANCE OF GUI BUTTON
                        self.toggleActuator(None, whichControl - 1, widget)
            
            # WAIT FOR BUTTON TO BE RELEASED
            else:
                self.data.configControllerButtonReleased[index] = True

    def processJoysticks(self, joystickValues):
        """
        PURPOSE
        -Analyses the values of all the joysticks.
        -Rounds their values to 1 decimal place.
        -Adds dead zone.

        INPUT

        - joystickValues = an array containing the values of all the joysticks (-1 -> 1).

        RETURNS

        NONE
        """
        # ADD DEADZONE OF 0.1
        joystickValues = [0 if (number < 0.1 and number > -0.1) else number for number in joystickValues]
        # ROUND TO 1 DECIMAL PLACE
        joystickValues = [round(number, 1) for number in joystickValues]
        
        # RUN THRUSTER VECTOR CONTROL ALGORITHM
        self.thrusterVectorAlgorithm(joystickValues)

        return(joystickValues)
        
    def controllerEventLoop(self):
        """
        PURPOSE

        - Initiates a seperate thread that continuously requests the controller joystick and button states.
        - Passes button states and joystick values to processing functions.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # TAKE SINGLE READINGS OF CONTROLLER STATES
        buttonStates, joystickValues = self.getControllerInputs(self.data.controlControllerCommsStatus)

        # PROCESS BUTTON STATES
        self.processButtons(buttonStates)
        
        # PROCESS JOYSTICK VALUES
        filteredJoystickValues = self.processJoysticks(joystickValues)

        # UPDATE GUI
        self.updateControllerValuesDisplay(buttonStates, filteredJoystickValues)

        # UPDATE CONTROLLER INPUTS AT A RATE OF 30FPS TO REDUCE CPU USAGE
        thread = threading.Timer(1/30,self.controllerEventLoop)
        thread.daemon = True                            
        thread.start()

    def getControllerInputs(self, connectStatus):
        """
        PURPOSE

        Gets a single readings of all the button and joystick values from the controller.

        INPUT

        connectStatus = False to disconnect the controller and close the thread.

        RETURNS

        - buttonStates = an array containing the states of all the controller buttons (0 or 1).
        - joystickValues = an array containing the values of all the joysticks (-1 -> 1).
        """
        # STORES THE STATE OF EACH BUTTON
        buttonStates = []
        # STORES THE VALUES OF EACH JOYSTICK
        joystickValues = []

        # EVENT PROCESSING STEP
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
        
        # GET NUMBER OF JOYSTICKS CONNECTED
        joystick_count = pygame.joystick.get_count()

        # INITIATE EACH JOYSTICK (ONLY 1 FOR THIS PROGRAM)
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()

            # GET NUMBER OF VARIABLE JOYSTICK AXES
            axes = joystick.get_numaxes()
            
            # GET VALUES OF EACH VARIABLE AXES
            for i in range(axes):
                axis = joystick.get_axis(i)
                joystickValues.append(axis)
    
            # GET NUMBER OF BUTTONS
            buttons = joystick.get_numbuttons()

            # GET STATE OF EACH BUTTON
            for i in range(buttons):
                button = joystick.get_button(i)
                buttonStates.append(button)
                           
            # GET NUMBER OF ARROW BUTTONS
            hats = joystick.get_numhats()
    
             # GET STATE OF EACH ARROW BUTTONS
            for i in range(hats):
                hat = joystick.get_hat(i)

        # DISCONNECT CONTROLLER AND EXIT THREAD IF DISCONNECT BUTTON HAS BEEN PRESSED
        if connectStatus == False:
            print('QUIT CONTROLLER')
            pygame.quit()
            exit()

        # RETURN ARRAY OF BUTTON STATES AND JOYSTICK VALUES
        return(buttonStates, joystickValues)

    def thrusterVectorAlgorithm(self, joystickValues):
        """
        PURPOSE

        Calculates the required speed of each thruster on the ROV to move a certain direction.

        INPUT
        - joystickValues = an array containing the filtered values of all the joysticks (-1 -> 1).

        RETURNS
        - motorSpeeds = array containing the speed of each thruster
        """
        pass

    def updateControllerValuesDisplay(self, buttonStates, joystickValues):
        """
        PURPOSE

        Updates the text fields on the configuration tab with the latest controller button states and joystick values.

        INPUT

        - buttonStates = an array containing the states of all the controller buttons (0 or 1).
        - joystickValues = an array containing the values of all the joysticks (-1 -> 1).

        RETURNS
        
        NONE
        """
        #print(buttonStates)
        # UPDATE JOYSTICK VALUES
        for index in range(5):
            self.data.configControllerLabelObjects[index].setText(str(joystickValues[index]))

        # UPDATE BUTTON STATES
        for index in range(5,13):
            # AVOID THE UNUSED BUTTON STATES
            if index > 10:
                self.data.configControllerLabelObjects[index].setText(str(buttonStates[index - 3]))
            else:
                self.data.configControllerLabelObjects[index].setText(str(buttonStates[index - 5]))

    def getSensorReadings(self):
        """
        PURPOSE

        Requests sensor readings from ROV and updates GUI.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # READ SENSORS EVERY 1 SECOND
        thread = threading.Timer(0.5, self.getSensorReadings)
        thread.daemon = True                 
        thread.start()
        if self.data.controlROVCommsStatus == False:
            thread.cancel()
        self.data.controlSensorValues = self.rov.getSensors([1]*self.data.configSensorNumber).tolist()
        if len(self.data.controlSensorLabelObjects) > 0:
            for index in range(0,len(self.data.controlSensorValues)):
                self.data.controlSensorLabelObjects[index].setText(str(self.data.controlSensorValues[index]))

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

    def toggleActuator(self, _, actuator, buttonObject):
        """
        PURPOSE

        Sends commmand to ROV when an actuator has been toggled.

        INPUT

        - _ = Not used.
        - actuator = the actuator being toggled.
        - buttonObject = pointer to the button widget (Allowed appearance to be modified)

        RETURNS

        NONE
        """
        if self.data.controlActuatorStates[actuator] == False:
            buttonObject.setText(self.data.configActuatorLabelList[actuator][2])
            buttonObject.setStyleSheet(self.data.redStyle)
            self.data.controlActuatorStates[actuator] = True
            self.rov.setActuators(actuator, True)

        elif self.data.controlActuatorStates[actuator] == True:
            buttonObject.setText(self.data.configActuatorLabelList[actuator][1])
            buttonObject.setStyleSheet(self.data.greenStyle)
            self.data.controlActuatorStates[actuator] = False
            self.rov.setActuators(actuator, False)

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
            self.ui.control_timer_start.setStyleSheet(self.data.redStyle)
            self.startTime = datetime.datetime.now()
            # START TIMER
            self.readSystemTime()
        else:
            self.data.controlTimerEnabled = False
            self.ui.control_timer_start.setText('Start')
            self.ui.control_timer_start.setStyleSheet(self.data.greenStyle)
    
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
            self.ui.control_switch_direction_forward.setStyleSheet(self.data.textDisabledStyle)
            self.ui.control_switch_direction_reverse.setStyleSheet(self.data.textGreenStyle)
        else:
            self.data.controlControlDirection = True
            self.ui.control_switch_direction_forward.setStyleSheet(self.data.textGreenStyle)
            self.ui.control_switch_direction_reverse.setStyleSheet(self.data.textDisabledStyle)

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
        currentTime = datetime.datetime.now()
        currentSeconds = (currentTime - self.startTime).total_seconds() + self.data.controlTimerMem
        self.updateTimer(currentSeconds)
    
        # READ SYSTEM TIME EVERY 1 SECOND (TO REDUCE CPU USAGE)
        thread = threading.Timer(0.5,self.readSystemTime)
        thread.daemon = True                            
        thread.start()
        
        # STOP THREAD IF STOP BUTTON CLICKED
        if self.data.controlTimerEnabled == False:
            thread.cancel()
            self.data.controlTimerMem = currentSeconds

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

class CONFIG():
    """
    PURPOSE

    Handles everything that happens on the Configuration tab.
    """
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3, Object4, Object5):
        """
        PURPOSE

        Initialises objects.

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

    def setThrustersNumber(self, number):
        """
        PURPOSE

        Adds specific number of thrusters to the GUI configration tab, with a ROV location menu, reverse checkbox and a test button.

        INPUT

        - number = the number of thrusters to add.

        RETURNS

        NONE
        """
        for thruster in range(number):
            # CREATE THRUSTER NUMBER LABEL
            thrusterLabel = QLabel("Thruster {}".format(thruster + 1))
            thrusterLabel.setStyleSheet("font-weight: bold;")
            thrusterLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            # CREATE ROV LOCATION DROP DOWN MENU AND ADD ITEMS
            thrusterLocation = QComboBox()
            thrusterLocation.addItems(self.data.configThrusterPositionList)           
            thrusterLocation.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[thruster]))
            # CREATE THRUSTER REVERSE CHECKBOX
            thrusterReverse = QCheckBox()
            thrusterReverse.setChecked(self.data.configThrusterReverse[thruster])
            # CREATE THRUSTER TEST BUTTON
            thrusterTest = QPushButton("Test")
            
            # CREATE GRID LAYOUT
            layout = QGridLayout()
            label1 = QLabel('ROV Location')
            label1.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            layout.addWidget(label1,0,0)
            layout.addWidget(thrusterLocation,0,1)
            label2 = QLabel('Reversed')
            label2.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            layout.addWidget(label2,1,0)
            layout.addWidget(thrusterReverse,1,1)
            layout.addWidget(thrusterTest,2,1)

            # ADD TO CONFIG TAB FORM LAYOUT
            self.ui.config_thruster_form.addRow(thrusterLabel, layout)

            # LINK EACH THRUSTER CONFIGURATION TO SAME SLOT, PASSING THE MENU INDEX, THRUSTER SELECTED, AND WHICH SETTING HAS BEEN CHANGED (POSITION, REVERSE, TEST, CONFIG)
            thrusterLocation.activated.connect(lambda index, thruster = thruster, setting = 0, controlObject = None: self.setROVThrusterSettings(index, thruster, setting, controlObject))
            thrusterReverse.toggled.connect(lambda index, thruster = thruster, setting = 1, controlObject = thrusterReverse: self.setROVThrusterSettings(index, thruster, setting, controlObject))
            thrusterTest.clicked.connect(lambda index, thruster = thruster, setting = 2, controlObject= None: self.setROVThrusterSettings(index, thruster, setting, controlObject))

    def setControllerValuesDisplay(self):
        """
        PURPOSE

        Adds a list of text box's on the configuration tab for each button/joystick to show their current values.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # NAMES OF JOYSTICK AXES
        joystickLabels = ['Left X', 'Left Y','Triggers', 'Right Y', 'Right X']
        buttonLabels = ['A','B','X','Y','LB','RB','LT','RT']
        
        # CREATE DISPLAY FOR JOYSTICKS
        for index in range(5):
            # CREATE JOYSTICK LABEL
            label = QLabel(joystickLabels[index])
            label.setStyleSheet("font-weight: bold;")
            label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            # CREATE TEXT BOX TO DISPLAY VALUE
            value = QLineEdit()
            value.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            value.setReadOnly(True)

            # ADD POINTER FOR THE QLINEEDIT INTO AN ARRAY FOR LATER ACCESS
            self.data.configControllerLabelObjects.append(value)

            # ADD TO FORM LAYOUT
            self.ui.config_controller_form.addRow(label, value)

        # CREATE DISPLAY FOR BUTTONS
        for index in range(8):
            # CREATE BUTTON LABEL
            label = QLabel(buttonLabels[index])
            label.setStyleSheet("font-weight: bold;")
            label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            # CREATE TEXT BOX TO DISPLAY VALUE
            value = QLineEdit()
            value.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            value.setReadOnly(True)

            # ADD POINTER FOR THE QLINEEDIT INTO AN ARRAY FOR LATER ACCESS
            self.data.configControllerLabelObjects.append(value)

            # ADD TO FORM LAYOUT
            self.ui.config_controller_form.addRow(label, value)

    def setROVThrusterSettings(self, index, thruster, setting, controlObject):
        """
        PURPOSE

        Stores thruster settings such as ROV position, reverse state and sends command to ROV to test thruster.

        INPUT

        - index = menu index of the ROV location selected.
        - thruster = teh thruster being modified.
        - setting = the thruster setting that has been modified (0 = position, 1 = reverse state, 2 = test).
        - controlObject = pointer to the checkbox object.

        RETURNS

        NONE
        """
        # THRUSTER POSITION
        if setting == 0:
            self.data.configThrusterPosition[thruster] = self.data.configThrusterPositionList[index]

        # THRUSTER REVERSE
        if setting == 1:
            self.data.configThrusterReverse[thruster] = controlObject.isChecked()

        # THRUSTER TEST
        if setting == 2:
            pass  

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
                actuatorNumber.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
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
                label1.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                actuatorLayout.addWidget(label1,0,0)
                actuatorLayout.addWidget(actuatorLabel,0,1)
                label2 = QLabel('Default State')
                label2.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                actuatorLayout.addWidget(label2,1,0)
                actuatorLayout.addWidget(state1,1,1)
                label3 = QLabel('Actuated State')
                label3.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                actuatorLayout.addWidget(label3,2,0)
                actuatorLayout.addWidget(state2,2,1)

                # SET DEFAULT STYLE SHEET
                actuatorToggle.setStyleSheet(self.data.greenStyle)

                # ADD TO CONFIG TAB ACTUATORS FORM
                self.ui.config_actuator_form.addRow(actuatorNumber, actuatorLayout)
                # ADD TO CONTROL PANEL TAB ACTUATORS FORM
                self.ui.control_panel_actuators.addRow(actuatorName, actuatorToggle)

                # LINK CONFIG ACTUATOR TEXT FIELDS TO SLOT - PASS OBJECT, ACTUATOR NUMBER AND WHICH TEXT FIELD HAS BEEN EDITED
                actuatorLabel.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 0, controlObject = actuatorName: self.changeActuatorType(text, actuator, label, controlObject))
                state1.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 1, controlObject = actuatorToggle: self.changeActuatorType(text, actuator, label, controlObject))
                state2.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 2, controlObject = actuatorToggle: self.changeActuatorType(text, actuator, label, controlObject))
                # LINK CONTROL PANEL ACTUATOR BUTTONS TO SLOT - PASS ACTUATOR NUMBER
                actuatorToggle.clicked.connect(lambda _, actuator = (oldNumber + number), buttonObject = actuatorToggle: self.control.toggleActuator(_, actuator, buttonObject))

                # CREATE KEYBINDING FOR ACTUATOR
                self.addKeyBinding("Actuator {}".format((oldNumber + number + 1)), oldNumber + number + 1, configStatus)

        # REMOVE ACTUATORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF ACTUATORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                # REMOVE ACTUATORS FROM CONFIG TAB
                self.ui.config_actuator_form.removeRow(oldNumber - number) 
                # REMOVE KEYBINDINGS FROM CONFIG TAB
                self.removeKeyBinding(oldNumber - number)
                # REMOVE ACTUATORS FROM CONTROL PANEL TAB
                self.ui.control_panel_actuators.removeRow(oldNumber - number - 1)

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

    def setSensorsNumber(self, configStatus):
        """
        PURPOSE

        Adds specific number of sensors to the GUI configration tab, with a drop down menu containing the sensor types.

        INPUT

        - configStatus = true if function is called by the configSetup function.

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
                # CREATE SENSOR LABEL
                sensorLabel = QLabel(self.data.configSensorTypeList[self.data.configSensorSelectedType[oldNumber + number]])
                # CREATE FORM LAYOUT
                layout = QFormLayout()
                layout.addRow(QLabel("Type"), sensorType)
                # ADD TO CONFIG TAB
                self.ui.config_sensor_form.addRow(QLabel("Sensor {}".format((oldNumber + number + 1))), layout)
                # ADD TO CONTROL PANEL TAB
                self.ui.control_panel_sensors.addRow(sensorLabel, sensorView)
                # STORE LABEL OBJECT IN ARRAY FOR FUTURE ACCESS
                self.data.controlSensorLabelObjects.append(sensorView)
                # LINK DROP DOWN MENU TO SLOT - PASS SENSOR NUMBER AND MENU INDEX SELECTED
                sensorType.activated.connect(lambda index, sensor = (oldNumber + number + 1), sensorSelected = sensorLabel,: self.changeSensorType(index, sensor, sensorSelected))

        # REMOVE SENSORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF SENSORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                # REMOVE SENSORS FROM CONFIG TAB
                self.ui.config_sensor_form.removeRow(oldNumber - number + 1) 
                # REMOVE SENSORS FROM CONTROL PANEL TAB
                self.ui.control_panel_sensors.removeRow(oldNumber - number - 1) 
                del self.data.configSensorSelectedType[oldNumber - number - 1]
                      
    def changeSensorType(self, index, sensor, sensorLabel):
        """
        PURPOSE

        Changes the type and label of a sensor.

        INPUT

        - index = menu index of the sensor type selected.
        - sensor = the sensor being modified.
        - sensorLabel = the sensor label object.

        RETURNS

        NONE
        """
        # SENSOR VARIABLE REPRESENTS WHICH SENSOR IS BEING MODIFIED
        # INDEX VARIABLE REPRESENTS THE MENU INDEX SELECTED
        sensorLabel.setText(self.data.configSensorTypeList[index])
        self.data.configSensorSelectedType[sensor - 1] = index

    def setCamerasNumber(self, configStatus):
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

    def addKeyBinding(self, label, index, configStatus):
        """
        PURPOSE

        Adds a keybinding configurator for a specific ROV control.

        INPUT

        label = the name of the ROV control.
        index = position of the keybinding configurator in the keybinding group box.
        configStatus = True if a config file exists.

        RETURNS

        NONE
        """
        # SET DEFAULT KEY BINDING IF NO CONFIG FILE IS FOUND
        if configStatus == False:
            self.data.configKeyBindings.append(0)
        
        # CREATE CONFIG TAB KEYBINDING WIDGETS
        keybindingLabel = QLabel(label)
        keybindingLabel.setStyleSheet("font-weight: bold;")
        keybindingLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        currentBinding = QComboBox()
        currentBinding.addItems(self.data.configKeyBindingsList)
        currentBinding.setCurrentIndex(self.data.configKeyBindings[index])
        setBinding = QPushButton('Auto Binding')

        # CREATE CONFIG TAB KEYBINDINGS LAYOUT
        keybindingLayout = QGridLayout()
        keybindingLayout.addWidget(currentBinding,0,0)
        keybindingLayout.addWidget(setBinding,1,0)

        # ADD TO CONFIG TAB KEYBINDINGS FORM
        self.ui.config_keybindings_form.addRow(keybindingLabel, keybindingLayout)

        # LINK KEYBINDING WIDGETS TO SLOT - PASS LAYOUT INDEX NUMBER, THE OBJECT, AND AN INDENTIFIER
        currentBinding.activated.connect(lambda binding, index = index, controlObject = currentBinding, identifier = 0: self.setKeyBindings(binding, index, controlObject, identifier))
        setBinding.clicked.connect(lambda binding, index = index, controlObject = setBinding, identifier = 1: self.setKeyBindings(binding, index, controlObject, identifier))

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
        print(self.data.configKeyBindings)

    def setKeyBindings(self, binding, index, controlObject, identifier):
        """
        PURPOSE

        Sets the keybinding for a specific control on the ROV. 
        The keybinding can be selected from a menu, or detected by pressing a button on the controller.

        INPUT
         
        binding = menu index selected.
        index = the ROV control having its key binding changed.
        controlObject = pointer to the widget that has been activated.
        identifier = 0 if the keybinding menu has been activated, 1 if the change binding button has been clicked.
        """
        # KEYBINDING CHANGED VIA DROP DOWN MENU
        if identifier == 0:
            self.data.configKeyBindings[index] = binding
            print(self.data.configKeyBindings)

        # KEYBINDING CHANGED VIA DETECTION BUTTON
        pass

class TOOLBAR():
    """
    PURPOSE

    Handles everything that happens on the toolbar.
    """
    def __init__(self, Object1, Object2):
        self.ui = Object1
        self.data = Object2

    def saveSettings(self):
        """
        PURPOSE

        Saves the current program configuration to the Config.xml file.

        INPUT

        NONE

        RETURNS

        NONE
        """
        root = xml.Element("root")

        ###################################
        ### CONFIGURATION FOR THRUSTERS ###
        ###################################
        thrusters = xml.SubElement(root, "thrusters")
        for index in range(8):
            thruster = xml.SubElement(thrusters, "thruster{}".format(index))
            xml.SubElement(thruster, "location").text = self.data.configThrusterPosition[index]
            xml.SubElement(thruster, "reversed").text = str(self.data.configThrusterReverse[index])
        
        ###################################
        ### CONFIGURATION FOR ACTUATORS ###
        ###################################
        actuators = xml.SubElement(root, "actuators")
        xml.SubElement(actuators, "quantity").text = str(self.data.configActuatorNumber)
        
        for index in range(self.data.configActuatorNumber):
            actuator = xml.SubElement(actuators, "actuator{}".format(index))
            xml.SubElement(actuator, "nameLabel").text = self.data.configActuatorLabelList[index][0]
            xml.SubElement(actuator, "offLabel").text = self.data.configActuatorLabelList[index][1]
            xml.SubElement(actuator, "onLabel").text = self.data.configActuatorLabelList[index][2]

        ###################################
        #### CONFIGURATION FOR SENSORS ####
        ###################################
        sensors = xml.SubElement(root, "sensors")
        xml.SubElement(sensors, "quantity").text = str(self.data.configSensorNumber)
        
        for index in range(self.data.configSensorNumber):
            sensor = xml.SubElement(sensors, "sensor{}".format(index))
            xml.SubElement(sensor, "type").text = str(self.data.configSensorSelectedType[index])

        ###################################
        #### CONFIGURATION FOR CAMERAS ####
        ###################################
        cameras = xml.SubElement(root, "cameras")
        analog = xml.SubElement(cameras, "analog")
        digital = xml.SubElement(cameras, "digital")

        # ANALOG CAMERAS
        xml.SubElement(analog, "quantity").text = str(self.data.configCameraNumber)
        for index in range(4):
            xml.SubElement(analog, "defaultfeed{}".format(index)).text = str(self.data.configDefaultCameraList[index])

        ###################################
        ## CONFIGURATION FOR KEYBINDINGS ##
        ###################################
        keybindings = xml.SubElement(root, "keybindings")

        # KEYBINDING TO SWITCH ROV CONTROL ORIENTATION
        xml.SubElement(keybindings, "switch_control_direction".format(index)).text = str(self.data.configKeyBindingsList[self.data.configKeyBindings[0]])
        
        # KEYBINDINGS TO ACTUATE EACH ACTUATOR
        for index in range(self.data.configActuatorNumber):
            xml.SubElement(keybindings, "actuator{}".format(index)).text = str(self.data.configKeyBindingsList[self.data.configKeyBindings[index + 1]])

        # SAVE TO XML FILE                                                           
        tree = xml.ElementTree(root)
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
        self.data.fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui, 'Open File','./','XML File (*.xml)')
        if self.data.fileName != '':
            self.ui.configSetup()
        else:
            # SET BACK TO DEFAULT NAME IF USER DOES NOT SELECT A FILE
            self.data.fileName = 'config.xml'

    def openDocumentation(self):
        """
        PURPOSE

        Opens up doxygen html interface to view detailed code documentation

        INPUT

        NONE

        RETURNS

        NONE
        """
        subprocess.call(['Documentation.bat'])

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
        webbrowser.open('https://github.com/AvalonROV')

class DATABASE():
    ###############################
    ######## CONTROL PANEL ########
    ###############################

    # LIST OF AVAILABLE COM PORTS
    comPorts = []
    rovID = 'AVALON'
    rovCOMPort = None
    controllerCOMPort = None
    controlROVCommsStatus = False
    controlControllerCommsStatus = False

    # STORES STATE OF EACH ACTUATOR
    controlActuatorStates = []

    # STORES RECIEVED SENSORS VALUES
    controlSensorValues = []
    # STORES SENSOR LABEL OBJECTS
    controlSensorLabelObjects = []

    # STORES THE SELECTED CAMERA FEEDS
    controlCameraViewList = [None] * 4
    
    # APPEARANGE STYLESHEETS
    greenStyle = 'background-color: #679e37'
    redStyle = 'background-color: #f44336'
    blueStyle = 'background-color: #0D47A1; color: white; font-weight: bold;'
    defaultBlue = 'color: #0D47A1; font-weight: bold;'
    textGreenStyle = 'color: #679e37; font-weight: bold;'
    textDisabledStyle = 'color: rgba(0,0,0,25%);'

    # ROV CONTROL ORIENTATION (TRUE = FORWARD, FALSE = REVERSE)
    controlControlDirection = True

    controlTimerEnabled = False
    controlTimerNew = True
    controlTimerMem = 0

    ###############################
    ######## CONFIGURATION ########
    ###############################

    # DEFAULT CONFIG FILE NAME
    fileName = 'config.xml'

    # STORES OPTIONS TO BE DISPLAYED ON THRUSTER POSITION DROP DOWN MENU
    configThrusterNumber = 8
    configThrusterPositionList = ['None', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    configThrusterPosition = ['None'] * 8
    configThrusterReverse = [False] * 8

    # STORES OPTIONS TO BE DISPLAYED ON SENSOR TYPE DROP DOWN MENU
    configSensorTypeList = ['None','Temperature (°C)','Depth (m)', 'Yaw (°)', 'Pitch (°)', 'Roll (°)']
    # STORES SELECTED SENSOR TYPES
    configSensorSelectedType = []
    # STORES CURRENT NUMBER OF SENSORS
    configSensorNumber = 0

    # STORES USER DEFINED LABELS FOR EACH ACTUATOR (NAME, DEFAULT STATE, ACTUATED STATE)
    configActuatorLabelList = []
    # STORES CURRENT NUMBER OF ACTUATORS
    configActuatorNumber = 0

    # STORES LIST OF AVAILABLE CAMERAS
    configCameraList = []
    # STORES TOTAL NUMBER OF CAMERAS
    configCameraNumber = 0
    # STORES LIST OF DEFAULT CAMERA FEEDS TO BE DIPLAYED ON PROGRAM START
    configDefaultCameraList = [0] * 4

    # STORES LIST OF CONTROLLER KEY BINDINGS FOR THE ACTUATORS
    configKeyBindingsList = ['None','A','B','X','Y','LB','RB','LT','RT','LEFT','RIGHT','UP','DOWN']
    # STORES THE ORDER THAT BUTTONS APPEAR IN THE CONTROLLER RETURN ARRAY
    configControllerButtons = ['A','B','X','Y','LB','RB','None','None','LT','RT']
    # USED FOR DEBOUNCING CONTROLLER BUTTONS
    configControllerButtonReleased = [True] * 10
    # STORES SELECTED BINDINGS
    configKeyBindings = []

    # STORES CONTROLLER LABEL OBJECTS
    configControllerLabelObjects = []

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
    app.setFont(QtGui.QFont("Bahnschrift Light", 10))
    app.setStyle("Fusion")
    UI()
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()