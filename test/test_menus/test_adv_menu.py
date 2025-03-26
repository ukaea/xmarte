import pdb

from test.utilities import *
from xmarte.qt5.services.type_db.windows.types_window import TypesDBWindow
from xmarte.qt5.windows.settings_window import SettingsWindow

def test_typedb_menuitem(mainwindow, qtbot, monkeypatch) -> None:
    adv_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Advanced')
    type_action = next(a for a in adv_menu.menu().actions() if a.text() == '&Type Database')
    type_action.triggered.emit()
    assert mainwindow.newwindow.__class__ == TypesDBWindow
    
def test_options_menuitem(mainwindow, qtbot, monkeypatch) -> None:
    adv_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Advanced')
    options_action = next(a for a in adv_menu.menu().actions() if a.text() == '&Options...')
    options_action.triggered.emit()
    assert mainwindow.newwindow.__class__ == SettingsWindow