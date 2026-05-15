'''
The JSON file handler
'''

from PyQt5.QtCore import pyqtRemoveInputHook
import copy
import os
import shutil
from PyQt5 import QtCore
from PyQt5.QtWidgets import QListWidgetItem

from martepy.marte2.datasources import TimingDataSource
from martepy.marte2.datasources.gam_datasource import GAMDataSource
from martepy.marte2.objects.http.directoryresource import MARTe2HttpDirectoryResource
from martepy.marte2.reader import readApplication, TreeNode
from martepy.marte2.objects.http.objectbrowser import MARTe2HTTPObjectBrowser
from martepy.marte2.datasources.async_bridge import AsyncBridge
from martepy.marte2.datasources.logger_datasource import LoggerDataSource
from xmarte.qt5.libraries.functions import fixSocketOrdering
from xmarte.qt5.plugins.base_plugin import FileHandlerPlugin, SplitText
from xmarte.qt5.libraries.functions import fixSocketOrdering

class MARTe2PythonFormat(FileHandlerPlugin):
    '''Import and export MARTe2 configuration files.'''

    def _delete(self, path):
        '''
        Delete the file tree or file - this is useful internally
        '''
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            if os.path.isfile(path):
                os.remove(path)

    def createFileContents(self):
        '''
        Export to file
        '''
        application = self.application.API.buildApplication()
        self.application.API.errorCheck(application)
        return str(application.toPython())

    def loadFile(self, fname):
        '''
        Dynamically load python file and run getApplication()
        '''
        pass

    def generatesplit(self):
        '''
        Generate the widget for the split view of text of our file
        '''
        split = SplitText(handler=self)
        num_nodes = 0
        for state_name, state in self.application.state_scenes.items():
            for thread_name, thread_scene in state.items():
                num_nodes += len(thread_scene.nodes)
        if num_nodes > 0:
            split.setPlainText(self.createFileContents())
        else:
            split.setPlainText("No node blocks exist in the editor")
        return split

    @staticmethod
    def getDescription():
        return "The MARTe2 Python File"

    @staticmethod
    def getFileExtension():
        return "*.py"
