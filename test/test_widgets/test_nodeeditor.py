import pdb
from PyQt5.QtGui import QKeySequence
from xmarte.nodeeditor.node_graphics_node import XMARTeQDMGraphicsNode
import pytest
import os
import re


from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QGraphicsItem
from qtpy.QtCore import QPoint

from test.utilities import *

from xmarte.qt5.widgets.nodeditor import EditorWidget
from xmarte.qt5.nodes.marte2_node import MARTe2Node

class mockobj():
    pass

class mockApp(QWidget):
    def __init__(self):
        super().__init__()

class mockGRNode(XMARTeQDMGraphicsNode):
    def __init__(self, node):
        super().__init__(node)
        
    def initSizes(self):
        pass
    
    def initAssets(self):
        pass
    
    def initUI(self):
        pass

    def scenePos(self):
        return QPoint()

def test_nodeeditor(qapp, qtbot, monkeypatch):
    app = mockApp()
    editor = EditorWidget(application=app)
    app.scene = editor.scene
    editor.view.addSetSceneListener(mockobj)
    assert len(editor.view._set_scene_listeners) == 1
    editor.view.clearSetSceneListeners()
    assert len(editor.view._set_scene_listeners) == 0
    node = MARTe2Node(app.scene, app)
    def override_selected():
        return [mockGRNode(node)]
    editor.fileSave('testfile.scene')
    wait_for_file('testfile.scene', exist=True)
    assert len(app.scene.nodes) == 1
    app.scene.clear()
    assert len(app.scene.nodes) == 0
    editor.fileLoad('testfile.scene')
    assert len(app.scene.nodes) == 1
    #editor.view.scene().removeItem = override_remove_gr
    editor.view.scene().selectedItems = override_selected
    # Testing deletion of edges i
    QTest.keyPress(editor.view, Qt.Key_Delete)
    assert len(app.scene.nodes) == 0
    qtbot.keySequence(editor.view, QKeySequence("Ctrl+Z"))
    assert len(app.scene.nodes) == 1
    qtbot.keySequence(editor.view, QKeySequence("Ctrl+Shift+Z"))
    assert len(app.scene.nodes) == 0
    qtbot.keySequence(editor.view, QKeySequence("Ctrl+Z"))
    assert len(app.scene.nodes) == 1
    qtbot.keySequence(editor.view, QKeySequence("Ctrl+C"))
    qtbot.keySequence(editor.view, QKeySequence("Ctrl+V"))
    assert len(app.scene.nodes) == 2
    # Cannot test the other editor Ctrl commands as they require the entire application
    