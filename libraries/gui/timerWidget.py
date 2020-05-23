from PyQt5.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QSizePolicy, QLCDNumber
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

from datetime import datetime
from threading import Timer
class TIMER(QVBoxLayout):
    """
    PURPOSE

    Contains the function to operate the competition timer.
    """
    # SIGNALS TO CALL FUNCTIONS IN MAIN PROGRAM

    # DATABASE
    timerEnabled = False 
    startTime = 0            
    timerNew = True                  
    timerMemory = 0

    def __init__(self, *, style = None):
        """
        PURPOSE

        Class constructor.
        Calls setup function.

        INPUT

        - style = pointer to the style library to access stylesheets.

        RETURNS

        NONE
        """
        self.style = style

        QWidget.__init__(self)

    def setup(self):
        """
        PURPOSE

        Builds a layout and add widgets for the timer on the control panel tab.

        INPUT
        
        NONE

        RETURNS

        NONE
        """
        # CREATE WIDGETS
        self.time = QLCDNumber()
        self.time.setSegmentStyle(QLCDNumber.Flat)
        self.time.setNumDigits(11)
        self.time.display('00:00:00:00')
        self.time.setMinimumHeight(48)
        
        buttonLayout = QHBoxLayout()
        self.startButton = QPushButton('Start')
        self.startButton.setCheckable(True)
        self.resetButton = QPushButton('Reset')
        buttonLayout.addWidget(self.startButton)
        buttonLayout.addWidget(self.resetButton)
        
        try:
            self.startButton.setStyleSheet(self.style.timerStartButton)
            self.time.setStyleSheet(self.style.timerLCD)
        except:
            pass

        # LINK WIDGETS
        self.startButton.clicked.connect(self.timerToggle)
        self.resetButton.clicked.connect(self.timerReset)

        # ADD TO PARENT LAYOUT
        self.addWidget(self.time)
        self.addLayout(buttonLayout)

    def timerStart(self):
        """
        PURPOSE

        Reads the system time in a new thread and calculates the number of seconds elapsed since the timer was started.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CALCULATE SECONDS ELAPSED SINCE TIMER STARTED 
        currentTime = datetime.now()
        self.currentSeconds = (currentTime - self.startTime).total_seconds() + self.timerMemory
        
        # UPDATE TIMER WIDGET
        self.updateTimer(self.currentSeconds)
    
        # READ SYSTEM TIME EVERY 0.5 SECONDS
        self.thread = Timer(0.5,self.timerStart)
        self.thread.daemon = True                            
        self.thread.start()

    def timerStop(self):
        """
        PURPOSE

        Stops the timer.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.thread.cancel()

        # SAVE STOP TIME
        self.timerMemory = self.currentSeconds

    def timerToggle(self, state):
        """
        PURPOSE

        Starts/Stops the timer.

        INPUT

        - state = state of the button (True or False)

        RETURNS

        NONE
        """
        # START TIMER
        if state:
            self.startButton.setText('Stop')
            self.startTime = datetime.now()
            self.timerStart()
        
        # STOP TIMER
        else:
            self.startButton.setText('Start')
            self.timerStop()
           
    def timerReset(self):
        """
        PURPOSE

        Resets the timer back to zero if the timer is stopped.

        INPUT

        NONE

        RETURNS

        NONE
        """
        if not self.startButton.isChecked():
            self.timerMemory = 0
            self.updateTimer(0)

    def updateTimer(self, currentSeconds):
        """
        PURPOSE

        Converts seconds into DD:HH:MM:SS format and updates the timer widget on the GUI.

        INPUT

        - currentSeconds = the number of seconds since the timer was started.

        RETURNS

        NONE
        """
        # CONVERT SECONDS TO DD:HH:MM:SS
        minutes, seconds = divmod(currentSeconds,60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        # DISPLAY TIME SINCE MEASUREMENT START
        self.time.display('%02d:%02d:%02d:%02d' % (days, hours, minutes, seconds))