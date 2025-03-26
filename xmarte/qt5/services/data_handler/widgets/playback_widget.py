''' The toolbar widget which contains the playback options and the graph window opening button '''
import os
import time

from PyQt5.QtWidgets import QToolBar, QAction, QWidget, QSizePolicy, QSlider, QLabel, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
from PyQt5 import QtCore

from qtpy.QtWidgets import QPushButton

from martepy.functions.extra_functions import isint

class PlayToolbarWidget(QToolBar):
    '''
    Edit Toolbar Widget for the application
    '''
    countChanged = QtCore.pyqtSignal(int)
    speedChanged = QtCore.pyqtSignal(int)
    runChanged = QtCore.pyqtSignal(bool)

    def __init__(self, title=None, parent=None):
        super().__init__(title, parent)
        self.playback = False
        self.parent = parent
        self.application = parent

        # Actually lets add all our buttons here
        data_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.icon_folder = os.path.join(data_dir, 'icons')
        self.btns = ['back_fastBtn', 'backBtn', 'stopBtn','pauseBtn',
                     'playBtn', 'forward_fastBtn', 'restartBtn']
        self.btnicons = ['back-faster.png', 'back.png', 'stop.png', 'pause.png',
                         'play.png', 'forward-faster.png', 'restart.png']
        self.btnfunctions = ['backFaster','back','stopEvent', 'pause',
                             'play', 'fastForward','restart']
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Horizontal)
        lbl = QLabel('Cycle:')
        self.cycleedt = QLineEdit('0')
        self.cycleedt.setFixedWidth(30)
        self.cycleedt.editingFinished.connect(self.cycleedtChanged)
        self.aftlbl = QLabel('/0')
        self.slider.setFixedWidth(100)
        self.slider.setFixedHeight(25)

        # After each value change, slot "scaletext" will get invoked.
        # Manage all connections
        self.slider.sliderMoved.connect(self.sliderMoved)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        #self.slider.setTickInterval(0)
        # Add our widgets now
        self.createButtons()
        self.connectButtons()
        self.addWidget(self.slider)

        self.addWidget(lbl)
        self.addWidget(self.cycleedt)
        self.addWidget(self.aftlbl)

        self.enableDisable(False)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer.setObjectName("MenuBarSpacer")

        parent_service = self.application.API.getServiceByName("DataManager")

        self.addWidget(spacer)
        self.clearAction = QAction("&Clear Data", self)
        self.clearAction.triggered.connect(parent_service.clearData)
        self.addAction(self.clearAction)
        self.graphAction = QAction("&Graph Window", self)
        self.graphAction.triggered.connect(parent_service.openGraphWnd)
        self.addAction(self.graphAction)

        self.counter_thread = CounterThread()
        self.countChanged.connect(self.counter_thread.updateCount)
        self.speedChanged.connect(self.counter_thread.speedChange)
        self.runChanged.connect(self.counter_thread.runChange)
        self.running = False
        self.speed = 1
        self.counter_thread.countChanged.connect(self.updateSlider)

    def updateSlider(self, value):
        ''' Playing mode - update the slider to track with play position '''
        try:
            self.slider.sliderMoved.disconnect()
        except TypeError:
            pass
        try:
            self.cycleedt.editingFinished.disconnect()
        except TypeError:
            pass
        self.slider.setTickPosition(int(value/(self.counter_thread.maxcount/100)))
        self.slider.setValue(int(value/(self.counter_thread.maxcount/100)))
        self.slider.update()
        self.slider.repaint()
        self.cycleedt.setText(str(value))
        for _, state in self.application.state_scenes.items():
            for _, scene in state.items():
                scene.count = int(value)
        self.cycleedt.editingFinished.connect(self.cycleedtChanged)
        self.slider.sliderMoved.connect(self.sliderMoved)

    def cycleedtChanged(self, text):
        ''' User has modified position in playback '''
        if isint(text):
            self.countChanged.emit(int(text))


    def sliderMoved(self):
        ''' React to user moving the slider '''
        position = self.slider.sliderPosition()
        position = position*int(self.counter_thread.maxcount/100)
        position = min(position, self.counter_thread.maxcount)
        self.countChanged.emit(position)

    def play(self):
        ''' User has selected to play the data '''
        self.speed = 1
        self.speedChanged.emit(self.speed)
        if not self.counter_thread.isRunning():
            self.counter_thread.start()
            for _, state in self.application.state_scenes.items():
                for _, scene in state.items():
                    scene.playback = True
                    scene.grScene.update()

    def backFaster(self):
        ''' Move back faster in playback '''
        if self.speed == -1:
            self.speed = -2
        self.speed = -int(self.speed ** 2) if self.speed < 0 else -1
        self.speedChanged.emit(self.speed)

    def pause(self):
        ''' Pause but don't stop playback '''
        self.speed = 0
        self.speedChanged.emit(self.speed)

    def back(self):
        ''' Start moving backwards or set back speed to 1 '''
        self.speed = -1
        self.speedChanged.emit(-1)

    def stopEvent(self):
        ''' Stopping has been triggered '''
        try:
            self.slider.sliderMoved.disconnect()
        except TypeError:
            pass
        try:
            self.cycleedt.editingFinished.disconnect()
        except TypeError:
            pass
        if self.counter_thread.isRunning():
            self.counter_thread.terminate()
        for _, state in self.application.state_scenes.items():
            for _, scene in state.items():
                scene.playback = False

    def fastForward(self):
        ''' Move forward faster - increase speed setting '''
        if self.speed == 1:
            self.speed = 2
        else:
            self.speed = int(self.speed ** 2) if self.speed > 0 else 1
        self.speedChanged.emit(self.speed)

    def restart(self):
        ''' Move back to zero position '''
        self.countChanged.emit(0)

    def connectButtons(self):
        ''' Connect our varying playback toolbar buttons to their functions '''
        for btn, func in zip(self.btns, self.btnfunctions):
            getattr(self, btn).clicked.connect(getattr(self, func))

    def createButtons(self):
        ''' Create our playback buttons '''
        for btn, icon in zip(self.btns, self.btnicons):
            new_btn = IconButton(os.path.join(self.icon_folder, icon))
            setattr(self, btn, new_btn)
            new_btn.setIconSize(QSize(12, 12))
            self.addWidget(new_btn)

    def enableDisable(self, enabled):
        ''' Toggle Enable/Disable depending on whether we have data - handled elsewhere '''
        for btn in self.btns:
            abtn = getattr(self, btn)
            abtn.setEnabled(enabled)
        self.slider.setEnabled(enabled)
        self.cycleedt.setEnabled(enabled)

class CounterThread(QtCore.QThread):
    ''' The thread which manages moving through data '''
    countChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.count = 0
        self.maxcount = 0
        self.running = False
        self.speed = 1

    def updateCount(self, value):
        ''' Update the count position '''
        self.count = value
        self.countChanged.emit(self.count)

    def speedChange(self, value):
        ''' Update our speed for the thread '''
        self.speed = value

    def run(self):
        ''' running action - iterate through the count for the nodes to track '''
        self.running = True
        while True:
            if self.running:
                if self.speed > 0:
                    if (self.count + self.speed) > (self.maxcount):
                        self.count = 0

                if self.speed < 0:
                    if (self.count-self.speed) < 0:
                        self.count = self.maxcount
                self.count += self.speed
                self.countChanged.emit(self.count)
            time.sleep(0.2)

    def runChange(self, value):
        ''' Start/Stop the thread '''
        self.running = value


class IconButton(QPushButton):
    ''' Change the push buttons so that they display the icon without a background overlay '''
    def __init__(self, icon_path):
        super().__init__()
        self.setIcon(QIcon(icon_path))
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
