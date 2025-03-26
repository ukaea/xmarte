'''
The StateScene class overrides methods from EditorScene to allow StateNodes
to be recognised and to trigger the state message window.
'''

import copy

from qtpy.QtGui import QKeyEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt, pyqtSignal

from nodeeditor.node_edge import EDGE_TYPE_DEFAULT
from nodeeditor.utils import dumpException

from xmarte.qt5.libraries.functions import PluginException
from xmarte.qt5.widgets.nodeditor import EditorGRView
from xmarte.qt5.widgets.scene import EditorScene
from xmarte.nodeeditor.node_graphics_socket import XMARTeQDMGraphicsSocket
from xmarte.nodeeditor.node_edge_dragging import XMARTeEdgeDragging
from .state_node import StateNode
from .state_edge import StateEdge, NextStateEdge, NextErrorStateEdge


class StateScene(EditorScene):
    '''Logical representation of the state machine scene.'''
    def nodeClassSelectorFunction(self, _) -> 'type[StateNode]':
        '''Override node classifier to point to the StateNode.'''
        return StateNode

    def getEdgeClass(self) -> 'type[StateEdge]':
        return StateEdge

    def deserialize( # pylint:disable=W1113,R0914,R0912
        self, data: dict, hashmap: dict = {}, restore_id: bool = True, *args, **kwargs
    ) -> bool:
        ''' Deserialise and override to include UUID '''
        prev = self.large_import
        self.large_import = True
        hashmap = {}

        if restore_id:
            self.id = data["id"]

        self.version_uuid = data["version_uuid"]
        # -- deserialize NODES

        # go through deserialized nodes:
        for node_data in data["nodes"]:
            try:
                new_node_class = self.getNodeClassFromData(node_data)
                new_node = new_node_class(self)
                new_node.deserialize(
                    node_data, hashmap, restore_id, *args, **kwargs
                )
                new_node.onDeserialized(node_data)
                # print("New node for", node_data['title'])
            except (KeyError, ValueError, AssertionError) as exc:
                raise PluginException() from exc

        # -- deserialize EDGES

        # go through deserialized edges:
        for edge_data in data["edges"]:
            StateEdge(self,).deserialize(
                edge_data, hashmap, restore_id, *args, **kwargs
            )

        # Convert StateEdges to NextState/ErrorState edges where required
        for state_edge in copy.copy(self.edges):
            if state_edge.start_socket.socket_type == 0:
                NextStateEdge(self, state_edge.start_socket, state_edge.end_socket,
                              state_message = state_edge.state_message)
            else:
                NextErrorStateEdge(self, state_edge.start_socket, state_edge.end_socket,
                                   state_message = state_edge.state_message)

        for edge in copy.copy(self.edges):
            # must use type() here because isinstance fails with inheritance
            if type(edge) == StateEdge:  # pylint:disable=C0123
                self.removeEdge(edge)

        # We should move the deserialisers to the end so that our hashmap is pre-defined
        for v in self.deserialisers.values():
            v(self, data, hashmap, restore_id, args, kwargs)

        self.large_import = prev
        return True


class StateEdgeDragging(XMARTeEdgeDragging):
    ''' Class used when the user drags the edge and the arc path needs recalculating '''
    def getStateEdgeClass(self, socket_type):
        """Helper function to get the Edge class. Using what Scene class provides"""
        if socket_type == 0:
            return NextStateEdge
        return NextErrorStateEdge

    def edgeDragStart(self, item):
        """Code handling the start of a dragging an `Edge` operation"""
        try:
            self.drag_start_socket = item.socket
            self.drag_edge = self.getStateEdgeClass(item.socket_type)(
                item.socket.node.scene,
                item.socket, None,
                EDGE_TYPE_DEFAULT
            )
            self.drag_edge.grEdge.makeUnselectable()
        except AttributeError as e:
            dumpException(e)

    def edgeDragEnd(self, item): # pylint:disable=R0912
        """Code handling the end of the dragging an `Edge` operation.
        If this code returns True then skip the
        rest of the mouse event processing. Can be called with ``None``
        to cancel the edge dragging mode

        :param item: Item in the `Graphics Scene` where we ended dragging an `Edge`
        :type item: ``QGraphicsItem``
        """

        # early out - clicked on something else than Socket
        if not isinstance(item, XMARTeQDMGraphicsSocket):
            self.grView.resetMode()
            self.drag_edge.remove(silent=True) # don't notify sockets about removing drag_edge
            self.drag_edge = None


        # clicked on socket
        if isinstance(item, XMARTeQDMGraphicsSocket): # pylint:disable=R1702

            # check if edge would be valid
            if not self.drag_edge.validateEdge(self.drag_start_socket, item.socket):
                print("NOT VALID EDGE")
                return False

            # regular processing of drag edge
            self.grView.resetMode()

            self.drag_edge.remove(silent=True) # don't notify sockets about removing drag_edge
            self.drag_edge = None

            try:
                if item.socket != self.drag_start_socket:
                    # if we released dragging on a socket (other then the beginning socket)
                    state_machine = self.grView.grScene.scene.application.newwindow
                    state = state_machine.statetree.model.findItems(
                        self.drag_start_socket.node.title)[0]
                    next_state = state_machine.statetree.model.findItems(item.socket.node.title)[0]
                    if item.socket.is_input:
                        state_machine.genEvent(state, next_state.text(), 'Event1')
                    else:
                        state_machine.genEvent(next_state, state.text(), 'Event1')

                    self.grView.grScene.scene.history.storeHistory("Created new edge by dragging",
                                                                   setModified=True)
                    return True
            except AttributeError as e:
                dumpException(e)
        return False

class StateEditorGRView(EditorGRView):
    '''Override the editor view to use the new dragging class.'''
    scene_click = pyqtSignal()

    def __init__(self, grScene, parent=None):
        super().__init__(grScene, parent)
        self.dragging = StateEdgeDragging(self)

    def leftMouseButtonPress(self, event: QMouseEvent):
        ''' Tell the scene that the user clicked left '''
        super().leftMouseButtonPress(event)
        self.scene_click.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        ''' Do not allow deletions '''
        if event.key() == Qt.Key_Delete:
            return
        super().keyPressEvent(event)
