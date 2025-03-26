'''
This window allows the user to manage the state machine,
what connected states it has and what states/threads execute.
It also provides the user with the ability to autogenerate the
error state as this requires maintenance of certain signals:

- Since you can't remove datasources and they exist in every state,
you must supply them with the signals they are defined with.
Despite this - with some you can use trigger signals to avoid
them outputting during this state.
'''
import copy
from functools import partial
from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QAbstractItemView, QAction, QGridLayout, QHeaderView, QInputDialog, QLabel,
    QLineEdit, QHBoxLayout, QMenu, QMessageBox, QScrollArea,
    QTreeView, QWidget, QPushButton, QVBoxLayout, QSizePolicy,
    QTableWidget, QTableWidgetItem,
)

from qtpy.QtWidgets import QComboBox

from martepy.marte2.objects import MARTe2RealTimeState
from martepy.marte2.objects.real_time_thread import MARTe2RealTimeThread
from martepy.functions.extra_functions import getname
from martepy.marte2.objects import MARTe2StateMachineEvent, MARTe2ReferenceContainer
from martepy.marte2.qt_classes import PanelledListConfig
from martepy.marte2.qt_functions import spacer
from martepy.marte2.qt_functions import deleteChildren, generateUniqueName, showErrorDialog
from martepy.functions.extra_functions import isint
from martepy.marte2.qt_classes import MessageConfigWindow

from xmarte.qt5.widgets.scene import EditorScene
from xmarte.qt5.windows.base_window import ModalOptionsWindow

from ..functions import genNextStateMsgs
from ..widgets.state_scene import StateScene, StateEditorGRView, StateNode
from ..widgets.state_edge import NextStateEdge, NextErrorStateEdge


class StateMachineWindow(ModalOptionsWindow):
    '''State machine window UI and logic.'''
    def __init__(self, application, app) -> None:
        super().__init__(application, app, 0.15,0.15,0.7,0.7)

        self.setWindowTitle("State Machine Configuration")
        self.app_def = self.application.API.getServiceByName('ApplicationDefinition')
        # Only take a copy rather than interact with this directly
        self.statemachine_def = copy.deepcopy(self.app_def.statemachine)
        self.application_states = copy.deepcopy(self.application.states)
        # We need to somehow map the keys of our states to their application_states def
        self.app_states_def = {}
        self.configBox = None
        self.stateNodes = None
        for state in self.application_states:
            state.prev_state_name = state.configuration_name.lstrip('+')
            for thread in state.threads.objects:
                thread.prev_thread_name = thread.configuration_name.lstrip('+')
        self.initUi()

    def initUi(self) -> None:
        '''Initialise the UI features.'''
        self.main_wgt = PanelledListConfig(self, 0.25, 0.75)
        self.central_layout = self.main_wgt.v_layout
        self.setCentralWidget(self.main_wgt)
        self.main_wgt.left_list.deleteLater()

        self.statetree = CustomTreeView(self)
        self.statetree.event_clicked.connect(self.eventClicked)
        self.statetree.state_clicked.connect(self.stateClicked)
        self.statetree.new_event.connect(self.createEvent)
        self.statetree.rem_event.connect(self.removeEvent)
        self.statetree.new_state.connect(self.createState)
        self.statetree.rem_state.connect(self.removeState)
        self.statetree.deselected.connect(self.deselect)
        self.main_wgt.left_panel_vlayout.addWidget(self.statetree)

        self.view_holder = QWidget()
        self.view_layout = QVBoxLayout()
        self.view_holder.setLayout(self.view_layout)

        self.main_view = StateEditorGRView(
            StateScene(self.application, real=True).grScene, self.view_holder
        )
        self.view_layout.addWidget(self.main_view)
        self.main_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view_holder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_wgt.right_panel_vlayout.addWidget(self.view_holder)
        self.configBox = None
        self.scene = self.main_view.scene().scene

        # Create a button for adding states
        btn_holder = QWidget()
        btn_layout = QHBoxLayout()
        btn_holder.setLayout(btn_layout)
        self.add_btn = QPushButton("Add State")
        self.rem_btn = QPushButton("Remove State")
        self.add_btn.clicked.connect(self.createState)
        self.rem_btn.clicked.connect(self.removeState)
        self.rem_btn.setEnabled(False)
        btn_layout.addWidget(spacer())
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.rem_btn)
        self.main_wgt.left_panel_vlayout.addWidget(btn_holder)

        self.createMenu()
        self.show()
        self.loadScene()
        self.main_view.scene_click.connect(self.deselect)

    def loadScene(self) -> None:
        """Load the states as StateNodes onto the scene."""
        # Load saved data
        if data := self.app_def.statemachine_serialized:
            self.scene.deserialize(data)
            self.stateNodes = {node.title: node for node in self.scene.nodes}
        # Generate new from application
        else:
            self.stateNodes = {
                getname(state): StateNode(
                    self.scene, getname(state),
                    inputs=[(0, ''), (1, '')], outputs=[(0, 'Next State'),
                                                        (1, 'Error State   ')]
                )
                for state in self.statemachine_def.states
            }
            for state in self.statemachine_def.states:
                try:
                    current_state = self.stateNodes[getname(state)]
                except (KeyError, AttributeError):
                    current_state = None
                for obj in state.objects:
                    try:
                        next_state = self.stateNodes[obj.nextstate]
                    except (KeyError, AttributeError):
                        next_state = None
                    if next_state and current_state:
                        NextStateEdge(self.scene, start_socket=current_state.outputs[0],
                                      end_socket=next_state.inputs[0], state_message = obj)
                    try:
                        next_error = self.stateNodes[obj.nextstateerror]
                    except (KeyError, AttributeError):
                        next_error = None
                    if next_error and current_state:
                        NextErrorStateEdge(self.scene, start_socket=current_state.outputs[1],
                                           end_socket=next_error.inputs[1], state_message = obj)

            self.application.API.cleanDiagram(self.scene, self.main_view)

    def createEvent(self, state_item):
        ''' Create a new event for the given state '''
        states = [a.configuration_name.replace('+','').upper() for a in self.application_states]
        event_name, done = QInputDialog.getText(
            self, 'Event name', 'Enter the event name:')
        if done:
            next_state, done = QInputDialog.getItem(
                self, 'Next state', 'Enter the next state:', states, editable=False)
            if done:
                # Its best to know this so we can auto generate the
                # messages for this event for the user
                self.genEvent(state_item, next_state, event_name)

    def genEvent(self, state_item, next_state, event_name):
        '''Abstract creation of a new event.'''
        msgs = genNextStateMsgs(next_state, self.app_def.app_name)
        event = MARTe2StateMachineEvent('+' + event_name.lstrip('+'), next_state, 'ERROR', 0, msgs)
        state_item.state.objects += [event]
        state_item.appendRow(EventItem(event.configuration_name, state_item, event))
        current_state = self.stateNodes[getname(state_item.state)]
        next_state = self.stateNodes[next_state]
        NextStateEdge(self.scene, start_socket=current_state.outputs[0],
                        end_socket=next_state.inputs[0], state_message = event)

    def removeEvent(self, event_item) -> None:
        """Remove an event."""
        # Remove from the tree view
        if event_item.event.configuration_name.replace('+','') == 'ERROR':
            QMessageBox.information(self,'Cannot delete ERROR event',
                                    '''You cannot delete the Error event,
 each state requires this eventuality.''', QMessageBox.Ok)
            return
        state_item = event_item.parent_item
        for row in range(state_item.rowCount()):
            if isinstance(row_item := state_item.child(row), EventItem):
                if row_item.event == event_item.event:
                    state_item.removeRow(row)

        # Remove from the application
        for state in self.statemachine_def.states:
            if state.configuration_name.lstrip('+').upper() == getname(state_item.state):
                for event in state.objects:
                    if event == event_item.event:
                        state.objects.remove(event)

        # Remove edge
        found_state = next((value for key, value in self.stateNodes.items() if
                            key == getname(state_item.state)),None)
        if found_state:
            found_edge = next((a for a in found_state.outputs[0].edges if
                               a.end_socket.node.title == event_item.event.nextstate), None)
            if found_edge:
                found_edge.remove()

    def createState(self):
        ''' create a new state '''
        thread_name = generateUniqueName([], 'Thread')
        # Create the state
        existing_names = [a.configuration_name.lstrip('+') for a in self.application_states]
        state_name = '+' + generateUniqueName(existing_names, 'State')
        tname = '+' + thread_name.lstrip('+')
        newthread = MARTe2ReferenceContainer(configuration_name='Threads',
                                             objects=[MARTe2RealTimeThread(tname)])
        self.application_states += [MARTe2RealTimeState('+' + state_name.lstrip('+'), newthread)]
        # Create the state machine definition
        state1 = MARTe2StateMachineEvent('+ERROR', 'ERROR', 'ERROR', 0, [])
        newstate = MARTe2ReferenceContainer(state_name.upper(), [state1])
        self.statemachine_def.states += [newstate]
        # Redraw
        state_item = StateItem(newstate.configuration_name, newstate)
        model = self.statetree.model
        second_to_last_index = model.rowCount() - 1
        root_item = model.invisibleRootItem()
        root_item.insertRow(second_to_last_index,state_item)
        state_item.appendRow(EventItem(state1.configuration_name, state_item, state1))
        index_to_select = model.indexFromItem(state_item)
        # Set the current selection in the selection model
        self.statetree.selectionModel().select(index_to_select, QItemSelectionModel.Select)

        # Emit the clicked signal on the QTreeView manually
        index_to_select = model.indexFromItem(state_item)
        clicked_index = QModelIndex(index_to_select)
        self.statetree.clicked.emit(clicked_index)

        # Add state to the scene
        cond_state_name = state_name.replace('+','').upper()
        self.stateNodes[cond_state_name] = StateNode(
            self.scene, cond_state_name,
            inputs=[(0, ''), (1, '')], outputs=[(0, 'Next State'), (1, 'Error State   ')]
        )
        # Get Error State Node
        NextErrorStateEdge(self.scene,
                           start_socket=self.stateNodes[cond_state_name].outputs[1],
                           end_socket=self.stateNodes['ERROR'].inputs[1],
                           state_message = state1)

    def removeState(self, state_item) -> None:
        """Remove a state."""
        # Check state item is defined
        if not state_item:
            curr_idx = self.statetree.selectionModel().currentIndex()
            state_item = self.statetree.model.itemFromIndex(curr_idx)
            if not state_item:
                return
        # Get the currently selected index
        selected_index = QModelIndex()
        item_idx = [self.statetree.model.indexFromItem(state_item)]
        if (index := self.statetree.selectedIndexes()) or (index := item_idx):
            selected_index = index[0]

        # Remove the item from the model
        if selected_index.isValid():
            if state_item.state.configuration_name.lstrip('+') == 'ERROR':
                QMessageBox.information(None, 'Cannot delete Error state',
                                              '''You cannot delete the error state,
 it must exist for the state machine to work''', QMessageBox.Ok)
                return
            if state_item.state.configuration_name.lstrip('+') == 'INITIAL':
                QMessageBox.information(None, 'Cannot delete Initial state',
                                              '''You cannot delete the initial state,
 it must exist for the state machine to work''', QMessageBox.Ok)
                return
            self.statetree.model.removeRow(selected_index.row(), selected_index.parent())

            # Remove the state from the application
            self.statemachine_def.states.remove(state_item.state)
            self.application_states = [a for a in self.application_states if
                                       not getname(a).upper() == getname(state_item.state)]
            # Remove state from the scene
            self.stateNodes[state_item.state.configuration_name.lstrip('+')].remove()
            del self.stateNodes[state_item.state.configuration_name.lstrip('+')]

    def deselect(self):
        ''' Deselect an item from treeview '''
        if self.configBox:
            self.configBox.deleteLater()
            self.configBox = None
        self.rem_btn.setEnabled(False)

    def stateClicked(self, state_item):
        ''' State has been selected, load config box '''
        if self.configBox:
            self.configBox.deleteLater()
        self.configBox = StateConfigurationBox(state_item, self.main_wgt.right_panel_wgt,
                                               self.application, self.statemachine_def,
                                               self.application_states)
        self.configBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.configBox.chg_state_name.connect(self.stateNameChg)
        self.main_wgt.right_panel_vlayout.addWidget(self.configBox)
        self.rem_btn.setEnabled(True)

    def stateNameChg(self, names) -> None:
        '''Update the StateNode title to reflect the new state name.'''
        oldname = names[0]
        newname = names[1]
        try:
            self.stateNodes[newname] = self.stateNodes.pop(oldname)
            self.stateNodes[newname].title = newname
        except KeyError:
            pass  # invalide node

    def eventClicked(self, event_item):
        ''' Event has been selected in treeview, open config box '''
        if self.configBox:
            self.configBox.deleteLater()
        self.configBox = EventConfigurationBox(event_item, self.application, self.app,
                                               self.main_wgt.right_panel_wgt,
                                               self.application_states)
        self.configBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.configBox.next_state_update.connect(partial(self.updateNextState, event_item))
        self.configBox.next_err_update.connect(partial(self.updateNextErr, event_item))
        self.main_wgt.right_panel_vlayout.addWidget(self.configBox)
        self.rem_btn.setEnabled(False)

    def updateNextState(self, event_item, next_state):
        ''' Update name of next state '''
        state_name = getname(event_item.parent_item.state)
        current_state, next_state_obj = self.getStatesToUpdate(state_name, next_state)
        if next_state_obj and current_state:
            # This assumes that the state has only one event
            # Find the edge associated with this
            found_edge = next((a for a in current_state.outputs[0].edges if
                               a.end_socket.node.title == event_item.event.nextstate), None)
            if found_edge:
                found_edge.remove()
            NextStateEdge(self.scene, start_socket=current_state.outputs[0],
                          end_socket=next_state_obj.inputs[0],
                          state_message = event_item.event)

    def updateNextErr(self, event_item, next_err):
        ''' Update name of next error state '''
        state_name = getname(event_item.parent_item.state)
        current_state, next_state_obj = self.getStatesToUpdate(state_name, next_err)
        if next_state_obj and current_state:
            found_edge = next((a for a in current_state.outputs[0].edges if
                               a.end_socket.node.title == event_item.event.nextstate), None)
            if found_edge:
                found_edge.remove()
            NextErrorStateEdge(self.scene, start_socket=current_state.outputs[1],
                               end_socket=next_state_obj.inputs[1],
                               state_message = event_item.event)

    def getStatesToUpdate(self, current, next_state):
        ''' Get state for updating '''
        try:
            current_state = self.stateNodes[current]
        except (KeyError, AttributeError):
            current_state = None
        try:
            next_state_obj = self.stateNodes[next_state]
        except (KeyError, AttributeError):
            next_state_obj = None
        return current_state, next_state_obj

    def createMenu(self):
        ''' Create the window menu '''
        # Create actions
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')  # Set Ctrl + S shortcut
        save_action.triggered.connect(self.save)
        exit_action = QAction("Exit", self)

        # Connect actions to slots (if needed)
        exit_action.triggered.connect(self.close)

        # Create menus
        file_menu = self.menuBar().addMenu("File")

        # Add actions to menus
        file_menu.addAction(save_action)
        file_menu.addAction(exit_action)

    def save(self) -> None: # pylint: disable=R0914,R0912,R0915
        '''Save changes made in the state machine and update application accordingly.'''
        # Build the state machine object
        app_def = self.application.API.getServiceByName('ApplicationDefinition')
        state_service = self.application.API.getServiceByName('StateDefinitionService')
        # Here we need to build the state
        app_def.statemachine = self.statemachine_def
        # We need to iterate through our applications states
        # definition self.application.states[][]
        # And remap these
        self.application.states = self.application_states
        def getStateDef(name):
            ''' get state definition given a state name from our states '''
            for state_name, state_dict in self.application.state_scenes.items():
                if state_name == name:
                    return state_dict
            return None

        def removeStateDef(name):
            ''' Given a state name, remove it from our known states '''
            new_dict = {}
            for k, v in self.application.state_scenes.items():
                if k != name:
                    new_dict[k] = v
            self.application.state_scenes = new_dict

        def removeThreadDef(state, name):
            ''' Remove a thread from a state '''
            new_dict = {}
            for k, v in state.items():
                if k != name:
                    new_dict[k] = v
            return new_dict

        def getThreadDef(state, name):
            ''' Get a thread definition '''
            for thread_name, thread_scene in state.items():
                if thread_name == name:
                    return thread_scene
            return None

        def handlePrevThread(thread, new_state_name):
            ''' Handler for the previous thread '''
            state_scene = self.application.state_scenes[new_state_name]
            thread_scene = getThreadDef(state_scene, thread.prev_thread_name)
            if thread_scene:
                # Thread does exist, possibly rename
                state_scene = removeThreadDef(state_scene, thread.prev_thread_name)
                state_scene[new_thread_name] = thread_scene
                thread_scene.scene_name = f'{new_state_name}-{new_thread_name}'
                return True
            return False

        for state in self.application_states: # pylint: disable=R1702
            # Find the corresponding prev state
            new_state_name = state.configuration_name.lstrip('+')
            if hasattr(state,'prev_state_name'):
                state_scene_dict = getStateDef(state.prev_state_name)
                if state_scene_dict:
                    # Reset name if changed
                    removeStateDef(state.prev_state_name)
                    self.application.state_scenes[new_state_name] = state_scene_dict
                    for thread in state.threads.objects:
                        # Same as with states really
                        new_thread_name = thread.configuration_name.lstrip('+')
                        if hasattr(thread,'prev_thread_name'):
                            if handlePrevThread(thread, new_state_name):
                                continue
                        # Thread does not exist, add it
                        new_scene = EditorScene(self.application, True,
                                                f'{new_state_name}-{new_thread_name}')
                        self.application.state_scenes[new_state_name][new_thread_name]= new_scene
                        state_service.resetScene(new_scene)
                continue

            # Was none - likely a new state, create it
            self.application.state_scenes[new_state_name] = {}
            # Now create its threads
            for thread in state.threads.objects:
                new_thread_name = thread.configuration_name.lstrip('+')
                new_scene = EditorScene(self.application, True,
                                        f'{new_state_name}-{new_thread_name}')
                self.application.state_scenes[new_state_name][new_thread_name]= new_scene
                state_service.resetScene(new_scene)
        # if a state/thread does not exist, create it's scene and layout
        # Note: make state and thread names all lower case in state_scenes for easier to find
        # If it shouldn't exist, delete it and the scene
        states_to_delete = []
        for state_name, state in self.application.state_scenes.items():
            if state_name not in [getname(a) for a in self.application.states]:
                states_to_delete.append(state_name)
        # Delete the keys after the iteration is complete
        for state in states_to_delete:
            for thread_name, thread in self.application.state_scenes.items():
                thread = None
            del self.application.state_scenes[state]

        for state_name, state in self.application.state_scenes.items():
            threads_to_delete = []
            for thread_name, thread in state.items():
                state_def = next(a for a in self.application.states if
                                 getname(a) == state_name)
                if thread_name not in [getname(a) for a in state_def.threads.objects]:
                    self.application.state_scenes[state_name][thread_name] = None
                    threads_to_delete.append(thread_name)
            for thread_name in threads_to_delete:
                del self.application.state_scenes[state_name][thread_name]

        # Update states populateCombo's method.
        state_service.thread_wdgt.currentIndexChanged.disconnect()
        state_service.thread_wdgt.clear()
        state_service.populateCombos(self.application.state_scenes)
        state_service.thread_wdgt.currentIndexChanged.connect(state_service.changeThread)

    def closeEvent(self, event) -> None:
        ''' Close prompt on the state machine window - ask to save and save definition '''
        app_def = self.application.API.getServiceByName('ApplicationDefinition')
        app_def.statemachine_serialized = self.scene.serialize()

        app_states = [a.serialize() for a in self.application_states]
        states = [a.serialize() for a in self.application.states]
        machine = app_def.statemachine.serialize()
        machine_def = self.statemachine_def.serialize()
        if not (machine == machine_def and states == app_states):
            reply = QMessageBox.question(
                self, 'Save Changes', "Do you want to save changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if reply == QMessageBox.Save:
                self.save()
            elif reply == QMessageBox.Cancel:
                event.ignore()

class EventConfigurationBox(QWidget):
    ''' The event configuration box for the user to modify event definitions '''
    next_state_update = pyqtSignal(str)
    next_err_update = pyqtSignal(str)

    def __init__(self, event_item, application, app, parent=None, app_states = None):
        super().__init__(parent)
        self.application = application
        self.app = app
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.configBox = QGridLayout()
        self.setLayout(self.configBox)
        self.state = event_item.parent_item.state
        self.event = event_item.event
        # Now populate with our options
        event_name_lbl = QLabel("Event Name:")
        event_name = self.event.configuration_name.lstrip('+')
        state_name = self.state.configuration_name.lstrip('+')
        self.event_name_edt = QLineEdit()
        self.event_name_edt.setText(event_name)
        self.configBox.addWidget(event_name_lbl, 0, 0)
        self.configBox.addWidget(self.event_name_edt, 0, 1)
        self.configBox.addWidget(spacer(), 0, 2)
        row = 0
        if event_name == 'ENTER' and state_name == 'ERROR':
            self.event_name_edt.setEnabled(False)
        else:
            states = [a.configuration_name.replace('+','').upper() for a in app_states]
            # Now populate with our options
            next_state_lbl = QLabel("Next State:")
            self.next_state_edt = QComboBox()
            self.next_state_edt.addItems(states)
            self.next_state_edt.setCurrentText(self.event.nextstate.upper())
            self.next_state_edt.currentTextChanged.connect(self.updateNextState)

            next_state_error_lbl = QLabel("Next State Error:")
            self.next_state_err_edt = QComboBox()
            self.next_state_err_edt.addItems(states)
            self.next_state_err_edt.setCurrentText(self.event.nextstateerror.upper())
            self.next_state_err_edt.currentIndexChanged.connect(self.updateNextErr)

            timeout_lbl = QLabel("Timeout:")
            self.timeout_edt = QLineEdit()
            self.timeout_edt.setText(str(self.event.timeout))

            self.configBox.addWidget(next_state_lbl, 1, 0)
            self.configBox.addWidget(self.next_state_edt, 1, 1)
            self.configBox.addWidget(spacer(), 1, 2)
            self.configBox.addWidget(next_state_error_lbl, 2, 0)
            self.configBox.addWidget(self.next_state_err_edt, 2, 1)
            self.configBox.addWidget(spacer(), 2, 2)
            self.configBox.addWidget(timeout_lbl, 3, 0)
            self.configBox.addWidget(self.timeout_edt, 3, 1)
            self.configBox.addWidget(spacer(), 3, 2)
            row = 3

        self.config_msg_btn = QPushButton("Configure Messages")
        self.config_msg_btn.clicked.connect(self.openmsgWnd)
        self.configBox.addWidget(self.config_msg_btn, row, 3)
        self.msg_window = None

    def updateNextState(self):
        ''' Update the next state for this event '''
        self.next_state_update.emit(self.next_state_edt.currentText())

    def updateNextErr(self):
        ''' Update the next error for this event '''
        self.next_err_update.emit(self.next_state_err_edt.currentText())

    def openmsgWnd(self):
        ''' Open the message configuration window for this event '''
        if not hasattr(self.event, 'messages') and hasattr(self.event, 'objects'):
            pointer = self.event.objects
        else:
            pointer = self.event.messages
        self.msg_window = MessageConfigWindow(self.application, self.app,
                                original=pointer,origin=pointer,
                                title='Event Messages Configuration',sizes=[0.2,0.2,0.6,0.6])

class StateConfigurationBox(QWidget):
    ''' The configuration box widgets for the user to configure this state '''
    chg_state_name = pyqtSignal(tuple)

    def __init__(self, state_item, parent=None, application=None,
                 statemachine_def=None, app_states=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.application = application
        self.app = application.app
        self.statemachine_def = statemachine_def
        self.state_item = state_item
        self.state = state_item.state
        self.application_states = app_states
        self.configBox = QVBoxLayout()
        self.state_def = None
        self.configBox.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.configBox)
        self.draw()

    def draw(self): # pylint: disable=R0914,R0915
        ''' Draw the configuration box for this state '''
        statemachine_def = self.statemachine_def
        deleteChildren(self.configBox)
        name_holder = QWidget()
        name_holder.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        name_layout = QHBoxLayout()
        name_holder.setLayout(name_layout)
        state_name = getname(self.state)
        # If this is the first entry in our statemachine_def then it is the
        # entrypoint and has no threads or executions
        if getname(statemachine_def.states[0]) == state_name:
            lbl = QLabel('''This is the entrypoint to the statemachine and not associated
 with an actual state in the application.''')
            self.configBox.addWidget(lbl)
        else:
            # Now we need to find our instance of state in the application
            # which differs from the statemachine state def
            self.state_def = next(state for state in self.application_states if
                                  getname(state).upper() == state_name.upper())
            if state_name == 'ERROR':
                lbl = QLabel('''This is the error state to the statemachine,
 you cannot change this states name, it must exist as named with a event named enter''')
                self.configBox.addWidget(lbl)
            name_lbl = QLabel("State Name:")
            self.name_edt = QLineEdit()
            if state_name == "ERROR":
                self.name_edt.setEnabled(False)
            self.name_edt.setText(getname(self.state_def))
            self.name_edt.textChanged.connect(self.stateNameChg)
            name_layout.addWidget(name_lbl)
            name_layout.addWidget(self.name_edt)
            name_layout.addWidget(spacer())
            self.configBox.addWidget(name_holder)
            # Need to provide the user with options to create threads here.

            thread_lbl = QLabel("Threads:")
            self.thread_tbl = QTableWidget()
            self.thread_tbl.setColumnCount(2)
            self.thread_tbl.setHorizontalHeaderLabels(["Thread Name", "CPU Mask"])
            self.thread_tbl.setSelectionBehavior(QTableWidget.SelectRows)
            self.thread_tbl.setEditTriggers(QTableWidget.DoubleClicked)
            header = self.thread_tbl.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)

            # Create a QScrollArea
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)  # Allow the scroll area to resize its widget

            # Need to find the state in the application based on our state name
            self.thread_tbl.setRowCount(len(self.state_def.threads.objects))
            for row, thread in enumerate(self.state_def.threads.objects):
                thread_name_item = QTableWidgetItem(getname(thread))
                thread_mask_item = QTableWidgetItem(str(thread.cpu_mask))
                thread_name_item.thread = thread
                thread_mask_item.thread = thread
                self.thread_tbl.setItem(row, 0, thread_name_item)
                self.thread_tbl.setItem(row,1, thread_mask_item)

            self.thread_tbl.itemChanged.connect(self.threadChange)

            # Add the QTableWidget to the QScrollArea
            scroll_area.setWidget(self.thread_tbl)

            # Calculate 20% of the window height
            max_height = self.parent().height() * 0.25
            # Set the maximum height of the QScrollArea
            scroll_area.setMaximumHeight(int(round(max_height)))
            self.configBox.addWidget(thread_lbl)
            self.configBox.addWidget(scroll_area)

            btn_holder = QWidget()
            btn_layout = QHBoxLayout()
            btn_holder.setLayout(btn_layout)

            self.add_thread_btn = QPushButton("Add Thread")
            self.add_thread_btn.clicked.connect(self.addThread)
            self.rem_thread_btn = QPushButton("Remove Thread")
            self.rem_thread_btn.clicked.connect(self.removeThread)
            btn_layout.addWidget(spacer())
            btn_layout.addWidget(self.add_thread_btn)
            btn_layout.addWidget(self.rem_thread_btn)
            self.configBox.addWidget(btn_holder)

    def threadChange(self, item):
        ''' User has changed something about the selected row/thread '''
        column = self.thread_tbl.indexFromItem(item).column()
        if column == 0:
            item.thread.configuration_name = '+' + item.text().lstrip('+')
        if column == 1:
            if isint(item.text()):
                item.thread.cpu_mask = int(item.text())
            else:
                showErrorDialog("CPU mask must be an integer.")
                item.setText(str(item.thread.cpu_mask))

    def addThread(self):
        ''' Add a new thread to the current selected state '''
        state_name = getname(self.state)
        self.state_def = next(state for state in self.application_states if
                              getname(state).upper() == state_name.upper())
        thread_names = [getname(a) for a in self.state_def.threads.objects]
        unique_name = generateUniqueName(thread_names, 'Thread')
        new_thread = MARTe2RealTimeThread('+' + unique_name)
        self.state_def.threads.objects += [new_thread]
        self.draw()

    def removeThread(self):
        ''' Remove a thread definition '''
        state_name = getname(self.state)
        self.state_def = next(state for state in self.application_states if
                              getname(state).upper() == state_name.upper())
        for item in self.thread_tbl.selectedItems():
            self.state_def.threads.objects = [a for a in self.state_def.threads.objects if
                                              not a == item.thread]
        self.draw()

    def stateNameChg(self):
        ''' User has changed the state name, handle across the board '''
        newname = self.name_edt.text()
        state_name = getname(self.state)
        self.state_def = next(state for state in self.application_states if
                              getname(state).upper() == state_name.upper())
        self.state_def.configuration_name = '+' + newname.lstrip('+')
        self.state.configuration_name = '+' + (newname := newname.upper().lstrip('+'))
        self.state_item.setText(newname)
        self.chg_state_name.emit((state_name, newname))

class StateItem(QStandardItem):
    ''' Stores informtiona on the state it represents in the tree view '''
    def __init__(self, text, state):
        text = text.strip('+')
        super().__init__(text)
        self.setEditable(False)
        self.state = state

class EventItem(QStandardItem):
    ''' Stores information on the event it represents in the tree view '''
    def __init__(self, text, parent_item, event):
        text = text.strip('+')
        super().__init__(text)
        self.setEditable(False)
        self.parent_item = parent_item
        self.event = event

class CustomTreeView(QTreeView):
    ''' Customised tree view for states and events '''
    clicked_add = pyqtSignal(QPoint)
    clear_sel = pyqtSignal()
    deselected = pyqtSignal()
    event_clicked = pyqtSignal(EventItem)
    state_clicked = pyqtSignal(StateItem)
    new_event = pyqtSignal(StateItem)
    rem_event = pyqtSignal(EventItem)
    new_state = pyqtSignal()
    rem_state = pyqtSignal(StateItem)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.statemachine_def = parent.statemachine_def
        self.initUI()
        # Connect clicked signal of the viewport to clear_selection function
        self.viewport().installEventFilter(self)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        # Connect the customContextMenuRequested signal of
        # the viewport to the showContextMenu function
        self.viewport().customContextMenuRequested.connect(self.showContextMenu)
        self.clicked_add.connect(self.showContextMenu)
        self.clicked.connect(self.handleSelectedItem)
        self.clear_sel.connect(self.clearSelection)

    def handleSelectedItem(self, idx):
        ''' Handle the user selecting an item and expand it '''
        item = self.model.itemFromIndex(idx)
        if isinstance(item, StateItem):
            self.state_clicked.emit(item)
        if isinstance(item, EventItem):
            self.event_clicked.emit(item)

    def eventFilter(self, obj, event):
        ''' filter user events and handle them '''
        if obj == self.viewport() and event.type() == event.MouseButtonPress:
            # Get the mouse position relative to the viewport
            mouse_pos = event.pos()

            # Get the index of the item at the mouse position
            index = self.indexAt(mouse_pos)

            # Check if the index is valid (i.e., an item is clicked)
            if index.isValid():
                if event.buttons() == Qt.LeftButton:
                    self.clicked.emit(QModelIndex(index))
            else:
                if event.buttons() == Qt.LeftButton:
                    self.clear_sel.emit()
                if event.buttons() == Qt.RightButton:
                    self.clicked_add.emit(mouse_pos)
        return super().eventFilter(obj, event)

    def clearSelect(self):
        ''' User has left clicked off an item in the treeview '''
        self.clearSelection()
        self.deselected.emit()

    def showContextMenu(self, point):
        ''' User has right clicked off an item in the treeview '''
        # Get the global position of the right-click
        global_point = self.viewport().mapToGlobal(point)

        # Create the context menu
        context_menu = QMenu(self)
        action = QAction('Add State', self)
        context_menu.addAction(action)
        action.triggered.connect(self.addState)

        # Show the context menu at the global position
        context_menu.exec_(global_point)

    def initUI(self):
        ''' Initialize the Tree View UI '''
        # Create the model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['States'])

        # Add items to the model
        root_item = self.model.invisibleRootItem()

        for state in self.statemachine_def.states:
            state_item = StateItem(state.configuration_name, state)
            root_item.appendRow(state_item)
            for event in state.objects:
                state_item.appendRow(EventItem(event.configuration_name, state_item, event))

        # Set the model for the tree view
        self.setModel(self.model)

    def contextMenuEvent(self, event):
        ''' Show the context menu for what event/state to add '''
        index = self.indexAt(event.pos())
        if index.isValid():
            item = self.model.itemFromIndex(index)
            if isinstance(item, EventItem):
                state_name = getname(item.parent().state)
                event_name = getname(item.event)
                if not event_name == 'ERROR' and not state_name == 'INITIAL':
                    if not (getname(item.parent().state) == 'ERROR' and event_name == 'ENTER'):
                        menu = QMenu(self)
                        action = QAction("Delete Event", self)
                        menu.addAction(action)
                        action.triggered.connect(partial(self.deleteEvent, item))
                        menu.exec_(self.viewport().mapToGlobal(event.pos()))
            elif isinstance(item, StateItem):
                if not getname(item.state) == 'INITIAL':
                    menu = QMenu(self)
                    if not getname(item.state) == 'ERROR':
                        action = QAction("Delete State", self)
                        menu.addAction(action)
                        action.triggered.connect(partial(self.deleteState, item))
                    action = QAction("Add Event", self)
                    menu.addAction(action)
                    action.triggered.connect(partial(self.addEvent, item))
                    menu.exec_(self.viewport().mapToGlobal(event.pos()))

    def addEvent(self, add_after) -> None:
        """Add an event to the selected state."""
        self.new_event.emit(add_after)

    def deleteEvent(self, item) -> None:
        """Delete an event from the menu."""
        self.rem_event.emit(item)

    def addState(self) -> None:
        """Add a state to the menu."""
        self.new_state.emit()

    def deleteState(self, item) -> None:
        """Delete a state from the menu."""
        self.rem_state.emit(item)
