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
import os
import datetime

#-----------------------------------------------------------------------------------------------------------------------------------------------
#DEFINITIONS
#-----------------------------------------------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------------------------------------------
#CLASSES
#-----------------------------------------------------------------------------------------------------------------------------------------------
class logFile():
    """
    PURPOSE
    
    A general class for producing simple log files. Messages can be passed to this class and they will be recorded with a timestamp
    in a log file. Log files are created as a basic text file.
    """
    #DEFINITIONS
    fileAddress = ""
    
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
        self.__createFileAddress(fileName, fileFolder)      #Generating the file address of the log file
        
        
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
            self.fileAddress = fileFolder + "\\" + fileName + ".txt"
        else:
            self.fileAddress = fileName + ".txt"
    
    def __checkFileAddress(self):
        """
        PURPOSE
        
        Checks the address of the file the logging folder information will be stored in to ensure it is suitable.
        
        INPUT
        
        NONE
        
        RETURNS
        
        - bool = True if the file passes tests, False if it does not.
        """
        pass