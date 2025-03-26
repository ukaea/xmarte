import pytest
import pdb
import copy
import os
import csv
import glob
import signal
import time
import datetime
import shutil
from subprocess import Popen
import subprocess
from xmarte.qt5.libraries.functions import getUserFolder
from xmarte.qt5.services.test_engine.test_run_thread import RunThread
from xmarte.qt5.services.data_handler.data_handler import DataManager
from test.utilities import *
from PyQt5.QtCore import QCoreApplication
import time

'''
Do not add tests to this file - it only works in isolation, something to do with subprocesses or mockers
'''

def open_test_window(mainwindow):
    test_button = mainwindow.editToolBar.service_layout.itemAt(0).widget()
    test_button.clicked.emit()

def setup_basic(mainwindow, qtbot):
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)
    mainwindow.scene.nodes[0].onDoubleClicked(None)
    mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('3')
    open_test_window(mainwindow)
    test_window = mainwindow.newwindow
    return test_window

def doNothinga(hostname, http_port, ftp_port, username, password, temp_directory):
    pass

def doNothingb():
    pass

def doNothingc(logfile):
    pass

def run_test(test_window, monkeypatch):
    log_file = os.path.join(getUserFolder(), 'temp', 'log_0.csv')
    output_file = os.path.join(getUserFolder(), 'temp', 'output.csv')
    if os.path.exists(log_file):
        os.remove(log_file)

    if os.path.exists(output_file):
        os.remove(output_file)

    sim_folder = os.path.join(getUserFolder(), 'temp')
    export_file = os.path.join(sim_folder, 'Simulation.cfg')
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (export_file, 'cfg (*.cfg)'))

    file_menu = next(a for a in test_window.menuBar().actions() if a.text() == "File")
    export_action = next(a for a in file_menu.menu().actions() if a.text() == "Export As...")
    export_action.triggered.emit()

    custom_send_to_server()
    
    assert os.path.exists(log_file)

    '''
    TODO: Run ascertion against expected data output
    '''

def test_run_basic(mainwindow, qtbot, mocker, monkeypatch, capsys):

    sim_folder = os.path.join(getUserFolder(), 'temp')
    if not os.path.exists(sim_folder):
        os.mkdir(sim_folder)
    # Set a test variable in the request.node object
    test_window = setup_basic(mainwindow, qtbot)
    with capsys.disabled():
        print("\nStarting basic test.")

    
    run_test(test_window, monkeypatch)
    
    with capsys.disabled():
        print("\nCompleted basic test successfully.")
    # close the test window and start testing against our directory
    test_dir = os.path.join('test', 'marte2_python','tests', 'frameworks', 'simulation_framework')
    sim_folder = os.path.join(getUserFolder(), 'temp')
    
    shutil.copy(os.path.join(test_dir, 'input.csv'), os.path.join(sim_folder, 'input.csv'))
    shutil.copy(os.path.join(test_dir, 'test1.so'), os.path.join(sim_folder, 'test1.so'))
    run_tests_against_directory(test_dir, monkeypatch, mainwindow, qtbot, capsys)
        
def discover_xmt_files(directory):
     """Discover all .xmt files in the specified directory."""
     return glob.glob(os.path.join(directory, '*.xmt'))

def run_tests_against_directory(directory, monkeypatch, mainwindow, qtbot, capsys):
    files = discover_xmt_files(directory)
    for filepath in files:
        with capsys.disabled():
            print(f"\ntesting {filepath}")
        monkeypatch.setattr(
            QFileDialog,
            "getOpenFileName",
            lambda *args, **kwargs: (
                filepath,
                "xmt (*.xmt)",
            ),
        )
        mainwindow.fileToolBar.openAction.trigger()
        open_test_window(mainwindow)
        test_window = mainwindow.newwindow
        file_menu = next(a for a in test_window.menuBar().actions() if a.text() == "File")
        run_action = next(a for a in file_menu.menu().actions() if a.text() == "Run")
    
        run_test(test_window, monkeypatch)
        with capsys.disabled():
            print(f"\nCompleted {filepath} test successfully.")

# def test_with_special_type(mainwindow, qtbot, mocker):
#     assert False

# def test_using_bespoke_user_built(mainwindow, qtbot, mocker):
#     # This test should prove that the user can inject their own GAMs into the test simulation
#     # and replace signals with that information rather than the reset template being used in test
#     assert False
    
# def test_load_def(mainwindow, qtbot, mocker):
#     assert False