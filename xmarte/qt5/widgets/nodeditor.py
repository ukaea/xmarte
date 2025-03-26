'''
Node Editor Redefinitions
'''
import os
import copy

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget, QVBoxLayout, QApplication, QMessageBox
from qtpy.QtGui import QKeyEvent, QKeySequence

from xmarte.qt5.libraries.functions import PluginException
from xmarte.qt5.widgets.scene import EditorScene
from xmarte.nodeeditor.node_graphics_edge import XMARTeQDMGraphicsEdge
from xmarte.nodeeditor.node_graphics_node import XMARTeQDMGraphicsNode
from xmarte.nodeeditor.node_edge import XMARTeEdge
from xmarte.nodeeditor.node_graphics_view import XMARTeQDMGraphicsView
from xmarte.nodeeditor.node_editor_widget import XMARTeNodeEditorWidget

class EditorGRView(XMARTeQDMGraphicsView):
    '''
    The Editor Views graphical component for overriding key press event in scene.
    '''

    def __init__(self, grScene, parent: 'QWidget'=None):
        self._set_scene_listeners = []
        self.clipboard = {}
        super().__init__(grScene, parent)

    def clearSetSceneListeners(self):
        ''' clear the setScene listeners '''
        self._set_scene_listeners = []

    def addSetSceneListener(self, func):
        ''' add a setScene listener '''
        self._set_scene_listeners.append(func)

    def keyPressEvent(self, event: QKeyEvent): # pylint:disable=R0912,R0915
        """
        .. note::
            This overridden Qt's method was used for handling key shortcuts,
           before we implemented proper ``QWindow`` with Actions and Menu.
           Still the commented code serves as an example on how to handle
            key presses without Qt's framework for Actions and shortcuts.
            There is also an example on how to solve the problem when a Node
            contains Text/LineEdit and we press the `Delete` key (also serving
           to delete `Node`)

        :param event: Qt's Key event
        :type event: ``QKeyEvent``
        :return:
        """
        # Use this code below if you wanna have shortcuts in this widget.
        # You want to use this, when you don't have a window which handles these shortcuts for you

        if event.key() == Qt.Key_Delete:
            self.scene().scene.large_import = True
            self.deleteSelected()
            self.scene().scene.large_import = False
            self.scene().scene._has_been_modified = True # pylint:disable=W0212
        #         super().keyPressEvent(event)
        # elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
        #     self.grScene.scene.saveToFile("graph.json")
        # elif event.key() == Qt.Key_L and event.modifiers() & Qt.ControlModifier:
        #     self.grScene.scene.loadFromFile("graph.json")
        elif (
            event.key() == Qt.Key_Z
            and event.modifiers() & Qt.ControlModifier
            and not event.modifiers() & Qt.ShiftModifier
        ):
            self.scene().scene.large_import = True
            self.scene().scene.history.undo()
            self.scene().scene.large_import = False
            self.scene().scene._has_been_modified = True # pylint:disable=W0212
        elif (
            event.key() == Qt.Key_Z
            and event.modifiers() & Qt.ControlModifier
            and event.modifiers() & Qt.ShiftModifier
        ):
            self.scene().scene.large_import = True
            self.scene().scene.history.redo()
            self.scene().scene.large_import = False
            self.scene().scene._has_been_modified = True # pylint:disable=W0212
        elif event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            selected = self.scene().selectedItems()
            # Somehow split these into node and edges
            grNodes = [i for i in selected if isinstance(i,XMARTeQDMGraphicsNode)]
            grEdges = [i for i in selected if isinstance(i,XMARTeQDMGraphicsEdge)]
            # Okay now serialise these
            self.clipboard = {}
            nodes = [grNode.node.serialize() for grNode in grNodes]
            edges = [grEdge.edge.serialize() for grEdge in grEdges]
            self.clipboard['nodes'] = nodes
            self.clipboard['edges'] = edges

        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            # Deserialise the selected nodes and edges but create new instances of them
            hashmap = {}
            try:
                for node in self.clipboard['nodes']:
                    # delink parameters
                    node['parameters'] = copy.deepcopy(node['parameters'])
                    node['inputsb'] = copy.deepcopy(node['inputsb'])
                    node['outputsb'] = copy.deepcopy(node['outputsb'])
                    newnode = self.scene().scene.getNodeClassFromData(node)(self.scene().scene)
                    prev = self.scene().scene.large_import
                    self.scene().scene.large_import = True
                    newnode.deserialize(node, hashmap, restore_id=False)
                    self.scene().scene.large_import = prev
                    self.scene().scene.has_been_modified = True
                    newnode.onDeserialized(node)

                for edge in self.clipboard['edges']:
                    # We have to manually create these as our ID's change
                    XMARTeEdge(self.scene().scene).deserialize(edge, hashmap, restore_id=False)
            except KeyError:
                pass
        else:
            try:
                keysequence = QKeySequence(int(event.modifiers()) + event.key())
                if (seq := keysequence) == 'Ctrl+N':
                    # New action
                    self.parent().application.fileToolBar.newAction.trigger()
                elif seq == 'Ctrl+I':
                    # Import action
                    self.parent().application.fileToolBar.importAction.trigger()
                elif seq == 'Ctrl+O':
                    # Open action
                    self.parent().application.fileToolBar.openAction.trigger()
                elif seq == 'Ctrl+S':
                    # Save action
                    self.parent().application.fileToolBar.saveAction.trigger()
                elif seq == 'Ctrl+E':
                    # Export action
                    self.parent().application.fileToolBar.exportAction.trigger()
            except UnicodeEncodeError:
                pass
        # elif QKeySequence(int(event.modifiers()) + event.key()).toString() == 'Ctrl+n'
        # elif event.key() == Qt.Key_H:
        #     print("HISTORY:     len(%d)" % len(self.grScene.scene.history.history_stack),
        #           " -- current_step", self.grScene.scene.history.history_current_step)
        #     ix = 0
        #     for item in self.grScene.scene.history.history_stack:
        #         print("#", ix, "--", item['desc'])
        #         ix += 1
        # else:
        super().keyPressEvent(event)

    def setScene(self, scene):
        ''' Call the setScene listeners - internal function '''
        super().setScene(scene)
        for listener in self._set_scene_listeners:
            listener(scene.scene)

    def deleteSelected(self):
        """Shortcut for safe deleting every object selected in the `Scene`."""
        for item in self.scene().selectedItems():
            if isinstance(item, XMARTeQDMGraphicsEdge):
                item.edge.remove()
                self.scene().scene.edges = [
                    a for a in self.scene().scene.edges if a is not item.edge
                ]
            elif hasattr(item, "node"):
                item.node.remove()
                self.scene().scene.nodes = [
                    a for a in self.scene().scene.nodes if a is not item.node
                ]

        self.scene().scene.history.storeHistory("Delete selected", setModified=True)


class EditorWidget(XMARTeNodeEditorWidget):
    '''
    Editor Widget used in the main application
    '''
    Scene_class = EditorScene
    GraphicsView_class = EditorGRView

    def __init__(self, parent: QWidget = None, application=None):
        self.Scene_class = EditorScene
        self.application = application
        super().__init__(parent)

    def initUI(self):
        """Set up this ``NodeEditorWidget`` with its layout, 
        :class:`~nodeeditor.node_scene.Scene` and
        :class:`~nodeeditor.node_graphics_view.QDMGraphicsView`"""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # crate graphics scene
        self.scene = self.__class__.Scene_class(self.application)

        # create graphics view
        self.view = self.__class__.GraphicsView_class(self.scene.grScene, self)
        self.layout.addWidget(self.view)

    def fileSave(self, filename: str = None, setcursor=True,
                 printoutput=True, updateModified=True):
        """Save serialized graph to JSON file. When called with an empty parameter,
        we won't store/remember the filename.

        :param filename: file to store the graph
        :type filename: ``str``
        """
        if filename is not None:
            self.filename = filename
        if setcursor:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        self.application.scene.saveToFile(
            self.filename, printoutput=printoutput, updateModified=updateModified)
        if setcursor:
            QApplication.restoreOverrideCursor()
        return True

    def fileLoad(self, filename: str, *args, **kwargs):
        """Load serialized graph from JSON file

        :param filename: file to load
        :type filename: ``str``
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            prev = self.application.scene.large_import
            self.application.scene.large_import = True
            self.application.scene.loadFromFile(filename, *args, **kwargs)
            self.application.scene.large_import = prev
            self.filename = filename
            self.application.scene.history.clear()
            self.application.scene.history.storeInitialHistoryStamp()
            return True
        except FileNotFoundError as exc:
            QMessageBox.warning(
                self,
                f"Error loading {os.path.basename(filename)}",
                str(exc).replace("[Errno 2]", ""),
            )
            raise PluginException(exc) from exc
        finally:
            QApplication.restoreOverrideCursor()
