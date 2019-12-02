#########################
######## IMPORTS ########
#########################

# PYQT5 MODULES FOR GUI
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QComboBox, QRadioButton, QFormLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, QFileDialog
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QImage, QFont

# ADDITIONAL MODULES
import sys
from threading import Thread, Timer
from datetime import datetime
from cv2 import VideoCapture, resize, cvtColor, COLOR_BGR2RGB, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_DSHOW
from xml.etree.ElementTree import parse, Element, SubElement, ElementTree
import pygame
from subprocess import call
from webbrowser import open
import serial

# SERIAL LIBRARY
from avalonComms import ROV
from avalonComms import controller as CONTROLLER

class UI(QMainWindow):
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
        self.data.sizeObject = QDesktopWidget().screenGeometry(-1)
        self.data.screenHeight = self.data.sizeObject.height()
        self.data.screenWidth = self.data.sizeObject.width()

        # SET DEFAULT WIDGET SIZES
        self.con_panel_functions_widget.resize(self.data.screenWidth/6,self.con_panel_functions_widget.height())

        # ADD AVALON LOGO
        avalonPixmap = QPixmap('logo.png')
        avalonPixmap = avalonPixmap.scaledToWidth(250)
        self.avalon_logo.setPixmap(avalonPixmap)

        # SET CAMERA FEED PLACE HOLDER
        cameraPixmap = QPixmap('no_signal.png')
        primaryCameraPixmap = cameraPixmap.scaledToHeight(self.primary_camera.size().height()*0.98)
        secondary1CameraPixmap = primaryCameraPixmap.scaledToHeight(self.secondary_camera_1.size().height()*0.98)
        secondary2CameraPixmap = primaryCameraPixmap.scaledToHeight(self.secondary_camera_2.size().height()*0.98)
        self.primary_camera.setPixmap(primaryCameraPixmap)
        self.secondary_camera_1.setPixmap(secondary1CameraPixmap)
        self.secondary_camera_2.setPixmap(secondary2CameraPixmap)

        # LINK GUI BUTTONS TO METHODS
        self.linkToolbarWidgets()
        self.linkControlPanelWidgets()
        self.linkConfigWidgets()

        # INITIATE CAMERA FEEDS
        self.initiateCameraFeed()

        # SEND OUT ID REQUEST TO EACH COM PORT TO AUTOMATICALLY FIND ROV
        self.data.comPorts = self.rov.findROVs(self.data.rovID)

        # LOAD SETTINGS FROM CONFIG FILE
        self.configSetup()

        # RESIZE CAMERA FEEDS WHEN WINDOW IS RESIZED
        self.resizeEvent(QResizeEvent(self.size(), QSize()))

        # INITIALISE UI
        self.showMaximized()

    def resizeEvent(self, event):
        self.data.windowSizeObject = self.size()
        self.data.windowHeight = self.data.windowSizeObject.height()
        self.data.windowWidth = self.data.windowSizeObject.width()

        cameraPixmap = QPixmap('no_signal.png')
        primaryCameraPixmap = cameraPixmap.scaledToHeight(self.primary_camera.size().height()*0.98)
        secondary1CameraPixmap = primaryCameraPixmap.scaledToHeight(self.secondary_camera_1.size().height()*0.98)
        secondary2CameraPixmap = primaryCameraPixmap.scaledToHeight(self.secondary_camera_2.size().height()*0.98)
        self.primary_camera.setPixmap(primaryCameraPixmap)
        self.secondary_camera_1.setPixmap(secondary1CameraPixmap)
        self.secondary_camera_2.setPixmap(secondary2CameraPixmap)

        QMainWindow.resizeEvent(self, event)
    
    def readConfigFile(self, fileName, 
                        thrusterPosition, 
                        thrusterReverse, 
                        actuatorLabelList, 
                        sensorSelectedType, 
                        defaultCameraList, 
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
            print('Configuration file not found')
            configFileStatus = False

        # IF CONFIGURATION FILE IS FOUND
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
                            pass

                ##############################
                ## READ KEYBINDING SETTINGS ##
                ##############################
                if child.tag == 'keybindings':
                    for control in child:
                        keyBindings.append(self.data.configKeyBindingsList.index(control.text))     

            #############################
            ######## RETURN DATA ########
            #############################

            return (thrusterPosition,
                    thrusterReverse, 
                    actuatorLabelList,
                    sensorSelectedType,
                    defaultCameraList,
                    keyBindings)

    def configSetup(self):
        """
        PURPOSE

        Calls functino to read the configuration file and configures the programs thruster, actuator, sensor, camera and controller settings.
        If no configuration file is found, the program will open with default settings. 

        INPUT

        NONE

        RETURNS

        NONE
        """
        # GET CONFIGURATION SETTINGS FROM CONFIG FILE
        
        (self.data.configThrusterPosition,
            self.data.configThrusterReverse, 
            self.data.configActuatorLabelList,
            self.data.configSensorSelectedType,
            self.data.configDefaultCameraList,
            self.data.configKeyBindings) = self.readConfigFile(self.data.fileName, 
                                                                self.data.configThrusterPosition,
                                                                self.data.configThrusterReverse, 
                                                                self.data.configActuatorLabelList,
                                                                self.data.configSensorSelectedType,
                                                                self.data.configDefaultCameraList,
                                                                self.data.configKeyBindings)       
        
        # APPLY SETTINGS TO GUI 

        # ADD KEYBINDING FOR SWITCHING CONTROL ORIENTATION
        self.config.addKeyBinding("Switch Orientation", 0, True)
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
        self.config.setCamerasNumber(True)                        

    def resetConfig(self, resetStatus):
        """
        PURPOSE

        Resets the program to default settings (nothing configured).
        
        INPUT

        - resetStatus = true when called via the 'Reset Configuration' (so that number of thruster automatically resets).

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
        self.control_switch_direction.setIcon(QIcon('graphics/switch_direction.png'))
        self.control_switch_direction.clicked.connect(self.control.switchControlDirection)
        self.control_switch_direction.setFixedHeight(self.control_switch_direction.geometry().height() * 1.5)
        self.control_switch_direction_forward.setStyleSheet(self.data.textGreenStyle)
        self.control_switch_direction_reverse.setStyleSheet(self.data.textDisabledStyle)
        self.control_switch_direction.setIconSize(QSize(50,50))
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
        self.config.setThrustersNumber(self.data.configThrusterNumber, 
                                        self.config_thruster_form,
                                        self.data.configThrusterPosition,
                                        self.data.configThrusterPositionList,
                                        self.data.configThrusterReverse)

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
        pixmap = QPixmap.fromImage(frame)
        pixmap = pixmap.scaledToHeight(self.primary_camera.size().height()*0.98)
        self.primary_camera.setPixmap(pixmap)

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
        pixmap = QPixmap.fromImage(frame)
        pixmap = pixmap.scaledToHeight(self.secondary_camera_1.size().height()*0.98)
        self.secondary_camera_1.setPixmap(pixmap)

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
        pixmap = QPixmap.fromImage(frame)
        pixmap = pixmap.scaledToHeight(self.secondary_camera_2.size().height()*0.98)
        self.secondary_camera_2.setPixmap(pixmap)

class CAMERA_FEED_1(QThread):
    # CREATE SIGNAL
    cameraNewFrame = pyqtSignal(QImage)

    # URL of camera stream
    channel = 0
    
    def run(self):
        # INITIATE SECONDARY 1 CAMERA
        cameraFeed = VideoCapture(self.channel, CAP_DSHOW)
        cameraFeed.set(CAP_PROP_FRAME_WIDTH, 1920)
        cameraFeed.set(CAP_PROP_FRAME_HEIGHT, 1080)
        
        while True:
            # CAPTURE FRAME
            ret, frame = cameraFeed.read()
            # IF FRAME IS SUCCESSFULLY CAPTURED            
            if ret:
                
                # CONVERT TO RGB COLOUR
                cameraFrame = cvtColor(frame, COLOR_BGR2RGB)
                # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
                height, width, _ = cameraFrame.shape
                # CONVERT TO QIMAGE
                cameraFrame = QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QImage.Format_RGB888)
                # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                self.cameraNewFrame.emit(cameraFrame)
                QThread.msleep(40)
            
            else:
                self.cameraNewFrame.emit(QImage("no_signal.png"))

class CAMERA_FEED_2(QThread):
    # CREATE SIGNAL
    cameraNewFrame = pyqtSignal(QImage)

    # URL of camera stream
    channel = 1
    
    def run(self):
        # INITIATE SECONDARY 1 CAMERA
        cameraFeed = VideoCapture(self.channel, CAP_DSHOW)
        cameraFeed.set(CAP_PROP_FRAME_WIDTH, 1920)
        cameraFeed.set(CAP_PROP_FRAME_HEIGHT, 1080)
        
        while True:
            # CAPTURE FRAME
            ret, frame = cameraFeed.read()
            # IF FRAME IS SUCCESSFULLY CAPTURED            
            if ret:
                # CONVERT TO RGB COLOUR
                cameraFrame = cvtColor(frame, COLOR_BGR2RGB)
                # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
                height, width, _ = cameraFrame.shape
                # CONVERT TO QIMAGE
                cameraFrame = QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QImage.Format_RGB888)
                # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                self.cameraNewFrame.emit(cameraFrame)
                QThread.msleep(40)
            
            else:
                self.cameraNewFrame.emit(QImage("no_signal.png"))

class CAMERA_FEED_3(QThread):
    # CREATE SIGNAL
    cameraNewFrame = pyqtSignal(QImage)

    # URL of camera stream
    channel = 2 
    
    def run(self):
        # INITIATE SECONDARY 1 CAMERA
        cameraFeed = VideoCapture(self.channel)
        cameraFeed.set(CAP_PROP_FRAME_WIDTH, 1920)
        cameraFeed.set(CAP_PROP_FRAME_HEIGHT, 1080)
        
        while True:
            # CAPTURE FRAME
            ret, frame = cameraFeed.read()
            # IF FRAME IS SUCCESSFULLY CAPTURED            
            if ret:
                # CONVERT TO RGB COLOUR
                cameraFrame = cvtColor(frame, COLOR_BGR2RGB)
                # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
                height, width, _ = cameraFrame.shape
                # CONVERT TO QIMAGE
                cameraFrame = QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QImage.Format_RGB888)
                # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                self.cameraNewFrame.emit(cameraFrame)

            else:
                self.cameraNewFrame.emit(QImage("no_signal.png"))

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

        Initialises communication with the XBOX controller.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if self.data.controlControllerCommsStatus == False:
            # UPDATE BUTTON STYLE
            self.data.controlControllerCommsStatus = True
            self.ui.control_controller_connect.setText('DISCONNECT')
            self.ui.control_controller_connect.setStyleSheet(self.data.blueStyle)
            # INITIATE COMMUNICATION WITH THE CONTROLLER
            self.controller.initialiseConnection(self.data.controllerCOMPort)
            (connectionStatus, controllerNumber) = self.initiateController()
            
            if connectionStatus == True:
                # READ CONTROLLER INPUTS IN A TIMED THREAD
                self.controllerEventLoop(controllerNumber)
            else:
                self.controllerConnect()
        else:
            self.data.controlControllerCommsStatus = False
            self.ui.control_controller_connect.setText('CONNECT')
            self.ui.control_controller_connect.setStyleSheet(self.data.defaultBlue)  

    def initiateController(self):
        """
        PURPOSE

        Initiates the PyGame library and any connected controllers.

        INPUT

        NONE

        RETURNS

        - connectionStatus = true if the correct controller is found.
        - controllerNumber = index of the connected controller from the list of available controllers.
        """

        connectionStatus = False
        controllerNumber = 0

        # INITIALISE PYGAME MODULE
        pygame.init()

        # INITIALISE JOYSICKS
        pygame.joystick.init()

        # GET NUMBER OF JOYSTICKS CONNECTED
        joystick_count = pygame.joystick.get_count()

        # THROW ERROR IS NO CONTROLLERS ARE DETECTED
        if joystick_count < 1:
            print('No Controllers Found...')
            connectionStatus = False
            pygame.quit()

        else:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                # GET NAME OF CONTROLLER/JOYSTICK FROM OS
                name = joystick.get_name()
            
                # ONLY ACCEPT XBOX ONE CONTROLLER
                if name == 'Controller (Xbox One For Windows)':
                    connectionStatus = True
                    controllerNumber = i
                    print('Connected to controller')

        return connectionStatus, controllerNumber

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

        # STORE BUTTON STATES IN DATABASE FOR ACCESS BY OTHER FUNCTIONS
        self.data.configButtonStates = buttonStates

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
        
    def controllerEventLoop(self, controllerNumber):
        """
        PURPOSE

        - Initiates a seperate thread that continuously requests the controller joystick and button states.
        - Passes button states and joystick values to processing functions.

        INPUT

        - controllerNumber = index of the connected controller from the list of available controllers.

        RETURNS

        NONE
        """
        # TAKE SINGLE READING OF CONTROLLER VALUES
        buttonStates, joystickValues = self.getControllerInputs(self.data.controlControllerCommsStatus, controllerNumber)

        # PROCESS BUTTON STATES
        self.processButtons(buttonStates)
        
        # PROCESS JOYSTICK VALUES
        filteredJoystickValues = self.processJoysticks(joystickValues)

        # UPDATE GUI
        self.updateControllerValuesDisplay(buttonStates, filteredJoystickValues)

        # UPDATE CONTROLLER INPUTS AT A RATE OF 30FPS TO REDUCE CPU USAGE
        thread = Timer(1/60,lambda controllerNumber = controllerNumber: self.controllerEventLoop(controllerNumber))
        thread.daemon = True                            
        thread.start()

    def getControllerInputs(self, connectionStatus, controllerNumber):
        """
        PURPOSE

        Gets a single readings of all the button and joystick values from the controller.

        INPUT

        - connectionStatus = False to disconnect the controller and close the thread.
        - controllerNumber = index of the connected controller from the list of available controllers.

        RETURNS

        - buttonStates = an array containing the states of all the controller buttons (0 or 1).
        - joystickValues = an array containing the values of all the joysticks (-1 -> 1).
        """
        # STORES THE STATE OF EACH BUTTON
        buttonStates = []
        # STORES THE VALUES OF EACH JOYSTICK
        joystickValues = []

        if connectionStatus == True:
            # EVENT PROCESSING STEP
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
            
            # GET NUMBER OF JOYSTICKS CONNECTED
            joystick_count = pygame.joystick.get_count()

            # INITIATE CONNECTED CONTROLLER
            joystick = pygame.joystick.Joystick(controllerNumber)
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
        if connectionStatus == False:
            print('Controller Disconnected')
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
        thread = Timer(0.5, self.getSensorReadings)
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
            self.startTime = datetime.now()
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
            thrusterLocation.activated.connect(lambda index, thruster = thruster, setting = 0, controlObject = None: self.setROVThrusterSettings(index, thruster, setting, controlObject))
            thrusterReverseCheck.toggled.connect(lambda index, thruster = thruster, setting = 1, controlObject = thrusterReverse: self.setROVThrusterSettings(index, thruster, setting, controlObject))
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
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # CREATE TEXT BOX TO DISPLAY VALUE
            value = QLineEdit()
            value.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
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
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # CREATE TEXT BOX TO DISPLAY VALUE
            value = QLineEdit()
            value.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
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
        keybindingLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        print(self.data.configKeyBindings)

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
            buttonObject.setStyleSheet(self.data.blueStyle)
            # INITIATE SEARCH FOR PRESSED BUTTON
            self.findKeyBinding(index, buttonObject, menuObject)
        
        else:
            # SET KEY BINDING
            self.setKeyBindings(binding + 1, index)
            menuObject.setCurrentIndex(binding + 1)
            # REVERT BUTTON STYLE
            buttonObject.setStyleSheet('')

    def findKeyBinding(self, index, buttonObject, menuObject):
        """
        PURPOSE

        Looks at the button states in a seperate thread and detects which button has been pressed on the controller.

        INPUT

        - index = which key binding is being changed.
        - buttonObject = pointer to the auto binding button widget.
        - menuObject = pointer to the key bindings menu widget.
        
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
        
        # FIND BUTTON CHANGES AT A RATE OF 60FPS TO REDUCE CPU USAGE
        thread = Timer(1/60, lambda index = index, buttonObject = buttonObject, menuObject = menuObject: self.findKeyBinding(index, buttonObject, menuObject))
        thread.daemon = True                            
        thread.start()

    def setKeyBindings(self, binding, index):
        """
        PURPOSE

        Sets the keybinding for a specific control on the ROV. 
        The keybinding can be selected from a menu, or detected by pressing a button on the controller.

        INPUT
         
        binding = menu index selected.
        index = the ROV control having its key binding changed.

        RETURNS 

        NONE
        """
        self.data.configKeyBindings[index] = binding

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

        Saves the current program configuration.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        # WRITE CURRENT PROGRAM CONFIGURATION TO XML FILE.
        self.writeConfig(self.data.configThrusterPosition,
                            self.data.configThrusterReverse, 
                            self.data.configActuatorLabelList,
                            self.data.configActuatorNumber,
                            self.data.configSensorSelectedType,
                            self.data.configSensorNumber,
                            self.data.configDefaultCameraList,
                            self.data.configCameraNumber,
                            self.data.configKeyBindings,
                            self.data.configKeyBindingsList)

        print('Program Settings Saved')

    def writeConfig(self, thrusterPosition, 
                        thrusterReverse, 
                        actuatorLabelList,
                        actuatorNumber, 
                        sensorSelectedType,
                        sensorNumber, 
                        defaultCameraList,
                        cameraNumber,
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

        ###################################
        ### CONFIGURATION FOR THRUSTERS ###
        ###################################
        thrusters = SubElement(root, "thrusters")
        for index in range(8):
            thruster = SubElement(thrusters, "thruster{}".format(index))
            SubElement(thruster, "location").text = thrusterPosition[index]
            SubElement(thruster, "reversed").text = thrusterReverse[index]
        
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

        ###################################
        ## CONFIGURATION FOR KEYBINDINGS ##
        ###################################
        keybindings = SubElement(root, "keybindings")

        # KEYBINDING TO SWITCH ROV CONTROL ORIENTATION
        SubElement(keybindings, "switch_control_direction".format(index)).text = str(keyBindingsList[keyBindings[0]])
        
        # KEYBINDINGS TO ACTUATE EACH ACTUATOR
        for index in range(actuatorNumber):
            SubElement(keybindings, "actuator{}".format(index)).text = str(keyBindingsList[keyBindings[index + 1]])

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
        call(['Documentation.bat'])

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
    # STORES CONTROLLER BUTTON STATES
    configButtonStates = []

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
    app.setFont(QFont("Bahnschrift Light", 10))
    app.setStyle("Fusion")
    UI()
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()