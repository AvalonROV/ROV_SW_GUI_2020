# -*- coding: utf-8 -*-
"""@package AVALON ROV SERIAL
This software provides serial interface functionality for the ROV developed by team Avalon at The University of Sheffield. The software produces
serial commands that are sent to the ROV; these commands initiate tasks such as Thruster control or Sensor Readings. Additionally, it acts as a
library that the surface GUI can make calls to in order to communicate with the ROV and surface controls.

For more information about the Avalon ROV project please visit the website: https://avalonrov.wixsite.com/avalonrov

AUTHOR: Sam Maxwell
DATE CREATED: 30/10/2019
VERSION: N/A
VERSION DATE: N/A
"""
#-----------------------------------------------------------------------------------------------------------------------------------------------
#MODULES
#-----------------------------------------------------------------------------------------------------------------------------------------------
import numpy
import logger
import serial

#-----------------------------------------------------------------------------------------------------------------------------------------------
#DEFINITIONS
#-----------------------------------------------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------------------------------------------
#CLASSES
#-----------------------------------------------------------------------------------------------------------------------------------------------
class ROV():
    """CURRENTLY A MOCK CLASS!
    PURPOSE

    This class covers all communication with the ROV as a whole.
    """
    def __init__(self):
        """
        PURPOSE
        
        Class Constructor: Forms a new ROV class that can be used to communicate with the ROV. This constructor does not initialise communications
        with the ROV; call initialiseConnection() to begin communication.
        
        INPUT
        
        NONE
        
        RETURNS
        
        NONE
        """
        print("INITIALISING THE ROV CLASS")
        
        self.logFile = logger.LogFile("ROV Log File")        #Creating a new log file to record communications activity
    
    def findROVs(self, rovID):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Finds all available ROVs connected to the PC COM Ports.
        
        INPUT
        
        - rovID = The unique ID of the ROV to find.
        
        RETURNS
        
        NONE
        """
        print("FINDING ROV")
        
        comPorts = []
        for comPortIndex in range(0, numpy.random.randint(0, high = 11)):
            comPorts.append("COM{}".format(comPortIndex))
            
        return comPorts
        
    def initialiseConnection(self, rovID, portID, baudRate):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Initialises a connection to the ROV. Be aware that the connection is not constantly open. The connection is opened for each communication to the ROV.
        
        INPUT
            
        - rovID = The unique ID of the ROV to communicate with.
        - portID = The USB Port to communicate over.
        - baudRate = The rate of serial communications (bits per second) to use.
        
        RETURNS
        
        NONE
        """
        print('CONNECTING TO ROV')
    
    def disconnect(self):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Disconnects the surface computer from the ROV it is currently connected to.
        
        INPUT
        
        NONE
        
        RETURNS
        
        NONE
        """
        print("DISCONNECTED FROM ROV")
        
    def getSensors(self, sensorIDs):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Gets the current reading from each of the sensors specified in the identifier list.
        
        INPUT
        
        - sensorIDs = A list of identifiers for the sensors to retrieve a reading from.
        
        RETURNS
        
        - sensorVals = A numpy array containing the requested values from each of the sensors.
        """
        print('REQUESTING SENSOR VALUES')
        
        numSensors = len(sensorIDs)
        sensorVals = numpy.random.rand(numSensors)
        
        return sensorVals

    def setActuators(self, actuatorIDs, actuatorStates):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Sets the state of a set of actuators based upon the given IDs and States.
        
        INPUT
        
        - actuatorIDs = The unique identifiers of the actuators to set the state for.
        - actuatorStates = The state to set each actuator to.
        
        RETURNS
        
        NONE
        """
        print('SENDING ACTUATOR VALUES')

    def setJoystickVals(self, joystickVals):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Sets the current value of each of the Joystick axis and translates these values into Thruster values.
        
        INPUT
        
        - joystickVals = The current value of each of the Joystick Axes.
        
        RETURNS
        
        NONE
        """
        print('SENDING THRUSTER VALUES')

class Controller():
    """CURRENTLY A MOCK CLASS!
    PURPOSE
    
    Communicates with the main controller used to pilot the ROV.
    """
    def __init__(self):
        """
        PURPOSE
        
        Initialises a new controller class.
        """
        print("INITIALISING A CONTROLLER OBJECT")
    
    def initialiseConnection(self, portID):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Initialises communication with the controller used to pilot the ROV.
        
        INPUT
        
        - portID = The communication port the Joystick is connected to.
        
        RETURNS
        
        NONE
        """
        print('CONNECTING TO CONTROLLER')
    
    def disconnect(self):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Disconnects the surface PC from the Controller it is currently connected to.
        
        INPUT
        
        NONE
        
        RETURNS
        
        NONE
        """
        print("DISCONNECTING FROM THE CONTROLLER")
    
    def getJoystickVals(self):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Gets the current value of the controller joysticks.
        
        INPUT
        
        NONE
        
        RETURNS
        
        - joystickVals = The current value of each of the Joystick Axes.
        """
        print("GETTING JOYSTICK VALS")
        
        joystickVals = numpy.random.rand(4)
        
        return joystickVals

    def getButtonStates(self):
        """CURRENTLY A MOCK METHOD!
        PURPOSE
        
        Gets the current state of all of the buttons on the controller.
        
        INPUT
        
        NONE
        
        RETURNS
        
        - buttonStates = The current state of each of the buttons on the controller. The order for this will be specified at a later date.
        """
        print("GETTING BUTTON STATES")
        
        buttonStates = numpy.random.randint(0, high = 2, size = 10)
        
        return buttonStates

class SerialInterface():
    """
    PURPOSE
    
    Acts as a general serial interface for communicating with devices across USB.
    """
    #DEFINITIONS
    numRetries = 5      #! The number of times a communication will be retried.
    
    def __init__(self, port, baudRate = 115200, bytesize = serial.Serial.EIGHTBITS, parity = serial.Serial.PARITY_NONE, stopbits = serial.Serial.STOPBITS_ONE, timeout = 2.0):
        """
        PURPOSE
        
        Constructor for the Serial Interface class, generates a new Serial Interface for communication.
        """
        #Creating a new Serial Adapter
        self.serialAdapter = serial.Serial(port, baudrate = baudRate, bytesize = bytesize, parity = parity, stopbits = stopbits, timeout = timeout)
        
        #Attempting to open the Serial Port and Close it as a brief test
        try:
            self.serialAdapter.open()
            self.serialAdapter.close()
            
        except serial.SerialException:
            print("Could not open specified Serial Port {}, please ensure you have entered the port name correctly".format(port))
        
        #Saving the information for the port
        self.port = port
        self.baudRate = baudRate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
    
    def send(self, stringToSend):
        """
        PURPOSE
        
        Sends a string over the serial interface.
        
        INPUT
        
        stringToSend = The string to be sent across the serial interface.
        
        OUTPUT
        
        communicationSuccess (bool) = Checks whether the string was successfully sent over the interface.
        """
        #Completing the communication over the serial interface
        communicationSuccess = False
        
        try:
            #Attempting to send the string over the serial port
            for retryCount in range(1, self.numRetries + 1):
                self.serialAdapter.open()
                bytesWritten = self.serialAdapter.write(stringToSend)
                self.serialAdapter.close()
                
                #If the string was written successfully
                if bytesWritten > 0:
                    communicationSuccess = True
                    break
                
                #If the string was not written successfully
                else:
                    print("Could not write string successfully, retry count {}".format(retryCount))
            
            #If the communication failed
            if communicationSuccess == False:
                print("Count not write the string over the serial port")
            
        except serial.SerialException:
            print("Failed to complete Serial Communication with String: {}".format(stringToSend))
        
        return communicationSuccess
    
    def receive(self):
        """
        PURPOSE
        
        Receives a string from the serial interface.
        
        INPUT
        
        NONE
        
        OUTPUT
        
        receivedString (string) = The string that was recieved over the serial port.
        """
        #Completing the recieve over the serial port
        receivedString = ""
        
        try:
            #Attempting to receive the string
            for retryCount in range(1, self.numRetries + 1):
                self.serialAdapter.open()
                receivedString = self.serialAdapter.readline()
                self.serialAdapter.close()
                
                #If a string was received
                if len(receivedString) > 0:
                    break
                
                #If no string was received
                else:
                    print("Did not receive string, retry count {}".format(retryCount))
            
            #If no string was received
            if len(receivedString) == 0:
                print("Could not received string after {} retrys".format(self.numRetries))
        
        except serial.SerialException:
            print("Failed to complete Serial Receive")
    #Definitions
    RETRY_COUNT = 5        #The number of times a serial communication is retried before it is abandoned
    
    #Methods
    def __init__(self, port, baudRate = 115200, bytesize = serial.Serial.EIGHTBITS, parity = serial.Serial.PARITY_NONE, stopbits = serial.Serial.STOPBITS_ONE, timeout = 2.0):
        """
        PURPOSE
        
        Creates a new serial interface instance with the given paramters.
        
        INPUT
        
        - port = The communication port to send messages over
        - baudrate = The bit rate to send messages at (use as high as possible)
        - bytesize = The number of bits to use in a byte for each message
        - parity = Wether or not the serial communication uses a parity bit (advisable for more secure communications)
        - stopbits = An indication of how many stop bits the communication uses
        - timeout = The amount of time it takes for the serial communication to timeout
        """
        #Creating a new Serial Adapter
        self.serialAdapter = serial.Serial(port, baudrate = baudRate, bytesize = bytesize, parity = parity, stopbits = stopbits, timeout = timeout)
        
        #Attempting to open the Serial Port and Close it as a brief test
        try:
            self.serialAdapter.open()
            self.serialAdapter.close()
            
        except serial.SerialException:
            print("Could not open specified Serial Port {}, please ensure you have entered the port name correctly".format(port))
        
        #Saving the information for the port
        self.port = port
        self.baudRate = baudRate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        
        #Creating a new logging file for the serial interface and adding the information
        self.logFile = logger.LogFile("Serial Interface Log {}".format(self.port), fileFolder = "Log Files")
        self.logFile.addLogEntry("Port: {}".format(self.port))
        self.logFile.addLogEntry("Baud Rate: {}".format(self.baudRate))
        self.logFile.addLogEntry("Byte Size: {}".format(self.bytesize))
        self.logFile.addLogEntry("Parity: {}".format(self.parity))
        self.logFile.addLogEntry("Stopbits : {}".format(self.stopbits))
        self.logFile.addLogEntry("Timeout : {}".format(self.timeout))

    def send(self, commandToSend):
        """
        PURPOSE
        
        Writes a command to the device via the serial port.
        
        INPUT
        
        - commandToSend = The text of the command to be sent over the serial port.
        
        OUTPUT
        
        - Boolean that indicates if the communication completed successfully or not. True for successful, false for otherwise.
        """
        try:
            self.serialAdapter.open()       #Opening the serial port for communication
            self.serialAdapter.flush()      #Flushing the communication buffer of any prior messages that did not send
            
        except serial.SerialException:
            print("Failed to open serial port, ensure that the configuration is correct and the device is connected.")
            self.logFile.addLogEntry("Failed to open serial port")
            return False
            
        #Attempting the communication with the device, using the specified number of retries
        for numberOfRetrys in range(1, self.RETRY_COUNT + 2):
            try:
                commandToSend = commandToSend + "\n"        #Adding line ending characters to message
                self.serialAdapter.write(commandToSend)     #Sending message over the serial port
                return True
                
            except serial.SerialException:
                print("Failed to send command {}, retry number {}".format(commandToSend, numberOfRetrys))
                self.logFile.addLogEntry("Failed to send command {}, retry number {}".format(commandToSend, numberOfRetrys))
                
        #Communication has failed after retry's returning false to indicate failure and logging incident
        print("Communication failed after {} retrys on command {}".format(self.RETRY_COUNT, commandToSend))
        self.logFile.addLogEntry("Communication failed after {} retrys on command {}".format(self.RETRY_COUNT, commandToSend))
        return False
                
                
    def receive(self):
        """
        PURPOSE
        
        Receives a message from the device via the serial port.
        
        INPUT
        
        NONE
        
        OUTPUT
        
        The message sent by the device. Returns False if a failure occured.
        """
        try:
            self.serialAdapter.open()       #Opening the serial port for communication
            self.serialAdapter.flush()      #Flushing the communication buffer of any prior messages that did not send
            
        except serial.SerialException:
            print("Failed to open serial port, ensure that the configuration is correct and the device is connected.")
            self.logFile.addLogEntry("Failed to open serial port")
            return False
        
        try:
            messageFromDevice = self.serialAdapter.read_until(expected = "\n")
            return messageFromDevice
        
        except serial.SerialException:
            print("Failed to read message from device")
            self.logFile.addLogEntry("Failed to read message from device")
            return False
        
        return receivedString            
