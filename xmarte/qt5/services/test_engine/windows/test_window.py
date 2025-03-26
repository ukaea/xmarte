'''
This Window executes whatever test executor is loaded in by the plugins and chosen in Advanced
Options.
'''
from functools import partial
import json
import os

from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QWidget,
    QLabel,
    QComboBox,
    QToolBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import pyqtSignal


from martepy.frameworks.simulation_frameworkv2 import SimulationGenerator
from martepy.marte2.qt_classes import PanelledListConfig
from martepy.marte2.type_database import TypeException
from martepy.functions.extra_functions import getname
from martepy.marte2.datasources import TimingDataSource, GAMDataSource
from martepy.marte2.datasource import MARTe2DataSource

from xmarte.qt5.libraries.functions import fixSocketOrdering, updateDefaultDialogDir
from xmarte.qt5.services.api_manager.widgets.error_widget import ErrorWidgetButton
from xmarte.qt5.widgets.node_editor_viewer import NodeEditorWidgetViewer
from xmarte.qt5.widgets.scene import EditorScene
from xmarte.qt5.windows.base_window import ModalOptionsWindow

from ..widgets.test_tab_panel import TestPanelWidget
from .progress_window import TestProgressWindow


class TestWindow(ModalOptionsWindow): # pylint: disable=R0904
    '''
    The Test Execution Window
    '''
    finished = pyqtSignal(int)
    def __init__(self, application, app):
        super().__init__(application, app, 0.12,0.12,0.75,0.75)
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        self.setWindowTitle("Test Configuration")
        if not hasattr(self.application,'test_definition'):
            self.application.test_definition = None
        self.main_wgt = PanelledListConfig(self, 0.25,0.75, make_list=False)
        self.setCentralWidget(self.main_wgt)
        self.vlayout = self.main_wgt.v_layout

        self.editor = NodeEditorWidgetViewer()
        self.main_wgt.right_panel_vlayout.addWidget(self.editor)
        self.main_wgt.left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tab_wgt = TestPanelWidget(self, self.editor.scene, self.application)
        self.tab_wgt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_wgt.left_panel_vlayout.addWidget(self.tab_wgt)

        self.marte_app_def = self.application.API.buildApplication()
        self.prog_window = TestProgressWindow(self.application, self.app, self, [])
        # Now we need to spoof some variables for our nodes to show their config bar
        # This should instead be later fixed in issue #29:
        # Marte2_node too coupled to application instance

        self.rightpanel = self.main_wgt.right_panel_wgt
        self.rightpanel.vlayout = self.main_wgt.right_panel_vlayout
        self.factories = self.application.factories
        self.rightpanel.parent = self
        self.API = self.application.API

        self.finished.connect(self.handleFinished)

        self.scene = None
        self.drawToolbar()
        self.drawMenu()
        self.closerror = False
        self.show()
        try:
            if self.application.test_definition:

                QMessageBox.information(self, 'Scene changes',
                                        '''Loading a previously defined test definition,
 if you have modified the MARTe2Application definition, you may want to reset your scene/s
 and restart otherwise this could result in a non-functional simulation''', QMessageBox.Ok)
                self.importDef(self.application.test_definition)
            else:
                self.editor.scene.clear()
                self.sim_generator = SimulationGenerator(self.marte_app_def)
                self.sim_generator.configure(self.marte_app_def)
                mcycles = self.tab_wgt.mcycles_edt.text()
                self.sim_generator.simulation_app.config['maxcycles'] = mcycles
                rate = self.tab_wgt.rate_edt.text()
                self.sim_generator.simulation_app.config['timefrequency'] = rate
                self.sim_app_def = self.sim_generator.build()
                self.drawNew(self.sim_app_def)
                self.application.test_definition = self.exportDef()

            # Now draw nicely that the scene exists and has viewport coords
            for _, state in self.state_scenes.items():
                for _, thread in state.items():
                    self.application.API.cleanDiagram(thread, self.editor.view)
        except TypeException as e:
            QGuiApplication.restoreOverrideCursor()
            QMessageBox.critical(self,'Type Error',
                                 f'''A Type defined within your application is not present
 within the type database and thus the simulation cannot be generated.
 \nType not found: {str(e)}''', QMessageBox.Ok)
            self.closerror = True
            self.close()
        QGuiApplication.restoreOverrideCursor()

    @property
    def scene(self):
        ''' Override the scene property to ensure it is set with the editor '''
        return self._scene

    @scene.setter
    def scene(self, value):
        ''' Override the scene property to ensure it is set with the editor '''
        if hasattr(value, 'grScene') and value.grScene:
            self.editor.scene = value.grScene
            self.editor.view.setScene(value.grScene)
            self.editor.view.grScene = value.grScene
        self._scene = value

    def handleFinished(self, _):
        ''' Handle the thread completion '''
        self.prog_window = TestProgressWindow(self.application, self.app, self, [])

    def deselected(self):
        '''
        On deselected
        Remove the parameter bar if it exists
        '''
        if hasattr(self.main_wgt.right_panel_wgt, "parameterbar"):
            if self.main_wgt.right_panel_wgt.parameterbar is not None:
                self.main_wgt.right_panel_wgt.parameterbar.deleteLater()
                self.main_wgt.right_panel_wgt.parameterbar = None
                self.editor.scene.has_been_modified = True
        self.update()

    def cleanDiagram(self):
        ''' Clean the layout of nodes '''
        self.application.API.cleanDiagram(self.scene, self.editor.view)

    def drawToolbar(self):
        ''' Draw the window toolbar options '''
        # Create actions for the toolbar buttons
        clean_action = QAction("Clean Diagram", self)
        autoconnect_action = QAction("Autoconnect", self)
        run_action = QAction("Run Simulation", self)
        reset_action = QAction("Reset Scene", self)
        reset_all_action = QAction("Reset All Scenes", self)

        # Connect actions to their respective slots (you can define these later)
        clean_action.triggered.connect(self.cleanDiagram)
        autoconnect_action.triggered.connect(self.autolink)
        run_action.triggered.connect(self.runSimulation)
        reset_action.triggered.connect(self.resetDiagram)
        reset_all_action.triggered.connect(self.resetAll)
        # Create the toolbar and add actions
        self.toolbar = QToolBar()
        self.toolbar.addAction(reset_action)
        self.toolbar.addAction(reset_all_action)
        self.toolbar.addAction(clean_action)
        self.toolbar.addAction(autoconnect_action)
        self.toolbar.addAction(run_action)
        # Add the toolbar to the main window
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toolbar.addWidget(spacer)
        self.error_widget = ErrorWidgetButton(self, self.application)
        self.toolbar.addWidget(self.error_widget)
        thread_lbl = QLabel("Thread:")
        self.thread_wdgt = QComboBox()

        self.toolbar.addWidget(thread_lbl)
        self.toolbar.addWidget(self.thread_wdgt)
        self.addToolBar(self.toolbar)

    def populateCombos(self) -> None:
        '''Populate the state and thread comboboxes.'''
        self.thread_wdgt.clear()
        for state_name, state in self.state_scenes.items():
            self.thread_wdgt.addItem(state_name)
            for thread_name, _ in state.items():
                self.thread_wdgt.addItem(f'   {thread_name}')

    def resolveThread(self):
        ''' This function uses the combobox to figure out what thread and
        state are currently selected '''
        selected_item_text = self.thread_wdgt.currentText()
        selected_item_idx = self.thread_wdgt.currentIndex()
        if selected_item_idx == -1:
            self.thread_wdgt.setCurrentIndex(0)
        indent = selected_item_text.count(" ")
        parent_key = None
        current_key = selected_item_text.strip()
        if indent > 0:
            # Find it's parent, traverse up the list until we find an
            # item without an indent
            count = 1
            while True:
                parent_key = self.thread_wdgt.itemText(selected_item_idx - count)
                indent = parent_key.count(" ")
                if indent == 0:
                    break
                count = count + 1
        if not parent_key:
            self.thread_wdgt.setCurrentIndex(selected_item_idx + 1)
            parent_key, current_key = self.resolveThread()
        return parent_key, current_key

    def exportAs(self):
        ''' Export the definition as a .cfg for e.g. local testing by users '''
        default_dir = ""
        if "file_location" in self.application.settings["GeneralPanel"].keys():
            default_dir = self.application.settings["GeneralPanel"]["file_location"]

        # Save the data setup to file
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Test Configuration", default_dir, "MARTe2cfg (*.cfg);;"
        )
        if filename:
            self.sim_generator = SimulationGenerator(self.marte_app_def)
            self.sim_generator.configure(self.marte_app_def)
            mcycles = self.tab_wgt.mcycles_edt.text()
            self.sim_generator.simulation_app.config['maxcycles'] = mcycles
            rate = self.tab_wgt.rate_edt.text()
            self.sim_generator.simulation_app.config['timefrequency'] = rate
            sim_app_def = self.sim_generator.build()
            for state_name, state in self.state_scenes.items():
                for thread_name, thread in state.items():
                    self.sceneToDef(state_name, thread_name, thread, sim_app_def)

            content = sim_app_def.writeToConfig()
            with open(filename, 'w', encoding='utf-8') as outfile:
                outfile.write(content)
            self.application.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename)
            updateDefaultDialogDir(os.path.dirname(filename))

    def runSimulation(self):
        ''' Run the simulation defined '''
        self.sim_generator = SimulationGenerator(self.marte_app_def)
        self.sim_generator.configure(self.marte_app_def)
        self.sim_generator.simulation_app.config['maxcycles'] = self.tab_wgt.mcycles_edt.text()
        self.sim_generator.simulation_app.config['timefrequency'] = self.tab_wgt.rate_edt.text()
        self.sim_app_def = self.sim_generator.build()
        for state_name, state in self.state_scenes.items():
            for thread_name, thread in state.items():
                self.sceneToDef(state_name, thread_name, thread, self.sim_app_def)

        self.prog_window.sim_app_def = self.sim_app_def
        self.prog_window.show()
        self.prog_window.startThread()

    def drawMenu(self):
        ''' Draw the window menu '''
        # Create actions
        save_action = QAction("Save", self)
        run_action = QAction("Run", self)
        import_action = QAction("Import Test Definition", self)
        export_action = QAction("Export Test Definition", self)
        export_as_action = QAction("Export As...", self)
        exit_action = QAction("Exit", self)
        #documentation_action = QAction("Documentation", self)

        # Connect actions to slots (if needed)
        run_action.triggered.connect(self.runSimulation)
        exit_action.triggered.connect(self.close)
        export_as_action.triggered.connect(self.exportAs)
        save_action.triggered.connect(self.savesetup)
        import_action.triggered.connect(self.importDialog)
        export_action.triggered.connect(self.exportDialog)
        # Create menus
        file_menu = self.menuBar().addMenu("File")
        #help_menu = self.menuBar().addMenu("Help")

        # Add actions to menus
        file_menu.addAction(run_action)
        file_menu.addAction(save_action)
        file_menu.addAction(export_as_action)
        file_menu.addAction(import_action)
        file_menu.addAction(export_action)
        file_menu.addAction(exit_action)
        #help_menu.addAction(documentation_action)

    def savesetup(self):
        ''' Save the current test setup '''
        self.application.test_definition = self.exportDef()

    def autolink(self):
        ''' Auto link all nodes in the scene '''
        self.application.API.autolink(self.editor.view.scene().scene)

    def resetAll(self):
        ''' Undo all user changes and reset to the auto generated simulation '''
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        self.editor.scene.clear()
        self.sim_generator = SimulationGenerator(self.marte_app_def)
        self.sim_generator.configure(self.marte_app_def)
        self.sim_generator.simulation_app.config['maxcycles'] = self.tab_wgt.mcycles_edt.text()
        self.sim_generator.simulation_app.config['timefrequency'] = self.tab_wgt.rate_edt.text()
        self.sim_app_def = self.sim_generator.build()
        self.drawNew(self.sim_app_def)
        self.application.test_definition = self.exportDef()
        QGuiApplication.restoreOverrideCursor()

    def resetDiagram(self):
        ''' Reset the current thread to that of what is auto generated by the sim generator '''
        # - we should reset for the entire simulation and then pluck the
        # current state and thread def
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        state_name, thread_name = self.resolveThread()
        scene = self.state_scenes[state_name][thread_name]
        scene.clear()
        self.sim_generator = SimulationGenerator(self.marte_app_def)
        self.sim_generator.configure(self.marte_app_def)
        self.sim_generator.simulation_app.config['maxcycles'] = self.tab_wgt.mcycles_edt.text()
        self.sim_generator.simulation_app.config['timefrequency'] = self.tab_wgt.rate_edt.text()
        self.sim_app_def = self.sim_generator.build()
        state_name, thread_name = self.resolveThread()
        state = next(state for state in self.sim_app_def.states if state_name == getname(state))
        thread = next(thread for thread in state.threads.objects if thread_name == getname(thread))
        self.drawScene(scene, thread, self.sim_app_def)
        QGuiApplication.restoreOverrideCursor()

    def sceneToDef(self, state_name, thread_name, scene, app_def):
        ''' Convert a scene to a MARTe2 cfg definition '''
        state = next(state for state in app_def.states if state_name == getname(state))
        thread = next(thread for thread in state.threads.objects if thread_name == getname(thread))
        thread.functions = []
        for node in scene.nodes:
            as_gam = self.API.toGAM(node)
            if isinstance(as_gam, MARTe2DataSource):
                existing = next((datasource for datasource in app_def.additional_datasources if
                                 getname(datasource) == getname(as_gam)), None)
                # Doesn't already exist in our definition
                if not existing:
                    app_def.additional_datasources.append(as_gam)
            else:
                # Is a GAM
                thread.functions.append(as_gam)

    def drawScene(self, scene, thread, app_def):
        ''' Draw the selected scene '''
        # This function converts a thread definition from MARTe2Application into a scene
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
            node.grNode.adjustTitleSize()
        # now load in datasources
        for datasource in app_def.additional_datasources:
            if isinstance(datasource, GAMDataSource):
                continue
            if isinstance(datasource, TimingDataSource):
                continue
            node = self.application.API.toNode(datasource, scene)
            if hasattr(datasource, 'input_signals'):
                inputs = [(0, a[0]) for a in datasource.input_signals]
                node.inputsb = datasource.input_signals
            else:
                inputs = []
            if hasattr(datasource, 'output_signals'):
                outputs = [(0, a[0]) for a in datasource.output_signals]
                node.outputsb = datasource.output_signals
            else:
                outputs = []
            node.initSockets(inputs, outputs)
            fixSocketOrdering(node)
            node.grNode.adjustTitleSize()
        self.application.API.autolink(scene)
        self.application.API.cleanDiagram(scene, self.editor.view)
        scene.large_import = prev

    def importDialog(self):
        ''' Import a test definition from file '''
        default_dir = ""
        if "file_location" in self.application.settings["GeneralPanel"].keys():
            default_dir = self.application.settings["GeneralPanel"]["file_location"]
        # Load data setup from file
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Test Configuration", default_dir, "xmarte test configuration (*.xmtest);;"
        )
        if filename:
            with open(filename, 'r', encoding='utf-8') as inifile:
                self.importDef(json.loads(inifile.read()))
            self.application.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename)
            updateDefaultDialogDir(os.path.dirname(filename))

    def exportDialog(self):
        ''' Export the current test definition to file '''
        default_dir = ""
        if "file_location" in self.application.settings["GeneralPanel"].keys():
            default_dir = self.application.settings["GeneralPanel"]["file_location"]

        # Save the data setup to file
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Test Configuration", default_dir, "xmarte test configuration (*.xmtest);;"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as outfile:
                outfile.write(json.dumps(self.exportDef()))
            self.application.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename)
            updateDefaultDialogDir(os.path.dirname(filename))

    def importDef(self, definition):
        ''' Import a definition from dict '''
        try:
            self.thread_wdgt.currentIndexChanged.disconnect()
        except TypeError:
            pass
        def filterToStates(x):
            if x in ('maxcycles', 'rate', 'solver'):
                return False
            return True

        self.state_scenes = {}

        for state_name in filter(filterToStates, list(definition.keys())):
            # Create the state
            self.state_scenes[state_name] = {}
            for thread_name, _ in definition[state_name].items():
                name = f'{state_name}-{thread_name}'
                self.state_scenes[state_name][thread_name] = EditorScene(self.application,
                                                                         True,
                                                                         name)
                scene = self.state_scenes[state_name][thread_name]
                scene.clearNodeRemoveListener()
                scene.addItemsDeselectedListener(self.deselected)
                scene.scene_name = f'TestConfigurationScene-{state_name}-{thread_name}'
                scene.application = self
                prev = scene.large_import
                scene.large_import = True
                scene.deserialize(definition[state_name][thread_name])
                for node in scene.nodes:
                    node.grNode.adjustTitleSize()
                self.application.API.autolink(scene)
                self.API.cleanDiagram(scene, self.editor.view)
                scene.large_import = prev

        self.populateCombos()
        self.tab_wgt.mcycles_edt.setText(definition['maxcycles'])
        self.tab_wgt.rate_edt.setText(definition['rate'])
        self.tab_wgt.solver_edt.setCurrentText(definition['solver'])

        self.changeThread(0)
        self.thread_wdgt.currentIndexChanged.connect(self.changeThread)

    def closeEvent(self, event):
        ''' Close window prompt occurred - save our test definition '''
        if not self.closerror:
            self.application.test_definition = self.exportDef()
        event.accept()

    def exportDef(self):
        ''' Export the current test definition '''
        # Unlike how we save a file with all it's scenes we're going with
        # a flat dictionary definition
        test_definition = {}
        for state_name, state in self.state_scenes.items():
            test_definition[state_name] = {}
            for thread_name, thread in state.items():
                test_definition[state_name][thread_name] = thread.serialize()
        test_definition['maxcycles'] = self.tab_wgt.mcycles_edt.text()
        test_definition['rate'] = self.tab_wgt.rate_edt.text()
        test_definition['solver'] = self.tab_wgt.solver_edt.currentText()
        return test_definition

    def deleteGAMfromApp(self, app, config_name):
        ''' Delete a specified GAM from the simulation app '''
        for state in app.states:
            for thread in state.threads:
                thread.functions = [a for a in thread.functions if
                                    not getname(a) == config_name.lstrip('+')]
        app.functions = [a for a in app.functions if
                         not getname(a) == config_name.lstrip('+')]

    def sceneChange(self):
        ''' Change thread '''
        for state_name, state in self.state_scenes.items():
            for thread_name, thread in state.items():
                self.sceneToDef(state_name, thread_name, thread, self.sim_app_def)

        self.error_widget.checkerrorwnd(self.sim_app_def)

    def drawNew(self, sim_app_def):
        ''' Draw a new simulation '''
        try:
            self.thread_wdgt.currentIndexChanged.disconnect()
        except TypeError:
            pass
        # Create the main application node
        self.state_scenes = {}
        for state in sim_app_def.states:
            # Find it's corresponding scene definitions
            state_name = getname(state)
            self.state_scenes[state_name] = {}
            for thread in state.threads.objects:
                thread_name = getname(thread)
                name = f'{state_name}-{thread_name}'
                self.state_scenes[state_name][thread_name] = EditorScene(self.application,
                                                                         True,
                                                                         name)
                scene = self.state_scenes[state_name][thread_name]
                scene.clearNodeRemoveListener()
                scene.addItemsDeselectedListener(self.deselected)
                scene.scene_name = f'TestConfigurationScene-{state_name}-{thread_name}'
                scene.application = self
                self.drawScene(scene, thread, sim_app_def)
        self.populateCombos()
        self.changeThread(0)
        self.thread_wdgt.currentIndexChanged.connect(self.changeThread)

    def updateScene(self, state, thread) -> None:
        '''Change the logical and graphical scene according to the selected state and thread.'''
        # Check that any threads exist in the state
        self.scene = self.state_scenes[state][thread]
        self.scene.clearNodeRemoveListener()
        self.scene.clearModifiedListener()
        if hasattr(self, 'sim_app_def'):
            self.scene.addModifiedListener(partial(self.error_widget.handleSceneChange,
                                                   self.sim_app_def))
        self.editor.view.setScene(self.scene.grScene)
        self.editor.view.update()

    def clearLayout(self, layout):
        ''' Remove all children from a layout '''
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def changeThread(self, _) -> None:
        '''Change the current scene in the viewport according to the thread.'''
        try:
            self.thread_wdgt.currentIndexChanged.disconnect()
        except TypeError:
            pass

        # Now figure out what the key pairs were
        state, thread = self.resolveThread()

        self.updateScene(state, thread)
        self.thread_wdgt.currentIndexChanged.connect(self.changeThread)
