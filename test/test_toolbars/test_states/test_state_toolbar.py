
import pdb

from PyQt5.QtWidgets import QToolBar
from test.utilities import *
from xmarte.qt5.services.state_service.windows.state_machine_window import StateMachineWindow

def test_thread_combo(mainwindow, qtbot, monkeypatch) -> None:
    '''Change threads in the main application and assert the scene changes.'''
    create_basic_diagram(mainwindow, qtbot)

    assert len(mainwindow.scene.nodes) == 2

    addThreadToState(mainwindow, qtbot, monkeypatch, 'State1', 'TestThread', '254')
    switchThread(mainwindow, 'State1', 'TestThread')

    assert len(mainwindow.scene.nodes) == 0
    
def test_open_state_window(mainwindow, qtbot, monkeypatch):
    state_service = mainwindow.API.getServiceByName('StateDefinitionService')
    state_btn = state_service.state_machine
    state_btn.clicked.emit()
    assert mainwindow.newwindow.__class__ == StateMachineWindow
    