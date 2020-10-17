from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QFrame, QSlider, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot

class CONTROLLER_DISPLAY(QObject):
    """
    PURPOSE

    Contains functions to display the controller joystick values and button states on the GUI, and control the controllers sensitivity.
    """
    # DATABASE
    joystickLabels = ['Left X', 'Left Y','Triggers', 'Right Y', 'Right X']
    buttonLabels = ['A','B','X','Y','LB','RB','SELECT','START','LS','RS','LEFT','RIGHT','DOWN','UP']
    textBoxObjects = []
    joystickSensitivity = 2/3
    yawSensitivity = 2/3

    def __init__(self, *, controlLayout = None, configLayout = None):
        """
        PURPOSE

        Class constructor.

        INPUT

        - controlLayout = layout widget located on the control panel tab to add widgets to.
        - controlLayout = layout widget located on the configuration tab to add widgets to.

        RETURNS

        NONE
        """
        QObject.__init__(self)
        
        # CREATE THRUSTER WIDGETS ON THE CONTROL PANEL AND CONFIGURATION TABS
        if configLayout != None and controlLayout != None:
            self.controlLayout = controlLayout
            self.configLayout = configLayout

    def setup(self):
        """
        PURPOSE

        Builds layout and add required widgets to the control panel and configuration tab.
        Controller sensitivity sliders are added to the control panel tab.
        Controller value displays text boxes are added to the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # ADD WIDGETS TO LAYOUT
        self.setupConfigLayout()
        self.setupControlLayout()

    def reset(self):
        """
        PURPOSE

        Resets the controller layouts to default configuration.
        * No action currently required by this function *
        
        INPUT

        NONE

        RETURNS

        NONE
        """
        pass
        
    #########################
    ### CONTROL PANEL TAB ###
    #########################
    def setupControlLayout(self):
        """
        PURPOSE

        Builds a layout on the control panel to add widgets to.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CHECK IF TIMER WIDGET HAS ALREADY BEEN SETUP
        if self.controlLayout.layout() == None:

            parentLayout = QVBoxLayout()

            # CREATE WIDGETS FOR CONTROLLER AND YAW SENSITIVITY CONTROL
            joystickLayout = self.setupControllerSensitivity()
            yawLayout = self.setupYawSensitivity()

            # ADD TO PARENT LAYOUT
            parentLayout.addLayout(joystickLayout)
            parentLayout.addLayout(yawLayout)

            # ADD TO GUI
            self.controlLayout.setLayout(parentLayout)

    def setupControllerSensitivity(self):
        """
        PURPOSE

        INPUT

        RETURNS

        NON£
        """
        # JOYSTICK SENSITIVITY WIDGETS
        label1 = QLabel("Joystick")
        label1.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.joystickSlider =  QSlider(Qt.Horizontal)
        self.joystickSlider.setValue(2)
        self.joystickSlider.setMinimum(1)
        self.joystickSlider.setMaximum(3)
        self.joystickSlider.setPageStep(1)
        self.joystickLow = QLabel("LOW")
        self.joystickLow.setAlignment(Qt.AlignLeft)
        self.joystickLow.setEnabled(False)
        self.joystickLow.setObjectName("label-on-off")
        self.joystickNormal = QLabel("NORMAL")
        self.joystickNormal.setAlignment(Qt.AlignCenter)
        self.joystickNormal.setEnabled(True)
        self.joystickNormal.setObjectName("label-on-off")
        self.joystickHigh = QLabel("HIGH")
        self.joystickHigh.setAlignment(Qt.AlignRight)
        self.joystickHigh.setEnabled(False)
        self.joystickHigh.setObjectName("label-on-off")

        # BUILD LAYOUT
        joystickLayout = QHBoxLayout()
        joystickInnerLayout = QVBoxLayout()
        joystickLabelLayout = QHBoxLayout()
        joystickLabelLayout.addWidget(self.joystickLow)
        joystickLabelLayout.addWidget(self.joystickNormal)
        joystickLabelLayout.addWidget(self.joystickHigh)
        joystickInnerLayout.addWidget(self.joystickSlider)
        joystickInnerLayout.addLayout(joystickLabelLayout)
        joystickLayout.addWidget(label1, 2)
        joystickLayout.addLayout(joystickInnerLayout, 5)

        # LINK WIDGETS
        self.joystickSlider.valueChanged.connect(self.changeJoystickSensitivity)

        return joystickLayout
        
    def setupYawSensitivity(self):
        """
        PURPOSE

        INPUT

        RETURNS
        """
        # YAW SENSITIVITY WIDGETS
        label2 = QLabel("Yaw")
        label2.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.yawSlider =  QSlider(Qt.Horizontal)
        self.yawSlider.setValue(2)
        self.yawSlider.setMinimum(1)
        self.yawSlider.setMaximum(3)
        self.yawSlider.setPageStep(1)
        self.yawLow = QLabel("LOW")
        self.yawLow.setAlignment(Qt.AlignLeft)
        self.yawLow.setEnabled(False)
        self.yawLow.setObjectName("label-on-off")
        self.yawNormal = QLabel("NORMAL")
        self.yawNormal.setAlignment(Qt.AlignCenter)
        self.yawNormal.setEnabled(True)
        self.yawNormal.setObjectName("label-on-off")
        self.yawHigh = QLabel("HIGH")
        self.yawHigh.setAlignment(Qt.AlignRight)
        self.yawHigh.setEnabled(False)
        self.yawHigh.setObjectName("label-on-off")

        # BUILD LAYOUT
        yawLayout = QHBoxLayout()
        yawInnerLayout = QVBoxLayout()
        yawLabelLayout = QHBoxLayout()
        yawLabelLayout.addWidget(self.yawLow)
        yawLabelLayout.addWidget(self.yawNormal)
        yawLabelLayout.addWidget(self.yawHigh)
        yawInnerLayout.addWidget(self.yawSlider)
        yawInnerLayout.addLayout(yawLabelLayout)
        yawLayout.addWidget(label2, 2)
        yawLayout.addLayout(yawInnerLayout, 5)

        # LINK WIDGETS
        self.yawSlider.valueChanged.connect(self.changeYawSensitivity)

        return yawLayout

    def changeJoystickSensitivity(self, sensitivity):
        """
        PURPOSE

        Selects the desired controller throttle sensitivity to control the ROV.
        Pilot can select between LOW, NORMAL and HIGH.

        INPUT

        - sensitivity = desired sensitivity of the controller (0 = LOW, 1 = NORMAL, 2 = HIGH).

        RETURNS

        NONE
        """
        # SCALE 1 -> 3 slide value to 1/3 -> 3/3
        self.joystickSensitivity = sensitivity/3

        self.joystickSlider.setValue(sensitivity)

        labels = [self.joystickLow, self.joystickNormal, self.joystickHigh]

        # APPLY STYLING
        try:
            for i, label in enumerate(labels):
                if i + 1 == sensitivity:
                    label.setEnabled(True)
                else:
                    label.setEnabled(False)
        except:
            pass

    def changeYawSensitivity(self, sensitivity):
        """
        PURPOSE

        Selects the desired controller yaw button sensitivity to control the ROV.
        Pilot can select between LOW, NORMAL and HIGH.

        INPUT

        - sensitivity = desired sensitivity of yaw control (0 = LOW, 1 = NORMAL, 2 = HIGH).

        RETURNS

        NONE
        """
        # SCALE 1 -> 3 slide value to 1/3 -> 3/3
        self.yawSensitivity = sensitivity/3

        self.yawSlider.setValue(sensitivity)

        labels = [self.yawLow, self.yawNormal, self.yawHigh]

        # APPLY STYLING
        try:
            for i, label in enumerate(labels):
                if i + 1 == sensitivity:
                    label.setEnabled(True)
                else:
                    label.setEnabled(False)
        except:
            pass

    #########################
    ### CONFIGURATION TAB ###
    #########################
    def setupConfigLayout(self):
        """
        PURPOSE

        Creates a series of text box's to display the values of the controller buttons/joysticks.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CHECK IF TIMER WIDGET HAS ALREADY BEEN SETUP
        if self.configLayout.layout() == None:
            parentLayout = QFormLayout()

            # CREATE DISPLAY FOR JOYSTICKS
            for index in range(5):
                # CREATE JOYSTICK LABEL
                label = QLabel(self.joystickLabels[index])
                label.setStyleSheet("font-weight: bold;")
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                # CREATE TEXT BOX TO DISPLAY VALUE
                value = QLineEdit()
                value.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                value.setReadOnly(True)

                # ADD POINTER FOR THE QLINEEDIT INTO AN ARRAY FOR LATER ACCESS
                self.textBoxObjects.append(value)

                # ADD TO FORM LAYOUT
                parentLayout.addRow(label, value)

            # CREATE DISPLAY FOR BUTTONS
            for index in range(14):
                # CREATE BUTTON LABEL
                label = QLabel(self.buttonLabels[index])
                label.setStyleSheet("font-weight: bold;")
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                # CREATE TEXT BOX TO DISPLAY VALUE
                value = QLineEdit()
                value.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                value.setReadOnly(True)

                # ADD POINTER FOR THE QLINEEDIT INTO AN ARRAY FOR LATER ACCESS
                self.textBoxObjects.append(value)

                # ADD TO FORM LAYOUT
                parentLayout.addRow(label, value)

            # ADD TO GUI
            self.configLayout.setLayout(parentLayout)

    def updateDisplay(self, buttonStates, joystickValues):
        """
        PURPOSE

        Updates the text fields on the configuration tab with the latest controller button states and joystick values.

        INPUT

        - buttonStates = an array containing the states of all the controller buttons (0 or 1).
        - joystickValues = an array containing the values of all the joysticks (-1 -> 1).

        RETURNS
        
        NONE
        """
        # DISPLAY JOYSTICK VALUES
        for i, joystick in enumerate(joystickValues):
            self.textBoxObjects[i].setText(str(joystick))

        # TEXT BOX STARTING INDEX FOR BUTTON STATES
        pos = len(joystickValues)        
        
        print(buttonStates)
        # DISLAY BUTTON VALUES
        for i, button in enumerate(buttonStates):
            try:
                self.textBoxObjects[i + pos].setText(str(button))
            except:
                pass





        
        

    