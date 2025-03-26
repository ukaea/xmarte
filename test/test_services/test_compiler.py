
import os
import shutil
from test.utilities import *
import warnings
from urllib import request
from ftplib import FTP
from unittest.mock import patch
from io import BytesIO

from PyQt5.QtCore import QCoreApplication

from xmarte.qt5.libraries.functions import getUserFolder

def create_compilable_files(mainwindow):
    type_service = mainwindow.API.getServiceByName("TypeDefinitionService")
    compile_settings = mainwindow.settings['CompilationPanel']
    paths = type_service.gen()
    # Decide whether to compile
    if os.path.exists(compile_settings['temp_folder']):
        shutil.rmtree(compile_settings['temp_folder'])
    shutil.copytree(type_service.output_path, compile_settings['temp_folder'])

def check_files_in_subfolders(root_folder):
    # Iterate over all items in the root folder
    for item in os.listdir(root_folder):
        item_path = os.path.join(root_folder, item)
        
        # Check if the item is a directory
        if os.path.isdir(item_path):
            # Construct expected file names based on subfolder name
            expected_a_file = os.path.join(item_path, f"{item}.a")
            expected_so_file = os.path.join(item_path, f"{item}.so")
            
            # Check if both files exist
            assert os.path.exists(expected_a_file) and os.path.exists(expected_so_file)

def delete_folder_contents(folder_path):
    # Iterate over all items in the folder
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        
        # Check if the item is a file or a directory and delete it accordingly
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.unlink(item_path)  # Remove the file or symbolic link
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)  # Remove the directory and its contents

def test_compile_locally(mainwindow):
    compile_settings = mainwindow.settings['CompilationPanel']
    if os.path.exists(compile_settings['temp_folder']):
        delete_folder_contents(compile_settings['temp_folder'])
    create_compilable_files(mainwindow)
    compile_service = mainwindow.API.getServiceByName("Compiler")
    compile_service.compileLocally(mainwindow.settings['CompilationPanel']['temp_folder'])
    
    # Now it's compiled, test the compilation    
    output_dir = os.path.join(compile_settings['temp_folder'], 'Build', 'x86-linux', 'Packets')
    assert os.path.exists(output_dir)

    check_files_in_subfolders(output_dir)

def set_server_settings(mainwindow):
    # Start by resetting the settings
    config_mgr = mainwindow.API.getServiceByName("ConfigManager")
    settings = config_mgr._generateSettingsYaml()
    config_mgr.saveSettings(settings)
    mainwindow.settings = settings
    # Open and return the window
    adv_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Advanced')
    options_action = next(a for a in adv_menu.menu().actions() if a.text() == '&Options...')
    options_action.triggered.emit()
    settings_wnd = mainwindow.newwindow
    index = 2
    settings_wnd.options.setCurrentItem(settings_wnd.options.item(index))
    QCoreApplication.processEvents()
    settings_wnd.options.clicked.emit(settings_wnd.options.indexFromItem(settings_wnd.options.item(index)))
    QCoreApplication.processEvents()
    self = settings_wnd.panel
    self.server_edt.setText('10.208.17.3')
    settings_wnd.save_btn.clicked.emit()

def test_compile_on_server(mainwindow, monkeypatch):
    compile_settings = mainwindow.settings['CompilationPanel']
    if os.path.exists(compile_settings['temp_folder']):
        delete_folder_contents(compile_settings['temp_folder'])
    create_compilable_files(mainwindow)
    compile_service = mainwindow.API.getServiceByName("Compiler")
    set_server_settings(mainwindow)
    #try:
    if True:
        mockftp = MockFTP(mainwindow.settings)
        mockftp.settings['RemotePanel']['remote_server'] = mainwindow.settings['CompilationPanel']['remote_server']
        mockftp.settings['RemotePanel']['remote_ftp_port'] = mainwindow.settings['CompilationPanel']['remote_ftp_port']
        with patch('ftplib.FTP', new=mockftp.returnme):
            with patch('urllib.request.urlopen', new=mockID):
                compile_service.compileOnServer()
                # Now it's compiled, test the compilation    
                output_dir = os.path.join(compile_settings['temp_folder'], 'Build', 'x86-linux', 'Packets')
                assert os.path.exists(output_dir)

                check_files_in_subfolders(output_dir)
    #except OSError:
    #    warnings.warn("""Could not contact server.""", UserWarning)
    
    assert compile_service.getDefaultSettings() == {}

def test_compile_relative_dir(mainwindow):
    compile_service = mainwindow.API.getServiceByName("Compiler")
    assert sorted(compile_service.getDirectoryContentsWithRelativePaths(os.path.join(TEST_FILES_DIR, 'type_db'))) == ['AELM_2_2.h', 'BELM_2_2.h', 'KC1E_5_7.h', 'stdrtdn.h']