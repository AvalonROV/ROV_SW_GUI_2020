from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QFrame, QSpinBox, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot

class ACTUATORS(QObject):
    """
    PURPOSE

    Contains the functions to configure and control the ROVs actuators.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM
    addKeybinding = pyqtSignal(str)
    removeKeybinding = pyqtSignal()
    toggleActuatorSignal = pyqtSignal(list)

    # DATABASE
    quantity = 0
    labelList = []
    actuatorStates = []

    def __init__(self, *, controlLayout = None, configLayout = None, style = None):
        """
        PURPOSE

        Class constructor.
        Calls setup functions.

        INPUT

        - controlLayout = layout widget located on the control panel tab to add widgets to.
        - controlLayout = layout widget located on the configuration tab to add widgets to.
        - style = pointer to the style library to access stylesheets.

        RETURNS

        NONE
        """
        QObject.__init__(self)
        
        # CREATE THRUSTER WIDGETS ON THE CONTROL PANEL AND CONFIGURATION TABS
        self.controlLayout = controlLayout 
        self.configLayout = configLayout
        self.style = style

        # INITIAL LAYOUT SETUP
        if configLayout != None and controlLayout != None:
            self.setupConfigLayout()
            self.setupControlLayout()

    def setup(self):
        """
        PURPOSE

        Adds desired number of actuators to the GUI.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.actuatorNumber.setValue(self.quantity)

        for i in range(self.quantity):
            self.addActuator()

    def addActuator(self):
        """
        PURPOSE

        Adds a single actuator to the program.
        Emits a signal to add a keybinding to the main program using the keybinding module.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.addConfigActuator()
        self.addControlActuator()

        # CREATE KEYBINDING
        index = self.configForm.rowCount()
        label = "Actuator {}".format(index)
        self.addKeybinding.emit(label)

    def removeActuator(self):
        """
        Removes a single actuator from the program.
        Emits a signal to remove a keybinding from the main program using the keybinding module.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.removeConfigActuator()
        self.removeControlActuator()

        # REMOVE KEYBINDING
        self.removeKeybinding.emit()
        
    def reset(self):
        """
        PURPOSE

        Resets the actuator layouts to default configuration.

        INPUT 

        NONE

        RETURNS

        NONE
        """
        for i in range(self.quantity):
            self.removeActuator()

        self.actuatorNumber.setValue(0)
        
        # RESET VARIABLES
        self.quantity = 0
        self.labelList = []
        self.actuatorStates = []

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

    def addControlActuator(self):
        """
        PURPOSE

        Adds a single actuator to the control panel tab.

        INPUT

        NONE

        RETURNS

        NONE
        """   
        # THE INDEX OF THE NEXT ACTUATOR
        nextActuator = self.controlForm.rowCount()

        labels = self.labelList[nextActuator]

        # CREATE WIDGETS ON CONTROL PANEL TAB
        actuatorName = QLabel(labels[0])
        actuatorName.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
       
        actuatorToggle = QPushButton(labels[1])
        actuatorToggle.setObjectName("actuator-button")
        actuatorToggle.setCheckable(True)
        
        # ADD TO FORM LAYOUT
        self.controlForm.addRow(actuatorName, actuatorToggle)

        #actuatorName.setFixedHeight(int(actuatorName.sizeHint().height() * 1.5))
        #actuatorToggle.setFixedHeight(int(actuatorToggle.sizeHint().height() * 1.5))

        # LINK WIDGETS
        actuatorToggle.clicked.connect(lambda state, actuator = nextActuator: self.toggleActuator(actuator))

    def removeControlActuator(self):
        """
        PURPOSE

        Removes a single actuator from the control panel tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REMOVE ACTUATOR FROM CONTROL PANEL TAB
        actuatorNumber = self.controlForm.rowCount() - 1
        self.controlForm.removeRow(actuatorNumber)

    def updateActuatorLabels(self):
        """
        PURPOSE

        Updates the actuator name and button labels.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for i in range(self.quantity):
            # UPDATE ACTUATOR NAME
            nameWidget = self.controlForm.itemAt(2 * i).widget()
            nameWidget.setText(self.labelList[i][0])

            # UPDATE ACTUATOR STATE LABEL
            button = self.controlForm.itemAt((2 * i) + 1).widget()
            state = self.actuatorStates[i]
            button.setText(self.labelList[i][state + 1])

    def toggleActuator(self, actuator):
        """
        PURPOSE

        Sends commmand to ROV when an actuator has been toggled.

        INPUT

        - state = state of the button (True or False)
        - actuator = the actuator being toggled (0, 1, 2...).
        - buttonObject = pointer to the actuator button widget.

        RETURNS

        NONE
        """
        # CURRENT STATE
        state = self.actuatorStates[actuator]

        # FIND BUTTON WIDGET
        buttonWidget = self.controlForm.itemAt((actuator * 2) + 1).widget()

        if state:
            self.actuatorStates[actuator] = False
            buttonWidget.setChecked(False)
            buttonWidget.setText(self.labelList[actuator][1])

        else:
            self.actuatorStates[actuator] = True
            buttonWidget.setChecked(True)
            buttonWidget.setText(self.labelList[actuator][2])

        # SEND COMMAND TO ROV
        self.toggleActuatorSignal.emit(self.actuatorStates)
        
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
        
        # WIDGETS TO CHANGE ACTUATOR QUANTITY
        quantityLayout = QFormLayout()
        self.actuatorNumber = QSpinBox()
        self.actuatorNumber.setMaximum(10)
        quantityLayout.addRow(QLabel("Quantity"), self.actuatorNumber)

        # LAYOUT TO SHOW THRUSTER SETTINGS
        self.configForm = QFormLayout()

        # SPACER TO PUSH ALL WIDGETS UP
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ADD CHILDREN TO PARENT LAYOUT
        parentLayout.addLayout(quantityLayout)
        parentLayout.addLayout(self.configForm)
        parentLayout.addItem(spacer)
        
        # LINK WIDGETS
        self.actuatorNumber.editingFinished.connect(self.changeActuatorsNumber)
        
        # ADD TO GUI
        self.configLayout.setLayout(parentLayout)
    
    def changeActuatorsNumber(self):
        """
        PURPOSE

        Sets the number of actuators based on the user entered value in the configuration tab.

        INPUT

        NONE

        RETURN

        NONE
        """
        newNumber = self.actuatorNumber.value()
        oldNumber = self.configForm.rowCount()

        self.quantity = newNumber

        delta = newNumber - oldNumber

        # ADD ACTUATORS
        if delta > 0:
            for i in range(delta):
                self.addActuator()

        # REMOVE ACTUATORS
        if delta < 0:
            for i in range(-delta):
                self.removeActuator()

    def addConfigActuator(self):
        """
        PURPOSE

        Adds a single actuator to the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """   
        # THE INDEX OF THE NEXT ACTUATOR
        nextActuator = self.configForm.rowCount()

        # TRY TO SET LABELS FROM CONFIG FILE
        try:
            labels = self.labelList[nextActuator]

        # OTHERWISE, SET DEFAULT LABELS
        except:
            labels = []
            labels.append('Actuator {}'.format(nextActuator + 1))
            labels.append('OFF')
            labels.append('ON')
            self.labelList.append(labels)

        # STORE ACTUATOR STATE
        self.actuatorStates.append(False)

        # CREATE WIDGETS
        actuatorNumber = QLabel("Actuator {}".format(nextActuator + 1))
        actuatorNumber.setStyleSheet("font-weight: bold;")
        actuatorNumber.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label1 = QLabel('Actuator Name')
        actuatorLabel = QLineEdit(labels[0])
        state1 = QLineEdit(labels[1])
        label2 = QLabel('Default State')
        state2 = QLineEdit(labels[2])
        label3 = QLabel('Actuated State')
        
        # PLACE WIDGETS INSIDE LAYOUT
        layout1 = QVBoxLayout()
        layout1.addWidget(actuatorNumber)
        layout2 = QFormLayout()
        layout2.addRow(label1, actuatorLabel)
        layout2.addRow(label2, state1)
        layout2.addRow(label3, state2)

        # ADD LAYOUTS TO FRAMES (TO ALLOW STYLING)
        frame1 = QFrame()
        frame1.setObjectName("actuator-frame")
        frame1.setLayout(layout1)
        frame2 = QFrame()
        frame2.setObjectName("settings-frame")
        frame2.setLayout(layout2)

        # ADD TO FORM LAYOUT
        self.configForm.addRow(frame1, frame2)
        
        # LINK WIDGETS
        actuatorLabel.textChanged.connect(lambda text, actuator = nextActuator, label = 0: self.changeActuatorLabels(text, actuator, label))
        state1.textChanged.connect(lambda text, actuator = nextActuator, label = 1: self.changeActuatorLabels(text, actuator, label))
        state2.textChanged.connect(lambda text, actuator = nextActuator, label = 2: self.changeActuatorLabels(text, actuator, label))

    def removeConfigActuator(self):
        """
        PURPOSE

        Removes a single actuator from the configuration tab.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # REMOVE ACTUATOR FROM CONFIGURATION TAB
        actuatorNumber = self.configForm.rowCount() - 1
        self.configForm.removeRow(actuatorNumber) 

        # REMOVE ACTUATOR STATE DATA
        del self.labelList[actuatorNumber]
        del self.actuatorStates[actuatorNumber]

    def changeActuatorLabels(self, text, actuator, label):
        """
        PURPOSE

        Changes the name label and button text on the actuator buttons.

        INPUT

        - text = the text entered by the user.
        - actuator = the actuator being modified.
        - label = the label being modified (0 = name, 1 = default state, 2 = actuated state).

        RETURNS

        NONE
        """
        # STORE NEW LABEL
        self.labelList[actuator][label] = text

        # UPDATE LABELS ON CONTROL PANEL BUTTONS  
        self.updateActuatorLabels()