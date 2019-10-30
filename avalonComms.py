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

class controller():
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