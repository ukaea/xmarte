'''
StateEdge class overrides methods from the Edge class and adds
functionality to store state messages.
'''
import math
from collections import OrderedDict
from martepy.marte2.objects import MARTe2StateMachineEvent

from qtpy.QtWidgets import QWidget
from PyQt5.QtGui import QPainterPath, QColor, QPen, QPolygonF
from PyQt5.QtCore import QPointF, Qt

from xmarte.nodeeditor.node_edge import XMARTeEdge
from xmarte.nodeeditor.node_graphics_edge_path import XMARTeGraphicsEdgePathBase
from xmarte.nodeeditor.node_graphics_edge import XMARTeQDMGraphicsEdge

from .state_message_preview import StateMessagePreview

class GraphicsEdgePathArc(XMARTeGraphicsEdgePathBase):
    '''Graphical arc path for proper state machine representation.'''

    def __init__(self, owner) -> None:
        super().__init__(owner)
        self.control = QPointF()

    def calcPath(self) -> QPainterPath:
        ''' Calculate the edge path '''
        path = QPainterPath()
        if (
            self.owner.edge.start_socket
            and self.owner.edge.end_socket
            and (self.owner.edge.start_socket.node == self.owner.edge.end_socket.node)
        ):
            # Looping individual node.
            # Option 1 -- ellipse
            # start = QPointF(self.owner.posSource[0] - 60, self.owner.posSource[1] - 90)
            # end = QPointF(self.owner.posDestination[0] + 60, self.owner.posDestination[1] + 60)
            # path.moveTo(start)
            # path.addEllipse(start, 40, 40)

            # Option 2 -- quad
            start = QPointF(self.owner.posSource[0], self.owner.posSource[1])
            end = QPointF(self.owner.posDestination[0], self.owner.posDestination[1])
            path.moveTo(start)
            path.quadTo(QPointF(self.control.x(), self.control.y() * 1.02), end)
        else:
            # Arc between nodes.
            start = QPointF(self.owner.posSource[0], self.owner.posSource[1])
            end = QPointF(self.owner.posDestination[0], self.owner.posDestination[1])
            path.moveTo(start)
            path.quadTo(self.control, end)
        return path

    def resetPath(self) -> None:
        ''' Reset the default state edge path '''
        self.resetControls()
        self.calcPath()

    def resetControls(self) -> None:
        ''' Reset the control position of our edge '''
        start = QPointF(self.owner.posSource[0], self.owner.posSource[1])
        end = QPointF(self.owner.posDestination[0], self.owner.posDestination[1])
        offset = -100 if start.y() > end.y() else 100
        self.control = QPointF(((start.x() + end.x()) / 2), start.y() + offset)

    def setControlPoint(self, _, x, y) -> None:
        ''' Set the control position '''
        self.control = QPointF(x, y)
        self.calcPath()


class StateGraphicsEdge(XMARTeQDMGraphicsEdge):
    '''Graphical representation of a StateEdge.'''
    def __init__(self, edge: 'Edge', parent: QWidget = None) -> None:
        super().__init__(edge, parent)
        self.edge = edge
        self._arrow_height = 10
        self._arrow_width = 5

    def hoverEnterEvent(self, event) -> None:
        ''' User has hovered over the edge, show the state information '''
        super().hoverEnterEvent(event)
        application = self.edge.scene.application
        application.state_msg_prev = StateMessagePreview(self.edge)
        application.state_msg_prev.setPos()
        application.state_msg_prev.show()

    def hoverLeaveEvent(self, event) -> None:
        ''' Unshow the state information '''
        super().hoverLeaveEvent(event)
        application = self.edge.scene.application
        application.state_msg_prev.close()

    def determineEdgePathClass(self):
        ''' return our overriding edge path class '''
        return GraphicsEdgePathArc

    def arrowCalc(self, start_point, end_point): # pylint: disable=R0914
        ''' Calculate the positioning of our arrow '''
        try:
            dx, dy = start_point.x() - end_point.x(), start_point.y() - end_point.y()

            leng = math.sqrt(dx ** 2 + dy ** 2)
            normX, normY = dx / leng, dy / leng  # normalize

            # perpendicular vector
            perpX = -normY
            perpY = normX

            leftX = end_point.x() + self._arrow_height * normX + self._arrow_width * perpX
            leftY = end_point.y() + self._arrow_height * normY + self._arrow_width * perpY

            rightX = end_point.x() + self._arrow_height * normX - self._arrow_width * perpX
            rightY = end_point.y() + self._arrow_height * normY - self._arrow_width * perpY

            point2 = QPointF(leftX, leftY)
            point3 = QPointF(rightX, rightY)

            return QPolygonF([point2, end_point, point3])
        except ZeroDivisionError:
            return None

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None) -> None:
        super().paint(painter, QStyleOptionGraphicsItem, widget)
        arrowhead = self.arrowCalc(
            self.path().pointAtPercent(0.5), self.path().pointAtPercent(0.55)
        )
        if arrowhead:
            painter.drawPolyline(arrowhead)


class StateEdge(XMARTeEdge):
    '''Logical representation of a StateEdge.'''
    def __init__(
            self,
            scene,
            start_socket=None,
            end_socket=None,
            edge_type: int=1,
            state_message = {}
        ) -> None:
        super().__init__(scene, start_socket, end_socket, edge_type)
        # Store state event messages here.
        self.state_message =  state_message

    def loadStateMessages(self) -> dict:
        '''Load state messages into state message window when edge is clicked.'''
        return self.state_message

    def saveStateMessages(self, transition) -> None:
        '''Save state messages when state message window is closed.'''
        self.state_message = transition

    def getGraphicsEdgeClass(self) -> 'type[StateGraphicsEdge]':
        '''Override this method from the parent class to return a custom state graphics edge.'''
        return StateGraphicsEdge

    def serialize(self) -> OrderedDict:
        ''' Serialize our state edge - store the associated state message '''
        data = super().serialize()
        data['state_message'] = self.state_message.serialize()
        return data

    def deserialize( # pylint: disable=W1113
            self,
            data:dict,
            hashmap:dict={},
            restore_id:bool=True,
            *args,
            **kwargs
        ) -> bool:
        ''' Deserialize our state edge and the stored associated state message '''
        super().deserialize(data, hashmap, restore_id, *args, **kwargs)
        self.state_message = MARTe2StateMachineEvent().deserialize(data['state_message'])
        return self


class NextStateGraphicsEdge(StateGraphicsEdge):
    '''Graphical representation of next state edge.'''
    def initAssets(self):
        """Initialize ``QObjects`` like ``QColor``, ``QPen`` and ``QBrush``"""
        self._color = self._default_color = QColor("#001000")
        self._color_selected = QColor("#00ff00")
        self._color_hovered = QColor("#FF37A6FF")
        self._pen = QPen(self._color)
        self._pen_selected = QPen(self._color_selected)
        self._pen_dragging = QPen(self._color)
        self._pen_hovered = QPen(self._color_hovered)
        self._pen_dragging.setStyle(Qt.DashLine)
        self._pen.setWidthF(3.0)
        self._pen_selected.setWidthF(3.0)
        self._pen_dragging.setWidthF(3.0)
        self._pen_hovered.setWidthF(5.0)


class NextStateEdge(StateEdge):
    '''Represents a specific type of edge for connecting to the next state.'''
    def getGraphicsEdgeClass(self):
        return NextStateGraphicsEdge


class NextErrorStateGraphicsEdge(StateGraphicsEdge):
    '''Graphical representation of next error state edge.'''
    def initAssets(self):
        """Initialize ``QObjects`` like ``QColor``, ``QPen`` and ``QBrush``"""
        self._color = self._default_color = QColor("#ff0000")
        self._color_selected = QColor("#00ff00")
        self._color_hovered = QColor("#FF37A6FF")
        self._pen = QPen(self._color)
        self._pen_selected = QPen(self._color_selected)
        self._pen_dragging = QPen(self._color)
        self._pen_hovered = QPen(self._color_hovered)
        self._pen_dragging.setStyle(Qt.DashLine)
        self._pen.setWidthF(3.0)
        self._pen_selected.setWidthF(3.0)
        self._pen_dragging.setWidthF(3.0)
        self._pen_hovered.setWidthF(5.0)


class NextErrorStateEdge(StateEdge):
    '''Represents a specific type of edge for connecting to the next error state.'''
    def getGraphicsEdgeClass(self):
        return NextErrorStateGraphicsEdge
