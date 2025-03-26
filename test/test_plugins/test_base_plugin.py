
from collections import OrderedDict
import pytest
import pdb
import os
import shutil
from ..utilities import *

from xmarte.nodeeditor.node_edge import XMARTeEdge
from nodeeditor.node_edge import EDGE_TYPE_BEZIER

from martepy.marte2.reader import readApplicationText

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QWidget, QPushButton
from xmarte.qt5.plugins.base_plugin import GUIPlugin, PluginException, FileHandlerPlugin

class application():
    def __init__(self):
        self.services = []
        self.settings = {'RemotePanel':{'temp_folder':''}}

class service():
    pass

def test_base_plugin():
    if not os.path.exists('plugins'):
        os.mkdir('plugins')
    basic = GUIPlugin(application())
    assert 'basic/basic.py' == basic.getPluginPath('basic')
    basic.registerService(service())
    with pytest.raises(PluginException):
        basic.registerService(service())
    
    with pytest.raises(NotImplementedError):
        basic.getServices()
    
    def returnMine():
        return [service()]
    basic.getServices = returnMine
    with pytest.raises(PluginException):
        basic.getServiceByClassName('hello')
    assert basic.getServiceByClassName('service').__class__.__name__ == 'service'

    with pytest.raises(NotImplementedError):
        basic.getFileHandlers()

    if os.path.exists("plugins"):
        shutil.rmtree("plugins")

def test_file_handler():
    handler = FileHandlerPlugin(application())
    assert handler.getDescription() == ''
    assert handler.getFileExtension() == ''
    if os.path.exists("plugins"):
        shutil.rmtree("plugins")