from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QLineEdit, QSpinBox, QFormLayout, QLabel, QSizePolicy, QComboBox, QCheckBox, QSpacerItem
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot, QTimer
from datetime import datetime

class KEYBINDINGS(QObject):
    """
    PURPOSE

    Contains all the functions to allow keybinding to be set for various ROV controls.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM
    getButtonStates = pyqtSignal()

    # DATABASE
    availableBindings = ['None','A','B','X','Y','LB','RB','SELECT','START','LS','RS','LEFT','RIGHT','DOWN','UP']
    bindings = []
    buttonStates = []

    def __init__(self, *, controlLayout = None, configLayout = None):
        """
        PURPOSE

        Class constructor.
        Calls setup function.

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
        if configLayout != None:
            self.setupConfigLayout()

    def setup(self):
        """
        PURPOSE

        Adds the default keybindings (non-configurable).

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.addBinding("Switch Orientation")
        self.addBinding("Change Sensitivity")
        self.addBinding("Yaw Right")
        self.addBinding("Yaw Left")
        self.addBinding("Yaw Sensitivity")

    def addBinding(self, label):
        """
        PURPOSE

        Adds a single keybinding to the program.

        INPUT

        - label = the name of the ROV control.

        RETURNS

        NONE
        """
        self.addConfigBinding(label)

    def removeBinding(self):
        """
        Removed a single keybinding from the program.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.removeConfigBinding()

    def reset(self):
        """
        PURPOSE

        Reset the keybinding layouts to their unconfigured state.

        INPUT

        NONE

        RETURNS

        NONE
        """
        quantity = self.configForm.rowCount()

        for i in range(quantity):
            self.removeConfigBinding()

        # RESET VARIABLES
        self.bindings = [] 

    #########################
    ### CONTROL PANEL TAB ###
    #########################
   
    #########################
    ### CONFIGURATION TAB ###
    #########################
    def setupConfigLayout(self):
        """
        PURPOSE

        Builds a layout on the configuation tab to add widgets to.

        INPUT

        NONE

        RETURNS

        NONE
        """
        parentLayout = QVBoxLayout()
        
        # LAYOUT TO SHOW EACH KEY BINDING
        self.configForm = QFormLayout()

        # SPACER TO PUSH ALL WIDGETS UP
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ADD CHILDREN TO PARENT LAYOUT
        parentLayout.addLayout(self.configForm)
        parentLayout.addItem(spacer)
        
        # ADD TO GUI
        self.configLayout.setLayout(parentLayout)
    
    def addConfigBinding(self, label = "Label"):
        """
        PURPOSE

        Adds a single keybinding configurator onto the configuration tab layout for a specific ROV control.

        INPUT

        label = the name of the ROV control.

        RETURNS

        NONE
        """
        bindingNumber = self.configForm.rowCount()

        # TRY TO SET KEYBDING FROM CONFIGURATION FILE
        try:
            binding = self.bindings[bindingNumber]

        # OTHERWISE, SET DEFAULT BINDING TO NONE
        except:
            binding = "None"
            self.bindings.append(binding)
        
        # CREATE WIDGETS
        keybindingLabel = QLabel(label)
        currentBinding = QComboBox()
        currentBinding.addItems(self.availableBindings)
        setBinding = QPushButton('Auto Binding')
        setBinding.setCheckable(True)
        
        # SET KEYBINDING
        bindingIndex = self.availableBindings.index(binding)
        currentBinding.setCurrentIndex(bindingIndex)
        
        # PLACE WIDGETS INSIDE LAYOUT
        layout1 = QVBoxLayout()
        layout1.addWidget(keybindingLabel)
        layout2 = QVBoxLayout()
        layout2.addWidget(currentBinding)
        layout2.addWidget(setBinding)
        
        # ADD LAYOUTS TO FRAMES (TO ALLOW STYLING)
        frame1 = QFrame()
        frame1.setObjectName("key-binding-frame")
        frame1.setLayout(layout1)
        frame2 = QFrame()
        frame2.setObjectName("settings-frame")
        frame2.setLayout(layout2)

        # ADD TO FORM LAYOUT
        self.configForm.addRow(frame1, frame2)
        
        # LINK WIDGETS
        currentBinding.activated.connect(lambda binding, index = bindingNumber: self.setKeyBindings(binding, index))
        setBinding.clicked.connect(lambda state, bindingIndex = bindingNumber: self.autoKeyBinding(bindingIndex))

    def removeConfigBinding(self):
        """
        PURPOSE

        Removes a single keybinding from the configuration tab layout.

        INPUT

        NONE

        RETURNS

        NONE
        """
        bindingNumber = self.configForm.rowCount() - 1
        
        # REMOVE ACTUATOR KEYBINDING FROM CONFIGURATION TAB
        self.configForm.removeRow(bindingNumber)

        # REMOVE KEYBINDING DATA
        del self.bindings[bindingNumber]

    def setKeyBindings(self, binding, index):
        """
        PURPOSE

        Sets the keybinding for a specific control on the ROV. 
        The keybinding can be selected from a menu, or detected by pressing a button on the controller.

        INPUT
         
        - binding = menu index selected.
        - index = the ROV control having its key binding changed.

        RETURNS 

        NONE
        """
        self.bindings[index] = self.availableBindings[binding]

        # UPDATE MENU (IF KEYBINDING IS SELECTED USING CONTROLLER)
        layout = self.configForm.itemAt((2 * index) + 1).widget()
        layout = layout.layout()
        widget = layout.itemAt(0).widget()
        widget.setCurrentIndex(binding)

        keyBinding = self.bindings[index]

        # PREVENT BINDING BEING ASSOCIATED WITH MULTIPLE CONTROLS
        for i, item in enumerate(self.bindings):
            # CHECK IF BINDING ALREADY EXISTS
            if i != index:
                if item == keyBinding and item != 'None':
                    # SET BINDING TO NONE
                    self.bindings[i] = 'None'
                    # FIND BINDING MENU WIDGET
                    layout = self.configForm.itemAt((2 * i) + 1).widget()
                    layout = layout.layout()
                    widget = layout.itemAt(0).widget()
                    # SET SELECTED MENU ITEM TO NONE
                    widget.setCurrentIndex(0)

    def autoKeyBinding(self, bindingIndex):
        """
        PURPOSE

        Initiates a timer that waits for a button to be pressed. 
        When a key binding has been found, the key binding is set.
        If no button is pressed within 3 seconds, the Timer will end and no changes will be made.

        INPUT

        - bindingIndex = the row on the form layout of the keybinding on being modified.

        RETURNS

        NONE
        """
        # DISABLE ALL AUTOBINDING BUTTONS UNTIL BINDING HAS BEEN FOUND
        self.enableAutoBindingButtons(False)
            
        # INITIATE WAIT FOR BUTTON TO BE PRESSED
        startTime = datetime.now()
        self.findKeyBinding(startTime, bindingIndex)

    def findKeyBinding(self, startTime, bindingIndex):
        """
        PURPOSE

        Looks at the button states in a seperate thread and detects which button has been pressed on the controller.

        INPUT

        - startTime = the system time when the search for a pressed button begins (used for a timeout).
        - bindingIndex = the row on the form layout of the keybinding on being modified.
        
        RETURNS

        NONE
        """
        self.timer = QTimer()
        self.timer.timeout.connect(lambda startTime = startTime, bindingIndex = bindingIndex: self.findKeyBinding(startTime, bindingIndex))
        self.timer.start(1000*1/60)
        
        # GET BUTTON STATES FROM MAIN PROGRAM
        self.getButtonStates.emit()

        # FIND WHICH BUTTON HAS BEEN PRESSED
        for i, state in enumerate(self.buttonStates):
            if state == 1:
                # INDEX OF KEYBINDING IN THE MENU
                keyBinding = i + 1
                # SET THE KEY BINDING
                self.setKeyBindings(keyBinding, bindingIndex)
                # RE-ENABLE AUTO-BINDING BUTTONS
                self.enableAutoBindingButtons(True)
                self.uncheckAutoBindingButtons()
                # STOP TIMER
                self.timer.stop()

        # 3 SECOND TIMEOUT
        elapsedTime = (datetime.now() - startTime).total_seconds()
        if elapsedTime > 3:
            # RE-ENABLE AUTO-BINDING BUTTONS
            self.enableAutoBindingButtons(True)
            self.uncheckAutoBindingButtons()
            self.timer.stop()

    def enableAutoBindingButtons(self, state):
        """
        PURPOSE

        Enables/disables all the 'Auto Binding' buttons so that only one binding is found at a time.

        INPUT

        - state = True to enable, False to disable.

        RETURNS

        NONE
        """
        for item in range(self.configForm.rowCount()):
            layout = self.configForm.itemAt((2 * item) + 1).widget()
            layout = layout.layout()
            widget = layout.itemAt(1).widget()
            widget.setEnabled(state)
        
    def uncheckAutoBindingButtons(self):
        """
        PURPOSE

        Checks/unchecks all the 'Auto Binding' buttons to show that the auto-binding process has finished.

        INPUT

        NONE

        RETURNS

        NONE
        """
        for item in range(self.configForm.rowCount()):
            layout = self.configForm.itemAt((2 * item) + 1).widget()
            layout = layout.layout()
            widget = layout.itemAt(1).widget()
            widget.setChecked(False)
