
import pdb

from ...utilities import *
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QToolBar, QMessageBox
from xmarte.qt5.services.api_manager.widgets.error_widget import ErrorWidgetButton
from xmarte.qt5.services.api_manager.windows.error_check_wnd import AppErrorWindow

def test_error_lbl(mainwindow,qtbot,monkeypatch) -> None:
    # If we import a good cfg, it will display no errors
    import_file = os.path.join(TEST_FILES_DIR,'multi_states_threads.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    error_wgt = next(mainwindow.editToolBar.service_layout.itemAt(a).widget() for a in range(mainwindow.editToolBar.service_layout.count()) if mainwindow.editToolBar.service_layout.itemAt(a).widget().__class__ == ErrorWidgetButton)
    assert error_wgt.error_lbl.text() == "Errors: 0"
    # If we import a bad cfg, it will display the correct number of errors
    import_file = os.path.join(TEST_FILES_DIR,'bad_config.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    assert error_wgt.error_lbl.text() == "Errors: 2"

def test_error_btn(mainwindow,qtbot,monkeypatch) -> None:
    # If we click check errors, it will show the error window
    import_file = os.path.join(TEST_FILES_DIR,'bad_config.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    error_wgt = next(mainwindow.editToolBar.service_layout.itemAt(a).widget() for a in range(mainwindow.editToolBar.service_layout.count()) if mainwindow.editToolBar.service_layout.itemAt(a).widget().__class__ == ErrorWidgetButton)
    assert error_wgt.error_lbl.text() == "Errors: 2"
    error_wgt.open_wnd.clicked.emit()
    assert mainwindow.newwindow.__class__ == AppErrorWindow
    
def test_error_reset(mainwindow,qtbot,monkeypatch) -> None:
    # If we click check errors, it will show the error window
    import_file = os.path.join(TEST_FILES_DIR,'bad_config.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    error_wgt = next(mainwindow.editToolBar.service_layout.itemAt(a).widget() for a in range(mainwindow.editToolBar.service_layout.count()) if mainwindow.editToolBar.service_layout.itemAt(a).widget().__class__ == ErrorWidgetButton)
    error_wgt.reseterrors(mainwindow.API.buildApplication())

def test_error_split(mainwindow,qtbot,monkeypatch) -> None:
    # ToDo: Give it a working config, check that no messagebox appears
    import_file = os.path.join(TEST_FILES_DIR,'multi_states_threads.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    # Mock QMessageBox.question and assert it is not called
    with patch.object(QMessageBox, 'question', wraps=QMessageBox.question) as mock_question:
        getSplitText(mainwindow)
        mock_question.assert_not_called()
    # ToDo: Give it a bad config, check that messagebox appears
    import_file = os.path.join(TEST_FILES_DIR,'bad_config.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    # Check that if we click yes, it displays the error window
    # Create a MagicMock to return when QMessageBox.question is called
    mock_message_box = MagicMock(spec=QMessageBox)
    mock_message_box.exec.return_value = QMessageBox.Yes
    with patch.object(QMessageBox, 'question', return_value=mock_message_box.exec.return_value) as mock_question:
        getSplitText(mainwindow)
        mock_question.assert_called_once_with(mainwindow, "Error Review",
                                         "Errors were found in the application.\nWould you like to review these errors?",
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
        assert mock_question.return_value == QMessageBox.Yes
    assert mainwindow.newwindow.__class__ == AppErrorWindow
    # If we click no, it does not and simply displays the split View
    mainwindow.newwindow = None
    mock_message_box = MagicMock(spec=QMessageBox)
    mock_message_box.exec.return_value = QMessageBox.No
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.question) as mock_question:
        getSplitText(mainwindow)
        mock_question.assert_called_once_with(mainwindow, "Error Review",
                                         "Errors were found in the application.\nWould you like to review these errors?",
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

    with qtbot.waitExposed(mainwindow.rightpanel.split, timeout=1000) as blocker:
        assert not mainwindow.newwindow.__class__ == AppErrorWindow