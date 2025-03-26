
from qtpy.QtCore import Qt
from qtpy.QtGui import QKeyEvent

from nodeeditor.node_graphics_view import QDMGraphicsView
from nodeeditor.utils import isCTRLPressed, isSHIFTPressed

from xmarte.nodeeditor.node_edge_dragging import XMARTeEdgeDragging

class XMARTeQDMGraphicsView(QDMGraphicsView):
    """Class representing NodeEditor's `Graphics View`"""
    def __init__(self, grScene: 'QDMGraphicsScene', parent: 'QWidget'=None):
        """
        :param grScene: reference to the :class:`~nodeeditor.node_graphics_scene.QDMGraphicsScene`
        :type grScene: :class:`~nodeeditor.node_graphics_scene.QDMGraphicsScene`
        :param parent: parent widget
        :type parent: ``QWidget``

        :Instance Attributes:

        - **grScene** - reference to the :class:`~nodeeditor.node_graphics_scene.QDMGraphicsScene`
        - **mode** - state of the `Graphics View`
        - **zoomInFactor**- ``float`` - zoom step scaling, default 1.25
        - **zoomClamp** - ``bool`` - do we clamp zooming or is it infinite?
        - **zoom** - current zoom step
        - **zoomStep** - ``int`` - the relative zoom step when zooming in/out
        - **zoomRange** - ``[min, max]``

        """
        super().__init__(grScene, parent)
        # edge dragging
        self.dragging = XMARTeEdgeDragging(self)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
    def keyPressEvent(self, event: QKeyEvent):
        """
        .. note::
            This overridden Qt's method was used for handling key shortcuts, before we implemented proper
            ``QWindow`` with Actions and Menu. Still the commented code serves as an example on how to handle
            key presses without Qt's framework for Actions and shortcuts. There is also an example on
            how to solve the problem when a Node contains Text/LineEdit and we press the `Delete`
            key (also serving to delete `Node`)

        :param event: Qt's Key event
        :type event: ``QKeyEvent``
        :return:
        """
        # Use this code below if you wanna have shortcuts in this widget.self.editor.view.setScene(self.scene.grScene)
        # You want to use this, when you don't have a window which handles these shortcuts for you

        if event.key() == Qt.Key_Delete:
            if not self.editingFlag:
                self.deleteSelected()
            else:
                super().keyPressEvent(event)
        # elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
        #     self.grScene.scene.saveToFile("graph.json")
        # elif event.key() == Qt.Key_L and event.modifiers() & Qt.ControlModifier:
        #     self.grScene.scene.loadFromFile("graph.json")
        elif event.key() == Qt.Key_Z and isCTRLPressed(event) and not isSHIFTPressed(event):
            self.grScene.scene.history.undo()
        elif event.key() == Qt.Key_Z and isCTRLPressed(event)  and isSHIFTPressed(event):
            self.grScene.scene.history.redo()
        # elif event.key() == Qt.Key_H:
        #     print("HISTORY:     len(%d)" % len(self.grScene.scene.history.history_stack),
        #           " -- current_step", self.grScene.scene.history.history_current_step)
        #     ix = 0
        #     for item in self.grScene.scene.history.history_stack:
        #         print("#", ix, "--", item['desc'])
        #         ix += 1
        # else:
        super().keyPressEvent(event)

