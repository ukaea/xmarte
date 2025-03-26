'''
The StateNode class overrides methods from node, providing functionality needed for
nodes in the state scene - such as different socket positions, and multi-connections.

The StateGraphicsNode class overrides methods from QDMGraphicsNode so that the
graphical representation of the node is different in the state scene.
'''
from qtpy.QtWidgets import QWidget
from qtpy.QtGui import QFont, QColor, QPen, QBrush
from qtpy.QtCore import Qt, QRect, QRectF

from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_socket import (
    LEFT_BOTTOM, LEFT_CENTER, LEFT_TOP,
    RIGHT_BOTTOM, RIGHT_CENTER, RIGHT_TOP,
)

from xmarte.nodeeditor.node_socket import XMARTeLabeledSocket
from xmarte.nodeeditor.node_graphics_socket import XMARTeQDMGraphicsLabeledSocket
from xmarte.nodeeditor.node_node import XMARTeLabeledSocketNode
from xmarte.nodeeditor.node_graphics_node import XMARTeQDMGraphicsNode

class StateGraphicsNode(XMARTeQDMGraphicsNode):
    '''Graphical representation of a StateNode.'''
    def __init__(self, node, parent: QWidget = None) -> None:
        super().__init__(node, parent)
        self.stateSelected = False
        self.sceneRect = QRectF(
            self.node.scene.application.editor.view.mapToScene(
                QRect(
                    0,
                    0,
                    self.node.scene.application.editor.view.viewport().width(),
                    self.node.scene.application.editor.view.viewport().height(),
                )
            ).boundingRect()
        )
        self.title_item.setPos(
            (self.width / 2) - self.title_horizontal_padding,
            (self.height / 2) - self.title_vertical_padding
        )
        super().setPos(self.sceneRect.center())
        self._pen_upstream = QColor()
        self._brush_title = QBrush(QColor("#FF313131"))

    def updateContent(self):
        '''
        Update the size of our content widget
        '''
        self.content.setGeometry(
            int(self.edge_padding),
            int(self.title_height + self.edge_padding),
            int(self.width - 2 * self.edge_padding),
            int(self.height - 2 * self.edge_padding - self.title_height),
        )

    def initSizes(self) -> None:
        '''Initialise graphical attributes.'''
        self.width = 120
        self.height = 120
        self.edge_roundness = 10.0
        self.edge_padding = 10.0
        self.title_height = self.height / 2
        self.title_horizontal_padding = 25.0
        self.title_vertical_padding = 10.0

    def initContent(self) -> None:
        '''Initialise node content geometry.'''
        if self.content is not None:
            self.content.setGeometry(
                int(self.edge_padding),
                int(self.title_height + self.edge_padding),
                int(self.width - 2 * self.edge_padding),
                int(self.height - 2 * self.edge_padding - self.title_height)
            )

    def initAssets(self):
        """Initialize ``QObjects`` like ``QColor``, ``QPen`` and ``QBrush``"""
        self._title_color = Qt.black
        self._title_font = QFont("Ubuntu", 10)

        self._color = QColor("#7F000000")
        self._color_selected = QColor("#FFFFA637")
        self._color_hovered = QColor("#FF37A6FF")

        self._pen_default = QPen(self._color)
        self._pen_default.setWidthF(2.0)
        self._pen_selected = QPen(self._color_selected)
        self._pen_selected.setWidthF(2.0)
        self._pen_hovered = QPen(self._color_hovered)
        self._pen_hovered.setWidthF(3.0)

        self._brush_title = QBrush(QColor("#FF313131"))
        self._brush_background = QBrush(QColor("#E3212121"))

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None) -> None:
        '''Paint the node.'''
        self._pen_upstream = QColor("#000")
        self._brush_title = QColor('#fff')
        painter.setPen(self._pen_upstream)
        # if self.isSelected() or self.stateSelected:
        #     painter.setBrush(QColor("#C87EDE"))
        # else:
        painter.setBrush(self._brush_title)
        painter.drawEllipse(0, 0, self.width, self.height)


class StateGraphicsLabeledSocket(XMARTeQDMGraphicsLabeledSocket):
    '''Override the label colour.'''
    def __init__(self, socket: 'LabeledSocket'):
        super().__init__(socket)
        self._color_label = QColor("#000")


class StateLabeledSocket(XMARTeLabeledSocket):
    '''Override the labeled socket graphics class.'''
    Socket_GR_Class = StateGraphicsLabeledSocket


class StateNode(XMARTeLabeledSocketNode):
    '''Logical representation of a StateNode.'''
    GraphicsNode_class = StateGraphicsNode
    NodeContent_class = QDMNodeContentWidget
    Socket_class = StateLabeledSocket

    def initSettings(self) -> None:
        '''Initialize properties and socket information.'''
        self.socket_spacing = 22
        self.graph = None
        self.rank = False
        self.input_socket_position = LEFT_TOP
        self.output_socket_position = RIGHT_TOP
        self.input_multi_edged = True
        self.output_multi_edged = True
        self.socket_offsets = {
            LEFT_BOTTOM: -1,
            LEFT_CENTER: -1,
            LEFT_TOP: -1,
            RIGHT_BOTTOM: 1,
            RIGHT_CENTER: 1,
            RIGHT_TOP: 1,
        }

    def onInputChanged(self, _) -> None:
        '''Input edge to node has changed.'''
        self.markDirty()
        self.markDescendantsDirty(all_descendants=[self])

    def markDescendantsDirty(self, new_value: bool=True, all_descendants=[]) -> None:
        '''Mark descendants dirty if not already so.'''
        for other_node in self.getChildrenNodes():
            if other_node not in all_descendants:  # stop max recursion depth exceeded error
                all_descendants.append(other_node)
                other_node.markDirty(new_value)
                other_node.markDescendantsDirty(new_value)
