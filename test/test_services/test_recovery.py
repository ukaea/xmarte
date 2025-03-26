import time

from test.utilities import *


def test_recovery_blank(mainwindow, qtbot, qapp, monkeypatch):
    # It has been found if you run, add a const block, make 2 signals, crash the app
    # re-run, recover, the const block is not visible but somehow exists - causes issues elsewhere too
    recovery_file = os.path.join(getUserFolder(), 'recovery.xmt')
    if os.path.exists(recovery_file):
        os.remove(recovery_file)
    wait_for_file(recovery_file, exist=False)

    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)  # add constantGAM
    mainwindow.scene.nodes[0].onDoubleClicked(None)  # configure constantGAM
    mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('2')  # add constant signal
    
    wait_for_file(recovery_file, exist=True)

    # Now crash the app
    del mainwindow

    monkeypatch.setattr(
        QMessageBox, 'question', lambda *args: QMessageBox.Yes
    )
    window = None
    window = XMARTeTool(qapp)
    window.show()
    qtbot.addWidget(window)
    window.test = True
    while not window.loaded:
        time.sleep(1)
        
    switchThread(window, 'State1', 'Thread1')
        
    assert len(window.scene.nodes) == 1
    assert window.scene.nodes[0].title == 'Constants (ConstantGAM)'
    #assert len(window.scene.nodes[0].outputs) == 2
    