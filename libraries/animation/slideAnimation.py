import random
import sys
from PyQt5.QtCore import Qt, QParallelAnimationGroup, QPropertyAnimation, QPoint, QEasingCurve, QTimeLine, QAbstractAnimation, pyqtSlot
from PyQt5.QtWidgets import QWidget, QMainWindow, QApplication, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout
from PyQt5.QtGui import QColor

class VIEW(QMainWindow):
    def __init__(self):
        super(VIEW, self).__init__()

        widget = QStackedWidget()
        self.animation = SLIDE_ANIMATION(widget)
        
        for i in range(5):
            label = QLabel("Screen {}".format(i), alignment = Qt.AlignCenter)
            color = QColor(*random.sample(range(255), 3))
            label.setStyleSheet("background-color: {}; color: white; font: 40pt".format(color.name()))
            widget.addWidget(label)

        screenNext = QPushButton("Next")
        #screenNext.clicked.connect(self.animation.screenNext)
        screenNext.clicked.connect(lambda state, page = 0: self.animation.jumpTo(page))

        screenPrevious = QPushButton("Previous")
        #screenPrevious.clicked.connect(self.animation.screenPrevious)
        screenPrevious.clicked.connect(lambda state, page = 1: self.animation.jumpTo(page))

        layout = QHBoxLayout()
        layout.addWidget(screenPrevious)
        layout.addWidget(screenNext)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        lay = QVBoxLayout(central_widget)
        lay.addLayout(layout)
        lay.addWidget(widget)

class SLIDE_ANIMATION(QWidget):
    def __init__(self, stackedWidget):
        QWidget.__init__(self)
        self.stackedWidget = stackedWidget
        self.m_direction = Qt.Horizontal
        self.m_speed = 500
        self.m_animationtype = QEasingCurve.InOutCubic
        self.m_now = 0
        self.m_next = 0
        self.m_wrap = False
        self.m_pnow = QPoint(0, 0)
        self.m_active = False
        self.animationComplete = True

    def setDirection(self, direction):
        self.m_direction = direction

    def setSpeed(self, speed):
        self.m_speed = speed

    def setAnimation(self, animationtype):
        self.m_animationtype = animationtype

    def setWrap(self, wrap):
        self.m_wrap = wrap

    def jumpTo(self, page):
        now = self.stackedWidget.currentIndex()
        if (self.m_wrap or now < (self.stackedWidget.count())):
            self.slideInIdx(page)

    def screenNext(self):
        now = self.stackedWidget.currentIndex()
        if self.m_wrap or now < (self.stackedWidget.count() - 1):
            self.slideInIdx(now + 1)

    def screenPrevious(self):
        now = self.stackedWidget.currentIndex()
        if self.m_wrap or now > 0:
            self.slideInIdx(now - 1)

    def slideInIdx(self, idx):
        if idx > (self.stackedWidget.count() - 1):
            idx = idx % self.stackedWidget.count()
        elif idx < 0:
            idx = (idx + self.stackedWidget.count()) % self.stackedWidget.count()
        self.slideInWgt(self.stackedWidget.widget(idx))

    def slideInWgt(self, newWidget):

        self.animationComplete = False

        if self.m_active:
            return

        self.m_active = True

        # DEFINE WIDGETS TO TRANSITION BETWEEN
        currentPage = self.stackedWidget.currentIndex()
        nextPage = self.stackedWidget.indexOf(newWidget)

        if currentPage == nextPage:
            self.m_active = False
            return
        
        # GET WIDGET DIMENSIONS
        offsetx, offsety = self.stackedWidget.frameRect().width(), self.stackedWidget.frameRect().height()
        # SET NEW WIDGET DIMENSIONS
        self.stackedWidget.widget(nextPage).setGeometry(self.stackedWidget.frameRect())

        # HORIZONTAL SLIDE
        if not self.m_direction == Qt.Horizontal:
            if currentPage < nextPage:
                offsetx, offsety = 0, -offsety
            else:
                offsetx = 0
        # VERTICAL SLIDE
        else:
            if currentPage < nextPage:
                offsetx, offsety = -offsetx, 0
            else:
                offsety = 0


        posNext = self.stackedWidget.widget(nextPage).pos()         # GET QPOINT OF NEXT WIDGET
        posCurrent = self.stackedWidget.widget(currentPage).pos()   # GET QPOINT OF CURRENT WIDGET
        self.m_pnow = posCurrent

        offset = QPoint(offsetx, offsety)
        self.stackedWidget.widget(nextPage).move(posNext - offset)
        self.stackedWidget.widget(nextPage).show()
        self.stackedWidget.widget(nextPage).raise_()                # BRING WIDGET TO FRONT OF GUI

        anim_group = QParallelAnimationGroup(
            self, finished=self.animationDoneSlot
        )

        for index, start, end in zip((currentPage, nextPage), 
                                    (posCurrent, posNext - offset), 
                                    (posCurrent + offset, posNext)):
            
            animation = QPropertyAnimation(self.stackedWidget.widget(index),
                                            b"pos",
                                            duration=self.m_speed,
                                            easingCurve=self.m_animationtype,
                                            startValue=start,
                                            endValue=end)
            
            anim_group.addAnimation(animation)

        self.m_next = nextPage
        self.m_now = currentPage
        self.m_active = True


        anim_group.start(QAbstractAnimation.DeleteWhenStopped)

    @pyqtSlot()
    def animationDoneSlot(self):
        self.stackedWidget.setCurrentIndex(self.m_next)
        self.stackedWidget.widget(self.m_now).hide()
        self.stackedWidget.widget(self.m_now).move(self.m_pnow)
        self.m_active = False
        self.animationComplete = True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VIEW()
    w.resize(1920, 1080)
    w.show()
    sys.exit(app.exec_())