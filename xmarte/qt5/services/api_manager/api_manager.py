'''
This service will manage API calls and allows services to share calls to them,
firstly by storing pointers to the original service it uses as the "self" call
'''

import io
from itertools import chain
import copy
import os
import json
import tarfile
from PyQt5.QtCore import QRect, QRectF, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from martepy.functions.extra_functions import getname
from martepy.marte2.generic_application import MARTe2Application
from martepy.marte2.objects import MARTe2ReferenceContainer
from martepy.marte2.objects.gam_scheduler import MARTe2GAMScheduler
from martepy.marte2.objects.http import (
    MARTe2HTTPObjectBrowser,
    MARTe2HttpDirectoryResource,
    MARTe2HttpMessageInterface,
    MARTe2HttpService,
)
from martepy.marte2.datasources.gam_datasource import GAMDataSource
from martepy.marte2.objects.message import MARTe2Message
from martepy.marte2.factory import Factory as mpyFactory
from martepy.marte2.datasources.timing_datasource import TimingDataSource
from martepy.functions.gam_functions import getAlias
from martepy import marte2

from nodeeditor.node_edge import EDGE_TYPE_BEZIER

from xmarte.nodeeditor.node_edge import XMARTeEdge
from xmarte.qt5.nodes.node_handler import NodeHandler
from xmarte.qt5.services.api_manager.widgets.error_widget import ErrorWidgetButton
from xmarte.qt5.services.api_manager.windows.error_check_wnd import AppErrorWindow
from xmarte.qt5.services.service import Service
from xmarte.qt5.nodes.node_factory import Factory
from xmarte.qt5.services.state_service.states import StateDefinitionService
from xmarte.qt5.libraries.functions import getUserFolder
from xmarte.qt5.nodes.node_graphics import BlockGraphicsNode

class APIException(Exception):
    '''
    The Exception that should be thrown when a bad call to an API object is made
    '''

functions = {}
services = {}

class APIManager(Service):
    '''API manager'''
    service_name = 'APIManager'
    def __init__(self, application):
        super().__init__(application=application)
        factory = Factory()
        factory.loadRemote()
        self.application.factories['nodes'] = factory
        mfactory = mpyFactory()
        mfactory.loadRemote(
            os.path.join(os.path.dirname(marte2.__file__), 'objects', 'objects.json')
        )
        mfactory.loadRemote(
            os.path.join(
                os.path.dirname(os.path.dirname(marte2.__file__)), 'frameworks', 'end.json'
            )
        )
        self.application.factories['additional'] = mfactory
        self.error_wgt = None

    def registerNewAPIFunction(self, func_name, func, service):
        '''Register function'''
        functions[func_name] = func
        services[func_name] = service

    def reloadFactories(self):
        '''Create new factory instance.'''
        factory = Factory()
        factory.loadRemote()
        del self.application.factories['nodes']
        self.application.factories['nodes'] = factory
        _ = [a.loadBlocks() for a in self.application.services]

    def toGAM(self, node):
        '''
        This function uses the internal factories to create the GAM equivalent of a node
        '''
        # We need to figure out which factory provides our node type
        try:
            block_class = next(
                value.create(node.btype) for (key, value) in self.application.factories.items()
                if any(b for b in list(value.classes.keys()) if b == node.btype)
            )
        except StopIteration as exc:
            raise APIException(
                f'Could not find node by type {node.btype} in any of the application factories'
            ) from exc
        block = block_class()

        # Now we have a block, we need to sort through our parameters and convert them
        # from our node form to the rtcc form.

        block.deserialize(copy.deepcopy(node.serialize()))
        return block

    def toNode(self, gam, scene=None, selector='label'):
        '''
        This function converts a GAM datagram object into a node in the GUI network
        '''
        if scene is None:
            scene = self.application.scene

        serialised_version = gam.serialize()
        node_class = self.application.factories['nodes'].create("MARTe2Node")
        node = node_class(
            scene,
            self.application,
            gam.plugin,
            serialised_version['block_type'],
            serialised_version[selector].lstrip('+'),
            serialised_version['comment'],
            serialised_version['parameters'],
            serialised_version['inputs'],
            serialised_version['outputs'],
            serialised_version['inputsb'],
            serialised_version['outputsb'],
            False,
        )
        pos = node.pos
        node.deserialize(serialised_version)
        node.configuration_name = node.configuration_name.lstrip('+') # Fix for adding +
        node.grNode.title = node.title
        node.setPos(pos.x(),pos.y())
        node.grNode.adjustTitleSize()
        return node

    def datasourceToNode(self, datasource_obj, scene=None):
        '''Convert datasource to node.'''
        if scene is None:
            scene = self.application.scene

        serialised_version = datasource_obj.serialize()
        node_class = self.application.factories['nodes'].create("MARTe2Node")
        inputs = [(3,a[0]) for a in datasource_obj.input_signals]
        outputs = [(3,a[0]) for a in datasource_obj.output_signals]
        node = node_class(
            scene,
            self.application,
            datasource_obj.plugin,
            serialised_version['class_name'],
            serialised_version['configuration_name'],
            0,
            "",
            {},
            inputs,
            outputs,
            False,
        )
        return node

    def linkNodes(self, scene):
        '''
        This function will work out all the inputs and outputs to a node/GAM
        '''

    def updateApp(self, scene):
        '''
        This function will call checkconfig, linkNodes and then also call the pre and
        post process functions for a given GAM object. The result of which should be
        an application object ready to go.
        '''

    def getServiceByName(self, service_name):
        ''' Get a service based on it's given name '''
        return [a for a in self.application.services if service_name == a.__class__.__name__][0]

    def autolink(self, scene): # pylint: disable=R0912
        ''' Automatically create edges between sockets which have the same signal
        and datasource. '''
        # Find signals of the same name between nodes and create edges for them
        # We'll use a dictionary where the key is the unique signal name and the
        # value is the socket associated with it, we'll do a first pass and find all producers
        ddb_signals = {}
        nodes = scene.nodes
        for node in nodes:
            for index, output in enumerate(node.outputs):
                # Get corresponding alias and ddb
                try:
                    actual_signal = node.outputsb[index]
                    alias = getAlias(actual_signal)
                    ddb = ''
                    if 'DataSource' in actual_signal[1]['MARTeConfig']:
                        ddb = actual_signal[1]['MARTeConfig']['DataSource']
                    else:
                        # Check if we're a datasource
                        if node.serialize()['plugin'] == 'marte2_datasources':
                            ddb = node.configuration_name.replace('+','')
                    socket = output
                    if ddb:
                        if ddb not in ddb_signals:
                            ddb_signals[ddb] = {}
                        ddb_signals[ddb][alias] = socket
                except AttributeError:
                    pass

        # Now we do a second pass and go through inputs, creating connects
        for node in nodes: # pylint: disable=R1702
            for index, input_soc in enumerate(node.inputs):
                if len(input_soc.edges) == 0:
                    try:
                        actual_signal = node.inputsb[index]
                        alias = getAlias(actual_signal)
                        ddb = node.configuration_name.replace('+','')
                        if not node.plugin == 'marte2_datasources':
                            ddb = actual_signal[1]['MARTeConfig']['DataSource']
                        if ddb in ddb_signals:
                            if alias in ddb_signals[ddb]:
                                XMARTeEdge(scene,ddb_signals[ddb][alias],
                                           input_soc, EDGE_TYPE_BEZIER)
                    except (AttributeError, ValueError):
                        pass


    def saveToFile(self, filename, cursor=True): # pylint:disable=R0914,R0915
        ''' Save the application definition to file '''
        if cursor:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        NodeHandler.resolveInputs(
            StateDefinitionService.getAllNodes(self.application.state_scenes)
        )
        app_def = self.application.API.getServiceByName("ApplicationDefinition")
        with tarfile.open(filename, 'w') as tarf:
            # Save all threads/scenes
            for state_name, threads in self.application.state_scenes.items():
                for thread_name, thread_scene in threads.items():
                    file_name = thread_name + ".xms"
                    t = tarfile.TarInfo(state_name)
                    t.type = tarfile.DIRTYPE
                    t.mode = 0o755
                    tarf.addfile(t)
                    string_contents = json.dumps(thread_scene.serialize(), indent=4)
                    byte_contents = string_contents.encode()
                    tarinfo = tarfile.TarInfo(name=os.path.join(state_name,
                                                                file_name).replace('\\', '/'))
                    tarinfo.size = len(byte_contents)
                    tarf.addfile(tarinfo, fileobj=io.BytesIO(byte_contents))
            # Save our App Definition
            tarinfo = tarfile.TarInfo(name="project_desc.json")
            string_contents = json.dumps(app_def.configuration, indent=4)
            byte_contents = string_contents.encode()
            tarinfo.size = len(byte_contents)
            tarf.addfile(tarinfo, fileobj=io.BytesIO(byte_contents))

            # Store our version for upconverters
            tarinfo = tarfile.TarInfo(name="version")
            string_contents = "db9c44e14fec01a0fe78b1cd9d9c991502a1cb75"
            byte_contents = string_contents.encode()
            tarinfo.size = len(byte_contents)
            tarf.addfile(tarinfo, fileobj=io.BytesIO(byte_contents))

            # Save HTTP messages
            tarinfo = tarfile.TarInfo(name="http_messages.json")
            string_contents = json.dumps([a.serialize() for a in app_def.http_messages], indent=4)
            byte_contents = string_contents.encode()
            tarinfo.size = len(byte_contents)
            tarf.addfile(tarinfo, fileobj=io.BytesIO(byte_contents))

            # Save our State Machine
            tarinfo = tarfile.TarInfo(name="state_def.json")
            string_contents = json.dumps(app_def.statemachine.serialize(), indent=4)
            byte_contents = string_contents.encode()
            tarinfo.size = len(byte_contents)
            tarf.addfile(tarinfo, fileobj=io.BytesIO(byte_contents))

            # Save state scene
            tarinfo = tarfile.TarInfo(name="state_scene.json")
            string_contents = json.dumps(app_def.statemachine_serialized, indent=4)
            byte_contents = string_contents.encode()
            tarinfo.size = len(byte_contents)
            tarf.addfile(tarinfo, fileobj=io.BytesIO(byte_contents))

            # Save our Test Configuration
            tarinfo = tarfile.TarInfo(name="test_def.json")
            dictionary = self.application.test_definition
            if dictionary is None:
                dictionary = json.dumps({}, indent=4)
            else:
                dictionary = json.dumps(dictionary, indent=4)
            byte_contents = dictionary.encode()
            tarinfo.size = len(byte_contents)
            tarf.addfile(tarinfo, fileobj=io.BytesIO(byte_contents))

            # states.json
            tarinfo = tarfile.TarInfo(name="states.json")
            # Get rid of functions
            states = copy.deepcopy(self.application.states)
            for state in states:
                for thread in state.threads.objects:
                    thread.functions = []
            string_contents = json.dumps([a.serialize() for a in states], indent=4)
            byte_contents = string_contents.encode()
            tarinfo.size = len(byte_contents)
            tarf.addfile(tarinfo, fileobj=io.BytesIO(byte_contents))

            if cursor:
                QApplication.restoreOverrideCursor()

    def loadFile(self, file_path): # pylint:disable=R0914
        ''' Load an application definition from file '''
        mfactory = mpyFactory()
        mfactory.loadRemote(
            os.path.join(os.path.dirname(marte2.__file__), 'objects', 'objects.json')
        )
        mfactory.loadRemote(
            os.path.join(
                os.path.dirname(os.path.dirname(marte2.__file__)), 'frameworks', 'end.json'
            )
        )

        # Delete all scenes
        for state_name, state in self.application.state_scenes.items():
            for thread_name, thread in state.items():
                thread.large_import = True
                thread.clear()
                thread = None

        QApplication.setOverrideCursor(Qt.WaitCursor)
        state_service = self.application.API.getServiceByName("StateDefinitionService")
        file_support_service = self.application.API.getServiceByName("FileSupportService")
        try:
            state_service.thread_wdgt.currentIndexChanged.disconnect()
        except TypeError:
            pass
        state_service.thread_wdgt.clear()
        state_service.thread_wdgt.update()
        self.application.state_scenes = {}
        # Open the tar file for reading
        with tarfile.open(file_path, 'r') as tar:
            file_names = tar.getnames()
            # Never been upconverted - needs upconverting, we can only assume it has the issues
            # from just prior to us inventing this method
            version = 'never'
            if 'version' in file_names:
                file_info = tar.getmember("version")
                file_content = tar.extractfile(file_info).read()
                version = file_content.decode('utf-8')

        file_support_service.upconvert(file_path, version, mfactory)

        state_service.populateCombos(self.application.state_scenes)
        try:
            state_service.thread_wdgt.currentIndexChanged.disconnect()
        except TypeError:
            pass
        state_service.thread_wdgt.setCurrentIndex(0)
        state_name, thread_name = state_service.resolveThread()
        state_service.thread_wdgt.currentIndexChanged.connect(state_service.changeThread)
        state_service.updateScene(state_name, thread_name)
        QApplication.restoreOverrideCursor()
        app = self.application.API.buildApplication()
        self.application.API.errorCheck(app)
        # Now clean diagrams
        for i, (state_name, state) in enumerate(self.application.state_scenes.items()):
            for j, (thread_name, thread) in enumerate(state.items()):
                self.application.API.cleanDiagram(thread, self.application.editor.view)
                if thread.nodes:
                    state_service.thread_wdgt.setCurrentIndex(i + j + 1)
                    state_service.updateScene(state_name, thread_name)

        # Reset playback
        state_service.changeThread(None)
        self.getServiceByName('DataManager').clearData()

    def cleanDiagram(self, scene, view): # pylint: disable=R0914
        """
        This function "cleans" the block diagram. That is to say that it arranges
        our nodes in a sensible fashion based on their linkage which subsequently
        demands their execution order.
        """
        # Get the scene viewport for the user
        viewportRect = QRect(
            0,
            0,
            view.viewport().width(),
            view.viewport().height(),
        )
        visibleSceneRect = QRectF(
            view.mapToScene(viewportRect).boundingRect()
        )
        # Get the coords of each visible corner of the viewport in reference
        # to the scene.
        left = visibleSceneRect.left()
        top = visibleSceneRect.top()
        bottom = visibleSceneRect.bottom()

        # Figure out a good starting point
        left = 0 if left < 0 else left
        top = 0 if top < 0 else top
        x = 300 + left
        y = ((top - bottom) / 2) + bottom

        # Figure out the largest width of a node to avoid overlapping
        # nodes in the offset
        largest_width = 0
        largest_height = 0

        for node in scene.nodes:
            largest_width = max(largest_width, node.grNode.width)
            largest_height = max(largest_height, node.grNode.height)

        y = y + largest_height

        offsets = [largest_width + 100, largest_height + 50]
        starting_position = [x, y]
        # Check whether this was clean all or just clean a selected set of nodes
        selected_items = scene.getSelectedItems()
        selected_nodes = [a for a in selected_items if isinstance(a, BlockGraphicsNode)]

        if len(selected_nodes) > 0:
            nodes = [a.node for a in selected_nodes]
        else:
            nodes = NodeHandler.getRealNodes(scene.nodes)

        # Now we're ready, clean!
        NodeHandler.repositionSpecificNodes(nodes, offsets, starting_position)

    def errorCheck(self, application, showdialog=False):
        ''' Check the given application instance for errors and show to the user '''
        # Check for errors, this could be:
        exceptions = application.onlyErrors()

        if len(exceptions) > 0 and showdialog:
            # Prompt our user about errors (only number of, found,
            # then to go to check errors window for more, ask if they want to open it, or cancel)

            reply = QMessageBox.question(self.application, "Error Review",
                                         """Errors were found in the application.
Would you like to review these errors?""",
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            # Execute the message box and handle the result
            if reply == QMessageBox.Yes:
                # if open, open the window
                self.application.newwindow = AppErrorWindow(self.application,
                                                            self.application.app,
                                                            exceptions)
                self.application.newwindow.show()
        # Populate errors into error label for later call
        self.error_wgt.error_lbl.setText(f"Errors: {len(exceptions)}")

    def addToolbarOptions(self, layout):
        """
        This function is called at startup and allows you to add functions to the toolbar
        """
        self.error_wgt = ErrorWidgetButton(application = self.application)
        layout.addWidget(self.error_wgt)

    def updateAllLargeImports(self, to_value=True,values=[]):
        ''' Set the large import flag across scenes '''
        prev_values = []
        index = 0
        for state_name, state in self.application.state_scenes.items():
            for thread_name, thread in state.items():
                prev_values.append(thread.large_import)
                if len(values) == 0:
                    self.application.state_scenes[state_name][thread_name].large_import = to_value
                else:
                    val = values[index]
                    self.application.state_scenes[state_name][thread_name].large_import = val
                index += 1
        return prev_values

    def buildApplication(self): # pylint: disable=R0914
        '''Build the application instance.'''
        prev_values = self.updateAllLargeImports(to_value=True)
        app_def = self.getServiceByName('ApplicationDefinition')
        application = MARTe2Application()
        cls_name = app_def.configuration['misc']['scheduler']
        time_source = app_def.configuration['misc']['timingsource']
        application.add(internals=[MARTe2GAMScheduler(class_name=cls_name,
                                                      timing_datasource_name=time_source)])
        application.additional_datasources.append(TimingDataSource(time_source))
        type_db = os.path.join(getUserFolder(),"typedb")
        if not os.path.exists(type_db):
            os.mkdir(type_db)
        application.loadTypeLibrary(type_db)
        # Fix the inputs
        NodeHandler.resolveInputs(
            StateDefinitionService.getAllNodes(self.application.state_scenes)
        )
        gam_functions = [
            self.application.API.toGAM(node)
            for node in StateDefinitionService.getAllFunctions(self.application)
        ]
        application.add(functions = gam_functions)
        datasources = [
            self.application.API.toGAM(datasource)
            for datasource in StateDefinitionService.getAllDataSources(self.application)
        ]
        application.add(additional_datasources=datasources)
        for gam_data in app_def.configuration['misc']['gamsources']:
            gam_datasource = GAMDataSource('+' + gam_data.lstrip('+'))
            application.add(additional_datasources=[gam_datasource])

        # Define our states
        for state in self.application.states:
            threads=[]

            for thread in state.threads.objects:
                nodes = StateDefinitionService.getStateThreadNodes(self.application,
                                                                   getname(state),
                                                                   getname(thread))
                groups = NodeHandler.getExecutionGroups(nodes)
                ordered_functions = []
                for group in groups:
                    ordered_functions.append([self.application.API.toGAM(a) for a in group.nodes])
                # Flatten 2D
                ordered_functions = list(chain.from_iterable(ordered_functions))
                thread.functions = []
                if ordered_functions:
                    thread.functions = ordered_functions

                if thread.functions:
                    threads.append(thread)
            newstate = copy.deepcopy(state)
            newstate.threads = MARTe2ReferenceContainer('+Threads', objects=threads)
            application.add(states=[newstate])

        # If selected for HTTP Server instance - create it
        self.buildHTTPServer(application, app_def.statemachine)

        # Update names
        self.updateNames(application)

        # Add State Machine
        application.add(externals=[app_def.statemachine])
        self.updateAllLargeImports(values=prev_values)
        return application

    def updateNames(self, app):
        ''' Update the timing source definition across all datasources in an app to our config '''
        app_def = self.getServiceByName('ApplicationDefinition')
        app.app_name = app_def.configuration['app_name']  # set the application name
        for datasource in app.additional_datasources:
            if isinstance(datasource, TimingDataSource):
                datasource.configuration_name = app_def.configuration['misc']['timingsource']

    def buildHTTPServer(self, app, statemachine=None):
        ''' Build the HTTP Instance based on our app definition '''
        app_def = self.getServiceByName('ApplicationDefinition')
        config = app_def.configuration
        if config['http']['use_http']:
            # Object Browser Definition
            ObjectBrowser = MARTe2HTTPObjectBrowser('+ObjectBrowse','/')
            Messages = app_def.http_messages
            # ResourcesHtml Definition
            ResourcesHtml = MARTe2HttpDirectoryResource('+ResourcesHtml',
                                                        config['http']['http_folder'])

            MessageInterface = MARTe2HttpMessageInterface('+HttpMessageInterface',Messages)

            Objectlist = [ObjectBrowser,ResourcesHtml,MessageInterface]

            HTTPBrowser = MARTe2HTTPObjectBrowser('+WebRoot','.',Objectlist)

            # Add WebServer
            service = MARTe2HttpService('+WebService')
            # Add this to application
            app.add(externals=[HTTPBrowser] + [service])
            if statemachine:
                # Assuming state 0 is INITIAL as it should be and
                # is kind of enforced by the MARTe2 State Machine
                first_state = statemachine.states[0]
                find_start = next(a for a in first_state.objects if getname(a).upper() == 'START')
                if not any(a for a in find_start.messages if
                           a.destination.strip('"') == 'WebServer' and
                           a.function.strip('"') == 'Start'):
                    # We need to start our web server at startup
                    find_start.messages.insert(0, MARTe2Message("StartHttpServer",
                                                                "WebServer",
                                                                "Start"))

    @staticmethod
    def getAlias(alias_s):
        '''Get alias given a dictionary.'''
        if 'Alias' in list(alias_s[1]['MARTeConfig'].keys()):
            alias = alias_s[1]['MARTeConfig']['Alias']
        else:
            alias = alias_s[0]
        return alias

    @staticmethod
    def getAliases(application):
        '''Get all aliases in the application.'''
        aliases = []
        for scene in chain.from_iterable(a.values() for a in application.state_scenes.values()):
            for node in scene.nodes:
                if node.plugin != 'marte2_datasources':
                    for output in node.outputsb:
                        aliases.append(APIManager.getAlias(output))
        return aliases
