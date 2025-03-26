'''
The Advanced Settings Window
'''
import copy

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
)
from PyQt5.QtCore import Qt

from xmarte.qt5.libraries.functions import GenericData
from xmarte.qt5.widgets.settings import GeneralPanel, DefaultPanel
from xmarte.qt5.services.test_engine.widgets.remote import RemotePanel
from xmarte.qt5.services.compilation.widgets.compilation_settings import CompilationPanel
from xmarte.qt5.services.test_engine.widgets.test_settings_panel import TestPanel

class SettingsWindow(QMainWindow):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self, application, app):
        self.application = application
        self.app = app
        super().__init__(application)
        self.setWindowTitle("Advanced Settings")

        self.setWindowModality(Qt.ApplicationModal)

        # Set Window Size
        self.screen = self.app.primaryScreen()
        self.size = self.screen.size()
        self.setGeometry(
            int(self.size.width() * 0.2),
            int(self.size.height() * 0.2),
            int(self.size.width() * 0.6),
            int(self.size.height() * 0.6),
        )
        self.setCentralWidget(QWidget(self))

        # Use copy of data so we can edit in the window and maintain between panels
        self.data = GenericData()
        self.data.settings = copy.deepcopy(self.application.settings)
        self.data.plugins = copy.copy(self.application.plugins)

        self.settingsoptions = self.getSettingsClasses()

        self.settingsoptions = {**self.settingsoptions, **self.application.settings_widgets}

        # Now add settings
        layout = QHBoxLayout()
        self.options = QListWidget()
        for i, panelk in enumerate(self.settingsoptions.keys()):
            self.options.insertItem(i, panelk)
        # This is so plugins can have registered panel setting

        self.options.clicked.connect(self.loadSettingsPanel)
        self.options.setCurrentRow(0)
        self.options.setFixedWidth(int(self.size.width() * 0.1))
        layout.addWidget(self.options)

        # Now add setting config box
        self.settingspanel = QWidget()
        layout.addWidget(self.settingspanel)
        self.vlayout = QVBoxLayout()
        self.settingspanel.setLayout(self.vlayout)
        self.panel = None
        self.loadSettingsPanel()
        self.centralWidget().setLayout(layout)

    @staticmethod
    def getSettingsClasses():
        ''' To do be replaced - return a statically defined set of panels to load '''
        return {
            "General": GeneralPanel,
            # Needs to be injected by service itself as above TODO.
            "Remote Execution": RemotePanel,
            # Needs to be injected by service itself as above TODO.
            "Compilation": CompilationPanel,
            # Needs to be injected by service itself as above TODO. - By App Def
            "Defaults": DefaultPanel,
            "Test Configuration": TestPanel,
        }

    def loadSettingsPanel(self):
        '''
        Load the panels
        '''
        for i in reversed(range(self.vlayout.count())):
            self.vlayout.itemAt(i).widget().setParent(None)

        selected = self.options.currentItem().text()

        panel = next(v for k, v in self.settingsoptions.items() if selected == k)

        self.panel = panel(self.settingspanel, self.data, self.application)
        self.vlayout.addWidget(self.panel)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.vlayout.addWidget(spacer)

        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.cancel)
        button_spacer = QWidget(self)
        button_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttons = QWidget(self)
        hlay = QHBoxLayout()
        hlay.addWidget(button_spacer)
        hlay.addWidget(self.save_btn)
        hlay.addWidget(self.cancel_btn)
        buttons.setLayout(hlay)
        self.vlayout.addWidget(buttons)

    def save(self):
        '''
        Save Settings
        '''
        self.application.settings = copy.deepcopy(self.data.settings)
        self.application.plugins = self.data.plugins
        for file_handler in self.application.file_handlers:
            if file_handler.getDescription() == self.data.settings['GeneralPanel']['split_view']:
                self.application.editToolBar.current_file_handler = file_handler.getName()

        config_manager = next(
            a for a in self.application.services if a.__class__.__name__ == "ConfigManager")
        config_manager.saveSettings(self.application.settings)
        self.application.newwindow = None
        self.close()

    def cancel(self):
        '''
        Close Window
        '''
        self.data.settings = copy.deepcopy(self.application.settings)
        self.application.newwindow = None
        self.close()
