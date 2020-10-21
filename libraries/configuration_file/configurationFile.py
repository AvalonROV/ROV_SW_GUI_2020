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
            return

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
            return

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
            return

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
            sensorViewType = 1
            sensorSelectedType = []

            for sensor in child:
                # NUMBER OF SENSORS
                if sensor.tag == 'quantity':
                    sensorNumber = int(sensor.text)

                if sensor.tag == 'viewType':
                    sensorViewType = int(sensor.text)
                
                # SENSOR TYPES
                else:
                    for sensorType in sensor:
                        sensorSelectedType.append(int(sensorType.text))

            return sensorNumber, sensorViewType, sensorSelectedType
             
        except:
            return

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
            child = self.root.find('analog_cameras')

            cameraNumber = 0
            cameraLabelList = []
            defaultCameraList = []

            for camera in child:
                
                # NUMBER OF CAMERAS
                if camera.tag == 'quantity':
                    cameraNumber = int(camera.text)

                # CAMERA LABELS
                if camera.tag == 'camera_labels':
                    for label in camera:
                        cameraLabelList.append(label.text)
                
                # DEFAULT CAMERAS
                if camera.tag == 'default_feeds':
                    for feed in camera:
                        defaultCameraList.append(int(feed.text))

            return cameraNumber, cameraLabelList, defaultCameraList
             
        except:
            return

    def readDigitalCamera(self):
        """
        PURPOSE

        Read the digital camera settings.

        INPUT

        NONE

        RETURNS

        - cameraNumber = number of cameras.
        - cameraLabels = array containing the name label of each camera.
        - cameraAddresses = array containing the source address of each camera.
        - defaultCameraList = array containing the default camera for each camera feed.
        """
        try:
            child = self.root.find('digital_cameras')

            cameraNumber = 0
            cameraLabels = []
            cameraAddresses = []
            defaultCameraList = []
            cameraResolutions = []

            for camera in child:

                # NUMBER OF CAMERAS
                if camera.tag == 'quantity':
                    cameraNumber = int(camera.text)
                
                # CAMERA LABELS
                if camera.tag == 'camera_labels':                                    
                    for label in camera:                        
                        cameraLabels.append(str(label.text))  

                # CAMERA ADDRESSES
                if camera.tag == 'camera_address':
                    for address in camera:
                        text = address.text 
                        if text == None:
                            text = ""     
                        cameraAddresses.append(str(text))
                
                # DEFAULT CAMERAS
                if camera.tag == 'default_feeds':
                    for item in camera:                        
                        defaultCameraList.append(int(item.text))

                # RESOLUTIONS
                if camera.tag == 'resolution':
                    for item in camera:
                        cameraResolutions.append(int(item.text))

            return cameraNumber, cameraLabels, cameraAddresses, defaultCameraList, cameraResolutions
             
        except:
            return

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
            return

class WRITE_CONFIG_FILE():
    """
    PURPOSE

    Writes the ROV programs configuration settings to an XML file.
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
        try:
            actuators = SubElement(self.root, "actuators")
            SubElement(actuators, "quantity").text = str(actuatorNumber)
            
            for index in range(actuatorNumber):
                actuator = SubElement(actuators, "actuator{}".format(index))
                SubElement(actuator, "nameLabel").text = actuatorLabelList[index][0]
                SubElement(actuator, "offLabel").text = actuatorLabelList[index][1]
                SubElement(actuator, "onLabel").text = actuatorLabelList[index][2]

        except:
            pass

    def saveSensor(self, sensorNumber, sensorViewType, sensorSelectedType):
        """
        PURPOSE

        Saves the sensors settings.

        INPUT

        - sensorNumber = number of sensors.
        - viewType = how readings are displayed on the control panel (0 = text box, 1 = graph).
        - sensorSelectedType = array containing the type of each sensor.

        RETURNS

        NONE
        """
        try:
            sensors = SubElement(self.root, "sensors")
            SubElement(sensors, "quantity").text = str(sensorNumber)

            SubElement(sensors, "viewType").text = str(sensorViewType)
            
            for index in range(sensorNumber):
                sensor = SubElement(sensors, "sensor{}".format(index))
                SubElement(sensor, "type").text = str(sensorSelectedType[index])
        
        except:
            pass

    def saveAnalogCamera(self, analogCameraNumber, analogCameraLabelList, analogDefaultCameraList):
        """
        PURPOSE

        Saves analog camera data.

        INPUT

        - analogCameraNumber = the number of analog cameras.
        - analogCameraLabelList = array contatining the label for each camera.
        - analogDefaultCameraList = array containing the default camera feeds.

        RETURNS

        NONE
        """
        try:  
            analog = SubElement(self.root, "analog_cameras")

            # NUMBER OF ANALOG CAMERAS
            SubElement(analog, "quantity").text = str(analogCameraNumber)

            # CAMERA LABELS
            cameraLabels = SubElement(analog, "camera_labels")
            for index, label in enumerate(analogCameraLabelList):
                SubElement(cameraLabels, "label{}".format(index)).text = str(label)

            # DEFAULT ANALOG CAMERA FEEDS
            defaultCameras = SubElement(analog, "default_feeds")
            for index, feed in enumerate(analogDefaultCameraList):
                SubElement(defaultCameras, "defaultfeed{}".format(index)).text = str(feed)

        except:
            pass

    def saveDigitalCamera(self, digitalCameraNumber, digitalCameraLabelList, digitalCameraAddressList, digitalDefaultCameraList, digitalResolutionsList):
        """
        PURPOSE

        Saves digital camera data.

        INPUT

        - digitalCameraNumber = number of digital cameras.
        - digitalCameraLabels = array containing the label for each digital camera.
        - digitalCameraAddressList = array containing the source address of each camera.
        - digitalDefaultCameraList = array containing the default digital camera for each feed.
        
        RETURNS

        NONE
        """
        try: 
            digital = SubElement(self.root, "digital_cameras")
            
            # NUMBER OF DIGITAL CAMERAS
            SubElement(digital, "quantity").text = str(digitalCameraNumber)

            # CAMERA LABELS
            cameraLabels = SubElement(digital, "camera_labels")
            for index, label in enumerate(digitalCameraLabelList):
                SubElement(cameraLabels, "label{}".format(index)).text = str(label)

            # CAMERA ADDRESSES
            cameraAddress = SubElement(digital, "camera_address")
            for index, address in enumerate(digitalCameraAddressList):
                SubElement(cameraAddress, "address{}".format(index)).text = str(address)

            # DEFAULT DIGITAL CAMERA FEEDS
            defaultCameras = SubElement(digital, "default_feeds")
            for index, feed in enumerate(digitalDefaultCameraList):
                SubElement(defaultCameras, "defaultfeed{}".format(index)).text = str(feed)

            # CAMERA FEED RESOLUTIONS
            cameraResolutions = SubElement(digital, "resolution")
            for index, resolution in enumerate(digitalResolutionsList):
                SubElement(cameraResolutions, "feed{}".format(index)).text = str(resolution)

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
