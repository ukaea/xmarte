import pdb
import pytest
import os
import re
import shutil

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from xmarte.qt5.services.file_support.file_support import FileSupportService

from test.utilities import *

def test_upconvert_file(mainwindow, qtbot, monkeypatch) -> None:
    '''Test importing a file and loading a network.'''
    filepath = os.path.join(TEST_FILES_DIR,'really_old.xmt')
    shutil.copy(filepath, os.path.join(TEST_FILES_DIR,'really_old_backup.xmt'))
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (
            filepath,
            "xmt (*.xmt)",
        ),
    )
    mainwindow.fileToolBar.openAction.trigger()  # load network
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[0].title == 'ConstantsTest (ConstantGAM)'
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[1].title == 'ConversionTest (ConversionGAM)'
    shutil.copy(os.path.join(TEST_FILES_DIR,'really_old_backup.xmt'), filepath)
    
    assert FileSupportService.getDefaultSettings() == {}