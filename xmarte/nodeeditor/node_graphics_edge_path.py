import math
from qtpy.QtCore import QPointF
from qtpy.QtGui import QPainterPath

from nodeeditor.node_graphics_edge_path import GraphicsEdgePathBase, GraphicsEdgePathBezier

EDGE_CP_ROUNDNESS = 100     #: Bezier control point distance on the line

class XMARTeGraphicsEdgePathBase(GraphicsEdgePathBase):
    """Base Class for calculating the graphics path to draw for an graphics Edge"""
    def resetPath(self):
        pass
    def resetControls(self):
        pass
    def setControlPoint(self,point,x,y):
        pass

class XMARTeGraphicsEdgePathBezier(XMARTeGraphicsEdgePathBase):
    """Cubic line connection Graphics Edge"""
    def resetControls(self):
        s = self.owner.posSource
        d = self.owner.posDestination
        dist = (d[0] - s[0]) * 0.5

        cpx_s = +dist
        cpx_d = -dist
        cpy_s = 0
        cpy_d = 0

        if self.owner.edge.start_socket is not None:
            ssin = self.owner.edge.start_socket.is_input
            ssout = self.owner.edge.start_socket.is_output

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
        self.cp1x = s[0] + cpx_s
        self.cp1y = s[1] + cpy_s
        self.cp2x = d[0] + cpx_d
        self.cp2y = d[1] + cpy_d
        self.path = self.resetPath()

    def setControlPoint(self,point,x,y):
        if point == 1:
            self.cp1x = x
            self.cp1y = y
        else:
            self.cp2x = x
            self.cp2y = y
        path = QPainterPath(QPointF(self.owner.posSource[0], self.owner.posSource[1]))
        path.cubicTo( self.cp1x, self.cp1y, self.cp2x, self.cp2y, self.owner.posDestination[0], self.owner.posDestination[1])
        self.path = path

    def resetPath(self):
        path = QPainterPath(QPointF(self.owner.posSource[0], self.owner.posSource[1]))
        path.cubicTo( self.cp1x, self.cp1y, self.cp2x, self.cp2y, self.owner.posDestination[0], self.owner.posDestination[1])
        return path

    def calcPath(self) -> QPainterPath:
        """Calculate the cubic Bezier line connection with 2 control points

        :returns: ``QPainterPath`` of the cubic Bezier line
        :rtype: ``QPainterPath``
        """

        return self.path