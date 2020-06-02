import serial
from datetime import datetime

from PyQt5.QtCore import pyqtSignal, QObject

class ROV_SERIAL(QObject):
    """
    PURPOSE

    A serial communication interface to send commands and receive data from the ROV.
    """
    # SIGNAL EMITTED TO UI FUNCTION WHEN THERE IS A COMMS FAIL EVENT
    uiSerialFunction = pyqtSignal(str)

    # DATABASE
    rovID = "AVALONROV"
    rovComPort = None
    comms = None
    commsStatus = False

    def __init__(self):
        """
        PURPOSE

        Class constructor.

        INPUT

        NONE

        RETURNS

        NONE
        """
        QObject.__init__(self)

    def findComPorts(self, menuObject, baudRate, rovIdentity):
        """
        PURPOSE

        Find all available COM ports and adds them to drop down menu.

        INPUT

        - menuObject = pointer to the drop down menu to display the available COM ports.
        - baudRate = baud rate of the serial interface.
        - rovIdentity = string containing the required device identity to connect to the ROV.

        RETURNS

        - availableComPorts = list of all the available COM ports.
        - rovComPort = the COM port that belongs to the ROV.
        - identity = the devices response from an identity request.
        """
        # DISCONNECTED FROM CURRENT COM PORT IF ALREADY CONNECTED
        if self.commsStatus == True:
            self.rovConnect()

        # CREATE LIST OF ALL POSSIBLE COM PORTS
        ports = ['COM%s' % (i + 1) for i in range(256)] 

        # CLEAR CURRENT MENU LIST
        menuObject.clear()
        menuObject.addItem("None")

        identity = ""
        rovComPort = None
        availableComPorts = []
        
        # CHECK WHICH COM PORTS ARE AVAILABLE
        for port in ports:
            try:
                comms = serial.Serial(port, baudRate, timeout = 1)
                
                # ADD AVAILABLE COM PORT TO MENU LIST
                availableComPorts.append(port)
                menuObject.addItem(port)
                
                # REQUEST IDENTITY FROM COM PORT
                self.commsStatus = True
                identity = self.getIdentity(comms, rovIdentity)
                comms.close()
                self.commsStatus = False
                
                # FIND WHICH COM PORT IS THE ROV
                if identity == rovIdentity:
                    rovComPort = port
                    menuIndex = availableComPorts.index(rovComPort) + 1
                    menuObject.setCurrentIndex(menuIndex)
                    break
                    
            # SKIP COM PORT IF UNAVAILABLE
            except (OSError, serial.SerialException):
                pass

        return availableComPorts, rovComPort, identity

    def getIdentity(self, serialInterface, identity):
        """
        PURPOSE

        Request identity from a defined COM port.

        INPUT

        - serialInterface = pointer to the serial interface object.
        - identity = the desired identity response from the device connected to the COM port.

        RETURNS

        - identity = the devices response.
        """
        identity = ""
        startTime = datetime.now()
        elapsedTime = 0
        # REPEATIDELY REQUEST IDENTIFICATION FROM DEVICE FOR UP TO 3 SECONDS
        while (identity == "") and (elapsedTime < 3):
            self.serialSend("?I", serialInterface)
            identity = self.serialReceive(serialInterface)
            elapsedTime = (datetime.now() - startTime).total_seconds()

        return identity

    def serialConnect(self, rovComPort, baudRate):
        """
        PURPOSE

        Attempts to initialise a serial communication interface with a desired COM port.

        INPUT

        - rovComPort = the COM port of the ROV.
        - baudRate = the baud rate of the serial interface.

        RETURNS

        NONE
        """
        self.commsStatus = False
        if rovComPort != None:
            try:
                self.comms = serial.Serial(rovComPort, baudRate, timeout = 1)
                message = "Connection to ROV successful."
                self.commsStatus = True
            except:
                message = "Failed to connect to {}.".format(rovComPort)
        else:
            message = "Failed to recognise device identity."

        return self.commsStatus, message

    def serialSend(self, command, serialInterface):
        """
        PURPOSE

        Sends a string down the serial interface to the ROV.

        INPUT

        - command = the command to send.
        - serialInterface = pointer to the serial interface object.

        RETURNS

        NONE
        """
        if self.commsStatus:
            try:
                serialInterface.write((command + '\n').encode('ascii'))
            except:
                message = "Failed to send command."
                self.uiSerialFunction.emit(message)

    def serialReceive(self, serialInterface):
        """
        PURPOSE

        Waits for data until a newline character is received.

        INPUT

        - serialInterface = pointer to the serial interface object.

        RETURNS

        NONE
        """
        received = ""
        try:
            received = serialInterface.readline().decode('ascii').strip()
        except:
            message = "Failed to receive data."
            self.uiSerialFunction.emit(message)
            
        return(received)

    def armThrusters(self):
        """
        PURPOSE

        Sends command to ROV to arm the thruster ESCs.

        INPUT

        NONE

        RETURN

        NONE
        """
        # COMMAND INITIALISATION  
        transmitArmThrusters = '?RX'
        self.serialSend(transmitArmThrusters, self.comms)

    def setThrusters(self, thrusterSpeeds):
        """
        PURPOSE

        Generates command to send to ROV with the desired thruster speeds.

        INPUT

        - thrusterSpeeds = array containing the desired speed of each thruster.

        RETURNS

        NONE
        """
        # COMMAND INITIALISATION  
        transmitThrusterSpeeds = '?RT'
        # ADD ACTUATOR STATES ONTO THE END OF STRING
        for speed in thrusterSpeeds:
            # CONVERT TO 'xxx' format (PAD EMPTY SPACES WITH ZEROS)
            transmitThrusterSpeeds += ('{0:03d}'.format(speed))

        self.serialSend(transmitThrusterSpeeds, self.comms)

    def setActuators(self, actuatorStates):
        """
        PURPOSE

        Generates command to send to ROV with the desired actuator states.

        INPUT

        - actuatorStates = array containing the desired state of each actuator.

        RETURNS

        NONE
        """
        # COMMAND INITIALISATION  
        transmitActuatorStates = '?RA'
        # ADD ACTUATOR STATES ONTO THE END OF STRING
        for state in actuatorStates:
            # CONVERT TRUE/FALSE TO '1'/'0'
            transmitActuatorStates += ('1' if state == True else '0')
        self.serialSend(transmitActuatorStates, self.comms)

    def getSensors(self):
        """
        PURPOSE

        Send request to ROV to get sensor readings and return them.
        
        INPUT

        NONE

        RETURNS

        - results = array containing the sensor readings.
        """
        # REQUEST SENSOR READINGS
        command = "?RS"
        self.serialSend(command, self.comms)
        # READ RESPONSE INTO AN ARRAY
        results = self.serialReceive(self.comms).split(",")

        return results
