from PyQt5 import QtWidgets, QtGui, QtCore, uic

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread

from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog,
QDialogButtonBox, QRadioButton, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
QLabel, QLineEdit, QMenu, QMenuBar, QPushButton, QSpinBox, QTextEdit,
QVBoxLayout)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QObject, pyqtSignal

import sys
import cv2
import serial

# SAMS SERIAL LIBRARY
from rov_serial import ROV_SERIAL as rovSerial

class UI(QtWidgets.QMainWindow):
    # INITIAL SETUP
    def __init__(self):
        super(UI,self).__init__()
        # LOAD UI FILE
        uic.loadUi('gui.ui',self)

        # CREATING OBJECTS AND PASSING OBJECTS TO THEM
        self.data = DATABASE()
        self.control = CONTROL_PANEL(self, self.data)
        self.config = CONFIG(self, self.data, self.control)
        self.test = FUNCTION_TEST(self, self.data)
        
        # FIND SCREEN SIZE
        self.sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)
        self.data.screenHeight = self.sizeObject.height()
        self.data.screenWidth = self.sizeObject.width()

        # SET DEFAULT WIDGET SIZES
        self.con_panel_functions_widget.resize(self.data.screenWidth/6,self.con_panel_functions_widget.height())
        self.func_testing_functions_widget.resize(self.data.screenWidth/6,self.con_panel_functions_widget.height())

        # ADD AVALON LOGO
        pixmap = QPixmap("logo.png")
        pixmap = pixmap.scaledToWidth(250)
        self.avalon_logo.setPixmap(pixmap)

        # LINK GUI BUTTONS TO METHODS
        self.linkControlPanelWidgets()
        self.linkConfigWidgets()
        self.linkFunctionTestWidgets()

        # INITIATE CAMERA FEEDS
        self.initiateCameraFeed()

        # INITIALISE UI
        self.showMaximized()

    @pyqtSlot(QImage)
    def updateCamera1Feed(self, frame):
        # DISPLAY NEW FRAME ON CAMERA FEED
        self.primary_camera.setPixmap(QPixmap.fromImage(frame))

    @pyqtSlot(QImage)
    def updateCamera2Feed(self, frame):
        # DISPLAY NEW FRAME ON CAMERA FEED
        self.secondary_camera_1.setPixmap(QPixmap.fromImage(frame))

    def initiateCameraFeed(self):
        # INITIATE CAMERAS IN SEPERATE THREADS
        # PRIMARY CAMERA
        camThread1 = CAMERA_FEED_1(self)
        camThread1.cameraNewFrame.connect(self.updateCamera1Feed)
        camThread1.start()
        # SECONDARY CAMERA 1
        camThread2 = CAMERA_FEED_2(self)
        camThread2.cameraNewFrame.connect(self.updateCamera2Feed)
        camThread2.start()

    def linkControlPanelWidgets(self):
        self.rov_connect.clicked.connect(rovSerial.rovConnect)
        self.controller_connect.clicked.connect(rovSerial.controllerConnect)

    def linkConfigWidgets(self):
        self.config_sensors_number.editingFinished.connect(self.config.configSetSensorsNumber)
        self.config_cameras_number.editingFinished.connect(self.config.configSetCamerasNumber)
        self.config_actuators_number.editingFinished.connect(self.config.configSetActuatorsNumber)

        # LINK EACH DEFAULT CAMERA DROP DOWN MANU TO THE SAME SLOT, PASSING THE CAMERA ID AS 1,2,3,4 ETC.
        self.config_primary_camera_list.activated.connect(lambda index, camera = 0: self.config.configChangeDefaultCameras(index, camera))
        self.config_secondary1_camera_list.activated.connect(lambda index, camera = 1: self.config.configChangeDefaultCameras(index, camera))
        self.config_secondary2_camera_list.activated.connect(lambda index, camera = 2: self.config.configChangeDefaultCameras(index, camera))
        self.config_secondary3_camera_list.activated.connect(lambda index, camera = 3: self.config.configChangeDefaultCameras(index, camera))

    def linkFunctionTestWidgets(self):
        pass

class CAMERA_FEED_1(QThread):
    # CREATE SIGNAL
    cameraNewFrame = pyqtSignal(QImage)

    # URL of camera stream
    channel = 0    
    
    def run(self):
        # INITIATE PRIMARY CAMERA
        cameraFeed = cv2.VideoCapture(self.channel)
        
        while True:
            # CAPTURE FRAME
            ret1, frame = cameraFeed.read()
            # IF FRAME IS SUCCESSFULLY CAPTURED            
            if ret1:
                # CONVERT TO RGB COLOUR
                cameraFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # GET FRAME DIMENSIONS AND NUMBER OF COLOUR CHANNELS
                height, width, _ = cameraFrame.shape
                # CONVERT TO QIMAGE
                cameraFrame = QtGui.QImage(cameraFrame.data, width, height, cameraFrame.strides[0], QtGui.QImage.Format_RGB888)
                # SET SIZE
                cameraFrame = cameraFrame.scaled(1280, 720, QtCore.Qt.KeepAspectRatio)
                # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                self.cameraNewFrame.emit(cameraFrame)

class CAMERA_FEED_2(QThread):
    # CREATE SIGNAL
    cameraNewFrame = pyqtSignal(QImage)

    # URL of camera stream
    channel = 'rtsp://192.168.0.103/user=admin&password=&channel=1&stream=0.sdp?'    
    
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
                cameraFrame = cameraFrame.scaled(1280, 720, QtCore.Qt.KeepAspectRatio)
                # EMIT SIGNAL CONTAINING NEW FRAME TO SLOT
                self.cameraNewFrame.emit(cameraFrame)

class CONTROL_PANEL():
    # CONSTUCTOR
    def __init__(self, Object1, Object2):
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2

    def controlToggleActuator(self, _, actuator, buttonObject):
        print('Actuator {} Toggled'.format(actuator + 1))

        if self.data.controlActuatorStates[actuator] == False:
            buttonObject.setText(self.data.configActuatorLabelList[actuator][2])
            buttonObject.setStyleSheet(self.data.actuatedStyle)
            self.data.controlActuatorStates[actuator] = True

        elif self.data.controlActuatorStates[actuator] == True:
            buttonObject.setText(self.data.configActuatorLabelList[actuator][1])
            buttonObject.setStyleSheet(self.data.defaultStyle)
            self.data.controlActuatorStates[actuator] = False

class CONFIG():
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3):
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2
        self.control = Object3

    def configSetActuatorsNumber(self):
        oldNumber = self.data.configActuatorNumber
        newNumber = self.ui.config_actuators_number.value()
        self.data.configActuatorNumber = newNumber

        # ADD ACTUATORS IF NEW NUMBER IS HIGHER
        if newNumber > oldNumber:
            # CALCULATE NUMBER OF ACTUATORS TO ADD ON TOP OF CURRENT NUMBER
            delta = newNumber - oldNumber
            for number in range(delta):
                # CREATE 2-DIMENSIONAL ARRAY TO STORE NAME, DEFAULT AND ACTUATED LABELS
                self.data.configActuatorLabelList.append([])
                self.data.configActuatorLabelList[oldNumber + number].append('Actuator {}'.format(oldNumber + number + 1))
                self.data.configActuatorLabelList[oldNumber + number].append('OFF')
                self.data.configActuatorLabelList[oldNumber + number].append('ON')

                # CREATE ARRAY TO STORE ACTUATOR STATES
                self.data.controlActuatorStates.append(False)

                # CREATE ACTUATOR NAME AND STATE NAME TEXT FIELDS
                actuatorLabel = QLineEdit()
                state1 = QLineEdit()
                state2 = QLineEdit()
                
                # CREATE ACTUATOR CONTROL BUTTON ON CONTROL PANEL
                actuatorToggle = QPushButton('Default State')
                actuatorToggle.setFixedHeight(50)
                # CREATE ACTUATOR LABEL ON CONTROL PANEL
                actuatorName = QLabel(self.data.configActuatorLabelList[oldNumber + number][0])
                actuatorName.setFixedHeight(50)
                
                # CREATE FORM LAYOUT
                layout = QGridLayout()
                layout.addWidget(QLabel('Actuator Name'),0,0)
                layout.addWidget(actuatorLabel,0,1)
                layout.addWidget(QLabel('Default State'),1,0)
                layout.addWidget(state1,1,1)
                layout.addWidget(QLabel('Actuated State'),2,0)
                layout.addWidget(state2,2,1)

                

                # SET DEFAULT STYLE SHEET
                actuatorToggle.setStyleSheet(self.data.defaultStyle)

                # ADD TO CONFIG TAB
                self.ui.config_actuator_form.addRow(QLabel("Actuator {}".format((oldNumber + number + 1))), layout)
                # ADD TO CONTROL PANEL TAB
                self.ui.control_panel_actuators.addRow(actuatorName, actuatorToggle)
                # LINK CONFIG ACTUATOR TEXT FIELDS TO SLOT - PASS ACTUATOR NUMBER AND WHICH TEXT FIELD HAS BEEN EDITED
                actuatorLabel.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 0, controlObject = actuatorName: self.configChangeActuatorType(text, actuator, label, controlObject))
                state1.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 1, controlObject = actuatorToggle: self.configChangeActuatorType(text, actuator, label, controlObject))
                state2.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 2, controlObject = actuatorToggle: self.configChangeActuatorType(text, actuator, label, controlObject))
                # LINK CONTROL PANEL ACTUATOR BUTTONS TO SLOT - PASS ACTUATOR NUMBER
                actuatorToggle.clicked.connect(lambda _, actuator = (oldNumber + number), buttonObject = actuatorToggle: self.control.controlToggleActuator(_, actuator, buttonObject))

        # REMOVE ACTUATORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF ACTUATORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                # REMOVE ACTUATORS FROM CONFIG TAB
                self.ui.config_actuator_form.removeRow(oldNumber - number) 
                # REMOVE ACTUATORS FROM CONTROL PANEL TAB
                self.ui.control_panel_actuators.removeRow(oldNumber - number - 1)

    def configChangeActuatorType(self, text, actuator, label, controlObject):
        # STORE NEW LABEL
        self.data.configActuatorLabelList[actuator][label] = text

        # IF NAME IS CHANGED
        if label == 0:
            print("Name of actuator {} changed to {}".format(actuator, text))
            controlObject.setText(text)

        # IF DEFAULT STATE IS CHANGED
        if label == 1:
            print("Default state of actuator {} changed to {}".format(actuator, text))

        # IF ACTUATED STATE IS CHANGED   
        if label == 2:
            print("Actuated state of actuator {} changed to {}".format(actuator, text))

    def configSetSensorsNumber(self):
        oldNumber = self.data.configSensorNumber
        newNumber = self.ui.config_sensors_number.value()
        self.data.configSensorNumber = newNumber

        # ADD SENSORS IF NEW NUMBER IS HIGHER
        if newNumber > oldNumber:
            # CALCULATE NUMBER OF SENSORS TO ADD ON TOP OF CURRENT NUMBER
            delta = newNumber - oldNumber
            for number in range(delta):
                # CREATE SENSOR TYPE DROP DOWN MENU AND ADD ITEMS
                sensorType = QComboBox()
                sensorType.addItems(self.data.configSensorTypeList)
                # CREATE SENSOR READINGS TEXT BOX
                sensorView = QLineEdit()
                sensorView.setReadOnly(True)
                # CREATE SENSOR LABEL
                sensorLabel = QLabel('Sensor {}'.format(oldNumber + number + 1))
                # CREATE FORM LAYOUT
                layout = QFormLayout()
                layout.addRow(QLabel("Type"), sensorType)
                # ADD TO CONFIG TAB
                self.ui.config_sensor_form.addRow(QLabel("Sensor {}".format((oldNumber + number + 1))), layout)
                # ADD TO CONTROL PANEL TAB
                self.ui.control_panel_sensors.addRow(sensorLabel, sensorView)
                # LINK DROP DOWN MENU TO SLOT - PASS SENSOR NUMBER AND MENU INDEX SELECTED
                sensorType.activated.connect(lambda index, sensor = (oldNumber + number + 1), sensorSelected = sensorLabel,: self.configChangeSensorType(index, sensor, sensorSelected))

        # REMOVE SENSORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF SENSORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                # REMOVE SENSORS FROM CONFIG TAB
                self.ui.config_sensor_form.removeRow(oldNumber - number + 1) 
                # REMOVE SENSORS FROM CONTROL PANEL TAB
                self.ui.control_panel_sensors.removeRow(oldNumber - number - 1) 
                      
    def configChangeSensorType(self, index, sensor, sensorLabel):
        # SENSOR VARIABLE REPRESENTS WHICH SENSOR IS BEING MODIFIED
        # INDEX VARIABLE REPRESENTS THE MENU INDEX SELECTED
        print('Sensor {} changed to {}'.format(sensor, self.data.configSensorTypeList[index]))
        sensorLabel.setText(self.data.configSensorTypeList[index])

    def configSetCamerasNumber(self):
        newNumber = self.ui.config_cameras_number.value()
        self.data.configCameraNumber = newNumber
        # ERASE LIST
        del self.data.configCameraList[:]

        # CLEAR MENU OPTIONS
        self.ui.control_primary_camera_list.clear()
        self.ui.control_secondary1_camera_list.clear()
        self.ui.control_secondary2_camera_list.clear()
        self.ui.control_secondary3_camera_list.clear()
        self.ui.config_primary_camera_list.clear()
        self.ui.config_secondary1_camera_list.clear()
        self.ui.config_secondary2_camera_list.clear()
        self.ui.config_secondary3_camera_list.clear()
        self.ui.test_camera_list.clear()
        
        self.data.configCameraList.append('None')
        # ADD CAMERAS TO LIST
        for number in range(self.data.configCameraNumber):
            self.data.configCameraList.append('Camera {}'.format(number + 1))

        # ADD LIST TO EACH DROP DOWN MENU
        # CONTROL PANEL
        self.ui.control_primary_camera_list.addItems(self.data.configCameraList)
        self.ui.control_secondary1_camera_list.addItems(self.data.configCameraList)
        self.ui.control_secondary2_camera_list.addItems(self.data.configCameraList)
        self.ui.control_secondary3_camera_list.addItems(self.data.configCameraList)

        # CONFIGURATION
        self.ui.config_primary_camera_list.addItems(self.data.configCameraList)
        self.ui.config_secondary1_camera_list.addItems(self.data.configCameraList)
        self.ui.config_secondary2_camera_list.addItems(self.data.configCameraList)
        self.ui.config_secondary3_camera_list.addItems(self.data.configCameraList)

        # FUNCTION TESTING
        self.ui.test_camera_list.addItems(self.data.configCameraList)
        
    def configChangeDefaultCameras(self, index, camera):
        # CAMERA VARIABLE REPRESENTS WHICH CAMERA FEED IS BEING MODIFIED (1,2,3,4)
        # INDEX VARIABLE REPRESENTS THE MENU INDEX SELECTED
        print('Camera feed {} has been changed to camera {}'.format(camera+1, index))
        self.data.configDefaultCameraList[camera] = index        

class FUNCTION_TEST():
    # CONSTUCTOR
    def __init__(self, Object1, Object2):
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2

class DATABASE():
    ###############################
    ######## CONTROL PANEL ########
    ###############################

    # STORES STATE OF EACH ACTUATOR
    controlActuatorStates = []
    # ACTUATOR STLYE SHEET FOR DEFAULT STATE
    defaultStyle = "background-color: #679e37"
    # ACTUATOR STLYE SHEET FOR ACTUATED STATE
    actuatedStyle = "background-color: #e53935"

    ###############################
    ######## CONFIGURATION ########
    ###############################

    # STORES OPTIONS TO BE DISPLAYED ON SENSOR TYPE DROP DOWN MENU
    configSensorTypeList = ['None','Temperature (°C)','Depth (m)', 'Yaw (°)', 'Pitch (°)', 'Roll (°)']
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
    configDefaultCameraList = [None] * 4


    ###############################
    ######## FUNCTION TEST ########
    ###############################


    ###############################
    ############ OTHER ############
    ###############################

    screenHeight = 0
    screenWidth = 0

def guiInitiate(): 
    """
    ### Input:
    """
    # CREATE QAPPLICATION INSTANCE (PASS SYS.ARGV TO ALLOW COMMAND LINE ARGUMENTS)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    UI()
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()