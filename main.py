from PyQt5 import QtWidgets, QtGui, QtCore, uic

from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog,
QDialogButtonBox, QRadioButton, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
QLabel, QLineEdit, QMenu, QMenuBar, QPushButton, QSpinBox, QTextEdit,
QVBoxLayout)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
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

        # CREATING OBJECTS AND PASSING UI OBJECT TO THEM
        self.data = DATABASE()
        self.controlPanel = CONTROL_PANEL(self, self.data)
        self.config = CONFIG(self, self.data)
        self.functionTest = FUNCTION_TEST(self, self.data)
        
        # FIND SCREEN SIZE
        sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)
        self.data.screenHeight = sizeObject.height()
        self.data.screenWidth = sizeObject.width() 

        # SET DEFAULT WIDGET SIZES
        self.con_panel_functions_widget.resize(self.data.screenWidth/6,self.con_panel_functions_widget.height())
        self.func_testing_functions_widget.resize(self.data.screenWidth/6,self.con_panel_functions_widget.height())

        # ADD AVALON LOGO
        pixmap = QPixmap("logo.png")
        pixmap = pixmap.scaledToWidth(250)
        self.avalon_logo.setPixmap(pixmap)

        # LINK GUI BUTTONS TO METHODS
        self.linkControlPanelButtons()
        self.linkConfigButtons()
        self.linkFunctionTestButtons()

        # INITIALISE UI
        self.showMaximized()

    def linkControlPanelButtons(self):
        self.rov_connect.clicked.connect(rovSerial.rovConnect)
        self.controller_connect.clicked.connect(rovSerial.controllerConnect)
        self.config_actuators_number.valueChanged.connect(self.config.configSetActuatorsNumber)

    def linkConfigButtons(self):
        self.config_sensors_number.valueChanged.connect(self.config.configSetSensorsNumber)

        for self.sensor in self.data.configSensorTypeMenu:
            self.sensor.activated.connect(self.config.configChangeSensorType)

    def linkFunctionTestButtons(self):
        pass

class CONTROL_PANEL():
    # CONSTUCTOR
    def __init__(self, Object1, Object2):
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2

class CONFIG():
    # CONSTUCTOR
    def __init__(self, Object1, Object2):
        # CREATE OBJECTS
        self.ui = Object1
        self.data = Object2

    def configSetActuatorsNumber(self):
        """
        ### Changes number of sensors to be read from.
        """
        oldNumber = self.data.configActuatorNumber
        newNumber = self.ui.config_actuators_number.value()
        self.data.configActuatorNumber = newNumber

        # ADD SENSORS IF NEW NUMBER IS HIGHER
        if newNumber > oldNumber:
            # CALCULATE NUMBER OF SENSORS TO ADD ON TOP OF CURRENT NUMBER
            delta = newNumber - oldNumber
            for number in range(delta):
                # CREATE ACTUATOR NAME AND STATE NAME TEXT FIELDS
                actuatorLabel = QLineEdit()
                state1 = QLineEdit()
                state2 = QLineEdit()
                
                # CREATE ACTUATOR CONTROL BUTTON
                actuatorToggle = QPushButton('Default State')
                # CREATE FORM LAYOUT
                layout = QGridLayout()
                layout.addWidget(QLabel('Actuator Name'),0,0)
                layout.addWidget(actuatorLabel,0,1)
                layout.addWidget(QLabel('Default State'),1,0)
                layout.addWidget(state1,1,1)
                layout.addWidget(QLabel('Actuated State'),2,0)
                layout.addWidget(state2,2,1)

                # ADD TO CONFIG TAB
                self.ui.config_actuator_form.addRow(QLabel("Actuator %s" % (oldNumber + number + 1)), layout)
                # ADD TO CONTROL PANEL TAB
                self.ui.control_panel_actuators.addRow(QLabel("Actuator %s" % (oldNumber + number + 1)), actuatorToggle)

        # REMOVE SENSORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF SENSORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                # REMOVE SENSORS FROM CONFIG TAB
                self.ui.config_actuator_form.removeRow(oldNumber - number) 
                # REMOVE SENSORS FROM CONTROL PANEL TAB
                self.ui.control_panel_actuators.removeRow(oldNumber - number - 1)
                # REMOVE QCOMBOBOX OBJECT FROM STORAGE ARRAY      
                #del self.data.configSensorTypeMenu.remove[oldNumber - number - 1]

    def configSetSensorsNumber(self):
        """
        ### Changes number of sensors to be read from.
        """
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
                # ADD OBJECT TO ARRAY TO ENABLE ACTIVATION EVENT OF EACH SENSOR MENU TO BE DETECTED
                self.data.configSensorTypeMenu.append(sensorType)
                # CREATE SENSOR READINGS TEXT BOX
                sensorView = QLineEdit()
                sensorView.setReadOnly(True)
                # CREATE FORM LAYOUT
                layout = QFormLayout()
                layout.addRow(QLabel("Type"), sensorType)
                # ADD TO CONFIG TAB
                self.ui.config_sensor_form.addRow(QLabel("Sensor %s" % (oldNumber + number + 1)), layout)
                # ADD TO CONTROL PANEL TAB
                self.ui.control_panel_sensors.addRow(QLabel("Sensor %s" % (oldNumber + number + 1)), sensorView)

        # REMOVE SENSORS IF NEW NUMBER IS LOWER
        if newNumber < oldNumber:
            # CALCULATE NUMBER OF SENSORS TO REMOVE FROM CURRENT NUMBER
            delta = oldNumber - newNumber
            for number in range(delta):
                print(number)
                # REMOVE SENSORS FROM CONFIG TAB
                self.ui.config_sensor_form.removeRow(oldNumber - number - 1) 
                # REMOVE SENSORS FROM CONTROL PANEL TAB
                self.ui.control_panel_sensors.removeRow(oldNumber - number - 1)
                # REMOVE QCOMBOBOX OBJECT FROM STORAGE ARRAY      
                #del self.data.configSensorTypeMenu.remove[oldNumber - number - 1]
                      
    def configChangeSensorType(self):
        print('CHANGED')

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

    # STORES OPTIONS TO BE DISPLAYED ON SENSOR TYPE DROP DOWN MENU
    configSensorTypeList = ['None','Temperature (°C)','Depth (m)', 'Yaw (°)', 'Pitch (°)', 'Roll (°)']
    # STORES EACH SENSOR QCOMBOBOX OBJECT
    configSensorTypeMenu =[]
    # STORES CURRENT NUMBER OF SENSORS
    configSensorNumber = 0

    # STORES USER DEFINED LABEL FOR EACH ACTUATOR
    configActuatorLabelList = []
    # STORES CURRENT NUMBER OF ACTUATORS
    configActuatorNumber = 0

    ###############################
    ######## CONFIGURATION ########
    ###############################


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
    window = UI()
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()