
from matplotlib.pyplot import minorticks_off
import pytest
import pdb
import copy
import os
import csv
import glob
import shutil
from subprocess import Popen
import subprocess
from unittest.mock import patch

from xmarte.qt5.libraries.functions import getUserFolder
from xmarte.qt5.services.test_engine.test_run_thread import RunThread, AbortException
from xmarte.qt5.services.test_engine.windows.progress_window import TestProgressWindow
from xmarte.qt5.services.data_handler.data_handler import DataManager
from test.utilities import *
from unittest.mock import patch, MagicMock
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QMessageBox

def open_test_window(mainwindow):
    test_button = mainwindow.editToolBar.service_layout.itemAt(0).widget()
    test_button.clicked.emit()

def test_empty_diagram(mainwindow, mocker):
    test_button = mainwindow.editToolBar.service_layout.itemAt(0).widget()
    assert test_button.text() == '&Test'
    mock = mocker.patch('PyQt5.QtWidgets.QMessageBox.information')
    test_button.clicked.emit()
    mock.assert_called_once_with(mainwindow, "No data", "No nodes exist in the editor to test against")

def setup_basic(mainwindow, qtbot):
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)
    mainwindow.scene.nodes[0].onDoubleClicked(None)
    mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('3')
    open_test_window(mainwindow)
    test_window = mainwindow.newwindow
    return test_window

def test_autoconnect(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)
    auto_action = next(a for a in test_window.toolbar.actions() if a.text() == 'Autoconnect')
    linux_timer = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Timer (LinuxTimer)')
    timer_handler = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'TimerHandler (IOGAM)')
    constants = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)')
    sim_log = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'LoggingGAM (IOGAM)')

    linux_timer.outputs[1].edges[0].remove()
    for i in range(3):
        constants.outputs[i].edges[0].remove()
    # Trigger it
    auto_action.triggered.emit()

    assert linux_timer.outputs[1].edges[0].end_socket == timer_handler.inputs[0]
    for i in range(3):
        assert constants.outputs[i].edges[0].end_socket.node == sim_log

def test_reset_scene(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)
    reset_action = next(a for a in test_window.toolbar.actions() if a.text() == 'Reset Scene')
    linux_timer = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Timer (LinuxTimer)')
    timer_handler = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'TimerHandler (IOGAM)')
    constants = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)')
    sim_log = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'LoggingGAM (IOGAM)')

    linux_timer.outputs[1].edges[0].remove()
    for i in range(3):
        constants.outputs[i].edges[0].remove()

    constants.remove()
    linux_timer.remove()

    linux_timer = next((a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Timer (LinuxTimer)'), None)
    constants = next((a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)'), None)

    assert linux_timer == None
    assert constants == None

    #Reset
    reset_action.triggered.emit()

    linux_timer = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Timer (LinuxTimer)')
    constants = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)')
    timer_handler = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'TimerHandler (IOGAM)')
    sim_log = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'LoggingGAM (IOGAM)')

    assert constants is not None
    assert linux_timer is not None

    assert linux_timer.outputs[1].edges[0].end_socket == timer_handler.inputs[0]
    for i in range(3):
        assert constants.outputs[i].edges[0].end_socket.node == sim_log


def test_add_constant(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)
    const_btn = next(a for a in test_window.tab_wgt.toolboxes.itemAt(0).widget().children() if hasattr(a, 'text') and a.text() == 'ConstantGAM')
    const_btn.clicked.emit()
    const_btn.clicked.emit()
    assert len([a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)']) == 3
    
def test_add_filereader(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)
    file_btn = next(a for a in test_window.tab_wgt.toolboxes.itemAt(0).widget().children() if hasattr(a, 'text') and a.text() == 'FileReader')
    file_btn.clicked.emit()
    file_btn.clicked.emit()
    assert len([a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'FileReader (FileReader)']) == 2
    
def test_reset_all(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)
    reset_action = next(a for a in test_window.toolbar.actions() if a.text() == 'Reset All Scenes')
    linux_timer = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Timer (LinuxTimer)')
    timer_handler = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'TimerHandler (IOGAM)')
    constants = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)')
    sim_log = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'LoggingGAM (IOGAM)')

    linux_timer.outputs[1].edges[0].remove()
    for i in range(3):
        constants.outputs[i].edges[0].remove()

    constants.remove()
    linux_timer.remove()

    linux_timer = next((a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Timer (LinuxTimer)'), None)
    constants = next((a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)'), None)

    assert linux_timer == None
    assert constants == None

    #Reset
    reset_action.triggered.emit()

    linux_timer = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Timer (LinuxTimer)')
    constants = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)')
    timer_handler = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'TimerHandler (IOGAM)')
    sim_log = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'LoggingGAM (IOGAM)')

    assert constants is not None
    assert linux_timer is not None

    assert linux_timer.outputs[1].edges[0].end_socket == timer_handler.inputs[0]
    for i in range(3):
        assert constants.outputs[i].edges[0].end_socket.node == sim_log

def test_save_def(mainwindow, qtbot, monkeypatch):
    test_window = setup_basic(mainwindow, qtbot)
    import_file = os.path.join(TEST_FILES_DIR, 'test_def.xmtest')
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (import_file, 'xmarte test configuration (*.xmtest);;'))
    test_window.menuBar().children()[1].children()[0].menu().actions()[4].trigger()

def test_load_def(mainwindow, qtbot, monkeypatch):
    test_window = setup_basic(mainwindow, qtbot)
    import_file = os.path.join(TEST_FILES_DIR, 'test_def.xmtest')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmarte test configuration (*.xmtest);;'))
    test_window.menuBar().children()[1].children()[0].menu().actions()[3].trigger()
    
def test_export_as(mainwindow, qtbot, monkeypatch):
    test_window = setup_basic(mainwindow, qtbot)
    import_file = os.path.join(TEST_FILES_DIR, 'test_def.cfg')
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (import_file, 'MARTe2cfg (*.cfg);;'))
    test_window.menuBar().children()[1].children()[0].menu().actions()[2].trigger()
    
def test_save(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)
    test_window.menuBar().children()[1].children()[0].menu().actions()[1].trigger()
    assert mainwindow.test_definition == test_window.exportDef()

def test_deselected(mainwindow,qtbot):
    test_window = setup_basic(mainwindow, qtbot)
    constants = next(a for a in test_window.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)')
    constants.onDoubleClicked(None)
    test_window.deselected()
    assert test_window.main_wgt.right_panel_wgt.parameterbar == None

def test_run_thread(mainwindow, qtbot):
    ''' This test provides the barebones to testing this complex thread and patching what is needed
    In future we can add additional test cases:
    - Run a test with a special Type
    - Check generated CSV for assertions of values
    - Check Exceptions are thrown as expected
    - Check signals are emitted as expected
    
    This also gives us the basic framework for overriding other areas of the code for testing
    '''
    # setup
    test_window = setup_basic(mainwindow, qtbot)
    settings = mainwindow.settings
    files = []
    
    # Test exception handling
    thread = RunThread(settings, files, mainwindow.API.getServiceByName('TypeDefinitionService'),mainwindow.API.getServiceByName('Compiler'))
    e = ''
    with pytest.raises(AbortException, match=f"Could not generate configuration file because of error {str(e)}"):
        thread.generateConfig()
        
    thread.sim_app_def = test_window.sim_app_def
    temp_dir = os.path.join(mainwindow.settings['RemotePanel']['temp_folder'], "temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    thread.generateLibraries()
    # Need to add in assertion of what is generated - need to add in a config which requires a type. Use multi type xmt.
    
    with qtbot.waitSignal(thread.label_update, check_params_cb=lambda value: value == 'Hello World'):
        thread.updateProgress('Hello World', 42)
    with qtbot.waitSignal(thread.progress_update, check_params_cb=lambda value: value == 42):
        thread.updateProgress('Hello World', 42)
        
    thread.remote_settings["use_remote"] = False
    thread.generateConfig()
    # Need to mock the cmd or docker commands
    with patch('subprocess.Popen', new=my_custom_popen):
        thread.executeConfig()
        pass
    # Assert that the config gets made
    mockftp = MockFTP(mainwindow.settings)
    thread.remote_settings["use_remote"] = True
    with patch('ftplib.FTP', new=mockftp.returnme):
        with patch('urllib.request.urlopen', new=mockID):
            thread.run()
            #test_window.run_simulation()
    # It's easiest to test progress window here as well
    #test_window.prog_window.thread_finished(0)
    
def test_prog_error_handling_server(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)    
    # Mock the QMessageBox and simulate the "Yes" response
    with patch('PyQt5.QtWidgets.QMessageBox.exec_', return_value=QMessageBox.Yes) as mock_msg_box:
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            test_window.prog_window.showErrorMessage("Ahhhhhh")
                

def test_prog_error_handling(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)

    mainwindow.settings['RemotePanel']["use_remote"] = False
    # Mock the QMessageBox and simulate the "Yes" response
    with patch('PyQt5.QtWidgets.QMessageBox.exec_', return_value=QMessageBox.Yes) as mock_msg_box:
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            test_window.prog_window.showErrorMessage("Ahhhhhh")
    
def test_callbacks_in_prog(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)

    test_window.prog_window.show()

    wnd = test_window.prog_window
    wnd.progressBarCallback(25)
    
    assert wnd.progress_bar.value() == 25
    
    wnd.progressLabelCallback('Hello')
    
    assert wnd.progress_lbl.text() == 'Hello'
    
    wnd.progressTextCallback('Hello there')
    
    assert wnd.progress_textbox.toPlainText() == '\nHello there'
    
def test_simple_close_prog_wnd(mainwindow, qtbot):
    test_window = setup_basic(mainwindow, qtbot)

    test_window.prog_window.show()
    
    test_window.prog_window.cancelThread()
    
class threadMock():
    def isRunning(self):
        return True
    
class workerMock():
    def interrupt(self):
        return True
    
def test_close_prog_wnd(mainwindow, qtbot, monkeypatch):
    test_window = setup_basic(mainwindow, qtbot)

    def mock_question(*args, **kwargs):
        return QMessageBox.Yes

    test_window.prog_window.show()
    test_window.prog_window.worker = workerMock()
    test_window.prog_window.thread = threadMock()
    monkeypatch.setattr(QMessageBox, 'question', mock_question)
    test_window.prog_window.cancelThread()
