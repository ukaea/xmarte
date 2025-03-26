'''
The main entry point to the XMARTe2 Graphical Application.
You can run this file directly or import this file and initialise the XMARTeTool
to start.
'''
# Ignore linting errors relating to module imports
# ruff: noqa: E402, F403, F405

import os
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout,
    QWidget, QMessageBox, QSplashScreen,
    QVBoxLayout
)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
import qdarkgraystyle

splash = None # pylint: disable=C0103

sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))

if __name__ == "__main__":
    app = QApplication([])
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    pixmap_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "splashscreen.jpg")
    )
    pixmap = QPixmap(pixmap_file)
    screen_resolution = QApplication.instance().desktop().screenGeometry().size()
    SIZE_RATIO = 0.5
    scaled_width = int(screen_resolution.width() * SIZE_RATIO)
    scaled_height = int(screen_resolution.height() * SIZE_RATIO)
    scaled_image = pixmap.scaled(scaled_width, scaled_height,
                                    aspectRatioMode=Qt.KeepAspectRatio)

    splash = QSplashScreen(scaled_image)
    splash.show()
    splash.setStyleSheet("font-size: 15px; font-weight: bold;")

    splash.showMessage("<h1><font color='white'>Importing modules...</font></h1>",
        Qt.AlignBottom | Qt.AlignLeft, QColor("white"))

from xmarte.qt5.services.config_manager import ConfigManager
from xmarte.qt5.widgets.menubar_widget import MARTeMenuBar
from xmarte.qt5.widgets.mainpanel_widget import MainPanelWidget
from xmarte.qt5.widgets.toolbar_widget import FileToolbarWidget, EditToolbarWidget
from xmarte.qt5.libraries.functions import loadPlugin
from xmarte.qt5.widgets.project_widget import ProjectWidget
from xmarte.qt5.widgets.nodeditor import EditorWidget
from xmarte.qt5.services import * # pylint: disable=W0614
from xmarte.qt5.exception_hook import * # pylint: disable=W0614

class XMARTeTool(QMainWindow):
    '''
    The main application instance of XMARTe GUI
    '''

    def __init__(self, application_instance=None):
        # Setup
        self.loaded = False
        super().__init__()
        self.hide()

        self.app = application_instance
        if splash:
            splash.showMessage("<h1><font color='white'>Initialising Variables...</font></h1>",
                               Qt.AlignBottom | Qt.AlignLeft, QColor("white"))

        if "pytest" not in sys.modules:
            top_lvl = os.path.dirname(__file__)
            css_file = os.path.join(top_lvl,'qt5','styles.css')
            with open(css_file, 'r', encoding='utf-8') as infile:
                style = infile.read()
                self.app.setStyleSheet(qdarkgraystyle.load_stylesheet() + style)
        # Accessed by other components
        # Initialize Components
        Nattributes = ['rightpanel', 'hbox', 'leftpanel','editToolBar','newwindow','fileToolBar']
        for attr in Nattributes:
            setattr(self, attr, None)

        self.editor = EditorWidget(application=self)
        self.scene = self.editor.scene

        arrays = ['devices', 'plugins', 'file_handlers']
        for array in arrays:
            setattr(self, array, [])

        dictionaries = ['factories', 'plugin_data', 'settings', 'settings_widgets']
        for dictionary in dictionaries:
            setattr(self, dictionary, {})

        self.doc_links = {
            'xmarte': 'https://github.com/ukaea/xmarte/',
            'marte2_python':
            'https://ukaea.github.io/MARTe2-python/',
        }
        self.API = APIManager(self)
        self.services = [ConfigManager(self), DataManager(self)]
        self.editParameterInput = self.emptyFunction
        self.test = False

        plugin_dir = os.path.join(self.settings["RemotePanel"]["temp_folder"], "plugins")
        if not os.path.exists(plugin_dir):
            os.mkdir(plugin_dir)

        if splash:
            splash.showMessage("<h1><font color='white'>Drawing...</font></h1>",
                               Qt.AlignBottom | Qt.AlignLeft, QColor("white"))

            splash.showMessage("<h1><font color='white'>Loading Plugins...</font></h1>",
                               Qt.AlignBottom | Qt.AlignLeft, QColor("white"))

        self.draw()

        self.services += [RecoveryService(self), ApplicationDefinition(self),
                          Compiler(self), FileSupportService(self)]
        self.services += [TestExecutor(self), StateDefinitionService(self)]
        # Manually load our check Error button
        self.API.addToolbarOptions(self.editToolBar.service_layout)

        self.loadPlugins()

        self.services += [SplitView(self), TypeDefinitionService(self)]

        self.editToolBar.findChild(QtWidgets.QLayout).setExpanded(True)
        # Connect the resize signal from the EditToolbarWidget to the slot in MainWindow
        self.editToolBar.resized.connect(self.fileToolBar.onEditToolbarResized)

        self.show()

        self.loaded = True
        self.API.getServiceByName("RecoveryService").loadRecovery()

    def show(self):
        ''' Override normal show method to ensure we don't have
        splash screen showing whilst we are showing'''
        if splash:
            splash.close()
        super().show()

    def emptyFunction(self, *args, **kwargs):
        ''' Overridable function by a plugin '''

    def loadPlugins(self):
        ''' Load our plugins '''
        if self.settings["plugins"]:
            for plugin in self.settings["plugins"]:
                if self.settings["plugins"][plugin]["status"] == "Enabled":
                    # We want to handle here that if we're in the one application instance
                    # our expectation is that a plugin has been added by a hook file as a data file
                    # into the /xmarte folder. therefore if we split at xmarte we
                    # should be able to figure out it's path
                    plugin_location = self.settings["plugins"][plugin]["location"]
                    new_plugin = loadPlugin(plugin_location, self)
                    self.plugins += [new_plugin] # pylint: disable=E1101

    def closeEvent(self, event):
        ''' close Event? '''
        event.ignore()
        self.exit()

    def exit(self):
        ''' So now we actually want this to also manage if the services handle exits. '''
        handled = False
        for service in self.services:
            handled = handled or service.exit()

        if not handled:
            if self.scene.has_been_modified:
                ret = QMessageBox.question(
                    self,
                    "",
                    "Are you sure you want to close the application without saving?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if ret == QMessageBox.Yes:
                    # Delete recovery doc
                    if os.path.exists(self.settings['hidden']['recovery_document']):
                        # os.remove(self.recovery_document)
                        pass
                    self.app.exit()
                    for w in QApplication.topLevelWindows():
                        del w
                    del self.app
            else:
                self.app.exit()
                for w in QApplication.topLevelWindows():
                    del w
                del self.app

    def draw(self):
        ''' Redraw everything as we may have loaded a new plugin '''
        if hasattr(self, "leftpanel") and self.leftpanel is not None:
            self.leftpanel.setParent(None)
            self.rightpanel.setParent(None)
            self.editToolBar.setParent(None)
            self.fileToolBar.setParent(None)
        self.createMenu()
        self.createToolbars()
        self.createWindow()

    def setTitle(self, append=""):
        ''' Set our window title - is overridable function '''
        self.setWindowTitle("XMARTe" + append)

    def createWindow(self):
        """Setup window parameters"""
        self.screen = self.app.primaryScreen()
        self.size = self.screen.size()
        self.setGeometry(
            int(self.size.width() * 0.1),
            int(self.size.height() * 0.1),
            int(self.size.width() * 0.8),
            int(self.size.height() * 0.8),
        )
        self.setTitle()
        # Redesign
        # Panels
        self.main_wgt = QWidget() # pylint: disable=W0201
        self.main_box = QVBoxLayout() # pylint: disable=W0201
        self.main_wgt.setLayout(self.main_box)
        self.first_widget = QWidget() # pylint: disable=W0201
        self.hbox = QHBoxLayout() # pylint: disable=W0201
        self.first_widget.setLayout(self.hbox)
        self.main_box.addWidget(self.first_widget)
        self.leftpanel = ProjectWidget(self) # pylint: disable=W0201
        self.rightpanel = MainPanelWidget(self, nodeeditor=self.editor) # pylint: disable=W0201
        self.hbox.addWidget(self.leftpanel)
        self.hbox.addWidget(self.rightpanel)
        self.setCentralWidget(self.main_wgt)

    def createMenu(self):
        ''' Create our menubar '''
        self.menuBar = MARTeMenuBar(self)

        self.setMenuBar(self.menuBar)

    def createToolbars(self):
        ''' Create our toolbars '''
        self.fileToolBar = FileToolbarWidget("File", self) # pylint: disable=W0201
        self.addToolBar(self.fileToolBar)

        self.editToolBar = EditToolbarWidget("Edit", self) # pylint: disable=W0201

        self.addToolBar(self.editToolBar)
        self.addToolBarBreak()
        for service in self.services:
            service.addToolBar()

if __name__ == "__main__":
    win = XMARTeTool(app)
    win.show()
    code = app.exec_()
