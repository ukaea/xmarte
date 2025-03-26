'''
This service stores and provides UI to interact with, variables specific to the configuration
and components of the MARTe2 application instance.
'''
import copy
from functools import partial

from PyQt5 import QtCore
from PyQt5.QtWidgets import QListWidgetItem
from xmarte.qt5.services.app_def.widgets.project_properties import ProjectPropertiesWidget

from xmarte.qt5.services.service import Service

class ApplicationDefinition(Service):
    ''' The service itself, provides a common location for data about the MARTe2 application
    and the UI components to configure them '''
    service_name = 'ApplicationDefinition'
    def __init__(self, application) -> None:
        """Initialise the service and create the recovery directory and file"""
        super().__init__(application=application)
        class EmptyState:
            ''' Fake state used for the initialisation of the state machine instance
            until it gets created by external sources '''
            def write(self, config_writer):
                ''' Mimic the write function to write nothing so as to avoid errors when
                writing to cfg if an external source hasn't created a state machine - i.e.
                there is no state machine for this application (yet) '''
        self.statemachine = EmptyState()
        self.statemachine_serialized = None
        self.http_messages = []
        self.app_name = 'App'
        self.configuration = {}
        self.resetDefaults()
        self.project_prop_panel = ProjectPropertiesWidget(self.application.leftpanel)
        self.application.leftpanel.project_panel = self.project_prop_panel
        self.application.leftpanel.tab_wgt.addTab(self.project_prop_panel, "Project Properties")
        self.loadConfig(self.configuration)
        self.project_prop_panel.app_edt.textChanged.connect(partial(self.updateConfig,
                                                                    ['app_name']))
        self.project_prop_panel.t_edt.textChanged.connect(partial(self.updateConfig,
                                                                  ['misc','timingsource']))
        self.initGAMList()
        self.project_prop_panel.g_edt.gam_added.connect(self.addGAM)
        self.project_prop_panel.g_edt.gam_removed.connect(self.removeGAM)
        self.project_prop_panel.g_edt.gam_modified.connect(self.modifiedGAM)
        self.project_prop_panel.sched_combo.currentTextChanged.connect(partial(self.updateConfig,
                                                                               ['misc',
                                                                                'scheduler']))
        self.project_prop_panel.http_use.stateChanged.connect(partial(self.updateConfig,
                                                                      ['http','use_http']))
        self.project_prop_panel.http_folder.loc.textChanged.connect(partial(self.updateConfig,
                                                                            ['http',
                                                                             'http_folder']))

    def updateConfig(self, keys, value):
        ''' Replace the configuration '''
        pointer = self.configuration
        for key in keys[:-1]:
            pointer = pointer[key]
        pointer[keys[-1]] = value

    def initGAMList(self):
        ''' Populate the GAM Listbox with our gamsources '''
        listwidget = self.project_prop_panel.g_edt.listbox
        listwidget.clear()
        item = QListWidgetItem(self.configuration['misc']['gamsources'][0])
        item.oldname = self.configuration['misc']['gamsources'][0]
        listwidget.addItem(item)
        for index in range(listwidget.count()):
            item = listwidget.item(index)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

    def addGAM(self, gam_name):
        ''' Add a GAM '''
        self.configuration['misc']['gamsources'] += [gam_name]

    def removeGAM(self, gam_name):
        ''' Remove a GAM '''
        self.configuration['misc']['gamsources'].remove(gam_name)

    def modifiedGAM(self, oldname, newname):
        ''' Change a GAM name '''
        self.configuration['misc']['gamsources'].remove(oldname)
        self.configuration['misc']['gamsources'] += [newname]

    def resetDefaults(self):
        ''' Grab from our default definitions and reset the application instance '''
        use_http = copy.copy(self.application.settings['DefaultPanel']['use_http'])
        http_folder = copy.copy(self.application.settings['DefaultPanel']['HTTP_folder'])
        timingsource = copy.copy(self.application.settings['DefaultPanel']['TimingDataSource'])
        gamsources = [copy.copy(self.application.settings['DefaultPanel']['GAMDataSource'])]
        scheduler = copy.copy(self.application.settings['DefaultPanel']['Scheduler'])
        self.configuration = {'http': {'use_http' : use_http,
                                       'http_folder': http_folder}}
        self.configuration['misc'] = {'timingsource':timingsource,
                                      'gamsources':gamsources,
                                      'scheduler':scheduler,}
        self.configuration['app_name'] = self.app_name

    def loadConfig(self, configuration):
        ''' Load a given configuration setup '''
        if not configuration['misc']['gamsources']:
            configuration['misc']['gamsources'] = ['DDB0']
        self.configuration = configuration
        self.project_prop_panel.loadConfiguration(self.configuration)
        