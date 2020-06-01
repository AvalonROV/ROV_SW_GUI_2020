from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QSlider, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import QIcon

class THRUSTERS(QObject):
    """
    PURPOSE

    Contains the functions to configure and control the thrusters.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM
    thrusterTestSignal = pyqtSignal(list)
    thrusterSpeedsSignal = pyqtSignal(list)

    # DATABASE
    quantity = 8
    rovControlDirection = True
    rovPositionOptions = ['None', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    rovPositions = ['None'] * 8
    reverseStates = [False] * 8
    testSpeed = 10
    yawState = [0, 0]

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

        # ADD WIDGETS TO LAYOUT
        if configLayout != None:
            self.setupConfigLayout()

    def setup(self):
        """
        PURPOSE

        Adds specific number of thrusters to the GUI configration tab.
        Eacht thruster object contains a ROV location menu, reverse checkbox and a test button.

        INPUT

        NONE

        RETURNS

        NONE 
        """
        for i in range(self.quantity):
            self.addThruster()

        self.setupControlLayout()

    def addThruster(self):
        """
        PURPOSE

        Adds a single thruster to the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.addConfigThruster()     

    def removeThruster(self):
        """
        PURPOSE

        Removes a single thruster from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.removeConfigThruster()

    def convertThrusterSpeeds(self, thrusterSpeeds):
        """
        PURPOSE

        Filters the thruster speeds before sending them to the ROV.
        Maps each thruster speed to correct position on the ROV.
        Checks which thrusters need to be reversed.

        INPUT

        - thrusterSpeeds = array containing the speed of each thruster.

        RETURNS

        - filteredThrusterSpeeds = array containing the filtered speed of each thruster.
        """
        filteredThrusterSpeeds = thrusterSpeeds.copy()

        # MAP EACH THRUSTER SPEED TO CORRECT ROV POSITION
        filteredThrusterSpeeds = self.mapThrusterPositions(filteredThrusterSpeeds)

        # CHECK IF ROV IS BEING DRIVEN IN REVERSE
        if self.rovControlDirection == False:
            filteredThrusterSpeeds = self.changeThrusterOrientation(filteredThrusterSpeeds)

        # REVERSE THRUSTERS WHERE NECCESSARY
        filteredThrusterSpeeds = self.reverseThrusterDirection(filteredThrusterSpeeds)

        # SEND FINAL THRUSTER SPEEDS TO MAIN PROGRAM
        self.thrusterSpeedsSignal.emit(filteredThrusterSpeeds)

    def mapThrusterPositions(self, thrusterSpeeds):
        """
        PURPOSE

        Maps each thruster speed to the correct position on the ROV.

        INPUT

        - thrusterSpeeds = array containing the speed of each thrusters 1 to 8 in order.

        NONE

        - mappedThrusterSpeeds = array containing the mapped thruster speeds.
        """
        mappedThrusterSpeeds = [500] * 8
            
        for index, position in enumerate(self.rovPositionOptions):
            if position != "None":
                try:
                    # FIND WHICH THRUSTER BELONGS TO THIS ROV POSITION
                    thrusterIndex = self.rovPositions.index(position)

                    # SET SPEED TO CORRECT THRUSTER
                    mappedThrusterSpeeds[thrusterIndex] = thrusterSpeeds[index - 1]

                except:
                    pass

        return mappedThrusterSpeeds

    def reverseThrusterDirection(self, thrusterSpeeds):
        """
        PURPOSE

        Reverses each thruster if neccessary.

        INPUT

        - thrusterSpeeds = an array containing the speed of each thruster.

        RETURNS

        - tempThrusterSpeeds = an array containing the filtered speed of each thruster.
        """
        newThrusterSpeeds = thrusterSpeeds.copy()

        for i, speed in enumerate(newThrusterSpeeds):
            if self.reverseStates[i] == True:
                newThrusterSpeeds[i] = 1000 - speed

        return newThrusterSpeeds

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

    def getYaw(self):
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
        if self.yawState[0] != self.yawState[1]:
            yawActive = True
            # RIGHT YAW
            if self.yawState[0] == 1:
                yawDirection = 1
            # LEFT YAW
            elif self.yawState[1] == 1:
                yawDirection = -1
            # NEUTRAL YAW
            else:
                yawDirection = 0
        else:
            yawDirection = 0
            yawActive = False
            # # CHECK IF YAW HAS CHANGED FROM PREVIOUS STATE
            # if self.data.yawButtonStatesPrevious != self.data.yawButtonStates:
            #     yawActive = True
            # else:
            #     yawActive = False

        return yawDirection, yawActive

    def reset(self):
        """
        PURPOSE

        Resets the thruster layouts to default configuration.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for i in range(self.quantity):
            self.removeThruster()

        # RESET VARIABLES
        self.quantity = 8
        self.rovPositions = ['None'] * 8
        self.reverseStates = [False] * 8

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
        # CHECK IF TIMER WIDGET HAS ALREADY BEEN SETUP
        if self.controlLayout.layout() == None:
            
            parentLayout = QHBoxLayout()
        
            # CREATE WIDGETS
            self.forwardLabel = QLabel("FORWARD")
            self.forwardLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.forwardLabel.setEnabled(True)
            self.forwardLabel.setObjectName("label-on-off")
            self.reverseLabel = QLabel("REVERSE")
            self.reverseLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.reverseLabel.setEnabled(False)
            self.reverseLabel.setObjectName("label-on-off")
            changeButton = QPushButton() 
            changeButton.setObjectName("change-orientation-button") 
            changeButton.setFixedSize(50, 50)        
            changeButton.setIcon(QIcon('graphics/switch_direction_white.png'))
            changeButton.setIconSize(QSize(40,40))
                
            # ADD TO PARENT LAYOUT
            parentLayout.addWidget(self.forwardLabel)
            parentLayout.addWidget(changeButton)
            parentLayout.addWidget(self.reverseLabel)

            # LINK WIDGETS
            changeButton.clicked.connect(self.toggleControlDirection)

            # ADD TO GUI
            self.controlLayout.setLayout(parentLayout)        

    def toggleControlDirection(self):
        """
        PURPOSE

        Flips the control orientation of the ROV, to allow easy maneuvering in reverse.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REVERSE CONTROL
        if self.rovControlDirection == True:
            self.rovControlDirection = False
            self.forwardLabel.setEnabled(False)
            self.reverseLabel.setEnabled(True)
        
        # FORWARD CONTROL
        else:
            self.rovControlDirection = True
            self.forwardLabel.setEnabled(True)
            self.reverseLabel.setEnabled(False)

    def changeThrusterOrientation(self, thrusterSpeeds):
        """
        PURPOSE

        Re-maps each thruster location to drive the ROV in reverse.

        INPUT

        - thrusterSpeeds = an array containing the speed of each thruster.

        RETURNS

        - mappedThrusterSpeeds = an array containing the filtered speed of each thruster.
        """
        # LOCATION MAP OF EACH THRUSTER WHEN DRIVING IN REVERSE
        arrayMap = [2,3,0,1,6,7,4,5]

        mappedThrusterSpeeds = [500] * 8
        
        # MAPS EACH THRUSTER SPEED TO NEW POSITION
        for i in range(8):
            thrusterIndex = arrayMap[i]
            mappedThrusterSpeeds[i] = thrusterSpeeds[thrusterIndex]

        return mappedThrusterSpeeds

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
        
        # WIDGETS TO CHANGE TEST SPEED
        testLayout = QHBoxLayout()
        self.testSlider = QSlider(Qt.Horizontal)
        self.testSlider.setMinimum(1)
        self.testSlider.setMaximum(100)
        self.testSlider.setValue(self.testSpeed)
        self.testValue = QLabel()
        self.testValue.setText("{}%".format(self.testSpeed))
        testLayout.addWidget(QLabel("Test Speed")) 
        testLayout.addWidget(self.testSlider)
        testLayout.addWidget(self.testValue)

        # LAYOUT TO SHOW THRUSTER SETTINGS
        self.configForm = QFormLayout()

        # SPACER TO PUSH ALL WIDGETS UP
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ADD CHILDREN TO PARENT LAYOUT
        parentLayout.addLayout(testLayout)
        parentLayout.addLayout(self.configForm)
        parentLayout.addItem(spacer)

        # LINK WIDGETS
        self.testSlider.valueChanged.connect(lambda value: self.changeTestSpeed(value))

        # ADD TO GUI
        self.configLayout.setLayout(parentLayout)

    def changeTestSpeed(self, value):
        """
        PURPOSE

        Changes the speed the thrusters spin when the test button is pressed.

        INPUT

        - value = the desired test speed (1 -> 100)

        RETURNS

        NONE
        """
        # UPDATE LABEL
        self.testValue.setText("{}%".format(value))

        # STORE NEW VALUE
        self.testSpeed = value

    def addConfigThruster(self):
        """
        PURPOSE

        Adds a single thruster to the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # INDEX OF THE NEXT THRUSTER
        index = self.configForm.rowCount()

        # CREATE THRUSTER NUMBER LABEL
        label = QLabel("Thruster {}".format(index + 1))
        label.setStyleSheet("font-weight: bold;")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # MENU TO SELECT THRUSTER POSITION
        label1 = QLabel('ROV Location')
        label1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        thrusterLocation = QComboBox()
        thrusterLocation.addItems(self.rovPositionOptions)      
        thrusterLocation.setCurrentIndex(self.rovPositionOptions.index(self.rovPositions[index]))
        
        # THRUSTER REVERSE CHECKBOX
        label2 = QLabel('Reversed')
        label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        thrusterReverseCheck = QCheckBox()
        thrusterReverseCheck.setChecked(self.reverseStates[index])
        
        # THRUSTER TEST BUTTON
        thrusterTest = QPushButton("Test")

        # PLACE WIDGETS INSIDE LAYOUT
        layout1 = QVBoxLayout()
        layout1.addWidget(label)
        layout2 = QFormLayout()
        layout2.addRow(label1, thrusterLocation)
        layout2.addRow(label2, thrusterReverseCheck)
        layout2.addRow(None, thrusterTest)

        # ADD LAYOUTS TO FRAMES (TO ALLOW STYLING)
        frame1 = QFrame()
        frame1.setObjectName("thruster-frame")
        frame1.setLayout(layout1)
        frame2 = QFrame()
        frame2.setObjectName("settings-frame")
        frame2.setLayout(layout2)

        # ADD TO FORM LAYOUT
        self.configForm.addRow(frame1, frame2)

        # LINK WIDGETS
        thrusterLocation.activated.connect(lambda index, thruster = index: self.thrusterPosition(index, thruster)) 
        thrusterReverseCheck.toggled.connect(lambda state, thruster = index: self.thrusterReverse(state, thruster))
        thrusterTest.pressed.connect(lambda state = True, thruster = index: self.thrusterTest(state, thruster))
        thrusterTest.released.connect(lambda state = False, thruster = index: self.thrusterTest(state, thruster))

    def removeConfigThruster(self):
        """
        PURPOSE

        Removes a single thruster from the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REMOVE THRUSTER FROM CONFIGURATION TAB
        thrusterNumber = self.configForm.rowCount() - 1
        self.configForm.removeRow(thrusterNumber) 

        # RESET ACTUATOR STATE DATA
        self.rovPositions[thrusterNumber] = 'None'
        self.reverseStates[thrusterNumber] = False

    def thrusterPosition(self, index, thruster):
        """
        PURPOSE

        Changes the position of the thrusters on the ROV.

        INPUT

        - index = menu index of the ROV location selected.
        - thruster = the thruster being modified.

        RETURNS

        NONE
        """
        self.rovPositions[thruster] = self.rovPositionOptions[index]

        # PREVENT MULTIPLE THRUSTERS PER ROV LOCATION
        for i, item in enumerate(self.rovPositions):
            if item == self.rovPositions[thruster] and i != thruster:
                # SET BINDING TO NONE
                self.rovPositions[i] = self.rovPositionOptions[0]
                # FIND BINDING MENU WIDGET
                layout = self.configForm.itemAt((2 * i) + 1).widget()
                layout = layout.layout()
                widget = layout.itemAt(1).widget()
                # SET TO NONE
                widget.setCurrentIndex(0)

    def thrusterReverse(self, state, thruster):
        """
        PURPOSE

        Switches the direction of a thruster.

        INPUT

        - state = state of the checkbox (True or False)
        - thruster = the thruster being reversed (0,1,2 etc).

        RETURNS

        NONE
        """
        self.reverseStates[thruster] = state

    def thrusterTest(self, state, thruster):
        """
        PURPOSE

        Allows each thruster to be individually turned on at a low speed.
        This lets the pilot known where each thruster is on the ROV and which direction they spin.

        INPUT

        - state = state of the 'test' button (True or False).
        - thruster = the thruster being tested (0,1,2 etc).

        RETURNS

        NONE
        """
        # MAP TEST SPEED (0 - > 999)
        testSpeed = int(500 + (499 * self.testSpeed/100))

        # SET ALL THRUSTER SPEEDS TO ZERO
        speeds = [500] * self.quantity

        if state:
            # SET DESIRED THRUSTER TO TEST SPEED
            speeds[thruster] = testSpeed

        # REVERSE THRUSTERS WHERE NECCESSARY
        speeds = self.reverseThrusterDirection(speeds)
        
        # EMIT SIGNAL TO MAIN PROGRAM
        self.thrusterTestSignal.emit(speeds)