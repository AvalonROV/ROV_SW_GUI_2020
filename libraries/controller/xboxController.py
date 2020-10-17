import sys
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, QTimer, Qt, QObject
from PyQt5.QtWidgets import (QWidget, QApplication, QFormLayout, QGridLayout, QLabel, 
                            QLineEdit, QPushButton, QSizePolicy)
from PyQt5.QtGui import QFont

from pygame import init
from pygame.joystick import quit, Joystick, get_count
from pygame.event import Event, get

class VIEW(QWidget):

    controllerConnectStatus = False
    
    def __init__(self):
        super(VIEW, self).__init__()
        self.setWindowTitle("Controller Values View")
        # INITIALISE CONTROLLER OBJECT
        self.controller = CONTROLLER()
        self.setupGUI()
        self.show()

    def setupGUI(self):
        self.layout = QGridLayout()
        self.connectButton = QPushButton("CONNECT")
        self.connectButton.clicked.connect(self.controllerConnect)
        self.formLayout = QFormLayout()
        
        # ADD INDICATOR FOR EACH CONTROLLER BUTTON TO THE FORM LAYOUT
        self.controllerLabelObjects = self.controller.setupControllerValuesDisplay(self.formLayout)
        
        self.layout.addWidget(self.connectButton,0,0)
        self.layout.addLayout(self.formLayout,1,0)
        self.setLayout(self.layout)

    def controllerConnect(self):
        if self.controllerConnectStatus == False:
            self.controllerConnectStatus = True
            self.connectButton.setText("DISCONNECT")
            
            connectionStatus, controllerNumber, message = self.controller.findController("Controller (Xbox One For Windows)")
            print(message)

            # IF CONTROLLER IS FOUND
            if connectionStatus == True:
                self.controller.startControllerEventLoop(controllerNumber)
            else:
                self.controllerConnect()

        else:
            self.controllerConnectStatus = False
            self.connectButton.setText("CONNECT")
            self.controller.stopControllerEventLoop()
            # UNINITIALISE JOYSTICK MODULE
            quit()

class CONTROLLER(QObject):
    """
    PURPOSE

    Contains the functions to connect and read from the XBOX controller.
    """
    # SIGNALS TO SEND BUTTON AND JOYSTICK DATA FOR FURTHER PROCESSING
    processInputSignal = pyqtSignal(list, list)

    # DATABASE
    buttonStates = []
    joystickValues = []
    buttonLabels = ['A','B','X','Y','LB','RB','SELECT','START','LS','RS','LEFT','RIGHT','DOWN','UP']
    buttonReleased = [True] * 14

    def __init__(self):
        """
        PURPOSE

        Class constructor

        INPUT

        NONE

        RETURNS

        NONE
        """
        QObject.__init__(self)

    def findController(self, controllerID):
        """
        PURPOSE

        Initiates the PyGame library and any connected controllers that are the correct type.

        INPUT

        - controllerID = required identity of the controller, for example: "Controller (Xbox One For Windows)".

        RETURNS

        - connectionStatus = true if the correct controller is found.
        - controllerNumber = index of the connected controller from the list of available controllers.
        - message = status message to be displayed on GUI.
        """
        connectionStatus = False
        controllerNumber = 0

        # INITIALISE PYGAME MODULE (JOYSTICK IS AUTOMATICALLY INITIATED)
        init()

        # GET NUMBER OF CONTROLLERS CONNECTED
        joystick_count = get_count()

        # THROW ERROR IS NO CONTROLLERS ARE DETECTED
        if joystick_count < 1:
            message = 'No controllers found.'
            connectionStatus = False
            # UNINITIALISE JOYSTICK MODULE
            quit()

        else:
            for i in range(joystick_count):
                joystick = Joystick(i)
                joystick.init()
                # GET NAME OF CONTROLLER/JOYSTICK FROM OS
                name = joystick.get_name()
            
                # CONNECT TO FIRST CONTROLLER WITH CORRECT IDENTITY
                if name == controllerID:
                    connectionStatus = True
                    controllerNumber = i
                    message = 'Connected to {}'.format(controllerID)
                    break

        return connectionStatus, controllerNumber, message

    def setupControllerValuesDisplay(self, formLayout):
        """
        PURPOSE

        Adds a list of text box's for each button/joystick to show their current values.

        INPUT

        - formLayout = pointer to the QFormLayout to add the widgets to.

        RETURNS

        - controllerLabelObjects = array containing pointers to the label objects to update the controller values.
        """
        # NAMES OF JOYSTICK AXES
        joystickLabels = ['Left X', 'Left Y','Triggers', 'Right Y', 'Right X']
        buttonLabels = ['A','B','X','Y','LB','RB','SELECT','START','LS','RS','LEFT','RIGHT','DOWN','UP']
        controllerLabelObjects = []
        self.formLayout = formLayout
        
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
            controllerLabelObjects.append(value)

            # ADD TO FORM LAYOUT
            formLayout.addRow(label, value)

        # CREATE DISPLAY FOR BUTTONS
        for index in range(14):
            # CREATE BUTTON LABEL
            label = QLabel(buttonLabels[index])
            label.setStyleSheet("font-weight: bold;")
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # CREATE TEXT BOX TO DISPLAY VALUE
            value = QLineEdit()
            value.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            value.setReadOnly(True)

            # ADD POINTER FOR THE QLINEEDIT INTO AN ARRAY FOR LATER ACCESS
            controllerLabelObjects.append(value)

            # ADD TO FORM LAYOUT
            formLayout.addRow(label, value)

        return controllerLabelObjects

    def startControllerEventLoop(self, controllerNumber):
        """
        PURPOSE

        Initiates a thread with a timer that repeatidly reads the values of the controllers joysticks and buttons.
        Connects signal to send values back to main program for processing.

        INPUT

        - controllerNumber = address of the controller to read from.

        RETURNS

        NONE
        """
        self.eventLoop = CONTROLLER_UPDATE(controllerNumber)
        
        # UPDATE GUI CONTROLLER INDICATORS
        self.eventLoop.controllerValues.connect(self.updateControllerValues)
        self.eventLoop.start()

    def stopControllerEventLoop(self):
        """
        PURPOSE

        Stops reading from the controller.

        INPUT

        NONE

        RETURNS

        NONE
        """
        try:
            self.eventLoop.exit()
        except:
            pass

    @pyqtSlot(list, list)
    def updateControllerValues(self, buttonStates, joystickValues):
        """
        PURPOSE

        Emits a signal to updates the text fields on the configuration tab with the latest controller button states and joystick values.

        INPUT

        - buttonStates = an array containing the states of all the controller buttons (0 or 1).
        - joystickValues = an array containing the values of all the joysticks (-1 -> 1).

        RETURNS
        
        NONE
        """
        # SEND BUTTON AND JOYSTICK VALUES TO MAIN PROGRAM
        if buttonStates != self.buttonStates or joystickValues != self.joystickValues:
            try:
                self.processInputSignal.emit(buttonStates, joystickValues)
            except:
                pass

        # SAVE DATA LOCALLY FOR FUTURE COMPARISON
        self.buttonStates = buttonStates
        self.joystickValues = joystickValues
              
class CONTROLLER_UPDATE(QThread):
    """
    PURPOSE

    Thread that contains the functions required to read from the controller.
    """
    # SIGNAL TO SEND DATA TO CONTROLLER OBJECT
    controllerValues = pyqtSignal(list, list)

    def __init__(self, controllerNumber):
        """
        PURPOSE

        Class constructor.
        Initialises a timer to repeatidly read from the XBOX controller.

        INPUT

        - controllerNumber = the address of the controller to read from.

        RETURNS

        NONE
        """
        QThread.__init__(self)
        self.controllerNumber = controllerNumber
        # UPDATE CONTROLLER VALUES AT A RATE OF 60FPS
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.run)
        self.timer.start(int(1000/60))

    def getControllerInputs(self, controllerNumber):
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

        # GET CONTROLLER EVENTS
        get()

        # INITIATE CONNECTED CONTROLLER
        joystick = Joystick(controllerNumber)
        joystick.init()

        # GET NUMBER OF VARIABLE JOYSTICK AXES
        axes = joystick.get_numaxes()
        
        # GET VALUES OF EACH VARIABLE AXES
        for i in range(axes):
            axis = joystick.get_axis(i)
            joystickValues.append(axis)

        # GET NUMBER OF BUTTONS
        buttons = joystick.get_numbuttons()

        # LATEST PYGAME VERSION RETRIEVES 11 BUTTONS, WE ONLY NEED 10
        buttons = 10

        # GET STATE OF EACH BUTTON
        for i in range(buttons):
            button = joystick.get_button(i)
            buttonStates.append(button)
                        
        # GET NUMBER OF ARROW BUTTONS
        arrows = joystick.get_numhats()

            # GET STATE OF EACH ARROW BUTTONS
        for i in range(arrows):
            arrowStates = joystick.get_hat(i)

        # RETURN ARRAY OF BUTTON STATES AND JOYSTICK VALUES
        return(buttonStates, arrowStates, joystickValues)

    def filterButtons(self, buttonStates, arrowStates):
        """
        PURPOSE

        Merges the button and arrow button states into a single array.

        INPUT

        - buttonStates = an array containing the states of all the controller buttons (0 or 1).
        - arrowSTates = and array containing the states of the arrow buttons (-1, 0 or 1).

        RETURNS

        -filteredButtonStates = an array containing the button states with the arrow button states added onto the end.

        NONE
        """
        filteredButtonStates = buttonStates.copy()

        # APPEND ARROW BUTTONS ONTO THE END OF BUTTONSTATES ARRAY
        for i in arrowStates:
            if i == -1:
                # LEFT OR DOWN PRESSED
                filteredButtonStates.append(1)
                filteredButtonStates.append(0)
            elif i == 1:
                # RIGHT OR UP PRESSED
                filteredButtonStates.append(0)
                filteredButtonStates.append(1)
            else:
                # NOT PRESSED
                filteredButtonStates.append(0)
                filteredButtonStates.append(0)

        return filteredButtonStates

    def filterJoysticks(self, joystickValues):
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
        filteredJoystickValues = joystickValues.copy()
        
        # ADD DEADZONE OF +/-0.1
        filteredJoystickValues = [0 if (number < 0.1 and number > -0.1) 
                                    else number 
                                    for number in filteredJoystickValues]
        # ROUND TO 1 DECIMAL PLACE
        filteredJoystickValues = [round(number, 2) for number in filteredJoystickValues]

        return(filteredJoystickValues)

    def run(self):
        """
        PURPOSE

        Main thread loop that reads, filters, and emits the button states and joystick values.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # TAKE SINGLE READING OF CONTROLLER VALUES
        buttonStates, arrowStates, joystickValues = self.getControllerInputs(self.controllerNumber)
        
        # PROCESS BUTTON STATES
        filteredButtonStates = self.filterButtons(buttonStates, arrowStates)
        
        # PROCESS JOYSTICK VALUES
        filteredJoystickValues = self.filterJoysticks(joystickValues)
        
        # EMIT SIGNAL FOR FURTHER PROCESSING
        self.controllerValues.emit(filteredButtonStates, filteredJoystickValues)

    def exit(self):
        """
        PURPOSE

        Stops the timer.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.timer.stop()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Bahnschrift Light", 10))
    ex = VIEW()
    sys.exit(app.exec_())