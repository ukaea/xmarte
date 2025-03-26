
from collections import OrderedDict
import pdb
import pytest

from unittest.mock import patch

from xmarte.qt5.widgets.node_editor_viewer import ViewNode

from ..utilities import *

from martepy.marte2.reader import readApplicationText

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QWidget, QPushButton, QVBoxLayout

from xmarte.qt5.windows.base_window import BaseWindow
from xmarte.qt5.widgets.path_browser import FileBrowser, FolderBrowser
from xmarte.qt5.widgets.base_scene import BaseScene
from xmarte.qt5.services.service import Service
from xmarte.qt5.libraries.functions import PluginException
from xmarte.qt5.services.test_engine.test_run_thread import RunThread

def test_base_window(mainwindow):
    wnd = BaseWindow(mainwindow)
    layout = QVBoxLayout()
    wnd.setCentralWidget(QWidget())
    wnd.centralWidget().setLayout(layout)
    def save():
        pass
    wnd.save = save
    wnd.cancel = save
    wnd.defineSaveCancelButtons(layout)

def test_filebrowser(mainwindow, monkeypatch):
    browser = FileBrowser(None, 'files','selector','.msn','msn file')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: ('helloworld.msn', 'msn file (*.msn)'))
    browser.browse()
    browser.linechange('helloworld')
    
def test_folderbrowser(mainwindow, monkeypatch):
    browser = FolderBrowser(None, 'files','selector')
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args, **kwargs: 'helloworld')
    browser.browse()
    browser.linechange('helloworld')
    
def test_base_scene(mainwindow):
    scene = BaseScene(mainwindow, False)
    scene.updateCounter(3)
    def nodeRem(node):
        pass
    scene.addNodeRemoveListener(nodeRem)
    scene.nodeRemovedListeners(None)
    
def test_editor(mainwindow):
    with patch.object(QMessageBox, 'warning', return_value=None):
        with pytest.raises(PluginException):
            mainwindow.editor.fileLoad('')

def test_interrupt():
    thrd = RunThread({'RemotePanel':{},'CompilationPanel':{}},[],None,None)
    thrd.interrupt()
    
def test_view_node(mainwindow):
    vnode = ViewNode(mainwindow.scene,[],[],'Hello')
    assert vnode.title == 'Hello'
    vnode.title = 'Hellob'
    
def test_basic_service():
    assert Service.getDefaultSettings() == {}
    class application():
        def __init__(self):
            self.settings = {'RemotePanel':{'temp_folder':'empty'}}
            
    Service(application()).getPluginDirectory()
    shutil.rmtree('empty')