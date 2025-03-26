import pdb
import pytest
import os
import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from test.utilities import *

def test_new(mainwindow, qtbot, monkeypatch) -> None:
    create_complex_diagram(mainwindow, qtbot, monkeypatch)
    
    # Then click new
    mainwindow.fileToolBar.newAction.trigger()
    # Now assert that these are no longer what they were set to before and have been reset
    assert len(mainwindow.scene.nodes) == 0
    assert len(mainwindow.scene.edges) == 0
    assert getStateThreads(mainwindow.API.getServiceByName('StateDefinitionService').thread_wdgt) == {'State1': ['Thread1'], 'Error': ['Thread1']}
    
    assert getSplitText(mainwindow) == 'No node blocks exist in the editor'
    assert mainwindow.API.getServiceByName('ApplicationDefinition').configuration == {'http': {'use_http': False, 'http_folder': ''}, 'misc': {'timingsource': 'TimingsDataSource', 'gamsources': ['DDB0'], 'scheduler': 'GAMScheduler'}, 'app_name': 'App'}
    assert mainwindow.API.getServiceByName('ApplicationDefinition').http_messages == []
    assert mainwindow.leftpanel.tab_wgt.widget(1).app_edt.text() == 'App'

def test_export_file(mainwindow, qtbot, monkeypatch):
    create_complex_diagram(mainwindow, qtbot, monkeypatch)
    import_file = os.path.join(TEST_FILES_DIR,'test_import.cfg')
    assert os.path.exists(import_file)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'cfg (*.cfg)'))
    mainwindow.fileToolBar.importAction.triggered.emit()
    export_file = os.path.join(TEST_FILES_DIR,'test_export.cfg')
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (export_file, 'cfg (*.cfg)'))
    mainwindow.fileToolBar.exportAction.triggered.emit()
    qtbot.waitUntil(lambda : os.path.exists(export_file))
    with open(import_file, 'r') as orig_file:
        orig_text = orig_file.read()

    with open(export_file, 'r') as new_file:
        new_text = new_file.read()

    assert orig_text == new_text

def test_import_file(mainwindow, qtbot, monkeypatch) -> None:
    '''Test importing a file and loading a network.'''
    import_file = os.path.join(TEST_FILES_DIR,'test_import.cfg')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'cfg (*.cfg)'))
    mainwindow.fileToolBar.importAction.triggered.emit()
    text = getSplitText(mainwindow)
    # Test App Name
    pattern = r'\$(\w+) = \{\s*Class = RealTimeApplication'
    match = re.search(pattern, text)
    assert match.group(1) == "TestApp"
    # Test GAMScheduler set
    pattern = '\+Scheduler\s*=\s*{\s*Class\s*=\s*(\w+)'
    match = re.search(pattern, text)
    assert match.group(1) == "FastScheduler"
    index = mainwindow.leftpanel.tab_wgt.widget(1).sched_combo.findText("FastScheduler")
    assert mainwindow.leftpanel.tab_wgt.widget(1).sched_combo.currentIndex() == index
    # Test DDB0's set
    listbox = mainwindow.leftpanel.tab_wgt.widget(1).g_edt.listbox
    testDDBs = ['DDB0', 'DDBTest']
    for i in range(listbox.count()):
        assert listbox.item(i).text() == testDDBs[i]
    # Test combobox wdgt def
    assert mainwindow.leftpanel.tab_wgt.widget(1).t_edt.text() == "TestTiming"
    pattern = r'\+(\w+)\s*=\s*{\s*Class\s*=\s*TimingDataSource\s*'
    match = re.search(pattern, text)
    assert match.group(1) == "TestTiming"
    pattern = r'TimingDataSource\s*=\s*(\w+)'
    match = re.search(pattern, text)
    assert match.group(1) == "TestTiming"
    # Test State Machine def
    state_service = mainwindow.API.getServiceByName('StateDefinitionService')
    app_def = state_service.app_def
    assert len(app_def.statemachine.states) == 3
    assert app_def.statemachine.states[1].configuration_name == '+STATE1'
    assert len(app_def.statemachine.states[1].objects) == 1
    thread_wgt = state_service.thread_wdgt
    items = [thread_wgt.itemText(i) for i in range(thread_wgt.count())]
    assert items == ['State1', '    Thread1', '    TestThread', 'Error', '    Thread1']
    assert list(mainwindow.state_scenes.keys()) == ['State1', 'Error']
    assert list(mainwindow.state_scenes['State1'].keys()) == ['Thread1', 'TestThread']
    assert list(mainwindow.state_scenes['Error'].keys()) == ['Thread1']
    for state_name, state in mainwindow.state_scenes.items():
        for thread_name, thread in state.items():
            assert thread.__class__.__name__ == "EditorScene"
    # Test each thread has the expected nodes
    assert len(mainwindow.state_scenes['Error']['Thread1'].nodes) == 0
    assert len(mainwindow.state_scenes['State1']['Thread1'].nodes) == 2
    assert len(mainwindow.state_scenes['State1']['TestThread'].nodes) == 2
    assert len(mainwindow.state_scenes['Error']['Thread1'].edges) == 0
    assert len(mainwindow.state_scenes['State1']['Thread1'].edges) == 1
    assert len(mainwindow.state_scenes['State1']['TestThread'].edges) == 1
    # Test each thread has the expected CPU Mask
    assert mainwindow.states[0].threads.objects[0].cpu_mask == 4294967295
    assert mainwindow.states[0].threads.objects[1].cpu_mask == 254
    assert mainwindow.states[1].threads.objects[0].cpu_mask == 4294967295
    # Test text output matches the file input
    with open(import_file, 'r') as orig_file:
        orig_text = orig_file.read()

    assert orig_text == text
    # Test the nodes defined
    assert mainwindow.state_scenes['State1']['Thread1'].nodes[0].parameters == {'Class name': 'ConstantGAM'}
    assert mainwindow.state_scenes['State1']['Thread1'].nodes[0].outputsb == [('newsignal', {'MARTeConfig': {'DataSource': 'DDB0', 'Type': 'uint32', 'Alias': 'newsignal', 'Default': '5'}})]
    assert mainwindow.state_scenes['State1']['Thread1'].nodes[0].inputsb == []
    assert mainwindow.state_scenes['State1']['Thread1'].nodes[0].title == 'Constants (ConstantGAM)'
    assert mainwindow.state_scenes['State1']['Thread1'].nodes[1].parameters == {'Class name': 'ConversionGAM'}
    assert mainwindow.state_scenes['State1']['Thread1'].nodes[1].outputsb == [('newsignal1', {'MARTeConfig': {'DataSource': 'DDBTest', 'Type': 'float32', 'Alias': 'newsignal2'}})]
    assert mainwindow.state_scenes['State1']['Thread1'].nodes[1].inputsb == [('newsignal1', {'MARTeConfig': {'DataSource': 'DDB0', 'Type': 'uint32', 'Alias': 'newsignal'}})]
    assert mainwindow.state_scenes['State1']['Thread1'].nodes[1].title == 'Conversion (ConversionGAM)'
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[0].parameters == {'Class name': 'ConstantGAM'}
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[0].outputsb == [('newsignal1', {'MARTeConfig': {'DataSource': 'DDBTest', 'Type': 'uint32', 'Alias': 'newsignal1', 'Default': '5'}})]
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[0].inputsb == []
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[0].title == 'ConstantsTest (ConstantGAM)'
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[1].parameters == {'Class name': 'ConversionGAM'}
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[1].outputsb == [('newsignal1', {'MARTeConfig': {'DataSource': 'DDBTest', 'Type': 'float32', 'Alias': 'newsignal3'}})]
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[1].inputsb == [('newsignal2', {'MARTeConfig': {'DataSource': 'DDBTest', 'Type': 'uint32', 'Alias': 'newsignal1'}})]
    assert mainwindow.state_scenes['State1']['TestThread'].nodes[1].title == 'ConversionTest (ConversionGAM)'

def test_save_open(mainwindow, monkeypatch, qtbot) -> None:
    '''Test saving a network, clearing, then loading the saved network.'''
    create_complex_diagram(mainwindow, qtbot, monkeypatch)
    
    filepath = os.path.join(TEST_FILES_DIR, "test_save.xmt")
    if os.path.exists(filepath):
        os.remove(filepath)
    qtbot.waitUntil(lambda : not os.path.exists(filepath))  # remove any existing file
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (
            filepath,
            "xmt (*.xmt)",
        ),
    )
    mainwindow.fileToolBar.saveAction.trigger()  # save network
    qtbot.waitUntil(lambda : os.path.exists(filepath))  # ensure file exists
    mainwindow.fileToolBar.newAction.trigger()  # clear network
    assert len(mainwindow.scene.nodes) == 0
    assert len(mainwindow.scene.edges) == 0
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (
            filepath,
            "xmt (*.xmt)",
        ),
    )
    mainwindow.fileToolBar.openAction.trigger()  # load network
    assert len(mainwindow.scene.nodes) == 2
    assert len(mainwindow.scene.edges) == 1
    mainwindow.scene.nodes[0].onDoubleClicked(None)
    assert int(mainwindow.scene.nodes[0].outputsb[0][1]['MARTeConfig']['Default']) == 5

def test_clear_network(mainwindow, monkeypatch, qtbot) -> None:
    '''Test clearing the network.'''
    create_basic_diagram(mainwindow, qtbot)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.Yes
    )
    mainwindow.editToolBar.clearAction.trigger()
    assert len(mainwindow.scene.nodes) == 0
