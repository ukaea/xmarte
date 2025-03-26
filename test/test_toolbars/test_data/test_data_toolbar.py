
from ...utilities import *

from PyQt5.QtWidgets import QToolBar
from xmarte.qt5.services.data_handler.widgets.playback_widget import PlayToolbarWidget
from xmarte.qt5.services.data_handler.graph_window.graph_window import GraphWindow

def test_cleardata_toolbar(mainwindow, qtbot, monkeypatch) -> None:
    # TODO: Once Test Engine is fixed and stable
    # Setup our diagram and application
    import_data(mainwindow, monkeypatch)
    playbackToolBar = next(a for a in mainwindow.findChildren(QToolBar) if a.__class__ == PlayToolbarWidget)
    clear_action = next(a for a in playbackToolBar.actions() if a.text() == '&Clear Data')
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
    
def test_graph_toolbar(mainwindow, qtbot, monkeypatch) -> None:
    import_data(mainwindow, monkeypatch)
    playbackToolBar = next(a for a in mainwindow.findChildren(QToolBar) if a.__class__ == PlayToolbarWidget)
    open_graph_action = next(a for a in playbackToolBar.actions() if a.text() == '&Graph Window')
    open_graph_action.triggered.emit()
    assert mainwindow.newwindow.__class__ == GraphWindow
    # Just test that we opened the window and test graph features in a seperate test section