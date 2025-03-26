'''
The Default Settings Panel as a widget
'''

from functools import partial
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QComboBox,
    QCheckBox
)

from xmarte.qt5.widgets.settings.panel import BasePanel
from xmarte.qt5.widgets.path_browser import FolderBrowser

class DefaultPanel(BasePanel):
    '''
    The General settings widget panel that appears on the right hand side in the
    settings window when general is selected (or by default on load).
    '''
    def __init__(self, parent=None, settings_data={}, application=None):
        super().__init__(parent)
        self.data = settings_data
        _ = application

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Generate the Advanced Panel
        ahlay = QHBoxLayout()
        panel = QWidget(self)
        panel.setLayout(ahlay)
        layout.addWidget(panel)

        link = """https://marte21.gitpages.ccfe.ac.uk/xmarte/\
options.html#general-menu"""
        self.defineHelp(layout, link)

        defaults = ['TimingDataSource','GAMDataSource']
        self.defineDefaultNames(layout, defaults)

        sched_lbl = QLabel("Default Scheduler:")
        layout.addWidget(sched_lbl)
        self.sched_combo = QComboBox()
        self.sched_combo.addItems(['GAMScheduler', 'FastScheduler', 'BareScheduler'])
        self.sched_combo.setCurrentText(self.data.settings['DefaultPanel']['Scheduler'])
        self.sched_combo.key = 'Scheduler'
        self.sched_combo.currentTextChanged.connect(partial(self.combochange,
                                                            widget=self.sched_combo))
        layout.addWidget(self.sched_combo)

        http_use = QLabel("Include HTTP Server Instance:")
        self.http_check = QCheckBox()
        self.http_check.setChecked(self.data.settings["DefaultPanel"]["use_http"])
        self.http_check.key = "use_http"
        self.http_check.stateChanged.connect(partial(self.chkboxchange,
                                                     widget=self.http_check))

        layout.addWidget(http_use)
        layout.addWidget(self.http_check)

        self.httpfile = FolderBrowser(self,"HTTP Resources Folder:",
                                      self.data.settings["DefaultPanel"]["HTTP_folder"])
        self.httpfile.key='HTTP_folder'
        self.httpfile.loc.textChanged.connect(partial(self.linechange, widget=self.httpfile))
        layout.addWidget(self.httpfile)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(spacer)

    def defineDefaultNames(self, layout, defaults):
        '''Create widgets to allow the user to define defaults for the application.'''
        for default in defaults:
            default_lbl = QLabel(f"Default name for the: {default}")
            default_edit = QLineEdit()
            default_edit.setText(self.data.settings["DefaultPanel"][default])
            default_edit.key = default
            default_edit.textChanged.connect(partial(self.linechange, widget=default_edit))
            layout.addWidget(default_lbl)
            layout.addWidget(default_edit)
            setattr(self, default.lower(),default_edit)

    @staticmethod
    def generateDefaults():
        ''' Generate the basic defaults panel dictionary for the application if config yaml
        doesn't exist '''
        return {
                "TimingDataSource":"TimingsDataSource",
                "GAMDataSource": "DDB0",
                "Scheduler": "GAMScheduler",
                "use_http": False,
                "HTTP_folder": "",
                }
