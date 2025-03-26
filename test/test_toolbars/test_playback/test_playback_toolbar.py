
import pdb
import copy
import time

from ...utilities import *

from PyQt5.QtWidgets import QToolBar
from xmarte.qt5.services.data_handler.widgets.playback_widget import PlayToolbarWidget

def test_disabled(mainwindow, qtbot, monkeypatch):
    playbackToolBar = next(a for a in mainwindow.findChildren(QToolBar) if a.__class__ == PlayToolbarWidget)
    btns = ['back_fastBtn', 'backBtn', 'stopBtn','pauseBtn', 'playBtn', 'forward_fastBtn', 'restartBtn']
    for btn in btns:
        btn_widget = getattr(playbackToolBar, btn)
        assert btn_widget.isEnabled() == False
    

def test_enabled(mainwindow, qtbot, monkeypatch):
    import_data(mainwindow, monkeypatch)
    playbackToolBar = next(a for a in mainwindow.findChildren(QToolBar) if a.__class__ == PlayToolbarWidget)
    btns = ['back_fastBtn', 'backBtn', 'stopBtn','pauseBtn', 'playBtn', 'forward_fastBtn', 'restartBtn']
    for btn in btns:
        btn_widget = getattr(playbackToolBar, btn)
        assert btn_widget.isEnabled() == True

def test_stepthrough(mainwindow, qtbot, monkeypatch):
    # Since we're running offscreen we can't really test if the QDisplays on edges are shown
    import_data(mainwindow, monkeypatch)
    playbackToolBar = next(a for a in mainwindow.findChildren(QToolBar) if a.__class__ == PlayToolbarWidget)
    playbackToolBar.playBtn.clicked.emit()
    #playbackToolBar.counter_thread.run()
    for state_name, state in mainwindow.state_scenes.items():
        for thread_name, thread in state.items():
            assert thread.playback == True
            # Could test count but we run the race condition risk that it is in fact zero so maybe
            for edge in thread.edges:
                pass # cannot actually test a displayed item
    playbackToolBar.counter_thread.runChange(False)
    playbackToolBar.counter_thread.updateCount(0)
    playbackToolBar.restart()
    playbackToolBar.fastForward()
    playbackToolBar.fastForward()
    playbackToolBar.back()
    playbackToolBar.backFaster()
    playbackToolBar.pause()
    playbackToolBar.sliderMoved()
    playbackToolBar.cycleedtChanged(1)