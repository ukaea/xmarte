
from collections import OrderedDict
import pytest
import pdb
from ..utilities import *

from xmarte.nodeeditor.node_edge import XMARTeEdge
from nodeeditor.node_edge import EDGE_TYPE_BEZIER

from martepy.marte2.reader import readApplicationText

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QWidget, QPushButton

@pytest.fixture
def add_conv_to_diagram(mainwindow, qtbot):
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(1).widget(), Qt.LeftButton)
    assert mainwindow.scene.nodes[0].title == 'Conversion (ConversionGAM)'
    assert mainwindow.scene.nodes[0].btype == 'ConversionGAM'
    standard_dict = {'id': 140062545550160, 'title': 'Conversion (ConversionGAM)', 'pos_x': 3039.0, 'pos_y': 3132.5, 'inputs': [], 'outputs': [],
                     'content': OrderedDict(), 'plugin': 'marte2', 'class_name': 'ConversionGAM', 'configuration_name': 'Conversion', 'comment': '',
                    'parameters': {'Class name': 'ConversionGAM'}, 'inputsb': [], 'outputsb': [], 'outputs_identities': {}, 'input_identities': {},
                   'type': 'MARTe2Node', 'scene_name': 'State1-Thread1'}
    assert compare_nodes(dict(mainwindow.scene.nodes[0].serialize()), standard_dict)
    return mainwindow

@pytest.fixture
def modify_signal_no(add_conv_to_diagram):
    mainwindow = add_conv_to_diagram
    mainwindow.scene.nodes[0].onDoubleClicked(None)
    mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('3')
    assert len(mainwindow.scene.nodes[0].inputs) == 3
    assert mainwindow.scene.nodes[0].inputsb == [('newsignal', {'MARTeConfig': {'DataSource': '', 'Type': 'uint32', 'NumberOfDimensions': '1', 'NumberOfElements': '1', 'Alias': 'newsignal'}}),
                                                  ('newsignal1', {'MARTeConfig': {'DataSource': '', 'Type': 'uint32', 'NumberOfDimensions': '1', 'NumberOfElements': '1', 'Alias': 'newsignal1'}}),
                                                 ('newsignal2', {'MARTeConfig': {'DataSource': '', 'Type': 'uint32', 'NumberOfDimensions': '1', 'NumberOfElements': '1', 'Alias': 'newsignal2'}})]
    mainwindow.rightpanel.configbarBox.itemAt(7).widget().setText('3')
    assert len(mainwindow.scene.nodes[0].outputs) == 3
    assert mainwindow.scene.nodes[0].outputsb == [('newsignal', {'MARTeConfig': {'DataSource': 'DDB0', 'Type': 'uint32', 'NumberOfDimensions': '1', 'NumberOfElements': '1', 'Alias': 'newsignal'}}),
                                                  ('newsignal1', {'MARTeConfig': {'DataSource': 'DDB0', 'Type': 'uint32', 'NumberOfDimensions': '1', 'NumberOfElements': '1', 'Alias': 'newsignal1'}}),
                                                 ('newsignal2', {'MARTeConfig': {'DataSource': 'DDB0', 'Type': 'uint32', 'NumberOfDimensions': '1', 'NumberOfElements': '1', 'Alias': 'newsignal2'}})]
    return mainwindow

def setup_complex_conv(mainwindow, qtbot, delete=True):
    mainwindow.rightpanel.configbarBox.itemAt(8).widget().clicked.emit()
    signal_window = mainwindow.newwindow
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
    assert len(mainwindow.scene.nodes[0].outputs) == 3
    assert signal_window.signal_tbl.rowCount() == 3
    if delete:
        signal_window.signal_tbl.cellWidget(0,6).clicked.emit()
        assert signal_window.signal_tbl.rowCount() == 2
    const_node = create_const_for_input(mainwindow, qtbot)
    conv_node = mainwindow.scene.nodes[0]
    XMARTeEdge(mainwindow.scene, const_node.outputs[0], conv_node.inputs[0], EDGE_TYPE_BEZIER)
    XMARTeEdge(mainwindow.scene, const_node.outputs[1], conv_node.inputs[1], EDGE_TYPE_BEZIER)
    XMARTeEdge(mainwindow.scene, const_node.outputs[2], conv_node.inputs[2], EDGE_TYPE_BEZIER)
    for i in range(3):
        mainwindow.scene.nodes[0].onInputChanged(mainwindow.scene.nodes[0].inputs[i])
    
    mainwindow.rightpanel.configbarBox.itemAt(5).widget().clicked.emit()
    return signal_window

@pytest.fixture
def setup_complex(modify_signal_no, qtbot):
    mainwindow = modify_signal_no
    const_gam = create_const_for_input(mainwindow, qtbot)
    mainwindow.scene.nodes[0].onDoubleClicked(None)
    setup_complex_conv(mainwindow, qtbot)
    return mainwindow
    
def test_upstream(setup_complex, qtbot):
    mainwindow = setup_complex
    mainwindow.scene.nodes[0].doSelect()
    mainwindow.scene.nodes[1].doSelect()

def test_delete(setup_complex, qtbot):
    mainwindow = setup_complex
    mainwindow.scene.nodes[0].delete()
    
def modify_node(node):
    pass

def test_listeners(setup_complex, qtbot):
    mainwindow = setup_complex
    mainwindow.scene.nodes[0].deleteAllListener()
    mainwindow.scene.nodes[0].addModifiedListener(modify_node)
    mainwindow.scene.nodes[0].modifiedListenerFunction()
    mainwindow.scene.nodes[0].eval()
    
class FalseClass():
    pass

def test_equal(setup_complex, qtbot):
    mainwindow = setup_complex
    assert not mainwindow.scene.nodes[0] == FalseClass