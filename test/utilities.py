
from functools import partial
import os
import sys
import time
import pytest
import signal
import subprocess
from subprocess import Popen
import re
import pdb
import gc
from pathlib import Path
import shutil
import time
from PyQt5.QtTest import QTest
from PyQt5.QtCore import QSize, Qt, QModelIndex
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QLineEdit, QStyle, QApplication
from nodeeditor.node_edge import EDGE_TYPE_BEZIER

from xmarte.nodeeditor.node_edge import XMARTeEdge
from xmarte.qt5.libraries.functions import getUserFolder
from xmarte.qt import XMARTeTool
# Always import martepy stuff after importing XMARTeTool
from martepy.marte2.reader import readApplicationText

TEST_FILES_DIR = os.path.join(os.getcwd(), 'test/files/')


def current_milli_time():
    return round(time.time() * 1000)

def wait_for_file(file_path, timeout=100, interval=0.5, exist=True):
    """Wait for a file to exist, with a specified timeout."""
    start_time = time.time()
    while not os.path.exists(file_path) == exist:
        if time.time() - start_time > timeout:
            raise TimeoutError(f"File {file_path} did not appear within {timeout} seconds.")
        time.sleep(interval)

@pytest.fixture(autouse=True)
def ensure_gc():
    gc.collect()

@pytest.fixture
def qapp():
    """Create a QApplication instance."""
    global app
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def mainwindow(qtbot, qapp, monkeypatch) -> XMARTeTool:
    user_path = os.path.join(os.path.abspath(str(Path.home())), r".xmarte/")
    
    if not os.path.exists(user_path):
        os.mkdir(user_path)

    config_file = os.path.join(user_path, 'config.yml')
    if os.path.exists(config_file):
        os.remove(config_file)
    wait_for_file(config_file, exist=False)
    
    # Reset type DB
    type_db = os.path.join(user_path, 'typedb')
    if os.path.exists(type_db):
        shutil.rmtree(type_db)
    wait_for_file(type_db, exist=False)

    # cp default_db/* ~/.xmarte/typedb/
    test_dir = os.path.abspath(os.path.dirname(__file__))
    default_db = os.path.join(test_dir, 'default_db')
    shutil.copytree(default_db, type_db)
    wait_for_file(type_db, exist=True)
    wait_for_file(os.path.join(type_db, 'test1_2_2.h'), exist=True)
    wait_for_file(os.path.join(type_db, 'test2_2_2.h'), exist=True)
    wait_for_file(os.path.join(type_db, 'test3_5_7.h'), exist=True)
    wait_for_file(os.path.join(type_db, 'std_import.h'), exist=True)
    
    monkeypatch.setattr(
        QMessageBox, 'question', lambda *args: QMessageBox.No
    )
    window = None
    window = XMARTeTool(qapp)
    window.show()
    qtbot.addWidget(window)
    window.test = True
    while not window.loaded:
        time.sleep(1)
        
    assert len(window.scene.nodes) == 0
    assert len(window.scene.edges) == 0
    return window

def compare_nodes(dict1, dict2):
    # Create filtered dictionaries excluding the specified keys
    ignore_keys = ['pos_x', 'pos_y', 'id', 'content', 'outputs', 'inputs', 'outputs_identities', 'input_identities']
    filtered_dict1 = {k: v for k, v in dict1.items() if k not in ignore_keys}
    filtered_dict2 = {k: v for k, v in dict2.items() if k not in ignore_keys}
    
    # Compare the filtered dictionaries
    for key, value in filtered_dict1.items():
        if key == 'outputsb' or key == 'inputsb':
            # We need a way of ignoring the fact that if the key is
            # NumberOfDimensions or NumberOfElements and the value 1, then it should ignore this
            for item1, item2 in zip(value, filtered_dict2[key]):
                assert item1[0] == item2[0]
                for second_key, second_value in item1[1]['MARTeConfig'].items():
                    if second_key == 'NumberOfElements':
                        if int(second_value) == 1:
                            if 'NumberOfElements' in list(item2[1]['MARTeConfig'].keys()):
                                assert item2[1]['MARTeConfig'][second_key] == second_value
                        else:
                            assert item2[1]['MARTeConfig'][second_key] == second_value
                    elif second_key == 'NumberOfDimensions':
                        if int(second_value) == 1:
                            if 'NumberOfDimensions' in list(item2[1]['MARTeConfig'].keys()):
                                assert item2[1]['MARTeConfig'][second_key] == second_value
                        else:
                            assert item2[1]['MARTeConfig'][second_key] == second_value
                    else:
                        assert item2[1]['MARTeConfig'][second_key] == second_value
            for item1, item2 in zip(filtered_dict2[key], filtered_dict1[key]):
                assert item1[0] == item2[0]
                for second_key, second_value in item1[1]['MARTeConfig'].items():
                    if second_key == 'NumberOfElements':
                        if int(second_value) == 1:
                            if 'NumberOfElements' in list(item2[1]['MARTeConfig'].keys()):
                                assert item2[1]['MARTeConfig'][second_key] == second_value
                        else:
                            assert item2[1]['MARTeConfig'][second_key] == second_value
                    elif second_key == 'NumberOfDimensions':
                        if int(second_value) == 1:
                            if 'NumberOfDimensions' in list(item2[1]['MARTeConfig'].keys()):
                                assert item2[1]['MARTeConfig'][second_key] == second_value
                        else:
                            assert item2[1]['MARTeConfig'][second_key] == second_value
                    else:
                        assert item2[1]['MARTeConfig'][second_key] == second_value

            continue
        if key not in list(filtered_dict2.keys()):
            raise Exception(f"key does not exist in second given node: {key}")
        if not filtered_dict2[key] == value:
            raise Exception(f"mismatch in comparison between {key} in both nodes")
    return True

def create_basic_diagram(mainwindow, qtbot):
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)  # add constantGAM
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(1).widget(), Qt.LeftButton)  # add conversionGAM
    mainwindow.scene.nodes[0].onDoubleClicked(None)  # configure constantGAM
    mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('1')  # add constant signal
    # Open signal window
    mainwindow.rightpanel.configbarBox.itemAt(5).widget().clicked.emit()
    # Set value of default
    signal_window = mainwindow.newwindow
    signal_window.signal_tbl.item(0,6).setText('5')
    # Save and close signal window
    signal_window.save_button.clicked.emit()
    mainwindow.scene.nodes[1].onDoubleClicked(None)  # configure conversionGAM
    mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('1')  # add conversion signal
    Edge = mainwindow.scene.getEdgeClass()  # get the edge class to create an edge
    XMARTeEdge(getActualScene(mainwindow), start_socket=mainwindow.scene.nodes[0].outputs[0], end_socket=mainwindow.scene.nodes[1].inputs[0], edge_type=2)  # add edge
    mainwindow.scene.nodes[1].onInputChanged(mainwindow.scene.nodes[1].inputs[0])
    assert mainwindow.scene.nodes[1].inputs[0].edges[0].start_socket.node.title == 'Constants (ConstantGAM)'
    assert mainwindow.scene.nodes[0].outputs[0].edges[0].end_socket.node.title == 'Conversion (ConversionGAM)'
    assert mainwindow.scene.edges[0].start_socket.node.title == 'Constants (ConstantGAM)'
    assert mainwindow.scene.edges[0].end_socket.node.title == 'Conversion (ConversionGAM)'

def setApplicationName(mainwindow, app_name):
    mainwindow.leftpanel.tab_wgt.widget(1).app_edt.setText(app_name)
    text = getSplitText(mainwindow)
    # Regex pattern
    pattern = r'\$(\w+) = \{\s*Class = RealTimeApplication'

    # Search for the pattern
    match = re.search(pattern, text)
    assert match.group(1) == app_name

def enableHTTP(mainwindow):
    mainwindow.leftpanel.tab_wgt.widget(1).http_use.setChecked(True)

    pattern = r'\+ResourcesHtml\s*=\s*\{\s*Class\s*=\s*HttpDirectoryResource\s*BaseDir\s*=\s*"(.*?)"\s*\}'

    # Search for the pattern in the multiline text
    match = re.search(pattern, getSplitText(mainwindow), re.DOTALL)
    assert match
    
def setHTTPFolder(mainwindow, folder):
    mainwindow.leftpanel.tab_wgt.widget(1).http_folder.loc.setText(folder)
    
    pattern = r'\+ResourcesHtml\s*=\s*\{\s*Class\s*=\s*HttpDirectoryResource\s*BaseDir\s*=\s*"(.*?)"\s*\}'
    match = re.search(pattern, getSplitText(mainwindow), re.DOTALL)
    assert match.group(1) == folder
    
def setHTTPMessage(mainwindow):
    mainwindow.leftpanel.tab_wgt.widget(1).config_msg.clicked.emit()
    httpWindow = mainwindow.newwindow
    httpWindow.add_remmsg.add_btn.clicked.emit()
    httpWindow.save_btn.clicked.emit()
    app = readApplicationText(getSplitText(mainwindow))[0]
    assert app.externals[1].objects[2].objects[0].destination == 'App'
    assert app.externals[1].objects[2].objects[0].function == 'StopCurrentStateExecution'
    assert int(app.externals[1].objects[2].objects[0].maxwait) == 0
    assert app.externals[1].objects[2].objects[0].mode == 'ExpectsReply'
    
def getActualScene(mainwindow):
    for state_name, state in mainwindow.state_scenes.items():
        for thread_name, thread in state.items():
            if id(thread) == id(mainwindow.scene):
                return thread
            
    return None

def get_list_items_as_text(list_widget):
    items_text = []
    for index in range(list_widget.count()):
        item = list_widget.item(index)
        items_text.append(item.text())
    return items_text

def create_complex_diagram(mainwindow, qtbot, monkeypatch):
    # We need a basic diagram to create a config
    create_basic_diagram(mainwindow, qtbot)
    # We also want to change some application parameters such as:
    # App name
    setApplicationName(mainwindow, 'TestApp')
    # GAMScheduler
    setScheduler(mainwindow, 'FastScheduler')
    # Set TimingDataSource
    setTimingDataSource(mainwindow, 'TestTiming')
    
    # States
    addThreadToState(mainwindow, qtbot, monkeypatch, 'State1', 'TestThread', '254')
    switchThread(mainwindow, 'State1', 'TestThread')
    assert mainwindow.scene.scene_name == 'State1-TestThread'
    assert len(mainwindow.scene.nodes) == 0
    assert len(mainwindow.scene.edges) == 0
    monkeypatch.setattr(
        QMessageBox, 'question', lambda *args: QMessageBox.No
    )
    create_basic_diagram(mainwindow, qtbot)
    # GAM DB's
    AddGAMDDB(mainwindow, 'DDBTest',qtbot)
    changeDataSource(mainwindow, mainwindow.scene.nodes[0], 'DDBTest')
    #changeDataSource(mainwindow, mainwindow.scene.nodes[1], 'DDBTest', 'inputsb')
    text = getSplitText(mainwindow)
    assert 'DDBTest' in getGAMSources(text)
    mainwindow.scene.nodes[0].onDoubleClicked(None)  # configure constantGAM
    line_edit = mainwindow.rightpanel.configbarBox.itemAt(1).widget()
    line_edit.setText('ConstantsTest')
    QTest.keyClick(line_edit, Qt.Key_Return)
    QTest.keyClick(line_edit, Qt.Key_Return)
    mainwindow.scene.nodes[1].onDoubleClicked(None)  # configure constantGAM
    line_edit = mainwindow.rightpanel.configbarBox.itemAt(1).widget()
    line_edit.setText('ConversionTest')
    QTest.keyClick(line_edit, Qt.Key_Return)
    QTest.keyClick(line_edit, Qt.Key_Return)
    text = getSplitText(mainwindow)
    test_thread_section = re.search(r'\+TestThread = {(.*?)\}', text, re.DOTALL)
    if test_thread_section:
        test_thread_section = test_thread_section.group(1)

    # Step 2: Extract the value associated with CPUs
        
    cpus_value = re.search(r'CPUs = (\S+)', test_thread_section)
    if cpus_value:
        cpus_value = cpus_value.group(1)
        
    assert cpus_value == '0xFE' or cpus_value == '0xfe'
    # Step 3: Extract values within the curly braces {} after Functions
    functions_values = re.search(r'Functions = \{([^{}]+)\}', test_thread_section + '}')
    if functions_values:
        functions_values = functions_values.group(1)
        functions_list = re.findall(r'\b\w+\b', functions_values)  # Extract individual words
    assert 'ConstantsTest' in functions_list
    assert 'ConversionTest' in functions_list
    
    # Setup HTTPex
    enableHTTP(mainwindow)
    setHTTPFolder(mainwindow, 'C:\Temp')
    setHTTPMessage(mainwindow)

def AddGAMDDB(mainwindow, gam_name, qtbot):
    mainwindow.leftpanel.tab_wgt.widget(1).g_edt.add_button.clicked.emit()
    listbox = mainwindow.leftpanel.tab_wgt.widget(1).g_edt.listbox
    listitem = listbox.item(listbox.count()-1)
    qtbot.waitExposed(listbox)
    item_rect = listbox.visualItemRect(listitem)
    qtbot.waitExposed(listitem)
    QTest.qWait(1000)
    qtbot.mouseDClick(listbox.viewport(), Qt.LeftButton, pos=item_rect.center())
    qtbot.mouseDClick(listbox.viewport(), Qt.LeftButton, pos=item_rect.center())
    lineedit = listbox.findChild(QLineEdit)
    QTest.keyClicks(lineedit, gam_name)
    QTest.keyClick(lineedit, Qt.Key_Enter)
    qtbot.waitExposed(listitem)
    QTest.qWait(500)
    assert listitem.text() == gam_name
    
def changeDataSource(mainwindow, node, data_source, attr='outputsb'):
    mainwindow.scene.nodes[0].onDoubleClicked(None)
    # Open signal window
    mainwindow.rightpanel.configbarBox.itemAt(5).widget().clicked.emit()
    # Set value of default
    signal_window = mainwindow.newwindow
    signal_window.signal_tbl.item(0,1).setText(data_source)
    # Save and close signal window
    signal_window.save_button.clicked.emit()
    outputs = getattr(node, attr)
    assert outputs[0][1]['MARTeConfig']['DataSource'] == data_source

def setScheduler(mainwindow, scheduler):
    index = mainwindow.leftpanel.tab_wgt.widget(1).sched_combo.findText(scheduler)
    mainwindow.leftpanel.tab_wgt.widget(1).sched_combo.setCurrentIndex(index)
    text = getSplitText(mainwindow)
    pattern = '\+Scheduler\s*=\s*{\s*Class\s*=\s*(\w+)'
    match = re.search(pattern, text)
    assert match.group(1) == scheduler

def setTimingDataSource(mainwindow, timing_name):
    mainwindow.leftpanel.tab_wgt.widget(1).t_edt.setText(timing_name)
    text = getSplitText(mainwindow)
    pattern = r'\+(\w+)\s*=\s*{\s*Class\s*=\s*TimingDataSource\s*'
    match = re.search(pattern, text)
    assert match.group(1) == timing_name
    pattern = r'TimingDataSource\s*=\s*(\w+)'
    match = re.search(pattern, text)
    assert match.group(1) == timing_name

def addThreadToState(mainwindow, qtbot, monkeypatch, state, thread_name, cpu_mask):
    mainwindow.API.getServiceByName('StateDefinitionService').state_machine.clicked.emit()
    state_window = mainwindow.newwindow
    index = find_state_event(state_window, state)
    state_window.statetree.scrollTo(index)
    qtbot.mouseClick(state_window.statetree.viewport(), Qt.LeftButton, pos=state_window.statetree.visualRect(index).center())
    configbox = state_window.configBox
    configbox.add_thread_btn.clicked.emit()
    row = configbox.thread_tbl.rowCount() - 1
    configbox.thread_tbl.item(row,0).setText(thread_name)
    configbox.thread_tbl.item(row,1).setText(cpu_mask)
    monkeypatch.setattr(
        QMessageBox, 'question', lambda *args: QMessageBox.Save
    )
    state_window.close()
    thread_wgt = mainwindow.API.getServiceByName('StateDefinitionService').thread_wdgt
    assert thread_name in getStateThreads(thread_wgt)[state]

def getStateThreads(thread_wgt):
    # Initialize an empty dictionary to store parent and child items
    items_dict = {}

    # Iterate over the items in the QComboBox
    for index in range(thread_wgt.count()):
        item_text = thread_wgt.itemText(index)
        # Calculate the level of indentation
        indent_level = item_text.count('    ')  # Count the number of '    ' strings

        if indent_level == 0:
            # Parent item
            parent_item = item_text
            items_dict[parent_item] = []
        else:
            # Child item
            child_item = item_text.strip()  # Remove leading/trailing whitespace
            parent_key = list(items_dict.keys())[-1]  # Get the last added parent item
            items_dict[parent_key].append(child_item)
    return items_dict

def getGAMSources(text):
    pattern = r'\+(\w+)\s*=\s*{\s*Class\s*=\s*GAMDataSource\s*'
    return re.findall(pattern, text)

def getSplitText(mainwindow):
    mainwindow.API.getServiceByName('SplitView').split_button.clicked.emit()
    if mainwindow.rightpanel.split is None:
        mainwindow.API.getServiceByName('SplitView').split_button.clicked.emit()
    return mainwindow.rightpanel.split.toPlainText()

def switchThread(mainwindow, state, thread):
    thread_wgt = mainwindow.API.getServiceByName('StateDefinitionService').thread_wdgt
    index = find_item_index(thread_wgt, state, thread)
    thread_wgt.setCurrentIndex(index)

def find_state_event(state_window, state_event):
    model = state_window.statetree.model

    # Get the number of rows under the parent index
    rows = model.rowCount()

    for row in range(rows):
        # Get the index of the child item
        index = model.index(row, 0)
        
        # Check if the item's text matches the search text
        if index.isValid():
            item_text = index.data()
            if item_text == state_event.upper():
                return index
            
def find_item_index(comboBox, parent_name, child_name):
    for index in range(comboBox.count()):
        item_text = comboBox.itemText(index)

        # Calculate the level of indentation
        indent_level = item_text.count('    ')

        # Extract parent and child names
        if indent_level == 0:
            # Parent item
            parent_item = item_text
            child_items = []
        else:
            # Child item
            child_item = item_text.strip()
            child_items.append(child_item)

            # Check if the current item matches the given parent-child pair
            if parent_item == parent_name and child_item == child_name:
                return index

    # If the parent-child pair is not found, return None
    return None

def import_data(mainwindow, monkeypatch):
    import_file = os.path.join(TEST_FILES_DIR,'multi_states_threads.xmt')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'xmt (*.xmt)'))
    mainwindow.fileToolBar.openAction.triggered.emit()
    
    data_file = os.path.join(TEST_FILES_DIR,'test_data_import.csv')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (data_file, 'csv (*.csv)'))
    data_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Data Manager')
    import_action = next(a for a in data_menu.menu().actions() if a.text() == '&Import Data')
    import_action.triggered.emit()
    assert mainwindow.state_scenes['Error']['Thread1'].nodes[0].outputs[0].data == ['0']*503
    assert mainwindow.state_scenes['State1']['Thread2'].nodes[0].outputs[0].data == ['0']*503
    assert mainwindow.state_scenes['State1']['Thread2'].nodes[0].outputs[1].data == ['0']*503
    io_gam = next(a for a in mainwindow.state_scenes['State1']['Thread1'].nodes if a.title == 'IO (IOGAM)')
    assert io_gam.outputs[0].data == ['0']*503
    assert io_gam.outputs[1].data == ['0']*503
    constant_gam = next(a for a in mainwindow.state_scenes['State1']['Thread1'].nodes if a.title == 'Constants (ConstantGAM)')
    newsignal = next(a for a in constant_gam.outputs if a.label == 'newsignal')
    newsignal1 = next(a for a in constant_gam.outputs if a.label == 'newsignal1')
    assert newsignal.data == ['2.000000']*503
    assert newsignal1.data == ['0.300000']*503
    
def setup_complex_const(mainwindow, node, delete=True):
    mainwindow.rightpanel.configbarBox.itemAt(5).widget().clicked.emit()
    signal_window = mainwindow.newwindow
    signal_window.signal_tbl.item(0,6).setText('5')
    signal_window.signal_tbl.item(1,6).setText('{3,2}')
    signal_window.signal_tbl.item(2,6).setText('1')
    signal_window.signal_tbl.item(0,0).setText('Signal1')
    signal_window.signal_tbl.item(1,0).setText('TestSignal')
    signal_window.signal_tbl.item(2,0).setText('Signal2')
    assert signal_window.signal_tbl.item(0,5).text() == 'Signal1'
    assert signal_window.signal_tbl.item(1,5).text() == 'TestSignal'
    assert signal_window.signal_tbl.item(2,5).text() == 'Signal2'
    signal_window.signal_tbl.item(0,1).setText('DDB0')
    signal_window.signal_tbl.item(1,1).setText('DDBTest')
    signal_window.signal_tbl.item(2,1).setText('DDB2')
    signal_window.signal_tbl.item(0,2).setText('uint64')
    signal_window.signal_tbl.item(1,2).setText('uint8')
    signal_window.signal_tbl.item(2,2).setText('float32')
    signal_window.signal_tbl.item(1,4).setText('2')
    assert len(node.outputs) == 3
    assert signal_window.signal_tbl.rowCount() == 3
    if delete:
        signal_window.signal_tbl.cellWidget(0,7).clicked.emit()
        assert signal_window.signal_tbl.rowCount() == 2
    return signal_window

def create_const_for_input(mainwindow, qtbot):
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)
    node = mainwindow.scene.nodes[-1]
    node.onDoubleClicked(None)
    mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('3')
    signal_window = setup_complex_const(mainwindow, node, False)
    signal_window.save_button.clicked.emit()
    return node

def create_io_for_output(mainwindow, qtbot):
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(3).widget(), Qt.LeftButton)
    node = mainwindow.scene.nodes[-1]
    node.onDoubleClicked(None)
    mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('3')
    mainwindow.rightpanel.configbarBox.itemAt(7).widget().setText('3')
    return node
    
def connect_io(mainwindow, qtbot):
    io_node = create_io_for_output(mainwindow, qtbot)
    sdn_node = mainwindow.scene.nodes[0]
    Edge(mainwindow.scene, sdn_node.outputs[0], io_node.inputs[0], EDGE_TYPE_BEZIER)
    Edge(mainwindow.scene, sdn_node.outputs[1], io_node.inputs[1], EDGE_TYPE_BEZIER)
    Edge(mainwindow.scene, sdn_node.outputs[2], io_node.inputs[2], EDGE_TYPE_BEZIER)
    for i in range(3):
        io_node.onInputChanged(io_node.inputs[i])
    return io_node

def custom_send_to_server():
    # Custom code to be executed during the test
    
    try:
        sim_folder = os.path.join(getUserFolder(), 'temp')

        if os.path.exists(os.path.join(sim_folder,'output.csv')):
            os.remove(os.path.join(sim_folder,'output.csv'))
        if os.name == "nt":
            sim_folder = "/mnt/" + str(sim_folder).replace('C:','c').replace('\\','/')
            cmd = f"/root/Projects/marte.sh -l RealTimeLoader -f Simulation.cfg -m StateMachine:START"
        else:
            cmd = f"/root/Projects/marte.sh -l RealTimeLoader -f Simulation.cfg -m StateMachine:START"
            
        
        start = current_milli_time()
        
        p = Popen(cmd.split(), cwd=sim_folder, start_new_session=True)#, stdout=subprocess.PIPE)#, stderr=subprocess.STDOUT)
        
        def monitor_process(proc):
            try:
                # Read the output line by line
                for line in iter(proc.stdout.readline, b''):
                    line = line.decode('utf-8').strip()
            
                    # Check for the specific line
                    if "[Information - MARTeApp.cpp:155]: [FileWriter] - instances: 0" in line or current_milli_time() < (start + 20000):
                        # Kill the process
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                        print("Process terminated because the specific line was found.")
                        break
            except Exception as e:
                print(f"An error occurred: {e}")
        
        monitor_process(p)
        p.wait()
        shutil.copy(os.path.join(sim_folder, 'output.csv'), os.path.join(sim_folder, 'log_0.csv'))
    except KeyboardInterrupt:
        pass
    
def my_custom_popen(cmd, *args, **kwargs):
    print(f"Custom Popen called with: {cmd}")
    class MockProcess:
        def __init__(self):
            custom_send_to_server()  # Simulate a non-zero exit code to test error handling

        def wait(self):
            return 0

        def communicate(self):
            return 0
        
        def quit(self):
            return 0

    return MockProcess()

class MockFTP():
    def __init__(self, settings):
        self.settings = settings
        
    def returnme(self):
        return self
    
    def connect(self, hostname, ftp_port):
        assert hostname == self.settings['RemotePanel']['remote_server']
        assert ftp_port == int(self.settings['RemotePanel']['remote_ftp_port'])
        
    def login(self, username, password):
        # When we deleted the temp directory it should reset to the defaults
        assert username == 'admin'
        assert password == 'admin'

    def storbinary(self, command, file_in):
        return
    
    def retrbinary(self, command, file_in):
        return
    
    def nlst(self):
        return ['Hello']
    
    def mkd(self, string_dir):
        return
    
    def cwd(self, dir):
        return

    def quit(self):
        return

def mockID(url, timeout=0):
    class simplereq():
        def read(self):
            return 'dhekhfkhefkdjshflks'.encode('ASCII')
        
    return simplereq()