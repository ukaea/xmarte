
from ...utilities import *

from PyQt5.QtWidgets import QToolBar

def test_split_view(mainwindow, qtbot, monkeypatch):
    import_file = os.path.join(TEST_FILES_DIR,'multi_states_threads.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    assert not getSplitText(mainwindow) == 'No node blocks exist in the editor' and getSplitText(mainwindow)
    
def test_split_none(mainwindow, qtbot, monkeypatch):
    assert getSplitText(mainwindow) == 'No node blocks exist in the editor'

def test_split_notonthread(mainwindow, qtbot, monkeypatch):
    create_basic_diagram(mainwindow, qtbot)
    switchThread(mainwindow, 'Error', 'Thread1')
    assert not getSplitText(mainwindow) == 'No node blocks exist in the editor' and getSplitText(mainwindow)