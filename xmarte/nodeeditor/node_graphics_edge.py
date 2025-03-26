# -*- coding: utf-8 -*-
"""
A module containing the Graphics representation of an Edge
"""
from PyQt5 import QtGui
import math
from PyQt5.QtCore import QSizeF
from PyQt5.QtGui import QBrush, QFont
from qtpy.QtWidgets import QGraphicsPathItem, QWidget, QGraphicsItem, QGraphicsTextItem
from qtpy.QtGui import QColor, QPen, QPainterPath
from qtpy.QtCore import Qt, QRectF, QPointF

from nodeeditor.node_graphics_edge_path import EDGE_CP_ROUNDNESS, GraphicsEdgePathDirect, GraphicsEdgePathSquare, GraphicsEdgePathImprovedSharp, GraphicsEdgePathImprovedBezier
from nodeeditor.node_graphics_edge import QDMGraphicsEdge

from xmarte.nodeeditor.node_graphics_edge_path import XMARTeGraphicsEdgePathBezier

class XMARTeQDMGraphicsEdge(QDMGraphicsEdge):
    def __init__(self, edge:'Edge', parent:QWidget=None):
        self.posDestination = [0, 0]
        self.text_item = None
        super().__init__(edge, parent)
        self.createEdgePathCalculator()
        
    def determineEdgePathClass(self):
        """Decide which GraphicsEdgePath class should be used to calculate path according to edge.edge_type value"""
        from nodeeditor.node_edge import EDGE_TYPE_BEZIER, EDGE_TYPE_DIRECT, EDGE_TYPE_SQUARE
        if self.edge.edge_type == EDGE_TYPE_BEZIER:
            return XMARTeGraphicsEdgePathBezier
        if self.edge.edge_type == EDGE_TYPE_DIRECT:
            return GraphicsEdgePathDirect
        if self.edge.edge_type == EDGE_TYPE_SQUARE:
            return GraphicsEdgePathSquare
        else:
            return XMARTeGraphicsEdgePathBezier

    def createEdgePathCalculator(self):
        """Create instance of :class:`~nodeeditor.node_graphics_edge_path.GraphicsEdgePathBase`"""
        self.pathCalculator = self.determineEdgePathClass()(self)
        self.pathCalculator.resetControls()
        return self.pathCalculator

    def mouseReleaseEvent(self, event):
        """Overridden Qt's method to handle selecting and deselecting this `Graphics Edge`"""
        if not(self.posSource == [0,0] or self.posDestination == [0,0]):
            self.setPath(self.calcPath())
        super().mouseReleaseEvent(event)

    def calcnewPath(self,x,y) -> QPainterPath:
        """Calculate the cubic Bezier line connection with 2 control points

        :returns: ``QPainterPath`` of the cubic Bezier line
        :rtype: ``QPainterPath``
        """
        s = self.posSource
        d = self.posDestination
        dist = (d[0] - s[0]) * 0.5

        cpx_s = +dist
        cpx_d = -dist
        cpy_s = 0
        cpy_d = 0

        if self.edge.start_socket is not None:
            ssin = self.edge.start_socket.is_input
            ssout = self.edge.start_socket.is_output

            if (s[0] > d[0] and ssout) or (s[0] < d[0] and ssin):
                cpx_d *= -1
                cpx_s *= -1

                cpy_d = (
                    (s[1] - d[1]) / math.fabs(
                        (s[1] - d[1]) if (s[1] - d[1]) != 0 else 0.00001
                    )
                ) * EDGE_CP_ROUNDNESS
                cpy_s = (
                    (d[1] - s[1]) / math.fabs(
                        (d[1] - s[1]) if (d[1] - s[1]) != 0 else 0.00001
                    )
                ) * EDGE_CP_ROUNDNESS

        path = QPainterPath(QPointF(self.posSource[0], self.posSource[1]))
        path.cubicTo( s[0] + cpx_s, s[1] + cpy_s, x, y, self.posDestination[0], self.posDestination[1])

        return path

    def mousePressEvent(self,event):
        sx = self.posSource[0]
        ex = self.posDestination[0]
        distance = ex-sx
        self.point = 1
        if (event.pos().x()-sx) > (distance/2):
            self.point = 2
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Overridden event to detect that we moved with this `Node`"""
        if not(self.posSource == [0,0] and self.posDestination == [0,0]):
            self.pathCalculator.setControlPoint(self.point,event.pos().x(),event.pos().y())
            self.setPath(self.calcPath())
        else:
            self.pathCalculator.resetControls()
        super().mouseMoveEvent(event)

    def setSource(self, x:float, y:float):
        """ Set source point

        :param x: x position
        :type x: ``float``
        :param y: y position
        :type y: ``float``
        """
        self.posSource = [x, y]
        self.pathCalculator.resetControls()
        self.setPath(self.calcPath())

    def setDestination(self, x:float, y:float):
        """ Set destination point

        :param x: x position
        :type x: ``float``
        :param y: y position
        :type y: ``float``
        """
        self.posDestination = [x, y]
        self.pathCalculator.resetControls()
        self.setPath(self.calcPath())

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        """Qt's overridden method to paint this Graphics Edge. Path calculated
            in :func:`~nodeeditor.node_graphics_edge.QDMGraphicsEdge.calcPath` method"""

        painter.setBrush(Qt.NoBrush)

        if self.hovered and self.edge.end_socket is not None:
            painter.setPen(self._pen_hovered)
            painter.drawPath(self.path())

        if self.edge.end_socket is None:
            painter.setPen(self._pen_dragging)
        else:
            painter.setPen(self._pen if not self.isSelected() else self._pen_selected)

        painter.drawPath(self.path())
        if self.edge.scene.playback:
            point = self.path().pointAtPercent(0.5)
            idx = self.edge.scene.count
            if self.edge.start_socket.data:
                try:
                    value = str(self.edge.start_socket.data[idx])
                    self.draw_box_at_point(painter, point, value)
                except:
                    pass
        else:
            if self.text_item is not None:
                self.text_item.deleteLater()
                self.text_item = None

    def draw_box_at_point(self, painter, center_point, number):
        gray_color = QColor(200, 200, 200)
        black_color = QColor(0, 0, 0)
        white_color = QColor(255,255,255)
        # Define the dimensions of the box
        box_width = 50
        if self.text_item:
            metrics = QtGui.QFontMetrics(self.text_item.font())
            box_width = (
                (metrics.width(number) + 20)
                if (metrics.width(number) + 20) > 50
                else 50
            )
        box_height = 30
    
        # Calculate the top-left corner of the box
        box_top_left = QPointF(center_point.x() - box_width / 2, center_point.y() - box_height / 2)
    
        # Create the rectangle for the box
        box_rect = QRectF(box_top_left, QSizeF(box_width, box_height))
    
        # Set pen and brush
        painter.setPen(QPen(gray_color))
        painter.setBrush(QBrush(black_color))
    
        # Draw the box
        painter.drawRect(box_rect)

        # Print a number within the box
        font = QFont("Arial", 12)
        painter.setFont(font)
        painter.setPen(QPen(white_color))
        text_rect = QRectF(box_rect)
        # Update or create text item
        if self.text_item:
            self.text_item.setPlainText(number)
            self.text_item.setPos(center_point - QPointF(self.text_item.boundingRect().width() / 2, self.text_item.boundingRect().height() / 2))  # Center the text item
        else:
            self.text_item = EditableTextItem(number, self)
            self.text_item.setPos(center_point - QPointF(self.text_item.boundingRect().width() / 2, self.text_item.boundingRect().height() / 2))  # Center the text item

class EditableTextItem(QGraphicsTextItem):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setDefaultTextColor(Qt.white)
        self.setFont(QFont("Arial", 16))  # Increased font size

        
    def mouseDoubleClickEvent(self, event):
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus()
        self.selectAll()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            self.clearFocus()
        else:
            super().keyPressEvent(event)