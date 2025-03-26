
import pdb

from ...utilities import *

from PyQt5.QtWidgets import QToolBar
from xmarte.qt5.services.test_engine.windows.test_window import TestWindow

def test_engine_toolbar(mainwindow, qtbot, monkeypatch) -> None:
    # TODO: Once Test Engine is fixed and stable
    # Setup our diagram and application
    import_data(mainwindow, monkeypatch)
    test_button = mainwindow.editToolBar.service_layout.itemAt(0).widget()
    assert test_button.text() == '&Test'
    test_button.clicked.emit()
    assert mainwindow.newwindow.__class__ == TestWindow