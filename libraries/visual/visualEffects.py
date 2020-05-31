from PyQt5.QtWidgets import QFrame, QGridLayout, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QPalette

class STYLE():
    """
    PURPOSE

    Contains a library of stylesheets and functions to modify the style of the program.
    """
    # VARIABLES
    theme = True

    # STYLESHEETS
    blueButtonLarge = ""
    blueButtonSmall = ""
    actuatorButton = ""
    orientationButton = ""
    deleteButton = ""
    scrollArea = ""
    comboBox = ""
    timerLCD = ""
    timerStartButton = ""
    programExit = ""
    groupBox = ""
    greenText = ""
    redText = ""
    disabledText = ""
    settingsFrame = ""
    thrusterFrame = ""
    actuatorFrame = ""
    digitalCameraFrame = ""
    keybindingFrame = ""
    infoLabel = ""

    def __init__(self):
        """
        PURPOSE

        Class constructor

        INPUT

        NONE

        RETURNS

        NONE
        """
        pass

    def setPalette(self, theme, appObject):
        """
        PURPOSE

        Sets the base palette for the program, which defines the default window colour, button colour, text box colour etc.

        INPUT

        - theme = True for DARK, False for LIGHT.
        - appObject = pointer to the QApplication object to apply the palette to.

        RETURNS

        NONE
        """
        # DARK THEME
        if theme:
            # CREATE QPALETTE
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor("#161616"))        # MAIN WINDOW BACKGROUND COLOR
            palette.setColor(QPalette.WindowText, QColor("#fafafa"))    # TEXT COLOR
            palette.setColor(QPalette.Base,QColor("#343434"))           # TEXT ENTRY BACKGROUND COLOR
            palette.setColor(QPalette.Text,QColor("#fafafa"))           # TEXT ENTRY COLOR
            palette.setColor(QPalette.Button,QColor("#353535"))         # BUTTON COLOR
            palette.setColor(QPalette.ButtonText,QColor("#fafafa"))     # BUTTON TEXT COLOR  

        # LIGHT THEME
        else:
            # CREATE QPALETTE
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor("#e8e8e8"))        # MAIN WINDOW BACKGROUND COLOR
            palette.setColor(QPalette.WindowText, QColor("#212121"))    # TEXT COLOR
            palette.setColor(QPalette.Base,QColor("#343434"))           # TEXT ENTRY BACKGROUND COLOR
            palette.setColor(QPalette.Text,QColor("#212121"))           # TEXT ENTRY COLOR
            palette.setColor(QPalette.Button,QColor("#eeeeee"))         # BUTTON COLOR
            palette.setColor(QPalette.ButtonText,QColor("#fafafa"))     # BUTTON TEXT COLOR 

            # CREATE QPALETTE
            #palette = appObject.style().standardPalette()

        # APPLY CUSTOM COLOR PALETTE
        appObject.setPalette(palette)

    def setStyleSheets(self, theme):
        """
        PURPOSE

        Sets the widget stylesheets for either the light or dark theme.

        INPUT

        - theme = True = dark theme, False = light theme.

        RETURNS

        NONE
        """
        # DARK THEME
        if theme:

            #########################
            ######## WIDGETS ########
            #########################
            self.normalButton = ("QPushButton {background-color: #424242; color: white; border-radius: 15px; padding: 5px 20px}" 
                                "QPushButton:hover {background-color: #393939;}"
                                "QPushButton:pressed {background-color: #1976d2;}"
                                "QPushButton:checked {background-color: #1976d2;}"
                                "QPushButton:checked:hover {background-color: #115293}")

            self.largeButton = ("#large-button {background-color: #424242; color: white; border-radius: 25px;}" 
                                "#large-button:hover {background-color: #393939;}"
                                "#large-button:pressed {background-color: #1976d2;}"
                                "#large-button:checked {background-color: #1976d2;}"
                                "#large-button:checked:hover {background-color: #115293}")
            
            self.actuatorButton = ("#actuator-button {background-color: #43a047; font-size: 20px; font-weight: bold; color: white; border-radius: 25px}" 
                                    "#actuator-button:hover {background-color: #388e3c}"
                                    "#actuator-button:checked {background-color: #c62828;}"
                                    "#actuator-button:checked:hover {background-color: #b71c1c}")

            self.orientationButton = ("#change-orientation-button {background-color: #424242; border-radius: 25px;}")

            self.timerStartButton = ("#timer-start-button {background-color: #43a047; color: white;}"
                                    "#timer-start-button:hover {background-color: #388e3c;}" 
                                    "#timer-start-button:checked {background-color: #c62828; color: white;}"
                                    "#timer-start-button:checked:hover {background-color: #b71c1c;}")

            self.renameButton = ("#rename-button {background-color: #43a047;}"
                                    "#rename-button:hover {background-color: #388e3c}")

            self.deleteButton = ("#delete-button {background-color: #c62828;}"
                                    "#delete-button:hover {background-color: #b71c1c}")

            self.programExitButton = ("#program-exit-button {background-color: #c62828; color: white; border-radius: 15px; padding: 5px 20px}" 
                                "#program-exit-button:hover {background-color: #b71c1c}")

            self.timerLCD = ("#timer-lcd {border: 0px;}")

            #########################
            ######## LAYOUTS ########
            #########################
            self.scrollArea = ("QScrollArea {background: transparent;}"
                                "QScrollArea > QWidget > QWidget {background: transparent;}"
                                "QScrollArea > QWidget > QScrollBar {background: 0}"
                                "QScrollBar {width: 16px; border-radius: 8px;}"
                                "QScrollBar:handle {background-color: #424242; min-height: 5px; border-radius: 8px;}"
                                "QScrollBar:handle:hover {background-color: #393939;}"
                                "QScrollBar:sub-line  {background-image: none;}"
                                "QScrollBar:add-line  {background-image: none;}")

            self.comboBox = ("QComboBox {background-color: #363636; border-radius: 15px; padding: 5px 20px 5px 10px;}"
                                "QComboBox:hover {background-color: #333333;}"
                                "QComboBox:down-arrow {image: url(./graphics/arrow_down_white.png); height: 30px; width: 30px; padding-right: 20px;}"
                                "QComboBox:drop-down {border: 0px;}")
          
            self.groupBox = ("QGroupBox {background-color: #212121; border-radius: 20px; font-size: 12pt; margin-top: 1.2em; padding: 10px}")
           
            #########################
            ### CONFIG TAB FRAMES ###
            #########################
            self.settingsFrame = ("#settings-frame {background-color: #282828; border-radius: 20px;}")
            self.thrusterFrame = ("#thruster-frame {background-color: #01579B; border-radius: 20px;}")
            self.actuatorFrame = ("#actuator-frame {background-color: #004D40; border-radius: 20px;}")
            self.digitalCameraFrame = ("#digital-camera-frame {background-color: #37474f; border-radius: 20px;}")
            self.keybindingFrame = ("#key-binding-frame {background-color: #d32f2f; border-radius: 20px;}")

            #########################
            ######### TEXT ##########
            #########################
            self.labelOnOff = ("#label-on-off:enabled {color: #679e37;}"
                                "#label-on-off:disabled {}")
            
            self.infoLabel = ("#info-label {color: rgba(255, 255, 255, 0.7)}")
            
        # LIGHT THEME
        else:
            
            self.blueButtonLarge = ("QPushButton {background-color: #eeeeee; color: white; border-radius: 25px;}" 
                                "QPushButton:hover {background-color: #393939;}"
                                "QPushButton:pressed {background-color: #1976d2;}"
                                "QPushButton:checked {background-color: #1976d2;}"
                                "QPushButton:checked:hover {background-color: #115293}")

            self.blueButtonSmall = ("QPushButton {background-color: #EEEEEE; color: black; border-radius: 15px; border: 2px solid #1976d2; padding: 5px 20px}" 
                                "QPushButton:hover {background-color: #393939;}"
                                "QPushButton:pressed {background-color: #1976d2;}"
                                "QPushButton:checked {background-color: #1976d2;}"
                                "QPushButton:checked:hover {background-color: #115293}")
            
            self.actuatorButton = ("QPushButton {background-color: #43a047; font-size: 20px; font-weight: bold; color: white; border-radius: 25px}" 
                                    "QPushButton:hover {background-color: #388e3c}"
                                    "QPushButton:checked {background-color: #c62828;}"
                                    "QPushButton:checked:hover {background-color: #b71c1c}")

            self.orientationButton = ("QPushButton {background-color: #424242; border-radius: 25px;}")

            self.renameButton = ("QPushButton {background-color: #43a047;}"
                                    "QPushButton:hover {background-color: #388e3c}")

            self.deleteButton = ("QPushButton {background-color: #c62828;}"
                                    "QPushButton:hover {background-color: #b71c1c}")

            self.scrollArea = ("QScrollArea {background: transparent;}"
                                "QScrollArea > QWidget > QWidget {background: transparent;}"
                                "QScrollArea > QWidget > QScrollBar {background: 0}"
                                "QScrollBar {width: 16px; border-radius: 8px;}"
                                "QScrollBar:handle {background-color: #424242; min-height: 5px; border-radius: 8px;}"
                                "QScrollBar:handle:hover {background-color: #393939;}"
                                "QScrollBar:sub-line  {background-image: none;}"
                                "QScrollBar:add-line  {background-image: none;}")

            self.comboBox = ("QComboBox {background-color: #9e9e9e; border-radius: 15px; padding: 5px 20px 5px 10px;}"
                                "QComboBox:hover {background-color: #333333;}"
                                "QComboBox:down-arrow {image: url(./graphics/arrow_down_white.png); height: 30px; width: 30px; padding-right: 20px;}"
                                "QComboBox:drop-down {border: 0px;}")

            self.timerLCD = ("QLCDNumber {border: 0px;}")
            
            self.timerStartButton = ("QPushButton {background-color: #43a047; color: white;}"
                                    "QPushButton:hover {background-color: #388e3c;}" 
                                    "QPushButton:checked {background-color: #c62828; color: white;}"
                                    "QPushButton:checked:hover {background-color: #b71c1c;}")

            self.programExit = ("QPushButton {background-color: #c62828; color: white; border-radius: 15px; padding: 5px 20px}" 
                                "QPushButton:hover {background-color: #b71c1c}")
                                
            self.groupBox = ("""QGroupBox {background-color: #f5f5f5;
                                            border-radius: 20px;
                                            font-size: 12pt;
                                            margin-top: 1.2em;
                                            padding: 10px}""")

            #########################
            ######### TEXT ##########
            #########################
            self.labelOnOff = ("#label-on-off {color: #679e37;}"
                                "#label-on-off {color: red;}")
            

            self.greenText = "color: #679e37"
            self.redText = 'color: #c62828'
            self.disabledText = 'color: rgba(0,0,0,40%);'
            self.settingsFrame = "QFrame {background-color: #282828; border-radius: 20px;}"
            self.thrusterFrame = "QFrame {background-color: #01579B; border-radius: 20px;}"
            self.actuatorFrame = "QFrame {background-color: #004D40; border-radius: 20px;}"
            self.digitalCameraFrame = "QFrame {background-color: #37474f; border-radius: 20px;}"
            self.keybindingFrame = "QFrame {background-color: #d32f2f; border-radius: 20px;}"
            self.infoLabel = "color: rgba(255, 255, 255, 0.7)"

    def setColouredFrame(self, labelFrame, settingsFrame, labelStyleSheet, settingsStyleSheet):  
        """
        PURPOSE

        Applies a coloured frame around a group of widgets on the configuration tab to make it easier to read.

        INPUT

        - labelFrame = pointer to frame containing the label.
        - settingsFrame = pointer to the frame containing the configuration widgets.
        - labelStyleSheet = the style sheet to apply to the settings frame.
        - settingsStyleSheet = the style sheet to apply to the settings frame.

        RETURNS

        - labelFrame = the label with a frame applied.
        - layoutFrame = the group of widgets with a frame applied.
        """
        labelFrame.setStyleSheet(labelStyleSheet)
        settingsFrame.setStyleSheet(settingsStyleSheet)

        return labelFrame, settingsFrame

    def applyGlow(self, widget, color, blurRadius):
        """
        PURPOSE

        Applies a coloured underglow effect to a widget.

        INPUT

        - widget = pointer to the widget to apply the glow to.
        - color = color to apply to the glow (HEX format)
        - blueRadius = radius of the glow.

        RETURNS

        NONE
        """
        shadowEffect = QGraphicsDropShadowEffect()
        shadowEffect.setBlurRadius(blurRadius)
        shadowEffect.setColor(QColor(color))
        shadowEffect.setXOffset(0)
        shadowEffect.setYOffset(0)
        # APPLY GLOW TO WIDGET
        widget.setGraphicsEffect(shadowEffect)