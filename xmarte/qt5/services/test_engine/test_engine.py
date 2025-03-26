'''
The Test Engine which provides capability to execute a network
on a remotely executing server or locally if your machine has docker installed and usable
(i.e. Linux)
'''

from PyQt5.QtWidgets import QPushButton, QMessageBox

from xmarte.qt5.services.service import Service
from .windows.test_window import TestWindow

class TestExecutor(Service):
    '''
    The Test Execution Class that can run our test and interact with the Test Window
    through Qt Signals
    '''
    service_name = 'TestExecutor'

    def __init__(self, application):
        super().__init__(application)
        self.addToolbarOptions(self.application.editToolBar.service_layout)
        self.application.test_definition = None

    def addToolbarOptions(self, layout):
        """
        This function is called at startup and allows you to add functions to the toolbar
        """
        testAction = QPushButton("&Test")
        testAction.clicked.connect(self.test)
        layout.addWidget(testAction)

    def test(self):
        """First we base this off our settings and what those might be
        - which should point to a plugin we pass this plugin to the test running Window"""
        num_nodes = 0
        for _, state in self.application.state_scenes.items():
            for _, thread_scene in state.items():
                num_nodes += len(thread_scene.nodes)
        if num_nodes > 0:
            self.application.newwindow = TestWindow(self.application, self.application.app)
        else:
            QMessageBox.information(self.application, "No data",
                                             "No nodes exist in the editor to test against")
