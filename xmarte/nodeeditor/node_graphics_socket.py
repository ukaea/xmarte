
from qtpy.QtCore import Qt, QRectF
from qtpy.QtGui import QColor, QBrush, QPen, QFontMetrics
from nodeeditor.node_graphics_socket import QDMGraphicsSocket

class XMARTeQDMGraphicsSocket(QDMGraphicsSocket):
    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        """Painting a circle"""
        painter.setBrush(self._brush)
        painter.setPen(self._pen if not self.isHighlighted else self._pen_highlight)
        if hasattr(self,"socket_shape"):
            if self.socket_shape == "Ellipse":
                painter.drawEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
            elif self.socket_shape == "Rectangle":
                painter.drawRect(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
            else:
                painter.drawEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        else:
            painter.drawEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

class XMARTeQDMGraphicsLabeledSocket(QDMGraphicsSocket):
    def __init__(self, socket: 'LabeledSocket'):
        super().__init__(socket)
        self.label_width = 0
        self._color_label = QColor("#FFF")
        self._pen_label = QPen(self._color_label)

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        super().paint(painter, QStyleOptionGraphicsItem, widget)
        painter.setPen(self._color_label)
        fm = QFontMetrics(painter.font())
        label_width = fm.horizontalAdvance(self.socket.label)
        self.label_width = label_width
        font_height = fm.height()

        if((label_width+20) > self.socket.node.grNode.width):
            self.socket.node.grNode.width = (label_width+21)
            self.socket.node.grNode.update()
            self.socket.node.grNode.updateContent()
            self.socket.node.updateSocketPositions()

        if self.socket.is_input:
            painter.drawText(self.radius + 5, -font_height // 2, label_width, font_height,
                             Qt.AlignVCenter, self.socket.label)
        else:
            painter.drawText(-self.radius - label_width - 5, -font_height // 2, label_width, font_height,
                             Qt.AlignRight | Qt.AlignVCenter, self.socket.label)

    def boundingRect(self) -> QRectF:
        """Defining Qt' bounding rectangle"""
        if self.socket.is_input:
            return QRectF(
                - self.radius - self.outline_width,
                - self.radius - self.outline_width,
                ((2 * (self.radius + self.outline_width)) + self.label_width),
                2 * (self.radius + self.outline_width),
            )
        else:
            return QRectF(
                - self.radius - self.outline_width - self.label_width,
                - self.radius - self.outline_width,
                ((2 * (self.radius + self.outline_width)))+ self.label_width,
                2 * (self.radius + self.outline_width),
            )