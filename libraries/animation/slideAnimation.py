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
        screenNext.clicked.connect(self.animation.screenNext)

        screenPrevious = QPushButton("Previous")
        screenPrevious.clicked.connect(self.animation.screenPrevious)

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
        if self.m_wrap or now < (self.stackedWidget.count()):
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

    def slideInWgt(self, newwidget):
        if self.m_active:
            return

        self.m_active = True

        _now = self.stackedWidget.currentIndex()
        _next = self.stackedWidget.indexOf(newwidget)

        if _now == _next:
            self.m_active = False
            return

        offsetx, offsety = self.stackedWidget.frameRect().width(), self.stackedWidget.frameRect().height()
        self.stackedWidget.widget(_next).setGeometry(self.stackedWidget.frameRect())

        if not self.m_direction == Qt.Horizontal:
            if _now < _next:
                offsetx, offsety = 0, -offsety
            else:
                offsetx = 0
        else:
            if _now < _next:
                offsetx, offsety = -offsetx, 0
            else:
                offsety = 0

        pnext = self.stackedWidget.widget(_next).pos()
        pnow = self.stackedWidget.widget(_now).pos()
        self.m_pnow = pnow

        offset = QPoint(offsetx, offsety)
        self.stackedWidget.widget(_next).move(pnext - offset)
        self.stackedWidget.widget(_next).show()
        self.stackedWidget.widget(_next).raise_()

        anim_group = QParallelAnimationGroup(
            self, finished=self.animationDoneSlot
        )

        for index, start, end in zip(
            (_now, _next), (pnow, pnext - offset), (pnow + offset, pnext)
        ):
            animation = QPropertyAnimation(
                self.stackedWidget.widget(index),
                b"pos",
                duration=self.m_speed,
                easingCurve=self.m_animationtype,
                startValue=start,
                endValue=end,
            )
            anim_group.addAnimation(animation)

        self.m_next = _next
        self.m_now = _now
        self.m_active = True
        anim_group.start(QAbstractAnimation.DeleteWhenStopped)

    @pyqtSlot()
    def animationDoneSlot(self):
        self.stackedWidget.setCurrentIndex(self.m_next)
        self.stackedWidget.widget(self.m_now).hide()
        self.stackedWidget.widget(self.m_now).move(self.m_pnow)
        self.m_active = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VIEW()
    w.resize(1920, 1080)
    w.show()
    sys.exit(app.exec_())