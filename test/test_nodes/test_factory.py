
from collections import OrderedDict
import pytest
import pdb
from ..utilities import *

from xmarte.nodeeditor.node_edge import XMARTeEdge
from nodeeditor.node_edge import EDGE_TYPE_BEZIER

from martepy.marte2.reader import readApplicationText

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QWidget, QPushButton
from xmarte.qt5.nodes.marte2_node import MARTe2Node

def test_factory(mainwindow, qtbot):
    assert mainwindow.factories['nodes'].getAll() == [MARTe2Node]
    mainwindow.factories['nodes'].getNodes()
    assert mainwindow.factories['nodes'].create('blah') == False
    mainwindow.factories['nodes'].unregisterBlock('MARTe2Node')
    mainwindow.factories['nodes'].unloadAll()
    mainwindow.factories['nodes'].loadOnlyClass('MARTe2Node')
    top_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    factory_path = os.path.join(top_dir, 'xmarte','qt5','nodes', "nodes.json")
    mainwindow.factories['nodes'].loadRemote(factory_path)