
import pdb

from ..utilities import *
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QToolBar, QMessageBox
from xmarte.qt5.services.api_manager.widgets.error_widget import ErrorWidgetButton
from xmarte.qt5.services.api_manager.windows.error_check_wnd import AppErrorWindow

def test_error_lbl(mainwindow,qtbot,monkeypatch) -> None:
    # If we import a good cfg, it will display no errors
    import_file = os.path.join(TEST_FILES_DIR,'multi_states_threads.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    app_def = mainwindow.API.getServiceByName('ApplicationDefinition')
    app_def.project_prop_panel.g_edt.listbox.setCurrentRow(0)
    with patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes):
        app_def.project_prop_panel.g_edt.removeItem()