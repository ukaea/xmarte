''' Organised widget of the UI section for the user to modify aspects of the 
MARTe2 Configuration '''

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QLabel, QLineEdit,
    QSizePolicy, QVBoxLayout, QWidget, QPushButton
)

from martepy.marte2.qt_classes import MessageConfigWindow

from xmarte.qt5.services.app_def.widgets.gam_datasources import GAMDataSourcesWgt

from xmarte.qt5.widgets.path_browser import FolderBrowser

class ProjectPropertiesWidget(QWidget):
    ''' The overall widget for the properties panel '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProjectPanel")
        self.initUI()
        self.application = self.parent().parent
        self.application.newwindow = None

    def initUI(self):
        ''' Create our subwidgets and layout and setup their UI features '''
        panel_layout = QVBoxLayout()
        self.setLayout(panel_layout)

        config_grp = QGroupBox("Universal Configuration Settings")

        v_layout = QVBoxLayout()
        app_lbl = QLabel("App Name:")
        self.app_edt = QLineEdit()

        t_lbl = QLabel("Timing Source Name:")
        self.t_edt = QLineEdit()

        g_lbl = QLabel("GAM DataSources:")
        self.g_edt = GAMDataSourcesWgt()

        sched_lbl = QLabel("GAM Scheduler:")
        self.sched_combo = QComboBox()
        self.sched_combo.addItems(['GAMScheduler', 'FastScheduler', 'BareScheduler'])

        v_layout.addWidget(app_lbl)
        v_layout.addWidget(self.app_edt)
        v_layout.addWidget(t_lbl)
        v_layout.addWidget(self.t_edt)
        v_layout.addWidget(g_lbl)
        v_layout.addWidget(self.g_edt)
        v_layout.addWidget(sched_lbl)
        v_layout.addWidget(self.sched_combo)
        config_grp.setLayout(v_layout)
        panel_layout.addWidget(config_grp)

        http_grp = QGroupBox("HTTP Server Instance")
        vh_layout = QVBoxLayout()
        http_grp.setLayout(vh_layout)

        http_use_lbl = QLabel("Include HTTP Instance:")
        self.http_use = QCheckBox()
        self.http_folder = FolderBrowser(self, "HTTP Resource Location:", "")

        vh_layout.addWidget(http_use_lbl)
        vh_layout.addWidget(self.http_use)
        vh_layout.addWidget(self.http_folder)

        self.config_msg = QPushButton("Configure Messages...")
        self.config_msg.clicked.connect(self.showMsgWnd)
        vh_layout.addWidget(self.config_msg)

        # Give user ability to define parameters of WebService
        # such as port, timeout, max threads, connections etc...

        panel_layout.addWidget(http_grp)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        panel_layout.addWidget(spacer)

    def showMsgWnd(self):
        ''' Show the window for configuring HTTP Messages '''
        app_def = self.application.API.getServiceByName('ApplicationDefinition')
        self.application.newwindow = MessageConfigWindow(
            self.application,
            self.application.app,
            original=app_def.http_messages,
            origin=app_def.http_messages,
            title='HTTP Server Messages Configuration',
            sizes=[0.2,0.2,0.6,0.6]
        )

    def loadConfiguration(self, configuration):
        ''' Load a new app configuration to the UI - is an easy one liner for other code '''
        self.app_edt.setText(configuration['app_name'])
        self.t_edt.setText(configuration['misc']['timingsource'])
        self.g_edt.listbox.clear()
        self.g_edt.listbox.addItems(configuration['misc']['gamsources'])
        for index in range(self.g_edt.listbox.count()):
            item = self.g_edt.listbox.item(index)
            item.oldname = item.text()
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable)
        self.sched_combo.setCurrentText(configuration['misc']['scheduler'])
        self.http_use.setChecked(configuration['http']['use_http'])
        self.http_folder.loc.setText(configuration['http']['http_folder'])
        