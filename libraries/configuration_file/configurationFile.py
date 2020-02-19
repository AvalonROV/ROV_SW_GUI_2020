from xml.etree.ElementTree import parse, Element, SubElement, ElementTree

class READ_CONFIG_FILE():
    """
    PURPOSE

    Extracts all the ROV control programs configuration settings from an XML file.
    """
    def __init__(self, fileName):
        """
        PURPOSE

        Constructor which defines the default directory for the config file.
        Calls the parseFile function to get the xml files root.

        INPUT

        - fileName = default directory of the config file.

        RETURNS

        NONE
        """
        self.fileName = fileName
        self.root = None
        self.children = None
        self.parseFile()

    def parseFile(self):
        """
        PURPOSE

        Read the xml configuration file at the desired directory at read the root.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # TRY TO FIND THE FILE SPECIFIED
        try:
            configFile = parse(self.fileName)
            configFileStatus = True
        except:
            configFileStatus = False

        # IF CONFIGURATION FILE IS FOUND
        if configFileStatus == True:
            self.root = configFile.getroot()

        return configFileStatus

    def readTheme(self):
        """
        PURPOSE

        Read the theme settings from the configuration file.

        INPUT

        NONE

        RETURNS

        - theme = True for dark theme, False for light theme.
        """
        try:
            child = self.root.find('theme')
            theme = True if child.text == "dark" else False
            return theme
        
        except:
            pass

    def readThruster(self):
        """
        PURPOSE

        Read the position and reverse settings for the thrusters.

        INPUT

        NONE

        RETURNS

        - thrusterPositionList = array containing the position of each thruster on the ROV.
        - thrusterReverseList = array containing the reverse state of each thruster.
        """
        try:
            child = self.root.find('thrusters')

            thrusterPositionList = []
            thrusterReverseList = []

            for thruster in child:
                thrusterPosition = thruster.find("location").text
                thrusterReverse = (True if thruster.find("reversed").text == 'True' else False)

                thrusterPositionList.append(thrusterPosition)
                thrusterReverseList.append(thrusterReverse)

            return thrusterPositionList, thrusterReverseList
             
        except:
            pass

    def readActuator(self):
        """
        PURPOSE

        Read the number of actuators and their label settings.

        INPUT

        NONE

        RETURNS

        - actuatorNumber = the number of actuators.
        - actuatorLabelList = array containing the labels of the actuator name, default state and actuated state.
        """
        try:
            child = self.root.find('actuators')

            actuatorNumber = 0
            actuatorLabelList = []

            for actuator in child:
                
                # NUMBER OF ACTUATORS
                if actuator.tag == 'quantity':
                    actuatorNumber = int(actuator.text)
                
                # ACTUATOR LABELS
                else:
                    labelList = []
                    for label in actuator:
                        labelList.append(label.text)

                    actuatorLabelList.append(labelList)

            return actuatorNumber, actuatorLabelList
             
        except:
            pass

    def readSensor(self):
        """
        PURPOSE

        Read the number of sensors and their types.

        INPUT

        NONE

        RETURNS

        - sensorNumber = the number of sensors to display on the GUI.
        - sensorSelectedType = array containing the selected sensors types.
        """
        try:
            child = self.root.find('sensors')

            sensorNumber = 0
            sensorSelectedType = []

            for sensor in child:
                # NUMBER OF SENSORS
                if sensor.tag == 'quantity':
                    sensorNumber = int(sensor.text)
                
                # SENSOR TYPES
                else:
                    for sensorType in sensor:
                        sensorSelectedType.append(int(sensorType.text))

            return sensorNumber, sensorSelectedType
             
        except:
            pass

    def readAnalogCamera(self):
        """
        PURPOSE

        Read the analog camera settings.

        INPUT

        NONE

        RETURNS

        - cameraNumber = the number of sensors to display on the GUI.
        - defaultCameraList = array containing the default camera for each camera feed.
        """
        try:
            child = self.root.find('cameras')

            # ANALOG CAMERAS
            cameraChild = child.find('analog')

            cameraNumber = 0
            defaultCameraList = []

            for camera in cameraChild:
                
                # NUMBER OF CAMERAS
                if camera.tag == 'quantity':
                    cameraNumber = int(camera.text)
                
                # DEFAULT CAMERAS
                else:
                    defaultCameraList.append(int(camera.text))

            return cameraNumber, defaultCameraList
             
        except:
            pass

    def readDigitalCamera(self):
        """
        PURPOSE

        Read the digital camera settings.

        INPUT

        NONE

        RETURNS

        - cameraLabels = array containing the name label of each camera.
        - defaultCameraList = array containing the default camera for each camera feed.
        """
        try:
            child = self.root.find('cameras')

            # DIGITAL CAMERAS
            cameraChild = child.find('digital')

            cameraLabels = []
            defaultCameraList = []

            for camera in cameraChild:
                
                # CAMERA LABELS
                if camera.tag == 'labels':                                    
                    for item in camera:                        
                        cameraLabels.append(str(item.text))   
                
                # DEFAULT CAMERAS
                if camera.tag == 'defaultfeeds':
                    for item in camera:                        
                        defaultCameraList.append(int(item.text))

            return cameraLabels, defaultCameraList
             
        except:
            pass

    def readKeyBinding(self):
        """
        PURPOSE

        Read the keybinding settings.

        INPUT

        NONE

        RETURNS

        - keyBindingList = array containing controller keybindings for each control.
        """
        try:
            child = self.root.find('keybindings')

            keyBindingList = []

            for binding in child:
                keyBindingList.append(binding.text)     

            return keyBindingList
             
        except:
            pass

class WRITE_CONFIG_FILE():
    """
    PURPOSE

    Writes the ROV programs settings to an XML file.
    """
    def __init__(self, fileName):
        """
        PURPOSE

        Constructor which defines the default directory for the config file.
        Calls the createFile function to create an XML file.

        INPUT

        - fileName = directory to save the config file to.

        RETURNS

        NONE
        """
        self.fileName = fileName
        self.root = None
        self.children = None
        self.createFile()

    def createFile(self):
        """
        PURPOSE

        Creates the root of the XML file.

        INPUT

        NONE

        RETURNS

        NONE
        """
        self.root = Element("root")

    def writeFile(self):
        """
        PURPOSE

        Creates a tree and writes the file to the desired directory.

        INPUT

        NONE

        RETURNS

        NONE
        """
        try:
            tree = ElementTree(self.root)
            tree.write(self.fileName, encoding='utf-8', xml_declaration=True)
            fileSaveStatus = True
        except:
            fileSaveStatus = False

        return fileSaveStatus

    def saveTheme(self, theme):
        """
        PURPOSE

        Saves the program theme settings

        INPUT

        - theme = True for dark theme, False for light theme.

        RETURNS

        NONE
        """
        try:
            SubElement(self.root, "theme").text = "dark" if theme else "light"

        except:
            pass

    def saveThruster(self, thrusterPosition, thrusterReverse):
        """
        PURPOSE

        Saves the thruster settings.

        INPUT

        - thrusterPosition = array containing the ROV position of each thruster.
        - thrusterReverse = array containing the direction of each thruster.

        RETURNS

        NONE
        """
        try:
            thrusters = SubElement(self.root, "thrusters")
            for index in range(len(thrusterPosition)):
                thruster = SubElement(thrusters, "thruster{}".format(index))
                SubElement(thruster, "location").text = thrusterPosition[index]
                SubElement(thruster, "reversed").text = "True" if thrusterReverse[index] else "False"            

        except:
            pass

    def saveActuator(self, actuatorNumber, actuatorLabelList):
        """
        PURPOSE

        Saves the actuator settings.

        INPUT

        - actuatorLabelList = array containing the labels for the name, default and actuated state of each actuator.
        - actuatorNumber = number of actuators.

        RETURNS

        NONE
        """
        actuators = SubElement(self.root, "actuators")
        SubElement(actuators, "quantity").text = str(actuatorNumber)
        
        for index in range(actuatorNumber):
            actuator = SubElement(actuators, "actuator{}".format(index))
            SubElement(actuator, "nameLabel").text = actuatorLabelList[index][0]
            SubElement(actuator, "offLabel").text = actuatorLabelList[index][1]
            SubElement(actuator, "onLabel").text = actuatorLabelList[index][2]

    def saveSensor(self, sensorNumber, sensorSelectedType):
        """
        PURPOSE

        Saves the sensors settings.

        INPUT

        - sensorNumber = number of sensors.
        - sensorSelectedType = array containing the type of each sensor.

        RETURNS

        NONE
        """
        sensors = SubElement(self.root, "sensors")
        SubElement(sensors, "quantity").text = str(sensorNumber)
        
        for index in range(sensorNumber):
            sensor = SubElement(sensors, "sensor{}".format(index))
            SubElement(sensor, "type").text = str(sensorSelectedType[index])

    def saveAnalogCamera(self, analogCameraNumber, analogDefaultCameraList):
        """
        PURPOSE

        Saves analog camera data.

        INPUT

        - analogCameraNumber = the number of analog cameras.
        - analogDefaultCameraList = array containing the default camera for each camera feed.

        RETURNS

        NONE
        """
        try:
            # CHECK IF 'CAMERAS' ELEMENT ALREADY EXISTS
            try:
                cameras = self.root.find("cameras")
            except:
                cameras = SubElement(self.root, "cameras")
            
            analog = SubElement(cameras, "analog")

            # NUMBER OF ANALOG CAMERAS
            SubElement(analog, "quantity").text = str(analogCameraNumber)

            # DEFAULT ANALOG CAMERA FEEDS
            for index in range(4):
                SubElement(analog, "defaultfeed{}".format(index)).text = str(analogDefaultCameraList[index])

        except:
            pass

    def saveDigitalCamera(self, digitalCameraLabels, digitalDefaultCameraList):
        """
        PURPOSE

        Saves digital camera data.

        INPUT

        - digitalCameraLabels = array containing the label for each digital camera.
        - digitalDefaultCameraList = array containing the default digital camera for each feed.
        
        RETURNS

        NONE
        """
        try:
            # CHECK IF 'CAMERAS' ELEMENT ALREADY EXISTS
            try:
                cameras = self.root.find("cameras")
            except:
                cameras = SubElement(self.root, "cameras")
            
            digital = SubElement(cameras, "digital")

            # DIGITAL CAMERA LABELS
            digitalLabels = SubElement(digital, "labels")
            for index in range(3):
                SubElement(digitalLabels, "camera{}".format(index + 1)).text = str(digitalCameraLabels[index])

            # DEFAULT DIGITAL CAMERA FEEDS
            defaultFeeds = SubElement(digital, "defaultfeeds")
            for index in range(3):
                SubElement(defaultFeeds, "feed{}".format(index + 1)).text = str(digitalDefaultCameraList[index])

        except:
            pass

    def saveKeybinding(self, keyBindings):
        """
        PURPOSE

        Saves the keybinding settings.

        INPUT

        - keyBindings = array contataining the keybinding for each ROV control.

        RETURNS

        NONE
        """
        try:
            bindings = SubElement(self.root, "keybindings")
            
            for index, binding in enumerate(keyBindings):

                # KEYBINDING TO SWITCH ROV CONTROL ORIENTATION
                if index == 0:
                    SubElement(bindings, "switch_control_direction").text = binding

                # KEYBINDING TO CHANGE CONTROLLER SENSITIVITY
                elif index == 1: 
                    SubElement(bindings, "controller_sensitivity").text = binding

                # KEYBINDING TO YAW RIGHT
                elif index == 2:
                    SubElement(bindings, "right_yaw").text = binding
                
                # KEYBINDING TO YAW LEFT
                elif index == 3:
                    SubElement(bindings, "right_left").text = binding

                # KEYBINDING TO YAW SENSITIVITY
                elif index == 4:
                    SubElement(bindings, "yaw_sensitivity").text = binding
                
                # KEYBINDINGS FOR THE ACTUATORS
                else:
                    SubElement(bindings, "actuator{}".format(index)).text = binding

        except:
            pass
