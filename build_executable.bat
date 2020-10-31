@ECHO OFF
echo This script will compile the program into an executable that can run on any windows PC without needing Python or any libraries installed.
pause

pyinstaller main.spec
mkdir "Pilot Control Program"
move ./build "./Pilot Control Program"
move ./dist "./Pilot Control Program"

pause