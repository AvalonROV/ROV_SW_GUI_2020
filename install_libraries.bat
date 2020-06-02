@ECHO OFF
echo This script will download the required Python libraries using PIP.
echo Libraries already installed will be skipped.
pause
echo.

echo #--- About to install PyQt5 ---#
pause
pip install pyqt5
echo.

echo #--- About to install OpenCV ---#
pause
pip install opencv-python
echo.

echo #--- About to install PyGame ---#
pause
pip install pygame
echo.

echo #--- About to install PySerial ---#
pause
pip install pyserial
echo.

echo All required libraries have been installed.
pause