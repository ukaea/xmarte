''' This service helps manage data stored and displayed from nodes themselves '''
import os

from PyQt5.QtWidgets import QMenu, QAction, QFileDialog
from xmarte.qt5.libraries.functions import updateDefaultDialogDir
from xmarte.qt5.services.data_handler.graph_window.graph_window import GraphWindow

from xmarte.qt5.services.service import Service
from .widgets.playback_widget import PlayToolbarWidget

class DataException(Exception):
    ''' A simple Exception case when the datahandler service receives bad data/commands '''

class DataManager(Service):
    '''
    This service will provide us with the menus to import data to our nodes, export it and playback
    '''
    service_name = 'DataManager'
    def __init__(self, application) -> None:
        super().__init__(application)
        self.playbackToolBar = None
        self.import_data_action = None
        self.clear_data_action = None

    def loadMenu(self, menu_bar):
        ''' Load our service menu '''
        dataMenu = QMenu("&Data Manager", menu_bar)
        self.import_data_action = QAction("&Import Data")
        self.import_data_action.triggered.connect(self.importData)
        dataMenu.addAction(self.import_data_action)
        self.clear_data_action = QAction("&Clear Data")
        self.clear_data_action.triggered.connect(self.clearData)
        dataMenu.addAction(self.clear_data_action)

        menu_bar.addMenu(dataMenu)

    def importData(self):
        ''' Import Data from a CSV into our nodes '''
        default_dir = ""
        if "file_location" in self.application.settings["GeneralPanel"].keys():
            default_dir = self.application.settings["GeneralPanel"]["file_location"]

        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(None, "Open File", default_dir,
                                                  "All Files (*);;CSV files (*.csv)",
                                                  options=options)
        if fileName:
            self.loadCSVData(fileName)
            self.application.settings["GeneralPanel"]["file_location"] = os.path.dirname(fileName)
            updateDefaultDialogDir(os.path.dirname(fileName))

    def addToolBar(self):
        ''' Add the playback toolbar '''
        self.playbackToolBar = PlayToolbarWidget("Playback", self.application)
        self.application.addToolBar(self.playbackToolBar)

    def openGraphWnd(self):
        ''' Open the Graph Window '''
        self.application.newwindow = GraphWindow(self.application,self)

    def clearData(self):
        ''' Clear all nodes of stored data '''
        for _, state in self.application.state_scenes.items():
            for _, thread in state.items():
                for node in thread.nodes:
                    for output in node.outputs:
                        output.data = None
        self.playbackToolBar.stopEvent()
        self.playbackToolBar.enableDisable(False)

    def loadCSVData(self, log_file_path): # pylint: disable=R0914
        ''' Load CSV data from file into our nodes '''
        D={}
        lines=open(log_file_path, encoding='utf-8').read().split('\n') # pylint: disable=R1732
        headers = lines[0].split(',')
        lines = lines[1:-1]
        values = [line.split(',') for line in lines]
        for header,index in zip(headers,range(len(headers))):
            D[header.replace('\n','').replace('#','')] = index
        if len(lines) == 0:
            raise DataException('''No output data was recorded, it is possible your configuration
 is unrunnable, you should check it locally or contact the support team.''')
        headers_simple = {key.split(' ')[0]: value for key, value in D.items()}
        for _, state in self.application.state_scenes.items():
            for _, thread in state.items():
                for node in thread.nodes:
                    for output in node.outputs:
                        if output.label in headers_simple:
                            # We have data for this output, get it's index
                            output_name = headers_simple[output.label]
                            output.data = [row[output_name] for row in values]
                            # Now load our data into our socket
        self.playbackToolBar.enableDisable(True)
        # Figure out maxcount
        self.playbackToolBar.counter_thread.maxcount = len(values) - 1
        self.playbackToolBar.aftlbl.setText(str(len(values) - 1))
