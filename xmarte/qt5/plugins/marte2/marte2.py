'''Definition of MARTe2GUIPlugin class.'''

import os
import martepy
from martepy.marte2.factory import Factory

from PyQt5.QtWidgets import (
    QGroupBox,
    QPushButton,
    QWidget,
    QSizePolicy,
    QGridLayout,
)

from xmarte.qt5.plugins.base_plugin import GUIPlugin
from xmarte.qt5.plugins.marte2.file_handlers.cfg import MARTe2ConfigFormat
from xmarte.qt5.plugins.widgets.hover_button import HoverButton

class MARTe2GUIPlugin(GUIPlugin):
    '''Definition of the MARTe2 graphical plugin.'''
    plugin_name = "marte2"
    plugin_description = """This is the MARTe2 plugin"""
    file_handlers = [MARTe2ConfigFormat]

    def __init__(self, application):
        super().__init__(application)

        # Create the factories
        self.factory = Factory()
        self.datasource_factory = Factory()
        datadir = os.path.dirname(martepy.__file__)

        # Create the services
        for service in self.getServices():
            self.registerService(service(self.application))

        # Create the file handlers
        for handler in self.getFileHandlers():
            self.registerFileHandler(handler(self.application))

        self.factory.loadRemote(  # load plugin gams
            os.path.abspath(
                os.path.join(
                    datadir,
                    'marte2',
                    'gams',
                    'gams.json'
                )
            )
        )
        self.datasource_factory.loadRemote(  # load plugin datasources
            os.path.abspath(
                os.path.join(
                    datadir,
                    'marte2',
                    'datasources',
                    'datasources.json'
                )
            )
        )
        self.loadNodes(self.application.leftpanel.toolboxes)  # load GUI functions
        self.application.factories['marte2'] = self.factory
        self.application.factories['marte2_datasources'] = self.datasource_factory

    @staticmethod
    def getServices():
        return []

    @staticmethod
    def getFileHandlers() -> list:
        return [MARTe2ConfigFormat]

    def loadNodes(self, toolboxes):
        '''
        Load our toolbox of blocks we provide in the plugin
        '''
        blocks = []
        for block in self.factory.getAll():
            if block not in blocks:
                blocks.append(block)
        row = 0
        column = 0
        marte2 = QGroupBox("marte2 functions")
        marte2.plugin = "marte2"
        toolboxes.insertWidget(0,marte2)
        toolboxes.marte2_functions = marte2
        marte2.gbox = QGridLayout()
        marte2.setLayout(marte2.gbox)
        for block in list(blocks):
            block_action = HoverButton(block.__name__, parent=self.application, tooltip=block.__doc__)
            block_action.setObjectName(block.__name__)
            block_action.clicked.connect(self.addBlock)
            marte2.gbox.addWidget(block_action, row, column)
            block_action.show()
            setattr(marte2.gbox, block.__name__, block_action)
            if column == 2:
                row = row + 1
                column = 0
            else:
                column = column + 1
        if column != 2:
            for i in range((2 - column)):
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
                marte2.gbox.addWidget(spacer, row, column + i)

        # Some datasources we need to know but the user cannot use as a function:
        # TimingDataSource
        # GAMDataSource
        # 
        
        blacklist = ['TimingDataSource','GAMDataSource']

        blocks = list(self.datasource_factory.getAll())
        blocks = set([item for item in blocks if item.__name__ not in blacklist])
        row = 0
        column = 0
        marte2 = QGroupBox("marte2 datasources")
        marte2.plugin = "marte2"
        toolboxes.insertWidget(1,marte2)
        toolboxes.marte2_datasources = marte2
        marte2.gbox = QGridLayout()
        marte2.setLayout(marte2.gbox)
        for block in list(blocks):
            block_action = HoverButton(block.__name__, parent=self.application, tooltip=block.__doc__)
            block_action.setObjectName(block.__name__)
            block_action.clicked.connect(self.addDatasource)
            marte2.gbox.addWidget(block_action, row, column)
            block_action.show()
            setattr(marte2.gbox, block.__name__, block_action)
            if column == 2:
                row = row + 1
                column = 0
            else:
                column = column + 1
        if column != 2:
            for i in range((2 - column)):
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
                marte2.gbox.addWidget(spacer, row, column + i)

    def addDatasource(self, _):
        '''
        Add a requested datasource and override it's input changed listener
        '''
        sending_button = self.application.sender()
        name = str(sending_button.objectName())
        _ = self.createDatasource(name)

    def createDatasource(self, name):
        ''' create a node given it's datasource name '''
        block_class = self.datasource_factory.create(name)
        block = block_class()
        block.label = name
        return self.application.API.toNode(block)

    def addBlock(self, _):
        '''
        Add a requested block and override it's input changed listener
        '''
        sending_button = self.application.sender()
        name = str(sending_button.objectName())
        _ = self.createNode(name)

    def createNode(self, name):
        ''' create a node given it's block name '''
        block_class = self.factory.create(name)
        block = block_class()
        block.label = name
        return self.application.API.toNode(block)

def registerPlugin(application):
    '''Register the plugin.'''
    plugin_object = MARTe2GUIPlugin(application)
    return plugin_object.pluginDescription()

def getPluginClass():
    '''Return the plugin class.'''
    return MARTe2GUIPlugin
