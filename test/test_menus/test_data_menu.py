import pdb

from PyQt5.QtWidgets import QFileDialog

from test.utilities import *
from xmarte.qt5.services.type_db.windows.types_window import TypesDBWindow
from xmarte.qt5.windows.settings_window import SettingsWindow

def test_importdata_menuitem(mainwindow, qtbot, monkeypatch) -> None:
    # Setup our diagram and application
    import_data(mainwindow, monkeypatch)

def test_cleardata_menuitem(mainwindow, qtbot, monkeypatch) -> None:
    # Setup our diagram and application
    import_data(mainwindow, monkeypatch)
    data_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Data Manager')
    clear_action = next(a for a in data_menu.menu().actions() if a.text() == '&Clear Data')
    clear_action.triggered.emit()
    assert mainwindow.state_scenes['Error']['Thread1'].nodes[0].outputs[0].data == None
    assert mainwindow.state_scenes['State1']['Thread2'].nodes[0].outputs[0].data == None
    assert mainwindow.state_scenes['State1']['Thread2'].nodes[0].outputs[1].data == None
    io_gam = next(a for a in mainwindow.state_scenes['State1']['Thread1'].nodes if a.title == 'IO (IOGAM)')
    assert io_gam.outputs[0].data == None
    assert io_gam.outputs[1].data == None
    constant_gam = next(a for a in mainwindow.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)')
    newsignal = next(a for a in constant_gam.outputs if a.label == 'newsignal')
    newsignal1 = next(a for a in constant_gam.outputs if a.label == 'newsignal1')
    assert newsignal.data == None
    assert newsignal1.data == None
    