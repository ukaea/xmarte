'''
Handles display of the split view window.
Loads each plugin's method for generating output.
'''
from qtpy.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QScrollArea, QPushButton
from xmarte.qt5.plugins.base_plugin import PluginException
from xmarte.qt5.services.service import Service


class SplitView(Service):
    '''Split view window.'''
    service_name = 'SplitView'
    def __init__(self, application) -> None:
        super().__init__(application)
        self.current_file_handler = ''
        self.addToolbarOptions(self.application.editToolBar.service_layout)

    def _getCurrentHandler(self):
        '''Get a reference to the current plugin.'''
        file_object = next(
            (a for a in self.application.file_handlers if a.getName() == self.current_file_handler),
            None)
        if file_object is None and len(self.application.file_handlers) > 0:
            file_object = self.application.file_handlers[0]
        return file_object

    def addToolbarOptions(self, layout):
        if self.application.file_handlers:
            self.split_format = QComboBox()
            for handler in self.application.file_handlers:
                self.split_format.addItem(handler.getName())
            self.split_format.currentTextChanged.connect(self.splitChange)
            layout.addWidget(self.split_format)
            self.split_button = QPushButton('Split View')
            self.split_button.clicked.connect(self.splitView)
            layout.addWidget(self.split_button)

    def createSplit(self, handler) -> None:
        '''Create the split view.'''
        self.application.rightpanel.scrollArea = QScrollArea(  # create split view
            self.application.rightpanel.splitter
        )
        self.application.rightpanel.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.application.rightpanel.splitter.addWidget(self.application.rightpanel.scrollArea)
        self.application.rightpanel.splitter.setSizes([150, 150])
        self.updateSplit(handler)
        self.application.rightpanel.splitter.addWidget(self.application.rightpanel.scrollArea)
        self.application.rightpanel.splitter.setSizes([150, 150])
        self.application.rightpanel.split.update()  # update the split view with the output

    def deleteSplit(self) -> None:
        '''Delete the split view.'''
        self.application.rightpanel.split.deleteLater()
        self.application.rightpanel.scrollArea.deleteLater()
        self.application.rightpanel.scrollArea = None
        self.application.rightpanel.split = None

    def updateSplit(self, handler) -> None:
        '''Update the text in the open split view window.'''
        app = self.application.API.buildApplication()
        self.application.API.errorCheck(app, showdialog=True)
        self.application.rightpanel.split = handler.generatesplit()  # generate the output
        self.application.rightpanel.scrollArea.setWidget(self.application.rightpanel.split)
        self.application.rightpanel.scrollArea.setMaximumHeight(
            self.application.rightpanel.splitter.height()
        )
        self.application.rightpanel.split.setFixedWidth(
            self.application.rightpanel.scrollArea.width()
        )

    def splitView(self) -> None:
        '''Split view button triggered.'''
        if self.application.loaded:  # check the application has finished loading up
            if not (handler := self._getCurrentHandler()):  # check a handler exists
                raise PluginException('No plugin found to generate split view!')

            if self.application.rightpanel.split:
                self.deleteSplit()
            else:
                self.createSplit(handler)

    def splitChange(self, text) -> None:
        '''Detect when the split format has changed.'''
        self.current_file_handler = text
        if self.application.rightpanel.split:
            self.deleteSplit()
