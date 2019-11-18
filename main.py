from PyQt5 import QtWidgets, QtGui, QtCore, uic

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, QTimer

from PyQt5.QtWidgets import QApplication, QComboBox, QRadioButton, QFormLayout, QGridLayout, QLabel, QLineEdit, QPushButton

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QObject, pyqtSignal

import threading
import time
import datetime
import sys
import cv2
import serial
import xml.etree.ElementTree as xml
import numpy

# SAMS SERIAL LIBRARY
from avalonComms import ROV
from avalonComms import controller as CONTROLLER

class UI(QtWidgets.QMainWindow):
    # INITIAL SETUP
    def __init__(self):
        super(UI,self).__init__()
        # LOAD UI FILE
        uic.loadUi('gui.ui',self)

        # CREATING OBJECTS AND PASSING OBJECTS TO THEM
        self.data = DATABASE()
        self.rov = ROV()
        self.controller = CONTROLLER()
        self.control = CONTROL_PANEL(self, self.data, self.rov, self.controller)
        self.config = CONFIG(self, self.data, self.control, self.rov, self.controller)
        
        # FIND SCREEN SIZE
        self.sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)
        self.data.screenHeight = self.sizeObject.height()
        self.data.screenWidth = self.sizeObject.width()

        # SET DEFAULT WIDGET SIZES
        self.con_panel_functions_widget.resize(self.data.screenWidth/6,self.con_panel_functions_widget.height())

        # ADD AVALON LOGO
        pixmap = QPixmap("logo.png")
        pixmap = pixmap.scaledToWidth(250)
        self.avalon_logo.setPixmap(pixmap)

        # LINK GUI BUTTONS TO METHODS
        self.linkControlPanelWidgets()
        self.linkConfigWidgets()

        # INITIATE CAMERA FEEDS
        self.initiateCameraFeed()

        # SEND OUT ID REQUEST TO EACH COM PORT TO AUTOMATICALLY FIND ROV
        self.data.comPorts = self.rov.findROVs(self.data.rovID)

        # LOAD SETTING FROM CONFIG FILE
        self.configSetup()

        # INITIALISE UI
        self.showMaximized()

    def configSetup(self):
        try:
            configFile = xml.parse(self.data.fileName)
            configFileStatus = True
        except:
            print('Configuration file not found')
            configFileStatus = False

        if configFileStatus == True:
            # FACTORY RESET GUI CONFIGURATION
            self.resetConfig()

            root = configFile.getroot()

            for child in root:
                ##############################
                ### READ THRUSTER SETTINGS ###
                ##############################
                if child.tag == 'thrusters':
                    for index, thruster in enumerate(child):
                        self.data.configThrusterPosition[index] = thruster.find("location").text
                        self.data.configThrusterReverse[index] = True if thruster.find("reversed").text == 'True' else False
                        self.config.setROVThrusterSettings(None, index, 3)
                        
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
                            
                    # UPDATE GUI WITH ACTUATOR DATA
                    self.config.setActuatorsNumber(True)

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
                    
                    # UPDATE GUI WITH SENSOR DATA
                    self.config.setSensorsNumber(True)

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
                                    self.data.configDefaultCameraList.append(int(camera.text))

                        # UPDATE GUI WITH ANALOG CAMERA DATA
                        self.config.setCamerasNumber(True)

                        # DIGITAL CAMERAS
                        if cameraType.tag == 'digital':
                            pass

    def resetConfig(self):
        ### RESET THRUSTER SETTINGS ###
        self.config_thruster1_position.setCurrentIndex(0)
        self.config_thruster2_position.setCurrentIndex(0)
        self.config_thruster3_position.setCurrentIndex(0)
        self.config_thruster4_position.setCurrentIndex(0)
        self.config_thruster5_position.setCurrentIndex(0)
        self.config_thruster6_position.setCurrentIndex(0)
        self.config_thruster7_position.setCurrentIndex(0)
        self.config_thruster8_position.setCurrentIndex(0)
        self.config_thruster1_reverse.setChecked(False)
        self.config_thruster2_reverse.setChecked(False)
        self.config_thruster3_reverse.setChecked(False)
        self.config_thruster4_reverse.setChecked(False)
        self.config_thruster5_reverse.setChecked(False)
        self.config_thruster6_reverse.setChecked(False)
        self.config_thruster7_reverse.setChecked(False)
        self.config_thruster8_reverse.setChecked(False)
        self.data.configThrusterPosition = ['None'] * 8
        self.data.configThrusterReverse = [False] * 8

        ### RESET ACTUATOR SETTINGS ###
        self.data.configActuatorLabelList = []
        # DELETE PREVIOUS ACTUATORS FROM GUI
        for number in range(self.data.configActuatorNumber):
            # REMOVE ACTUATORS FROM CONFIG TAB
            self.config_actuator_form.removeRow(1) 
            # REMOVE ACTUATORS FROM CONTROL PANEL TAB
            self.control_panel_actuators.removeRow(0)
        self.config_actuators_number.setValue(0)
        self.data.configActuatorNumber = 0

        ### RESET SENSOR SETTINGS ###
        self.data.configSensorSelectedType = []
        # DELETE PREVIOUS SENSORS FROM GUI
        for number in range(self.data.configSensorNumber):
            # REMOVE SENSORS FROM CONFIG TAB
            self.config_sensor_form.removeRow(2) 
            # REMOVE SENSORS FROM CONTROL PANEL TAB
            self.control_panel_sensors.removeRow(0)
        self.config_sensors_number.setValue(0)
        self.data.configSensorNumber = 0

        ### RESET CAMERA SETTINGS ###
        self.data.configDefaultCameraList = [0] * 4
        self.data.configCameraList = []
        self.config_cameras_number.setValue(0)
        self.config_camera_1_list.clear()
        self.config_camera_2_list.clear()
        self.config_camera_3_list.clear()
        self.config_camera_4_list.clear()

    def linkControlPanelWidgets(self):
        self.control_rov_connect.clicked.connect(self.control.rovConnect)
        self.control_rov_connect.setFixedHeight(50)
        self.control_controller_connect.clicked.connect(self.control.controllerConnect)
        self.control_controller_connect.setFixedHeight(50)
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

    def linkConfigWidgets(self):
        self.config_sensors_number.editingFinished.connect(lambda: self.config.setSensorsNumber(False))
        self.config_cameras_number.editingFinished.connect(lambda: self.config.setCamerasNumber(False))
        self.config_actuators_number.editingFinished.connect(lambda: self.config.setActuatorsNumber(False))
        self.config_load_settings.clicked.connect(self.config.loadSettings)
        self.config_reset_settings.clicked.connect(self.resetConfig)
        self.config_save_settings.clicked.connect(self.config.saveSettings)

        # ADD ROV THRUSTER POSITIONS TO DROP DOWN MENUS
        self.config_thruster1_position.addItems(self.data.configThrusterPositionList)
        self.config_thruster2_position.addItems(self.data.configThrusterPositionList)
        self.config_thruster3_position.addItems(self.data.configThrusterPositionList)
        self.config_thruster4_position.addItems(self.data.configThrusterPositionList)
        self.config_thruster5_position.addItems(self.data.configThrusterPositionList)
        self.config_thruster6_position.addItems(self.data.configThrusterPositionList)
        self.config_thruster7_position.addItems(self.data.configThrusterPositionList)
        self.config_thruster8_position.addItems(self.data.configThrusterPositionList)

        # LINK EACH THRUSTER CONFIGURATION TO SAME SLOT, PASSING THE MENU INDEX, THRUSTER SELECTED, AND WHICH SETTING HAS BEEN CHANGED (POSITION, REVERSE, TEST, CONFIG)
        self.config_thruster1_position.activated.connect(lambda index, thruster = 0, setting = 0: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster2_position.activated.connect(lambda index, thruster = 1, setting = 0: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster3_position.activated.connect(lambda index, thruster = 2, setting = 0: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster4_position.activated.connect(lambda index, thruster = 3, setting = 0: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster5_position.activated.connect(lambda index, thruster = 4, setting = 0: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster6_position.activated.connect(lambda index, thruster = 5, setting = 0: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster7_position.activated.connect(lambda index, thruster = 6, setting = 0: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster8_position.activated.connect(lambda index, thruster = 7, setting = 0: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster1_reverse.toggled.connect(lambda index, thruster = 0, setting = 1: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster2_reverse.toggled.connect(lambda index, thruster = 1, setting = 1: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster3_reverse.toggled.connect(lambda index, thruster = 2, setting = 1: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster4_reverse.toggled.connect(lambda index, thruster = 3, setting = 1: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster5_reverse.toggled.connect(lambda index, thruster = 4, setting = 1: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster6_reverse.toggled.connect(lambda index, thruster = 5, setting = 1: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster7_reverse.toggled.connect(lambda index, thruster = 6, setting = 1: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster8_reverse.toggled.connect(lambda index, thruster = 7, setting = 1: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster1_test.toggled.connect(lambda index, thruster = 0, setting = 2: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster2_test.toggled.connect(lambda index, thruster = 1, setting = 2: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster3_test.toggled.connect(lambda index, thruster = 2, setting = 2: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster4_test.toggled.connect(lambda index, thruster = 3, setting = 2: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster5_test.toggled.connect(lambda index, thruster = 4, setting = 2: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster6_test.toggled.connect(lambda index, thruster = 5, setting = 2: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster7_test.toggled.connect(lambda index, thruster = 6, setting = 2: self.config.setROVThrusterSettings(index, thruster, setting))
        self.config_thruster8_test.toggled.connect(lambda index, thruster = 7, setting = 2: self.config.setROVThrusterSettings(index, thruster, setting))

        # LINK EACH DEFAULT CAMERA DROP DOWN MANU TO THE SAME SLOT, PASSING THE CAMERA ID AS 1,2,3,4 ETC.
        self.config_camera_1_list.activated.connect(lambda index, camera = 0: self.config.changeDefaultCameras(index, camera))
        self.config_camera_2_list.activated.connect(lambda index, camera = 1: self.config.changeDefaultCameras(index, camera))
        self.config_camera_3_list.activated.connect(lambda index, camera = 2: self.config.changeDefaultCameras(index, camera))
        self.config_camera_4_list.activated.connect(lambda index, camera = 3: self.config.changeDefaultCameras(index, camera))

    def initiateCameraFeed(self):
        # INITIATE CAMERAS IN SEPERATE THREADS
        # PRIMARY CAMERA
        camThread1 = CAMERA_FEED_1(self)
        camThread1.cameraNewFrame.connect(self.updateCamera1Feed)
        camThread1.start()
        # SECONDARY CAMERA 1
        #camThread2 = CAMERA_FEED_2(self)
        #camThread2.cameraNewFrame.connect(self.updateCamera2Feed)
        #camThread2.start()
        # SECONDARY CAMERA 2
        #camThread3 = CAMERA_FEED_3(self)
        #camThread3.cameraNewFrame.connect(self.updateCamera3Feed)
        #camThread3.start()

    @pyqtSlot(QImage)
    def updateCamera1Feed(self, frame):
        # DISPLAY NEW FRAME ON CAMERA FEED
        self.primary_camera.setPixmap(QPixmap.fromImage(frame))

    @pyqtSlot(QImage)
    def updateCamera2Feed(self, frame):
        # DISPLAY NEW FRAME ON CAMERA FEED
        self.secondary_camera_1.setPixmap(QPixmap.fromImage(frame))

    @pyqtSlot(QImage)
    def updateCamera3Feed(self, frame):
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
                cameraFrame = cameraFrame.scaled(1280, 720, QtCore.Qt.KeepAspectRatio)
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
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3, Object4):
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2
        self.rov = Object3
        self.controller = Object4

    def rovConnect(self):
        if self.data.controlROVCommsStatus == False:
            self.data.controlROVCommsStatus = True
            self.ui.control_rov_connect.setText('Disconnect')
            self.ui.control_rov_connect.setStyleSheet(self.data.blueStyle)
            self.rov.initialiseConnection('AVALON',self.data.rovCOMPort, 115200)
            self.getSensorReadings()
        else:
            self.data.controlROVCommsStatus = False
            self.ui.control_rov_connect.setText('Connect')
            self.ui.control_rov_connect.setStyleSheet('')
            self.rov.disconnect()

    def controllerConnect(self):
        if self.data.controlControllerCommsStatus == False:
            self.data.controlControllerCommsStatus = True
            self.ui.control_controller_connect.setText('Disconnect')
            self.ui.control_controller_connect.setStyleSheet(self.data.blueStyle)
            self.controller.initialiseConnection(self.data.controllerCOMPort)
        else:
            self.data.controlControllerCommsStatus = False
            self.ui.control_controller_connect.setText('Connect')
            self.ui.control_controller_connect.setStyleSheet('')       

    def getSensorReadings(self):
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

    def changeExternalCameraFeed(self, index, camera):
        # CAMERA VARIABLE REPRESENTS WHICH CAMERA FEED IS BEING MODIFIED (0,1,2,3)
        # INDEX VARIABLE REPRESENTS THE MENU INDEX SELECTED

        # STORE WHICH CAMERA HAS BEEN SELECTED FOR EACH FEED
        self.data.controlCameraViewList[camera] = index

    def toggleActuator(self, _, actuator, buttonObject):
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
    
    def resetTimer(self):
        if self.data.controlTimerEnabled == False:
            self.data.controlTimerMem = 0
            self.updateTimer(0)

    def readSystemTime(self):
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
        # CONVERT SECONDS TO DD:HH:MM:SS
        minutes, seconds = divmod(currentSeconds,60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        # DISPLAY TIME SINCE MEASUREMENT START
        self.ui.control_timer.display('%02d:%02d:%02d:%02d' % (days, hours, minutes, seconds))

class CONFIG():
    # CONSTUCTOR
    def __init__(self, Object1, Object2, Object3, Object4, Object5):
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2
        self.control = Object3
        self.rov = Object4
        self.controller = Object5

    def setROVThrusterSettings(self, index, thruster, setting):
        # THRUSTER POSITION
        if setting == 0:
            self.data.configThrusterPosition[thruster] = self.data.configThrusterPositionList[index]

        # THRUSTER REVERSE
        if setting == 1:
            self.data.configThrusterReverse[0] = self.ui.config_thruster1_reverse.isChecked()
            self.data.configThrusterReverse[1] = self.ui.config_thruster2_reverse.isChecked()
            self.data.configThrusterReverse[2] = self.ui.config_thruster3_reverse.isChecked()
            self.data.configThrusterReverse[3] = self.ui.config_thruster4_reverse.isChecked()
            self.data.configThrusterReverse[4] = self.ui.config_thruster5_reverse.isChecked()
            self.data.configThrusterReverse[5] = self.ui.config_thruster6_reverse.isChecked()
            self.data.configThrusterReverse[6] = self.ui.config_thruster7_reverse.isChecked()
            self.data.configThrusterReverse[7] = self.ui.config_thruster8_reverse.isChecked()

        # THRUSTER TEST

        # CONFIG 
        if setting == 3:
            # SET LOCATION OF EACH THRUSTER
            self.ui.config_thruster1_position.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[0]))
            self.ui.config_thruster2_position.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[1]))
            self.ui.config_thruster3_position.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[2]))
            self.ui.config_thruster4_position.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[3]))
            self.ui.config_thruster5_position.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[4]))
            self.ui.config_thruster6_position.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[5]))
            self.ui.config_thruster7_position.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[6]))
            self.ui.config_thruster8_position.setCurrentIndex(self.data.configThrusterPositionList.index(self.data.configThrusterPosition[7]))
            # SET REVERSE STATE
            self.ui.config_thruster1_reverse.setChecked(self.data.configThrusterReverse[0])      
            self.ui.config_thruster2_reverse.setChecked(self.data.configThrusterReverse[1]) 
            self.ui.config_thruster3_reverse.setChecked(self.data.configThrusterReverse[2]) 
            self.ui.config_thruster4_reverse.setChecked(self.data.configThrusterReverse[3]) 
            self.ui.config_thruster5_reverse.setChecked(self.data.configThrusterReverse[4]) 
            self.ui.config_thruster6_reverse.setChecked(self.data.configThrusterReverse[5]) 
            self.ui.config_thruster7_reverse.setChecked(self.data.configThrusterReverse[6]) 
            self.ui.config_thruster8_reverse.setChecked(self.data.configThrusterReverse[7])  

    def setActuatorsNumber(self, configStatus):
        oldNumber = self.data.configActuatorNumber
        newNumber = self.ui.config_actuators_number.value()
        self.data.configActuatorNumber = newNumber

        # ADD ACTUATORS IF NEW NUMBER IS HIGHER
        if newNumber > oldNumber:
            # CALCULATE NUMBER OF ACTUATORS TO ADD ON TOP OF CURRENT NUMBER
            delta = newNumber - oldNumber
            for number in range(delta):
                # CREATE 2-DIMENSIONAL ARRAY TO STORE NAME, DEFAULT AND ACTUATED LABELS FOR EACH ACTUATOR
                # ONLY CREATED WHEN CONFIG FILE IS EMPTY
                if configStatus == False:
                    self.data.configActuatorLabelList.append([])
                    self.data.configActuatorLabelList[oldNumber + number].append('Actuator {}'.format(oldNumber + number + 1))
                    self.data.configActuatorLabelList[oldNumber + number].append('OFF')
                    self.data.configActuatorLabelList[oldNumber + number].append('ON')

                # CREATE ARRAY TO STORE ACTUATOR STATES
                self.data.controlActuatorStates.append(False)

                # CREATE ACTUATOR NAME AND STATE NAME TEXT FIELDS
                actuatorLabel = QLineEdit(self.data.configActuatorLabelList[oldNumber + number][0])
                state1 = QLineEdit(self.data.configActuatorLabelList[oldNumber + number][1])
                state2 = QLineEdit(self.data.configActuatorLabelList[oldNumber + number][2])
                
                # CREATE ACTUATOR CONTROL BUTTON ON CONTROL PANEL
                actuatorToggle = QPushButton(self.data.configActuatorLabelList[oldNumber + number][1])
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
                actuatorToggle.setStyleSheet(self.data.greenStyle)

                # ADD TO CONFIG TAB
                self.ui.config_actuator_form.addRow(QLabel("Actuator {}".format((oldNumber + number + 1))), layout)
                # ADD TO CONTROL PANEL TAB
                self.ui.control_panel_actuators.addRow(actuatorName, actuatorToggle)

                # LINK CONFIG ACTUATOR TEXT FIELDS TO SLOT - PASS OBJECT, ACTUATOR NUMBER AND WHICH TEXT FIELD HAS BEEN EDITED
                actuatorLabel.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 0, controlObject = actuatorName: self.changeActuatorType(text, actuator, label, controlObject))
                state1.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 1, controlObject = actuatorToggle: self.changeActuatorType(text, actuator, label, controlObject))
                state2.textChanged.connect(lambda text, actuator = (oldNumber + number), label = 2, controlObject = actuatorToggle: self.changeActuatorType(text, actuator, label, controlObject))
                # LINK CONTROL PANEL ACTUATOR BUTTONS TO SLOT - PASS ACTUATOR NUMBER
                actuatorToggle.clicked.connect(lambda _, actuator = (oldNumber + number), buttonObject = actuatorToggle: self.control.toggleActuator(_, actuator, buttonObject))

        # REMOVE ACTUATORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF ACTUATORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                # REMOVE ACTUATORS FROM CONFIG TAB
                self.ui.config_actuator_form.removeRow(oldNumber - number) 
                # REMOVE ACTUATORS FROM CONTROL PANEL TAB
                self.ui.control_panel_actuators.removeRow(oldNumber - number - 1)

    def changeActuatorType(self, text, actuator, label, controlObject):
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
        oldNumber = self.data.configSensorNumber
        newNumber = self.ui.config_sensors_number.value()
        self.data.configSensorNumber = newNumber

        # ADD SENSORS IF NEW NUMBER IS HIGHER
        if newNumber > oldNumber:
            # CALCULATE NUMBER OF SENSORS TO ADD ON TOP OF CURRENT NUMBER
            delta = newNumber - oldNumber
            for number in range(delta):
                # CREATE SENSOR TYPE STORAGE ARRAY IF NO CONFIG FILE FOUND
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
        # SENSOR VARIABLE REPRESENTS WHICH SENSOR IS BEING MODIFIED
        # INDEX VARIABLE REPRESENTS THE MENU INDEX SELECTED
        sensorLabel.setText(self.data.configSensorTypeList[index])
        self.data.configSensorSelectedType[sensor - 1] = index

    def setCamerasNumber(self, configStatus):
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

    def saveSettings(self):
        root = xml.Element("root")

        # CONFIGURATION FOR THRUSTERS
        thrusters = xml.SubElement(root, "thrusters")
        for index in range(8):
            thruster = xml.SubElement(thrusters, "thruster{}".format(index))
            xml.SubElement(thruster, "location").text = self.data.configThrusterPosition[index]
            xml.SubElement(thruster, "reversed").text = str(self.data.configThrusterReverse[index])
        
        # CONFIGURATION FOR ACTUATORS
        actuators = xml.SubElement(root, "actuators")
        xml.SubElement(actuators, "quantity").text = str(self.data.configActuatorNumber)
        
        for index in range(self.data.configActuatorNumber):
            actuator = xml.SubElement(actuators, "actuator{}".format(index))
            xml.SubElement(actuator, "nameLabel").text = self.data.configActuatorLabelList[index][0]
            xml.SubElement(actuator, "offLabel").text = self.data.configActuatorLabelList[index][1]
            xml.SubElement(actuator, "onLabel").text = self.data.configActuatorLabelList[index][2]

        # CONFIGURATION FOR SENSORS
        sensors = xml.SubElement(root, "sensors")
        xml.SubElement(sensors, "quantity").text = str(self.data.configSensorNumber)
        
        for index in range(self.data.configSensorNumber):
            sensor = xml.SubElement(sensors, "sensor{}".format(index))
            xml.SubElement(sensor, "type").text = str(self.data.configSensorSelectedType[index])

        # CONFIGURATION FOR CAMERAS
        cameras = xml.SubElement(root, "cameras")
        analog = xml.SubElement(cameras, "analog")
        digital = xml.SubElement(cameras, "digital")

        # ANALOG CAMERAS
        xml.SubElement(analog, "quantity").text = str(self.data.configCameraNumber)
        for index in range(4):
            xml.SubElement(analog, "defaultfeed{}".format(index)).text = str(self.data.configDefaultCameraList[index])

        # SAVE TO XML FILE                                                           
        tree = xml.ElementTree(root)
        tree.write(self.data.fileName,encoding='utf-8', xml_declaration=True)

    def loadSettings(self):
        # USER CHOOSES SEQUENCE FILE
        self.data.fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui, 'Open File','./','XML File (*.xml)')
        if self.data.fileName != '':
            self.ui.configSetup()
        else:
            # SET BACK TO DEFAULT NAME IF USER DOES NOT SELECT A FILE
            self.data.fileName = 'config.xml'

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
    
    greenStyle = 'background-color: #679e37'
    redStyle = 'background-color: #f44336'
    blueStyle = 'background-color: #0D47A1; color: white;'

    controlTimerEnabled = False
    controlTimerNew = True
    controlTimerMem = 0

    ###############################
    ######## CONFIGURATION ########
    ###############################

    # DEFAULT CONFIG FILE NAME
    fileName = 'config.xml'

    # STORES OPTIONS TO BE DISPLATED ON THRUSTER POSITION DROP DOWN MENU
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
    app.setFont(QtGui.QFont("Bahnschrift Light", 10))
    app.setStyle("Fusion")
    UI()
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()