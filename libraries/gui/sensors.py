from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QLineEdit, QSpinBox, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem, QRadioButton
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot, QPoint, QPointF
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QXYSeries, QValueAxis, QSplineSeries
from PyQt5.QtGui import QPainter

class SENSORS(QObject):
    """
    PURPOSE

    Contains functions to configure and control the ROVs sensors.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM

    # DATABASE
    quantity = 0
    typeOptions = ['None','Temperature (°C)','Depth (m)', 'Yaw (°)', 'Pitch (°)', 'Roll (°)']
    axisRange = [[0,0],[0,50],[0,10],[0,180],[0,180],[0,180]]
    selectedTypes = []
    viewType = 1
    data = []
    dataPoints = 100
    seriesObjects = []

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

        if self.viewType == 0:
            self.textBoxViewButton.setChecked(True)
        elif self.viewType == 1:
            self.graphViewButton.setChecked(True)

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

        self.data.append([0])

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
        self.seriesObjects = []

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

        # GET SENSOR LABEL
        selectedType = self.selectedTypes[nextSensor]
        typeLabel = self.typeOptions[selectedType]

        # CREATE SENSOR READINGS TEXT BOX
        if self.viewType == 0:
            sensorView, sensorLabel = self.addSensorTextBox(typeLabel)

            # ADD TO CONTROL PANEL TAB
            self.controlForm.addRow(sensorLabel, sensorView)
        
        # CREATE SENSOR READINGS GRAPH
        elif self.viewType == 1:
            # GET GRAPH AXIS RANGE
            rangeMin, rangeMax = self.axisRange[selectedType]

            sensorView = self.addSensorGraph(typeLabel, rangeMin, rangeMax)

            # ADD TO CONTROL PANEL TAB (BLANK LABEL)
            self.controlForm.addRow(QLabel(), sensorView)

    def addSensorTextBox(self, label):
        """
        PURPOSE

        Creates a text box to display the sensor readings.

        INPUT

        - label = text to describe the sensor.

        OUTPUT

        - sensorView = the textbox object.
        """
        sensorView = QLineEdit()
        sensorView.setReadOnly(True)
        sensorView.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        sensorLabel = QLabel(label)

        return sensorView, sensorLabel

    def addSensorGraph(self, label, rangeMin = 0, rangeMax = 100):
        """
        PURPOSE

        Creates a live graph to display the sensor readings.

        INPUT

        - label = text to describe the sensor.

        OUTPUT

        - sensorView = the graph object.
        """
        chart =  QChart()
        chart.setTitle(label)
        chart.legend().setVisible(False)
        chart.setBackgroundRoundness(20)
        #chart.legend().setAlignment(Qt.AlignBottom)

        # DATA SERIES TO ADD DATA TO
        series = QSplineSeries(self)
    
        chart.addSeries(series)
        chart.createDefaultAxes()

        xAxis = QValueAxis()
        xAxis.setRange(0, self.dataPoints)
        xAxis.setLabelsVisible(False)

        yAxis = QValueAxis()
        yAxis.setRange(rangeMin, rangeMax)
        yAxis.setLabelsVisible(True)

        chart.setAxisX(xAxis, series)
        chart.setAxisY(yAxis, series)
 
        sensorView = QChartView(chart)
        sensorView.setFixedHeight(200)
        chart.layout().setContentsMargins(0, 0, 0, 0)
        
        sensorView.setRenderHint(QPainter.Antialiasing)

        self.seriesObjects.append(series)

        return sensorView

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

        # DELETE ANY EXCESS GRAPH OBJECTS
        while len(self.seriesObjects) > sensorNumber:
            self.seriesObjects.pop()

    def removeSensorTextBox(self):
        """
        PURPOSE

        Remove sensor display text box from control panel

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

    def removeSensorGraph(self):
        """
        PURPOSE

        Remove sensor display graph from control panel

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

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

            if i <= self.quantity:
                try:
                    # ADD READINGS TO HISTORY
                    self.data[i].append(float(reading))
                    
                    # IF HISTORY IS FULL, REMOVE FIRST DATA POINT
                    if len(self.data[i]) > self.dataPoints:
                        
                        self.data[i].pop(0)

                    if i <= quantity:

                        # TEXT BOX DISPLAY
                        if self.viewType == 0:
                            self.updateSensorTextBox(i, reading)
                        
                        # GRAPH DISPLAY
                        if self.viewType == 1:
                            self.updateSensorGraph(i, reading)
                except:
                    pass

    def updateSensorTextBox(self, sensor, reading):
        """
        PURPOSE

        Update each sensor text box with the latest reading.

        INPUT

        - sensor = the index of the sensor text box to modify.
        - reading = the value to display.

        OUTPUT

        NONE
        """
        # FIND LABEL WIDGET FOR EACH SENSOR
        try:
            labelObject = self.controlForm.itemAt((2 * sensor) + 1).widget()
            labelObject.setText(str(reading))
        except:
            pass

    def updateSensorGraph(self, sensor, reading):
        """
        PURPOSE

        Update each sensor graph, adding the latest value to the series.

        INPUT

        - sensor = the index of the sensor graph to modify.
        - reading = the value to display.

        OUTPUT

        NONE
        """
        try:
            # CREATE ARRAY OF QPOINTS FROM DATA HISTORY
            newData = [QPoint(x, y) for x, y in enumerate(self.data[sensor])]

            # GET SENSOR LABEL
            label = self.typeOptions[self.selectedTypes[sensor]]
        
            self.seriesObjects[sensor].chart().setTitle(label + ": " + "{:3.2f}".format(float(reading)))
            
            self.seriesObjects[sensor].replace(newData)
        except:
            pass
        
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
        
        for i in range(quantity):

            # FIND NEW LABEL
            label = self.typeOptions[self.selectedTypes[i]]

            # UPDATE EACH SENSOR LABEL
            if self.viewType == 0:
                try:
                    # FIND LABEL WIDGET FOR EACH SENSOR
                    labelObject = self.controlForm.itemAt(2 * i).widget()
                    labelObject.setText(label)
                except:
                    pass
            
            elif self.viewType == 1:
                try:
                    # UPDATE GRAPH TITLE
                    chartView = self.controlForm.itemAt((2 * i) + 1).widget() 
                    chart = chartView.chart()
                    chart.setTitle(label)

                    # UPDATE GRAPH AXIS RANGES
                    rangeMin, rangeMax = self.axisRange[self.selectedTypes[i]]
                    xAxis, yAxis = chart.axes()
                    yAxis.setRange(rangeMin, rangeMax)
                except:
                    pass

    def toggleDisplay(self):
        """
        PURPOSE

        Toggles the sensor reading display between a number and a graph.

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

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

        # WIDGETS TO CHANGE SENSOR VIEW TYPE (TEXTBOX, GRAPH ETC.)
        settingsChildLayout = QVBoxLayout()
        self.textBoxViewButton = QRadioButton("Text Box")
        self.graphViewButton = QRadioButton("Graph")
        settingsChildLayout.addWidget(self.textBoxViewButton)
        settingsChildLayout.addWidget(self.graphViewButton)
        settingsLayout.addRow(QLabel("Display Type"), settingsChildLayout)

        # LAYOUT TO SHOW SENSOR SETTINGS
        self.configForm = QFormLayout()

        # SPACER TO PUSH ALL WIDGETS UP
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ADD CHILDREN TO PARENT LAYOUT
        parentLayout.addLayout(settingsLayout)
        parentLayout.addLayout(self.configForm)
        parentLayout.addItem(spacer)
        
        # LINK WIDGETS
        self.sensorNumber.editingFinished.connect(self.changeSensorsNumber)
        self.textBoxViewButton.clicked.connect(self.changeViewType)
        self.graphViewButton.clicked.connect(self.changeViewType)
        
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

    def changeViewType(self):
        """
        PURPOSE

        Changes the way sensors are displayed on the control panel.

        INPUT

        NONE

        OUTPUT

        NONE
        """
        if self.textBoxViewButton.isChecked():
            self.viewType = 0
            
        elif self.graphViewButton.isChecked():
            self.viewType = 1
        
        while self.controlForm.rowCount():
            self.removeControlSensor()
        
        for i in range(self.quantity):
            self.addControlSensor()

        print(self.seriesObjects)
           
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