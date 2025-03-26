import pdb

from test.utilities import *
from xmarte.qt5.services.deployment.windows.deploy_window import DeployWindow

def test_deploy_menuitem(mainwindow, qtbot, monkeypatch) -> None:
    deploy_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Deployment')
    deploy_action = next(a for a in deploy_menu.menu().actions() if a.text() == '&Deploy')
    deploy_action.triggered.emit()
    assert mainwindow.newwindow.__class__ == DeployWindow
    assert mainwindow.newwindow.status == False
    
def test_status_menuitem(mainwindow, qtbot, monkeypatch) -> None:
    deploy_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Deployment')
    status_action = next(a for a in deploy_menu.menu().actions() if a.text() == '&Status')
    status_action.triggered.emit()
    assert mainwindow.newwindow.__class__ == DeployWindow
    assert mainwindow.newwindow.status == True