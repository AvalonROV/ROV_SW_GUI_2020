import sys
import math

from PyQt5.QtCore import pyqtSignal, QPoint, QSize, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QGridLayout, QOpenGLWidget, QWidget)

import OpenGL.GL as gl

class VIEW(QWidget):

    def __init__(self):
        super(VIEW, self).__init__()

        self.glWidget = ROV_SIMULATION()
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.glWidget)
        self.setLayout(mainLayout)
        self.setWindowTitle("ROV Simulation")

class ROV_SIMULATION(QOpenGLWidget):
    """
    """
    def __init__(self, parent=None):
        super(ROV_SIMULATION, self).__init__(parent)

        self.object = 0
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0

        self.lastPos = QPoint()

        self.trolltechGreen = QColor("#3f51b5")
        self.background = QColor.fromCmykF(0, 0, 0, 0)

    def minimumSizeHint(self):
        return QSize(50, 50)

    def sizeHint(self):
        return QSize(400, 400)

    def setXRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.xRot:
            self.xRot = angle
            #self.xRotationChanged.emit(angle)
            self.update()

    def setYRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.yRot:
            self.yRot = angle
            #self.yRotationChanged.emit(angle)
            self.update()

    def setZRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.zRot:
            self.zRot = angle
            #self.zRotationChanged.emit(angle)
            self.update()

    def initializeGL(self):
        # SET BACKGROUND COLOR
        self.setClearColor(self.background)
        # CREATE MODEL
        self.object = self.makeObject()

        gl.glShadeModel(gl.GL_FLAT)
        gl.glEnable(gl.GL_DEPTH_TEST)       
        gl.glEnable(gl.GL_CULL_FACE)

    def paintGL(self):
        gl.glClear(
            gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        gl.glTranslated(0.0, 0.0, -10.0)
        gl.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
        gl.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
        gl.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
        gl.glCallList(self.object)

    def resizeGL(self, width, height):
        side = min(width, height)
        if side < 0:
            return

        gl.glViewport((width - side) // 2, (height - side) // 2, side,
                           side)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        # ROTATE MODEL
        if event.buttons() & Qt.LeftButton:
            self.setXRotation(self.xRot - 8 * dy)
            self.setYRotation(self.yRot + 8 * dx)
        # elif event.buttons() & Qt.RightButton:
        #     self.setXRotation(self.xRot + 8 * dy)
        #     self.setZRotation(self.zRot + 8 * dx)

        self.lastPos = event.pos()

    def makeObject(self):
        genList = gl.glGenLists(1)
        gl.glNewList(genList, gl.GL_COMPILE)

        gl.glBegin(gl.GL_QUADS)

        x1, y1 = -0.2, -0.2
        x2, y2 = -0.2, 0.2
        x3, y3 = 0.2, 0.2
        x4, y4 = 0.2, -0.2
        
        self.quad(x1, y1, x2, y2, x3, y3, x4, y4)
        
        gl.glEnd()
        gl.glEndList()

        return genList

    def quad(self, x1, y1, x2, y2, x3, y3, x4, y4):
        self.setColor(self.trolltechGreen)

        gl.glVertex3d(x1, y1, 0)
        gl.glVertex3d(x2, y2, 0)
        gl.glVertex3d(x3, y3, 0)
        gl.glVertex3d(x4, y4, 0)

        gl.glVertex3d(x4, y4, 0)
        gl.glVertex3d(x3, y3, 0)
        gl.glVertex3d(x2, y2, 0)
        gl.glVertex3d(x1, y1, 0)

    def extrude(self, x1, y1, x2, y2):
        self.setColor(self.trolltechGreen.darker(250 + int(100 * x1)))

        gl.glVertex3d(x1, y1, +0.05)
        gl.glVertex3d(x2, y2, +0.05)
        gl.glVertex3d(x2, y2, -0.05)
        gl.glVertex3d(x1, y1, -0.05)

    def normalizeAngle(self, angle):
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle

    def setClearColor(self, c):
        gl.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def setColor(self, c):
        gl.glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())

if __name__ == '__main__':

    app = QApplication(sys.argv)
    widget = VIEW()
    widget.show()
    sys.exit(app.exec_())