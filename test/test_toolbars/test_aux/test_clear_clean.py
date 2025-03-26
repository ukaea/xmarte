import pdb

from test.utilities import *
from PyQt5.QtWidgets import QMessageBox

def test_clear_action(mainwindow, qtbot, monkeypatch) -> None:
    create_basic_diagram(mainwindow, qtbot)
    clear_action = next(a for a in mainwindow.editToolBar.actions() if a.text() == '&Clear')
    monkeypatch.setattr(
        QMessageBox, 'question', lambda *args: QMessageBox.Yes
    )
    clear_action.triggered.emit()
    assert mainwindow.scene.nodes == []
    assert mainwindow.scene.edges == []

def test_clean_action(mainwindow, qtbot, monkeypatch) -> None:
    create_basic_diagram(mainwindow, qtbot)
    clean_action = next(a for a in mainwindow.editToolBar.actions() if a.text() == '&Clean diagram')
    clean_action.triggered.emit()
    # We can't actually test the position sets of nodes in offscreen as there is no
    # screen to define positions in the GUI so we're only testing that thsi function runs
    # without triggering an error.