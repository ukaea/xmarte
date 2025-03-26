import copy
import pytest
import yaml
import os
import base64

from cryptography.fernet import Fernet

from test.utilities import *
from unittest.mock import patch
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QCoreApplication
from xmarte.qt5.windows.settings_window import SettingsWindow
from xmarte.qt5.libraries.functions import getUserFolder

top_dir = os.getcwd()

def open_settings_menu(mainwindow) -> None:
    # Start by resetting the settings
    config_mgr = mainwindow.API.getServiceByName("ConfigManager")
    settings = config_mgr._generateSettingsYaml()
    config_mgr.saveSettings(settings)
    mainwindow.settings = settings
    # Open and return the window
    adv_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Advanced')
    options_action = next(a for a in adv_menu.menu().actions() if a.text() == '&Options...')
    options_action.triggered.emit()
    assert mainwindow.newwindow.__class__ == SettingsWindow
    return mainwindow.newwindow
    
def test_panels_available(mainwindow):
    settings_wnd = open_settings_menu(mainwindow)
    options = [settings_wnd.options.item(a).text() for a in range(settings_wnd.options.count())]
    assert options == ['General', 'Remote Execution','Compilation','Defaults','Test Configuration'] # If you add a panel, don't just update this! Create two similar tests as below for it

def test_modify_general_save(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    settings_wnd.options.setCurrentRow(0) # Select the general tab
    # Try every button
    split_types = [settings_wnd.panel.sview_type.itemText(a) for a in range(settings_wnd.panel.sview_type.count())]
    assert split_types == ['The MARTe2 executable config file'] # if you add supported files, you need to add it here also
    self = settings_wnd.panel
    self.file_ext.setText('xms')
    self.filed_ext.setText('Test bespoke configuration')
    
    # Not sure if to test file browser default location
    # Instead what we do is remember the last location the user used in dialog
    # windows and use that instead
    #self.dtool.setCurrentIndex(self.dtool.findText('WinMerge'))
    
    settings_wnd.save_btn.clicked.emit()

    # Now test that our changes have taken affect
    with patch.object(QFileDialog, 'getSaveFileName', return_value=('test.xms', 'Test bespoke configuration (*.xms)')) as mock_dialog:
        mainwindow.fileToolBar.saveAction.trigger()
        # Check that the dialog was called with the correct parameters
        mock_dialog.assert_called_with(
            mainwindow.fileToolBar, 
            "Save Project", 
            top_dir, 
            "Test bespoke configuration (*.xms);;All Files (*)"
        )

        # Check the returned value
        file_name, selected_filter = mock_dialog.return_value
        assert file_name == 'test.xms'
        assert selected_filter == 'Test bespoke configuration (*.xms)'

    # Diff is no longer a part of the general tab - not tested yet as no feature set for this yet.
    
def test_modify_general_cancel(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    settings_wnd.options.setCurrentRow(0) # Select the general tab
    # Try every button
    split_types = [settings_wnd.panel.sview_type.itemText(a) for a in range(settings_wnd.panel.sview_type.count())]
    assert split_types == ['The MARTe2 executable config file'] # if you add supported files, you need to add it here also
    self = settings_wnd.panel
    self.file_ext.setText('xms')
    self.filed_ext.setText('Test bespoke configuration')
    
    settings_wnd.cancel_btn.clicked.emit()
    
    with patch.object(QFileDialog, 'getSaveFileName', return_value=('test.xmt', 'xMARTe Design (*.xmt)')) as mock_dialog:
        mainwindow.fileToolBar.saveAction.trigger()
        # Check that the dialog was called with the correct parameters
        mock_dialog.assert_called_with(
            mainwindow.fileToolBar, 
            "Save Project", 
            top_dir, 
            "xMARTe Design (*.xmt);;All Files (*)"
        )

        # Check the returned value
        file_name, selected_filter = mock_dialog.return_value
        assert file_name == 'test.xmt'
        assert selected_filter == 'xMARTe Design (*.xmt)'
    
def go_to_panel(settings_wnd, index):
    settings_wnd.options.setCurrentItem(settings_wnd.options.item(index))
    QCoreApplication.processEvents()
    settings_wnd.options.clicked.emit(settings_wnd.options.indexFromItem(settings_wnd.options.item(index)))
    QCoreApplication.processEvents()

def set_remote(settings_wnd):
    self = settings_wnd.panel
    self.server_chk.setChecked(False)
    self.server_edt.setText('127.0.0.1')
    self.port_edt.setText('1')
    self.ftp_port_edt.setText('2')
    self.ftp_user_edt.setText('test_user')
    self.ftp_pass_edt.setText('1234')

def test_modify_remote_save(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd, 1)
    set_remote(settings_wnd)

    settings_wnd.save_btn.clicked.emit()
    
    copy_settings = copy.deepcopy(mainwindow.settings['RemotePanel'])
    del copy_settings['ftp_username']
    del copy_settings['ftp_password']

    assert copy_settings == {'temp_folder': '/root/.xmarte/', 'use_remote': False, 'remote_server': '127.0.0.1', 'remote_http_port': '1', 'remote_ftp_port': '2'}
    
def test_modify_remote_cancel(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd, 1)
    set_remote(settings_wnd)

    settings_wnd.cancel_btn.clicked.emit()
    
    copy_settings = copy.deepcopy(mainwindow.settings['RemotePanel'])
    del copy_settings['ftp_username']
    del copy_settings['ftp_password']

    assert copy_settings == {'temp_folder': '/root/.xmarte/', 'use_remote': False, 'remote_server': '127.0.0.1', 'remote_http_port': '8001', 'remote_ftp_port': '8234'}
    
def set_compile(settings_wnd):
    self = settings_wnd.panel
    self.server_chk.setChecked(False)
    self.server_edt.setText('127.30747.232987.237947')
    self.port_edt.setText('1')
    self.ftp_port_edt.setText('2')
    self.ftp_user_edt.setText('test')
    self.ftp_pass_edt.setText('testpass')
    self.server_static_chk.setChecked(False)

def test_modify_compile_save(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd, 2)
    set_compile(settings_wnd)

    settings_wnd.save_btn.clicked.emit()
    
    copy_settings = copy.deepcopy(mainwindow.settings['CompilationPanel'])
    del copy_settings['ftp_username']
    del copy_settings['ftp_password']
    assert copy_settings == {'temp_folder': '/root/.xmarte/compile', 'use_remote': False, 'remote_server': '127.30747.232987.237947',
                            'remote_http_port': '1', 'remote_ftp_port': '2', 'static': False}
    
def test_modify_compile_cancel(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd,2)
    set_compile(settings_wnd)

    settings_wnd.cancel_btn.clicked.emit()
    
    copy_settings = copy.deepcopy(mainwindow.settings['CompilationPanel'])
    del copy_settings['ftp_username']
    del copy_settings['ftp_password']
    assert copy_settings == {'temp_folder': '/root/.xmarte/compile', 'use_remote': False, 'remote_server': '127.0.0.1', 'remote_http_port': '8012',
                            'remote_ftp_port': '8235',  'static': True}
    
def set_default(settings_wnd):
    self = settings_wnd.panel
    self.sched_combo.setCurrentText('FastScheduler')
    self.http_check.setChecked(True)
    self.httpfile.loc.setText('/jdgakjdg')
    self.timingdatasource.setText('Timidbueg')
    self.gamdatasource.setText('DDBIudij')

def test_modify_default_save(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd,3)
    set_default(settings_wnd)

    settings_wnd.save_btn.clicked.emit()
    
    copy_settings = copy.deepcopy(mainwindow.settings['DefaultPanel'])
    assert copy_settings == {'TimingDataSource': 'Timidbueg', 'GAMDataSource': 'DDBIudij', 'Scheduler': 'FastScheduler', 'use_http': True, 'HTTP_folder': '/jdgakjdg'}
    
def test_modify_default_cancel(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd,3)
    set_default(settings_wnd)

    settings_wnd.cancel_btn.clicked.emit()
    
    copy_settings = copy.deepcopy(mainwindow.settings['DefaultPanel'])
    assert copy_settings == {'TimingDataSource': 'TimingsDataSource', 'GAMDataSource': 'DDB0', 'Scheduler': 'GAMScheduler', 'use_http': False, 'HTTP_folder': ''}
    
def set_test(settings_wnd):
    self = settings_wnd.panel
    self.max_cycles.setText('4658')
    self.execution_rate_hz.setText('354')
    self.sched_combo.setCurrentText('MARTe2')

def test_modify_test_save(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd,4)
    set_test(settings_wnd)
    

    settings_wnd.save_btn.clicked.emit()
    
    copy_settings = copy.deepcopy(mainwindow.settings['TestPanel'])
    assert copy_settings == {'solver': 'MARTe2', 'Max Cycles': '4658', 'Execution Rate (Hz)': '354'}
    
def test_modify_test_cancel(mainwindow, monkeypatch, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd,4)
    set_test(settings_wnd)
    

    settings_wnd.cancel_btn.clicked.emit()
    
    copy_settings = copy.deepcopy(mainwindow.settings['TestPanel'])
    assert copy_settings == {'solver': 'MARTe2', 'Max Cycles': '500', 'Execution Rate (Hz)': '500'}

def test_save_to_file(mainwindow, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd,0)
    self = settings_wnd.panel
    self.file_ext.setText('xms')
    self.filed_ext.setText('Test bespoke configuration')
    go_to_panel(settings_wnd,1)
    set_remote(settings_wnd)
    go_to_panel(settings_wnd,2)
    set_compile(settings_wnd)
    go_to_panel(settings_wnd,3)
    set_default(settings_wnd)
    go_to_panel(settings_wnd,4)
    set_test(settings_wnd)

    config_file = os.path.join(getUserFolder(),'config.yml')
    os.remove(config_file)

    wait_for_file(config_file, exist=False)

    settings_wnd.save_btn.clicked.emit()

    wait_for_file(config_file)

    with open(config_file, encoding='utf-8') as yamlfile:  # read plugin info from yaml
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
    del data['CompilationPanel']['ftp_password']
    del data['CompilationPanel']['ftp_username']
    del data['RemotePanel']['ftp_password']
    del data['RemotePanel']['ftp_username']
    assert data == {'CompilationPanel': {'remote_ftp_port': '2', 'remote_http_port': '1', 'remote_server': '127.30747.232987.237947',
                                         'static': False, 'temp_folder': '/root/.xmarte/compile', 'use_remote': False},
                    'DefaultPanel': {'GAMDataSource': 'DDBIudij', 'HTTP_folder': '/jdgakjdg', 'Scheduler': 'FastScheduler',
                                     'TimingDataSource': 'Timidbueg', 'use_http': True},
                   'GeneralPanel': {'diff_tool': 'meld', 'file_description': 'Test bespoke configuration', 'file_extension': 'xms',
                                    'file_location': top_dir, 'split_view': 'MARTe2ConfigFormat', 'test_handler': 'marte2'},
                   'RemotePanel': {'remote_ftp_port': '2', 'remote_http_port': '1', 'remote_server': '127.0.0.1', 'temp_folder': '/root/.xmarte/',
                                   'use_remote': False}, 'TestPanel': {'Execution Rate (Hz)': '354', 'Max Cycles': '4658', 'solver': 'MARTe2'},
                  'gui': {'scene_height': 6400, 'scene_width': 6400}, 
                  'hidden': {'recovery_document': '/root/.xmarte/recovery.xmt'}}

def test_cancel_to_file(mainwindow, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd,0)
    self = settings_wnd.panel
    self.file_ext.setText('xms')
    self.filed_ext.setText('Test bespoke configuration')
    go_to_panel(settings_wnd,1)
    set_remote(settings_wnd)
    go_to_panel(settings_wnd,2)
    set_compile(settings_wnd)
    go_to_panel(settings_wnd,3)
    set_default(settings_wnd)
    go_to_panel(settings_wnd,4)
    set_test(settings_wnd)

    settings_wnd.cancel_btn.clicked.emit()

    with open(os.path.join(getUserFolder(),'config.yml'), encoding='utf-8') as yamlfile:  # read plugin info from yaml
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        
    del data['CompilationPanel']['ftp_password']
    del data['CompilationPanel']['ftp_username']
    del data['RemotePanel']['ftp_password']
    del data['RemotePanel']['ftp_username']
    assert data == {'CompilationPanel': {'remote_ftp_port': '8235', 'remote_http_port': '8012', 'remote_server': '127.0.0.1', 'static': True, 'temp_folder': '/root/.xmarte/compile', 'use_remote': False}, 
                    'DefaultPanel': {'GAMDataSource': 'DDB0', 'HTTP_folder': '', 'Scheduler': 'GAMScheduler', 'TimingDataSource': 'TimingsDataSource', 'use_http': False},
                   'GeneralPanel': {'diff_tool': 'meld', 'file_description': 'xMARTe Design', 'file_extension': 'xmt', 'file_location': top_dir, 'split_view': 'MARTe2ConfigFormat', 'test_handler': 'marte2'}, 
                   'RemotePanel': {'remote_ftp_port': '8234', 'remote_http_port': '8001', 'remote_server': '127.0.0.1', 'temp_folder': '/root/.xmarte/', 'use_remote': False}, 
                   'TestPanel': {'Execution Rate (Hz)': '500', 'Max Cycles': '500', 'solver': 'MARTe2'}, 
                   'gui': {'scene_height': 6400, 'scene_width': 6400}, 
                   'hidden': {'recovery_document': '/root/.xmarte/recovery.xmt'}}

# Function to load the key
def load_key():
    if not os.path.exists(os.path.join(getUserFolder(),'secret.key')):
        # Generate a key
        key = Fernet.generate_key()

        # Save the key to a file
        with open(os.path.join(getUserFolder(),'secret.key'), 'wb') as key_file:
            key_file.write(key)
    return open(os.path.join(getUserFolder(),'secret.key'), 'rb').read()

# Load the previously generated key
key = load_key()
cipher = Fernet(key)

def test_encrypt_password(mainwindow, qtbot):
    settings_wnd = open_settings_menu(mainwindow)
    go_to_panel(settings_wnd,1)
    set_remote(settings_wnd)
    go_to_panel(settings_wnd,2)
    set_compile(settings_wnd)

    settings_wnd.save_btn.clicked.emit()
    with open(os.path.join(getUserFolder(),'config.yml'), encoding='utf-8') as yamlfile:  # read plugin info from yaml
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
    encrypted_data = data['CompilationPanel']['ftp_password']
    decrypted_data = base64.decodebytes(cipher.decrypt(str(encrypted_data)[2:-1])).decode('utf-8')
    assert decrypted_data == 'testpass'
    encrypted_data = data['CompilationPanel']['ftp_username']
    decrypted_data = base64.decodebytes(cipher.decrypt(str(encrypted_data)[2:-1])).decode('utf-8')
    assert decrypted_data == 'test'
    encrypted_data = data['RemotePanel']['ftp_password']
    decrypted_data = base64.decodebytes(cipher.decrypt(str(encrypted_data)[2:-1])).decode('utf-8')
    assert decrypted_data == '1234'
    encrypted_data = data['RemotePanel']['ftp_username']
    decrypted_data = base64.decodebytes(cipher.decrypt(str(encrypted_data)[2:-1])).decode('utf-8')
    assert decrypted_data == 'test_user'