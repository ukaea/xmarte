
import os
import shutil

from martepy.marte2.datasources import EPICSPublisher
from test.utilities import *
import warnings
from urllib import request
from ftplib import FTP
from unittest.mock import patch
from io import BytesIO

from PyQt5.QtCore import QCoreApplication

from xmarte.qt5.services.api_manager.api_manager import APIException

class falseNode():
    def __init__(self):
        self.btype = 'falseError'

def test_compile_locally(mainwindow):
    mainwindow.API.reloadFactories()
    mainwindow.API.registerNewAPIFunction('funk',None,None)
    with pytest.raises(APIException):
        mainwindow.API.toGAM(falseNode())
        
    mainwindow.API.datasourceToNode(EPICSPublisher())
    
    alias = ('hello',{'MARTeConfig':{}})
    assert mainwindow.API.getAlias(alias) == 'hello'
