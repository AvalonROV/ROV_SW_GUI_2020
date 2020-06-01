from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QLineEdit, QSpinBox, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot

class SENSORS(QObject):
    """
    PURPOSE

    Contains functions to configure and control the ROVs sensors.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM

    # DATABASE
    quantity = 0
    typeOptions = ['None','Temperature (°C)','Depth (m)', 'Yaw (°)', 'Pitch (°)', 'Roll (°)']
    selectedTypes = []

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

        Adds specific number of sensors to the GUI.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        sensorNumber = self.quantity

        self.sensorNumber.setValue(sensorNumber)

        for i in range(sensorNumber):
            self.addSensor()

    def addSensor(self):
        """
        PURPOSE

        Adds a single sensor to the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.addConfigSensor()
        self.addControlSensor()

    def removeSensor(self):
        """
        PURPOSE
        
        Removes a single sensor from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.removeConfigSensor()
        self.removeControlSensor()

    def reset(self):
        """
        PURPOSE

        Resets the sensor configuration to default settings.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for i in range(self.quantity):
            self.removeSensor()

        self.quantity = 0
        self.selectedTypes = []

        # UPDATE WIDGETS
        self.sensorNumber.setValue(self.quantity)

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
        self.controlForm = QFormLayout()
        self.controlLayout.setLayout(self.controlForm)

    def addControlSensor(self):
        """
        PURPOSE

        Adds a single sensor to the control panel tab.

        INPUT

        NONE

        RETURN

        NONE
        """
        # THE INDEX OF THE NEXT SENSOR
        nextSensor = self.controlForm.rowCount()

        # CREATE SENSOR READINGS TEXT BOX
        sensorView = QLineEdit()
        sensorView.setReadOnly(True)
        sensorView.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        # CREATE SENSOR LABEL
        selectedType = self.selectedTypes[nextSensor]
        typeLabel = self.typeOptions[selectedType]
        sensorLabel = QLabel(typeLabel)

        # ADD TO CONTROL PANEL TAB
        self.controlForm.addRow(sensorLabel, sensorView)

    def removeControlSensor(self):
        """
        PURPOSE

        Removes a single sensor from the control panel tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REMOVE SENSORS FROM CONTROL PANEL TAB
        sensorNumber = self.controlForm.rowCount() - 1
        self.controlForm.removeRow(sensorNumber)

    def updateSensorReadings(self, readings):
        """
        PURPOSE

        Updates the sensor text boxes with the latest sensor readings.

        INPUT

        - readings = an array containing the sensor readings.

        RETURNS

        NONE
        """
        quantity = self.controlForm.rowCount()

        # UPDATE EACH SENSOR LABEL
        for i, reading in enumerate(readings):
            if i <= quantity:
                # FIND LABEL WIDGET FOR EACH SENSOR
                labelObject = self.controlForm.itemAt((2 * i) + 1).widget()
                labelObject.setText(str(reading))

    def updateControlLabels(self):
        """
        PURPOSE

        Updates the name label of each sensors.

        INPUT

        NONE

        RETURNS

        NONE
        """
        quantity = self.controlForm.rowCount()

        # UPDATE EACH SENSOR LABEL
        for i in range(quantity):
            # FIND LABEL WIDGET FOR EACH SENSOR
            labelObject = self.controlForm.itemAt(2 * i).widget()
            label = self.typeOptions[self.selectedTypes[i]]
            labelObject.setText(label)

    #########################
    ### CONFIGURATION TAB ###
    #########################
    def setupConfigLayout(self):
        """
        PURPOSE

        Builds a layout on the configuration tab to add widgets to.

        INPUT

        NONE

        RETURNS

        NONE
        """
        parentLayout = QVBoxLayout()
        
        # WIDGETS TO CHANGE SENSOR QUANTITY
        settingsLayout = QFormLayout()
        self.sensorNumber = QSpinBox()
        self.sensorNumber.setMaximum(10)
        settingsLayout.addRow(QLabel("Quantity"), self.sensorNumber) 

        # LAYOUT TO SHOW THRUSTER SETTINGS
        self.configForm = QFormLayout()

        # SPACER TO PUSH ALL WIDGETS UP
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ADD CHILDREN TO PARENT LAYOUT
        parentLayout.addLayout(settingsLayout)
        parentLayout.addLayout(self.configForm)
        parentLayout.addItem(spacer)
        
        # LINK WIDGETS
        self.sensorNumber.editingFinished.connect(self.changeSensorsNumber)
        
        # ADD TO GUI
        self.configLayout.setLayout(parentLayout)
    
    def changeSensorsNumber(self):
        """
        PURPOSE

        Sets the number of sensors based on the user entered value in the configuration tab.

        INPUT

        NONE

        RETURN

        NONE
        """
        newNumber = self.sensorNumber.value()
        oldNumber = self.configForm.rowCount()

        self.quantity = newNumber

        delta = newNumber - oldNumber

        # ADD ACTUATORS
        if delta > 0:
            for i in range(delta):
                self.addSensor()

        # REMOVE ACTUATORS
        if delta < 0:
            for i in range(-delta):
                self.removeSensor()

    def addConfigSensor(self):
        """
        PURPOSE

        Adds a single sensor to the configuration tab.

        INPUT

        NONE

        RETURN

        NONE
        """
        # THE INDEX OF THE NEXT SENSOR
        nextSensor = self.configForm.rowCount()

        # TRY TO SET SENSOR TYPE FROM CONFIG FILE
        try:
            selectedType = self.selectedTypes[nextSensor]
        
        # OTHERWISE, SET DEFAULT AS NONE
        except:
            selectedType = 0
            self.selectedTypes.append(selectedType)

        # CREATE CONFIGURATION WIDGETS
        label = QLabel("Sensor {}".format(nextSensor + 1))
        typeLabel = QLabel("Type")
        sensorType = QComboBox()
        sensorType.addItems(self.typeOptions)
        sensorType.setCurrentIndex(selectedType)
        
        # PLACE WIDGETS INSIDE LAYOUT
        layout1 = QVBoxLayout()
        layout1.addWidget(label)
        layout2 = QFormLayout()
        layout2.addRow(typeLabel, sensorType)

        # ADD LAYOUTS TO FRAMES (TO ALLOW STYLING)
        frame1 = QFrame()
        #frame1.setObjectName("sensor-frame")
        frame1.setLayout(layout1)
        frame2 = QFrame()
        #frame2.setObjectName("settings-frame")
        frame2.setLayout(layout2)
        
        # ADD TO FORM LAYOUT
        self.configForm.addRow(frame1, frame2)
        
        # LINK WIDGETS
        sensorType.activated.connect(lambda index, sensor = nextSensor: self.changeSensorType(index, sensor))

    def removeConfigSensor(self):
        """
        PURPOSE

        Removes a single sensor from the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REMOVE SENSORS FROM CONFIG TAB
        sensorNumber = self.configForm.rowCount() - 1
        self.configForm.removeRow(sensorNumber) 
        
        # REMOVE SENSOR DATA
        del self.selectedTypes[sensorNumber]

    def changeSensorType(self, index, sensor):
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
        self.selectedTypes[sensor] = index 

        # UPDATE LABEL ON CONTROL PANEL
        self.updateControlLabels()