"""
This template is for implementing computer vision algorithms into the main program.

The runAlgorithm() function is called by the camera library, hence all the processing functions
must be called inside this function.

Data from the algorithm such as positional data to control the ROV can be sent back to the
main program via emitting the transmitData signal (using the sendData function).

All the processing functions must be defined inside the TASK_NAME class.
"""

######################
### MODULE IMPORTS ###
######################
from PyQt5.QtCore import pyqtSignal, QObject

class TASK_NAME(QOBject):
    """
    PURPOSE

    Description of the image processing algorithm.
    """

    # SIGNAL THAT CAN SEND USEFUL DATA TO THE MAIN PROGRAM
    # DATA TYPE CAN BE STR, INT ETC.
    transmitData = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)

    def runAlgorithm(self, frame):
        """
        PURPOSE

        Calls all the required image processing functions, and returns the processed camera frame.
        Useful data is transmitted via a signal and slot.

        INPUT

        - frame = camera frame to process.

        RETURNS

        NONE
        """
        processedFrame = None
        data = None

        # CALL ALL PROCESSING FUNCTIONS HERE
        processedFrame = processingFunction1(frame)

        # SEND USEFUL DATA TO MAIN PROGRAM
        self.sendData(data)

        # DISPLAY PROCESSED FRAME
        return processedFrame

    def sendData(self, data):
        """
        PURPOSE

        Sends required data back to main program via a PyQt signal.

        INPUT

        - data = the data to send.

        RETURNS

        NONE
        """
        self.transmitData.emit(data)

    ############################
    ### PROCESSING FUNCTIONS ###
    ############################

    def processingFunction1(self, frame):
        """
        PURPOSE

        Description of what the function does.

        INPUT

        - frame = camera frame to process

        OUTPUT

        - processedFrame = the processed camera frame
        """
        processedFrame = frame

        return processedFrame







########################
##### TESTING CODE #####
########################
"""
Any code required to test the algorithm can be written here (outside of the class)
"""
algorithm = TASK_NAME()