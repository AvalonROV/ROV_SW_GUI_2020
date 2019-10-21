from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
import sys

class UI(QtWidgets.QMainWindow):
    # INITIAL SETUP
    def __init__(self):
        super(UI,self).__init__()
        # LOAD UI FILE
        uic.loadUi('gui.ui',self)

        # SET DEFAULT WIDGET SIZES
        self.con_panel_functions_widget.resize(400,self.con_panel_functions_widget.height())
        self.func_testing_functions_widget.resize(400,self.con_panel_functions_widget.height())

        # ADD AVALON LOGO
        pixmap = QPixmap("logo.png")
        pixmap = pixmap.scaledToWidth(250)
        self.avalon_logo.setPixmap(pixmap)

        # INITIALISE UI
        self.showMaximized()

def guiInitiate():
    # CREATE QAPPLICATION INSTANCE (PASS SYS.ARGV TO ALLOW COMMAND LINE ARGUMENTS)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = UI()
    # START EVENT LOOP
    app.exec_()

if __name__ == '__main__':
    guiInitiate()