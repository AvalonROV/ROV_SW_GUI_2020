from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread, QTimer, QSize, Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimeLine
from PyQt5.QtWidgets import (QGroupBox, QWidget, QStyleFactory, QMainWindow, QApplication, QComboBox, 
                            QRadioButton, QVBoxLayout, QFormLayout, QGridLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSizePolicy, QDesktopWidget, 
                            QFileDialog, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QPixmap, QImage, QResizeEvent, QIcon, QImage, QFont, QColor, QPalette, QPainter

class CONTROLLER_UPDATE(QThread):

    sensorReading = pyqtSignal(list)

    def __init__(self, controllerNumber):
        QThread.__init__(self)
        self.controllerNumber = controllerNumber
        # UPDATE CONTROLLER VALUES AT A RATE OF 60FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self.run)
        self.timer.start(1000)

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
        
        # ADD DEADZONE OF 0.1
        filteredJoystickValues = [0 if (number < 0.1 and number > -0.1) 
                                    else number 
                                    for number in filteredJoystickValues]
        # ROUND TO 1 DECIMAL PLACE
        filteredJoystickValues = [round(number, 1) for number in filteredJoystickValues]

        return(filteredJoystickValues)

    def run(self):
        # TAKE SINGLE READING OF CONTROLLER VALUES
        buttonStates, arrowStates, joystickValues = self.getControllerInputs(self.controllerNumber)
        # PROCESS BUTTON STATES
        filteredButtonStates = self.filterButtons(buttonStates, arrowStates)
        # PROCESS JOYSTICK VALUES
        filteredJoystickValues = self.filterJoysticks(joystickValues)
        # SHOW NEW CONTROLLER VALUES ON GUI
        self.controllerValues.emit(filteredButtonStates, filteredJoystickValues)

    def exit(self):