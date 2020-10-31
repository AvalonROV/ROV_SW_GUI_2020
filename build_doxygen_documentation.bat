@ECHO OFF
ECHO This script will generate DOXYGEN code documentation for all the Python files in this project. 
ECHO You must first install Doxygen at https://www.doxygen.nl/index.html
pause
doxygen doxygen_settings.doxyfile
move ./html "./documentation"
ECHO Doxygen Documentation is up to date.
PAUSE