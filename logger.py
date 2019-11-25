# -*- coding: utf-8 -*-
"""@package LOGGER
This software provides an easy interface for logging messages and errors to a log file. It is designed as a general interface so that it can be used in
many different pieces of python software. This software was originally developed as part of the Avalon ROV project.

For more information about the Avalon ROV project please visit the website: https://avalonrov.wixsite.com/avalonrov

AUTHOR: Sam Maxwell
DATE CREATED: 17/11/2019
VERSION: N/A
VERSION DATE: N/A
"""
#-----------------------------------------------------------------------------------------------------------------------------------------------
#MODULES
#-----------------------------------------------------------------------------------------------------------------------------------------------
from os import path
import datetime

#-----------------------------------------------------------------------------------------------------------------------------------------------
#CLASSES
#-----------------------------------------------------------------------------------------------------------------------------------------------
class LogFile():
    """
    PURPOSE
    
    A general class for producing simple log files. Messages can be passed to this class and they will be recorded with a timestamp
    in a log file. Log files are created as a basic text file.
    """
    #DEFINITIONS
    __fileAddress = ""                    #The address of the logging file
    timeFormat = "%Y%m%dT%H%M%SZ"       #The format of the timestamp to be placed in the logging file name and in the logging file entries
    seperator = ","                     #The character used to seperate terms in a log entry
    delimiter = "\n"                    #The character used to create a new line
    
    def __init__(self, fileName, fileFolder = None):
        """
        PURPOSE
        
        Class Constructor. Initiates a new log file with the given file name. This log file is always created in the same folder as the code
        is running unless otherwise specified.
        
        INPUT
        
        - fileName = The name of the log file to be created.
        - fileFolder = The folder the log file is to be stored in, defaults to None.
        
        RETURNS
        
        NONE
        """
        self.__createFileAddress(fileName, fileFolder)
        self.__checkFileAddress()
        self.__createLogFile()
        
    def __createFileAddress(self, fileName, fileFolder = None):
        """
        PURPOSE
        
        Generates the address of the file the logging information will be stored in.
        
        INPUT
        
        - fileName = The name of the log file to be created.
        - fileFolder = The folder the log file is to be stored in, defaults to None.
        
        RETURNS
        
        NONE
        """
        #If no file folder is given, create the file in the folder the code is running. Otherwise, create it in the specified folder.
        if fileFolder != None:
            self.__fileAddress = fileFolder + "\\" + fileName + ".txt"
        else:
            self.__fileAddress = fileName + ".txt"
        
        #Adding a timestamp to the file address
        currentTime = datetime.datetime.now()
        self.__fileAddress = currentTime.strftime(self.timeFormat) + " " + self.__fileAddress
    
    def __checkFileAddress(self):
        """
        PURPOSE
        
        Checks the address of the file the logging folder information will be stored in to ensure it is suitable.
        
        INPUT
        
        NONE
        
        RETURNS
        
        NONE
        """
        #Checking if the file exists
        if path.exists(self.__fileAddress):
            raise IOError("A file at {} already exists".format(self.__fileAddress))
    
    def __createLogFile(self):
        """
        PURPOSE
        
        Creates the log file at the given address.
        
        INPUT
        
        NONE
        
        OUTPUT
        
        NONE
        """
        #Creating the log file
        self.addLogEntry("Logging Started")
    
    def addLogEntry(self, logEntryText):
        """
        PURPOSE
        
        Adds a single log entry to the log file with the given text.
        
        INPUT
        
        logEntryText = The text to be recorded in the log entry as a string.
        
        OUTPUT
        
        logAdded (Bool) = Returns whether the log entry was successfully added or not.
        """
        #Creating the success tracking boolean
        logAdded = False
        
        #Building the log entry
        currentTime = datetime.datetime.now()
        logEntry = currentTime.strftime(self.timeFormat) + self.seperator + logEntryText + self.delimiter
        
        #Opening the log file and writing the entry
        try:
            logFile = open(self.__fileAddress, "a")
            logFile.write(logEntry)
            logFile.close()
            logAdded = True
            
        except IOError:
            print("Failed to write to log file, ensure it is not open in another program or create a new file")
        
        return logAdded
    
    def getFileAddress(self):
        """
        PURPOSE
        
        Returns the file address of the log file.
        
        INPUT
        
        NONE
        
        OUTPUT
        
        fileAddress (string) = The address of the logging file.
        """
        return self.__fileAddress