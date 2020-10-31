
        """
        PURPOSE

        Write the program settings to an XML file.

        INPUT

        NONE

        RETURNS

        NONE
        """
        # CREATE ROOT
        configFile = WRITE_CONFIG_FILE(self.fileName)
        configFile.createFile()

        # SAVE THEME SETTINGS
        configFile.saveTheme(self.style.theme)

        # SAVE THRUSTER SETTINGS
        configFile.saveThruster(self.thrusters.rovPositions, self.thrusters.reverseStates)

        # SAVE ACTUATOR SETTINGS
        configFile.saveActuator(self.actuators.quantity, self.actuators.labelList)

        # SAVE ANALOG CAMERA SETTINGS
        configFile.saveAnalogCamera(self.analogCameras.quantity, self.analogCameras.labelList, self.analogCameras.defaultCameras)

        # SAVE DIGITAL CAMERA SETTINGS
        configFile.saveDigitalCamera(self.digitalCameras.quantity, self.digitalCameras.labelList, self.digitalCameras.addressList, self.digitalCameras.defaultCameras, self.digitalCameras.selectedResolutions)
        
        # SAVE KEYBINDING SETTINGS
        configFile.saveKeybinding(self.keybindings.bindings)

        # SAVE SENSOR SETTINGS
        configFile.saveSensor(self.sensors.quantity, self.sensors.viewType, self.sensors.selectedTypes)

        # WRITE SETTINGS TO XML FILE
        configFile.writeFile()

    def writeDefaultConfigFile(self, directory):