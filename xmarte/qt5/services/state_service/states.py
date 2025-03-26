'''Define the state definition service which handles all aspects relating to states.'''

from PyQt5.QtWidgets import (
    QLabel,
    QComboBox,
    QPushButton,
    QStyledItemDelegate,
)

from martepy.marte2.datasource import MARTe2DataSource
from martepy.marte2.objects import (MARTe2StateMachine,
                                    MARTe2StateMachineEvent,
                                    MARTe2ReferenceContainer)
from martepy.marte2.objects.real_time_state import MARTe2RealTimeState
from martepy.marte2.objects.real_time_thread import MARTe2RealTimeThread

from xmarte.qt5.services.service import Service
from xmarte.qt5.widgets.scene import EditorScene
from .functions import genNextStateMsgs
from .windows.state_machine_window import StateMachineWindow

class StateDefinitionService(Service):
    '''State definition service handles states and threads.'''

    service_name = 'StateDefinitionService'

    def __init__(self, application) -> None:
        super().__init__(application)
        # Get our internal app definition
        self.app_def = self.application.API.getServiceByName('ApplicationDefinition')
        self.recovery_service = self.application.API.getServiceByName('RecoveryService')

        self.setupDefaultStates()

        self.setupStateScenes()

        self.updateScene('State1', 'Thread1')

        self.addToolbarOptions(self.application.editToolBar.service_layout)

    def setupDefaultStates(self):
        ''' Reset the state machine on startup and set the normal default states '''
        # First we must define our list of states
        states = []
        # First you want an entry point which just starts the application
        app_name = self.app_def.app_name
        msgs = genNextStateMsgs('State1', app_name)
        msgs.pop(0)
        initial_event = MARTe2StateMachineEvent('+START', 'STATE1', 'ERROR', 0, msgs)
        states += [MARTe2ReferenceContainer("+INITIAL", [initial_event])]
        msgs = genNextStateMsgs('Error', app_name)
        state1 = MARTe2StateMachineEvent('+ERROR', 'ERROR', 'ERROR', 0, [])
        states += [MARTe2ReferenceContainer("+STATE1", [state1])]

        # The error state is special, it needs the enter and reset state,
        # the enter state must exist!
        msgs = genNextStateMsgs('Error', app_name)
        error_enter = MARTe2ReferenceContainer('+ENTER', msgs)
        msgs = genNextStateMsgs('State1', app_name)
        error_reset = MARTe2StateMachineEvent('+RESET', 'STATE1', 'STATE1', 0, msgs)
        states += [MARTe2ReferenceContainer("+ERROR", [error_enter, error_reset])]

        self.app_def.statemachine = MARTe2StateMachine('+StateMachine', states)

        # Now we have the state machine defined, define it's
        # associated states in the application
        # and threads
        self.application.states = []

        threads = MARTe2ReferenceContainer(configuration_name='Threads',
                                           objects=[MARTe2RealTimeThread('+Thread1',
                                                                         functions = [])])
        self.application.states += [MARTe2RealTimeState('+State1',threads)]

        threads = MARTe2ReferenceContainer(configuration_name='Threads',
                                           objects=[MARTe2RealTimeThread('+Thread1',
                                                                         functions = [])])
        self.application.states += [MARTe2RealTimeState('+Error',threads)]

    def deleteAll(self):
        ''' Delete all scenes and states '''
        # Do not leave this called and then not populate the application with new items
        for _, state in self.application.state_scenes.items():
            for _, thread_scene in state.items():
                thread_scene.clear()
                thread_scene = None

        self.application.state_scenes = {}
        self.application.states = []
        self.app_def.statemachine = None
        self.thread_wdgt.currentIndexChanged.disconnect()
        self.thread_wdgt.clear()
        self.thread_wdgt.currentIndexChanged.connect(self.changeThread)

    def loadStates(self, marte2_application, state_machine):
        ''' Load states from a given app definition '''
        # Given a MARTe2 application definition, load up the states and threads
        self.deleteAll()
        # Now populate based on our given definition, for statemachine this is easy
        self.app_def.statemachine = state_machine
        self.application.states = marte2_application.states
        self.setupStateScenes()
        self.thread_wdgt.currentIndexChanged.disconnect()
        self.populateCombos(self.application.state_scenes)
        self.thread_wdgt.currentIndexChanged.connect(self.changeThread)

    def setupStateScenes(self):
        ''' Setup the scenes for each state '''
        if not hasattr(self.application,'state_scenes'):
            self.application.state_scenes = {}

        def removePlus(string):
            if string.startswith('+'):
                return string[1:]
            return string

        for state in self.application.states:
            # For each state and subsequently thread, create a scene if it doesn't already exist
            state_name = removePlus(state.configuration_name)
            if state_name not in list(self.application.state_scenes.keys()):
                self.application.state_scenes[state_name] = {}
            for thread in state.threads.objects:
                thread_name = removePlus(thread.configuration_name)
                if thread_name not in list(self.application.state_scenes[state_name].keys()):
                    # Doesn't exist, create scene
                    new_scene = EditorScene(self.application, True,
                                            f'{state_name}-{thread_name}')
                    self.resetScene(new_scene)
                    self.application.state_scenes[state_name][thread_name] = new_scene

    def addToolbarOptions(self, layout) -> None:
        """
        This function is called at startup and allows you to add functions to the toolbar
        """
        thread_label = QLabel('StateThread:')
        thread_label.setObjectName('ThreadLbl')
        layout.addWidget(thread_label)

        self.thread_wdgt = QComboBox(self.application)
        self.thread_wdgt.setItemDelegate(QStyledItemDelegate(self.thread_wdgt))

        layout.addWidget(self.thread_wdgt)

        self.populateCombos(self.application.state_scenes)

        self.thread_wdgt.setCurrentIndex(1)
        self.thread_wdgt.currentIndexChanged.connect(self.changeThread)


        self.state_machine = QPushButton("State Machine")
        self.state_machine.clicked.connect(self.openWindow)
        layout.addWidget(self.state_machine)

    def openWindow(self):
        '''Open the state machine window when clicked.'''
        self.application.newwindow = StateMachineWindow(self.application, self.application.app)

    def populateCombos(self, dictionary, indent=0) -> None:
        '''Populate the state and thread comboboxes.'''
        for key, value in dictionary.items():
            if isinstance(value, dict):
                item_text = " " * indent + key
                self.thread_wdgt.addItem(item_text)
                self.populateCombos(value, indent=indent+2)
            else:
                item_text = " " * (indent + 2) + key
                self.thread_wdgt.addItem(item_text)


    def changeThread(self, _) -> None:
        '''Change the current scene in the viewport according to the thread.'''
        self.thread_wdgt.currentIndexChanged.disconnect()

        # Now figure out what the key pairs were
        state, thread = self.resolveThread()

        self.updateScene(state, thread)
        self.thread_wdgt.currentIndexChanged.connect(self.changeThread)

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

    def updateScene(self, state, thread) -> None:
        '''Change the logical and graphical scene according to the
        selected state and thread.'''
        # Check that any threads exist in the state
        self.application.scene = self.application.state_scenes[state][thread]
        self.application.editor.view.setScene(self.application.scene.grScene)
        self.application.editor.view.update()

    def resetScene(self, scene=None) -> None:
        '''
        Reset variables stored in our scene definitions
        '''
        if scene is None:
            scene = self.application.scene

        scene.application = self.application
        scene.resetClearCallbacks()
        scene.addClearListener(self.resetScene)
        scene.clearNodeRemoveListener()
        scene.clearModifiedListener()
        scene.addModifiedListener(self.recovery_service.saveRecovery)
        scene.addModifiedListener(self.application.rightpanel.splitlistener)
        scene.addItemsDeselectedListener(self.application.rightpanel.deselected)

    def clearScene(self) -> None:
        '''
        Reset rtcc2 variables in the scene
        '''
        self.resetScene(self.application.scene)

    @staticmethod
    def getStates(application) -> list:
        '''Get all states in the application.'''
        return list(application.state_scenes.keys())

    @staticmethod
    def getStateThreads(application, state: str):
        '''Get all threads in a given state.'''
        return list(application.state_scenes[state].keys())

    @staticmethod
    def getStateThreadFunctions(application, state:str, thread:str) -> list:
        '''Get all gams in a given thread and state'''
        gam = []
        for node in application.state_scenes[state][thread].nodes:
            blk = application.API.toGAM(node)
            if not isinstance(blk, MARTe2DataSource):
                gam.append(application.API.toGAM(node))
        return gam

    @staticmethod
    def getStateThreadNodes(application, state:str, thread:str) -> list:
        '''Get all non-datasource nodes in a given thread and state'''
        gam = []
        for node in application.state_scenes[state][thread].nodes:
            blk = application.API.toGAM(node)
            if not isinstance(blk, MARTe2DataSource):
                gam.append(node)
        return gam

    @staticmethod
    def getAllFunctions(application) -> list:
        '''Get all nodes in the application.'''
        return [
            a for a in StateDefinitionService.getAllNodes(application.state_scenes)
            if not isinstance(application.API.toGAM(a), MARTe2DataSource)
        ]

    @staticmethod
    def getAllDataSources(application) -> list:
        '''Get all datasources in the application.'''
        return [
            a for a in StateDefinitionService.getAllNodes(application.state_scenes)
            if isinstance(application.API.toGAM(a), MARTe2DataSource)
        ]

    @staticmethod
    def getAllNodes(states) -> list:
        '''Get all nodes from all threads in all states.'''
        nodes = []
        for state in states.values():
            for thread in state.values():
                nodes.extend(thread.nodes)
        return nodes
