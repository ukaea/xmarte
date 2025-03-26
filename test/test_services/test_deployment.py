import pdb

from PyQt5.QtWidgets import QWidget, QMessageBox

from test.utilities import *

from xmarte.qt5.services.deployment.windows.deploy_window import DeployWindow

def test_deployment_wnd_deploy(qapp, qtbot, monkeypatch):
    mockParent = QWidget()
    mockParent.devices = []
    wnd = DeployWindow(mockParent, qapp)
    qtbot.waitSignal(wnd.udp_worker.finished_signal)
    wnd.drawDevices()
    wnd.deploy()
    monkeypatch.setattr(
        QMessageBox, 'question', lambda *args: QMessageBox.Yes
    )
    wnd.close()
    
def test_deployment_wnd_status(qapp, qtbot):
    mockParent = QWidget()
    mockParent.devices = []
    wnd = DeployWindow(mockParent, qapp, status=True)
    #qtbot.waitSignal(wnd.udp_worker.finished_signal)
    