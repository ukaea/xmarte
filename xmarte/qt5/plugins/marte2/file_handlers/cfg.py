'''
The marte2.cfg file handler
'''

from PyQt5.QtCore import pyqtRemoveInputHook
import pdb

import copy
import os
import shutil
from PyQt5 import QtCore
from PyQt5.QtWidgets import QListWidgetItem

from martepy.marte2.datasources import TimingDataSource
from martepy.marte2.datasources.gam_datasource import GAMDataSource
from martepy.marte2.objects.http.directoryresource import MARTe2HttpDirectoryResource
from martepy.marte2.reader import readApplication
from martepy.marte2.objects.http.objectbrowser import MARTe2HTTPObjectBrowser
from martepy.marte2.datasources.async_bridge import AsyncBridge
from martepy.marte2.datasources.logger_datasource import LoggerDataSource
from xmarte.qt5.libraries.functions import fixSocketOrdering
from xmarte.qt5.plugins.base_plugin import FileHandlerPlugin, SplitText
from xmarte.qt5.libraries.functions import fixSocketOrdering

class MARTe2ConfigFormat(FileHandlerPlugin):
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
        return application.writeToConfig()

    def loadFile(self, fname):
        '''
        Read the application and load it
        '''
        try:
            app, state_machine, http_browser, http_messages = readApplication(fname)
        except ValueError as e:
            raise RuntimeError(e)
        state_service = self.application.API.getServiceByName("StateDefinitionService")
        app_def = self.application.API.getServiceByName("ApplicationDefinition")
        listwidget = app_def.project_prop_panel.g_edt.listbox
        app_def.configuration['misc']['gamsources'] = []
        scheduler = next(a for a in app.internals if a.__class__.__name__ == 'MARTe2GAMScheduler')
        app_def.configuration['misc']['scheduler'] = scheduler.class_name
        listwidget.clear()
        state_service.loadStates(app, state_machine)
        # This needs to handle as states so we need a nice way to first populate our states combo and scenes
        # TODO: Add support for importing HTTP Service definition
        app_def.configuration['app_name'] = app.app_name
        if http_browser:
            app_def.configuration['http']['use_http'] = True
            app_def.http_messages = http_messages
            object_browser = next((a for a in http_browser.objects if a.__class__ == MARTe2HttpDirectoryResource), None)
            if object_browser:
                app_def.configuration['http']['http_folder'] = object_browser.basedir.replace('"','')
        for state in app.states:
            # Find it's corresponding scene definitions
            for thread in state.threads.objects:
                scene = self.application.state_scenes[state.configuration_name.lstrip('+')][thread.configuration_name.lstrip('+')]
                prev = scene.large_import
                scene.large_import = True
                for function in thread.functions:
                    node = self.application.API.toNode(function, scene)
                    inputs = [(0, a[0]) for a in function.inputs]
                    outputs = [(0, a[0]) for a in function.outputs]
                    node.outputsb = function.outputs
                    node.inputsb = function.inputs
                    node.initSockets(inputs, outputs)
                    fixSocketOrdering(node)
                # now load in datasources
                for datasource in app.additional_datasources:
                    if isinstance(datasource, GAMDataSource):
                        # Need to add this to the app_def
                        if datasource.configuration_name.lstrip('+') not in app_def.configuration['misc']['gamsources']:
                            app_def.configuration['misc']['gamsources'] += [datasource.configuration_name.lstrip('+')]
                            item = QListWidgetItem(datasource.configuration_name.lstrip('+'))
                            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                            listwidget.addItem(item)
                        continue
                    if isinstance(datasource, TimingDataSource):
                        app_def.configuration['misc']['timingsource'] = datasource.configuration_name.lstrip('+')
                        continue
                    node = self.application.API.toNode(datasource, scene)
                    if hasattr(datasource, 'output_signals'):
                        outputs = [(0, a[0]) for a in datasource.output_signals]
                        node.outputsb = datasource.output_signals
                    else:
                        outputs = []
                    if hasattr(datasource, 'input_signals'):
                        inputs = [(0, a[0]) for a in datasource.input_signals]
                        node.inputsb = datasource.input_signals
                    else:
                        inputs = []
                    if isinstance(datasource, AsyncBridge) or isinstance(datasource, LoggerDataSource):
                        # Because the asyncbridge doesn't contain any signals in it's definition
                        # But does in the states and IOGAMs communicating with it, we need to define it based on
                        # Knowing it's signals
                        node.parameters['input'] = True
                        # Find all input signals matching the DataSource value
                        matching_input_signals = [
                            signal for obj in thread.functions for signal in obj.input_signals
                            if 'DataSource' in list(signal[1]['MARTeConfig'].keys()) and signal[1]['MARTeConfig']['DataSource'] == datasource.configuration_name
                        ]

                        # Find all output signals matching the DataSource value
                        matching_output_signals = [
                            signal for obj in thread.functions for signal in obj.output_signals
                            if 'DataSource' in list(signal[1]['MARTeConfig'].keys()) and signal[1]['MARTeConfig']['DataSource'] == datasource.configuration_name
                        ]
                        # Only one can have values in our definition but we'll somewhat allow both here for now
                        if matching_output_signals:
                            node.parameters['input'] = False
                        inputs = [copy.deepcopy(a) for a in matching_input_signals]
                        for inputcfg in inputs:
                            if 'Datasource' in list(inputcfg[1]['MARTeConfig'].keys()):
                                del inputcfg[1]['MARTeConfig']['DataSource']
                        outputs = [copy.deepcopy(a) for a in matching_output_signals]
                        for outputcfg in outputs:
                            if 'Datasource' in list(outputcfg[1]['MARTeConfig'].keys()):
                                del outputcfg[1]['MARTeConfig']['DataSource']
                        node.inputsb = outputs
                        node.outputsb = inputs
                        inputs = [(0, a[0]) for a in node.inputsb]
                        outputs = [(0, a[0]) for a in node.outputsb]
                        pass
                    node.initSockets(inputs, outputs)
                    fixSocketOrdering(node)
                self.application.API.autolink(scene)
                scene.large_import = prev

        state_service.changeThread(1)
        # Now run clean diagram
        app_def.loadConfig(app_def.configuration)
        for state_name, state in self.application.state_scenes.items():
            for thread_name, thread in state.items():
                self.application.API.cleanDiagram(thread, self.application.editor.view)
        self.application.API.getServiceByName('DataManager').clearData()

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
        return "The MARTe2 executable config file"

    @staticmethod
    def getFileExtension():
        return "*.cfg"
