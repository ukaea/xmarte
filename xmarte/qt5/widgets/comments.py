''' Adds a comment to the scene when double clicked for easier reading '''
import math

from PyQt5.QtWidgets import (
    QGraphicsProxyWidget, QGraphicsLineItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsPolygonItem
)
from PyQt5.QtGui import QPen, QBrush, QColor, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QLineF

from xmarte.nodeeditor.node_graphics_edge import XMARTeQDMGraphicsEdge
from xmarte.qt5.nodes.node_graphics import BlockGraphicsNode
from xmarte.qt5.nodes.marte2_node import MARTe2Node
from xmarte.nodeeditor.node_edge import XMARTeEdge

def pointToDict(p: QPointF):
    ''' Get dictionary from point '''
    return {'x': p.x(), 'y': p.y()}

def pointFromDict(d):
    ''' Get point from dictionary '''
    return QPointF(d['x'], d['y'])

# ---------- CommentEdge ----------
class CommentEdge(QGraphicsLineItem):
    """Simple straight-line edge connecting a comment pin to either a target item or a point."""
    def __init__(self, start_pin, end_item=None, end_pos=None):
        super().__init__()
        self.start_pin = start_pin
        self.start_pin.temp_edge = self
        self.end_item = end_item
        self.setEndItem(end_item)
        self.end_pos = end_pos
        self.setPen(QPen(QColor(255, 255, 255), 2))
        self.setZValue(-1)
        self.setFlags(
            QGraphicsLineItem.ItemIsSelectable |
            QGraphicsLineItem.ItemIsFocusable
        )
        self.updatePosition()

    def _registerWithItems(self):
        ''' Connect our edge from comment to item '''
        # Ensure start item (comment) knows about this edge
        try:
            comment = self.start_pin.parent_comment
            if not hasattr(comment, 'edges'):
                comment.edges = []
            if self not in comment.edges:
                comment.edges.append(self)
        except IndexError:
            pass

        # If end_item exists, register it too
        if self.end_item is not None:
            if not hasattr(self.end_itemnode, 'comment_edges'):
                self.end_item.node.comment_edges = []
            if self not in self.end_item.node.comment_edges:
                self.end_item.node.comment_edges.append(self)

    def _unregisterFromItems(self):
        ''' Disconnect our comment from an item '''
        try:
            comment = self.start_pin.parent_comment
            if hasattr(comment, 'edges') and self in comment.edges:
                comment.edges.remove(self)
        except IndexError:
            pass

        if self.end_item is not None:
            try:
                if hasattr(self.end_item, 'comment_edges') and self in self.end_item.comment_edges:
                    self.end_item.comment_edges.remove(self)
            except IndexError:
                pass

    def setEndItem(self, item):
        ''' Set the end item we point to '''
        # unregister from old end_item and register to new one
        if self.end_item is not None:

            try:
                if hasattr(self.end_item, 'comment_edges') and self in self.end_item.comment_edges:
                    self.end_item.comment_edges.remove(self)
            except IndexError:
                pass
        self.end_item = item
        self.end_pos = None
        if isinstance(item, (QGraphicsTextItem,QGraphicsProxyWidget,BlockGraphicsNode)):
            if hasattr(item, 'node'):
                item = item.node
                self.end_item = item.grNode
        if item is not None:
            if not hasattr(item, 'comment_edges'):
                item.comment_edges = []
            if self not in item.comment_edges:
                item.comment_edges.append(self)
        self.updatePosition()

    def setEndPos(self, pos):
        ''' Clip to the end item '''
        # used during dragging
        self.end_pos = pos
        self.end_item = None
        self.updatePosition()


    def updatePosition(self):
        """Compute start and end in scene coords and set the line.
           Safely handles when end_item is None (dragging) or when it exists.
           The end point is shortened to sit on the border of the target item.
        """
        # compute start in scene coords
        start = self.start_pin.mapToScene(self.start_pin.pinCenter())

        # choose end
        if self.end_item is not None:
            # connect to end_item center, but then clip to its boundary
            # compute candidate end = center (works for most items)
            try:
                b = self.end_item.boundingRect()
                candidate_end = self.end_item.mapToScene(b.center())
            except IndexError:
                candidate_end = start
            # Now shorten the line so it stops on the border of the end_item
            end = self._pointOnItemBorder(self.end_item, start, candidate_end)
        elif self.end_pos is not None:
            end = self.end_pos
        else:
            end = start

        # avoid zero-length line issues
        if (start - end).manhattanLength() < 0.0001:
            end = start

        self.setLine(QLineF(start, end))

    def _pointOnItemBorder(self, item, p_from: QPointF, p_to: QPointF) -> QPointF:
        """Return the intersection between the line (p_from->p_to) and the
           item's boundingRect mapped into scene coords. If none found,
           return p_to shortened by a small margin.
        """
        rect = item.mapToScene(item.boundingRect()).boundingRect()  # rect in scene coords
        line = QLineF(p_from, p_to)

        # Check intersection with each edge of rect
        edges = [
            QLineF(rect.topLeft(), rect.topRight()),
            QLineF(rect.topRight(), rect.bottomRight()),
            QLineF(rect.bottomRight(), rect.bottomLeft()),
            QLineF(rect.bottomLeft(), rect.topLeft())
        ]
        for edge in edges:
            ip = QPointF()
            intersect_type = line.intersect(edge, ip)
            if intersect_type == QLineF.BoundedIntersection:
                # ip is in scene coords and lies on the border
                # Move the point a tiny bit outward along the line so arrow sits outside exactly
                v = QLineF(ip, p_from)
                if v.length() == 0:
                    return ip
                # push outward by a margin (so arrow doesn't overlap)
                margin = 1.0
                dx = (ip.x() - p_from.x()) / v.length()
                dy = (ip.y() - p_from.y()) / v.length()
                return QPointF(ip.x() - dx * margin, ip.y() - dy * margin)
        # fallback: shorten the line by a half of the smaller dimension (safe heuristic)
        fallback_margin = min(rect.width(), rect.height()) * 0.5
        if line.length() > fallback_margin:
            line.setLength(line.length() - fallback_margin)
            return line.p2()
        return p_to

    def keyPressEvent(self, event):
        ''' Delete if requested to do so '''
        if event.key() == Qt.Key_Delete:
            self.delete()
            return  # don’t propagate
        super().keyPressEvent(event)

    def paint(self, painter, option, widget=None): # pylint: disable=W0613
        ''' Paint the edge line '''
        # draw main line
        painter.setPen(self.pen())
        painter.drawLine(self.line())

        # draw arrowhead at actual line end (line.p2())
        line = self.line()
        if line.length() == 0:
            return

        arrow_size = 8.0
        angle = math.atan2(-line.dy(), line.dx())

        p2 = line.p2()
        arrow_p1 = QPointF(
            p2.x() + math.sin(angle - math.pi / 3) * arrow_size,
            p2.y() + math.cos(angle - math.pi / 3) * arrow_size
        )
        arrow_p2 = QPointF(
            p2.x() + math.sin(angle - math.pi + math.pi / 3) * arrow_size,
            p2.y() + math.cos(angle - math.pi + math.pi / 3) * arrow_size
        )
        arrow = QPolygonF([p2, arrow_p1, arrow_p2])

        painter.setBrush(QBrush(Qt.white))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(arrow)

        # selected highlight
        if self.isSelected():
            sel_pen = QPen(Qt.red, 2, Qt.DashLine)
            painter.setPen(sel_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(self.line())

    def delete(self):
        ''' Delete self '''
        if self.scene():
            s = self.scene().scene
            if s and hasattr(s, "comment_edges"):
                s.comment_edges = [e for e in s.comment_edges if e is not self]
        self._unregisterFromItems()
        if self.scene():
            self.scene().removeItem(self)
        del self

    def remove(self):
        ''' Same as delete self '''
        self.delete()

    def serialize(self):
        """Serialize the edge as a dict with references to start/end comments."""
        end_id = None
        if isinstance(self.end_item, BlockGraphicsNode):
            end_id = self.end_item.node.serialize()['id']
        elif isinstance(self.end_item, XMARTeQDMGraphicsEdge):
            end_id = self.end_item.edge.serialize()['id']
        data = {
            'start_id': id(self.start_pin.parent_comment),
            'end_id': end_id if self.end_item else None,
            'end_pos': pointToDict(self.end_pos) if self.end_pos else None
        }
        return data

    @staticmethod
    def deserialize(data, comments_by_id):
        """Recreate edge from dict. comments_by_id maps id->CommentItem."""
        start_comment = comments_by_id.get(data['start_id'])
        if not start_comment:
            return None
        start_pin = start_comment.pin

        end_item = comments_by_id.get(data['end_id']) if data['end_id'] else None
        if end_item:
            if isinstance(end_item, MARTe2Node):
                end_item = end_item.grNode
            elif isinstance(end_item, XMARTeEdge):
                end_item = end_item.grEdge
        #end_pos = pointFromDict(data['end_pos']) if data['end_pos'] else None
        end_pos = None
        edge = CommentEdge(start_pin, end_item=end_item, end_pos=end_pos)
        return edge

# ---------- CommentPin ----------
class CommentPin(QGraphicsPolygonItem):
    """Small triangular pin (bottom-right). Handles drag to create/pin an edge."""
    def __init__(self, parent_comment):
        # triangle pointing down
        poly = QPolygonF([QPointF(0, 0), QPointF(12, 0), QPointF(6, 10)])
        super().__init__(poly, parent_comment)
        self.parent_comment = parent_comment
        self.setBrush(QBrush(QColor(255, 255, 255)))
        self.setPen(QPen(Qt.white, 1))
        #self.setCursor(Qt.OpenHandCursor)
        self.setZValue(2)
        self.dragging = False
        self.temp_edge = None  # CommentEdge used while dragging (keeps persistent if released)

    def pinCenter(self):
        ''' Pin our edge to center '''
        r = self.boundingRect()
        return QPointF(r.center().x(), r.center().y())

    def mousePressEvent(self, event):
        ''' User has pressed, begin dragging '''
        # begin dragging => create an edge starting from this pin
        self.setCursor(Qt.ClosedHandCursor)
        self.dragging = True
        scene = self.scene()
        if scene:
            # create a new persistent edge and keep it in scene.comment_edges
            if self.temp_edge:
                self.temp_edge.remove()
            self.temp_edge = CommentEdge(start_pin=self)
            scene.addItem(self.temp_edge)
            if not hasattr(scene.scene, "comment_edges"):
                scene.scene.comment_edges = []
            scene.scene.comment_edges.append(self.temp_edge)
        event.accept()

    def mouseMoveEvent(self, event):
        ''' Being dragged maybe '''
        if not self.dragging or not self.temp_edge:
            event.ignore()
            return
        # update edge end to current mouse position
        scene_pos = self.mapToScene(event.pos())
        self.temp_edge.setEndPos(scene_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        ''' Mouse release - clip to an item with the edge if possible '''
        if not self.dragging or not self.temp_edge:
            event.ignore()
            return
        self.dragging = False
        self.setCursor(Qt.OpenHandCursor)
        scene = self.scene()
        scene_pos = self.mapToScene(event.pos())
        target = scene.itemAt(scene_pos, scene.views()[0].transform())

        # Don't consider the comment and its children as valid target
        if target is None or target is self.parent_comment or target is self:
            pass
        else:
            if not target is self.temp_edge:
                # pin to the item (store the item)
                self.temp_edge.setEndItem(target)
            else:
                self.temp_edge.delete()

        # ensure edge updates when items move (we'll rely on notifications from itemChange)
        self.temp_edge.updatePosition()
        event.accept()

# ---------- CommentItem ----------
class CommentItem(QGraphicsRectItem):
    """Comment box containing text and a pin. Auto-resizes on text edits."""
    def __init__(self, pos, initial_text="New comment"):
        super().__init__()
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges# |
            #QGraphicsRectItem.ItemIsFocusable
        )
        self.setBrush(QBrush(QColor(255, 255, 180)))
        self.setPen(QPen(Qt.black, 1.2))

        # Text
        self.text_item = QGraphicsTextItem(initial_text, self)
        self.text_item.setDefaultTextColor(Qt.black)
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        # connect text changes to resize
        self.text_item.document().contentsChanged.connect(self.adjustSizeToText)
        self.text_item.comment = self
        # Pin
        self.pin = CommentPin(self)

        # initial layout
        self.setPos(pos)
        self.adjustSizeToText()

        # start in editing mode
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_item.setFlag(QGraphicsTextItem.ItemIsFocusable)
        self.text_item.setFocus()

    def delete(self):
        ''' Delete self '''
        s = self.scene().scene
        if s and hasattr(s, "comments"):
            s.comments = [e for e in s.comments if e is not self]
        if self.hasEdge():
            e = self.getEdge()
            e.delete()
        if self.scene():
            self.scene().removeItem(self)
        del self

    def hasEdge(self):
        ''' Check that we have an edge '''
        if self.scene():
            s = self.scene().scene
            if not s or not hasattr(s, "comment_edges"):
                return False
            for e in s.comment_edges:
                if e.start_pin.parent_comment is self:
                    return True
        return False

    def getEdge(self):
        ''' Get our edge object '''
        if self.scene():
            s = self.scene().scene
            for e in s.comment_edges:
                if e.start_pin.parent_comment is self:
                    return e
        return None

    def adjustSizeToText(self):
        ''' Readjust size for text '''
        tr = self.text_item.boundingRect()
        margin = 10
        w = tr.width() + margin
        h = tr.height() + margin
        self.setRect(0, 0, w, h)
        self.text_item.setPos(5, 5)
        # position the pin just outside the bottom-right corner
        pin_offset_x = 6   # small gap from the edge
        pin_offset_y = 2
        self.pin.setPos(self.rect().width() - self.pin.boundingRect().width()/2 + pin_offset_x,
                        self.rect().height() - self.pin.boundingRect().height()/2 + pin_offset_y)
        # update any connected edges (scene.comment_edges)
        if self.hasEdge():
            self.getEdge().updatePosition()

    def focusOutEvent(self, event):
        ''' User left the item so no text changes now '''
        if not self.text_item.hasFocus():
            self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        super().focusOutEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Re-enter editing mode when double-clicked (even if the parent has focus)."""
        item = self.scene().itemAt(event.scenePos(), self.scene().views()[0].transform())
        if item is self.pin:
            # Don't edit if double-click was on the pin
            return super().mouseDoubleClickEvent(event)

        # If click hits text, let text handle it
        if item is self.text_item:
            return super().mouseDoubleClickEvent(event)

        # Enable editing
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_item.setFocus()

        return None

    def itemChange(self, change, value):
        ''' notify connected edges to update when the comment moves '''
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            if self.hasEdge():
                self.getEdge().updatePosition()
        return super().itemChange(change, value)

    def keyPressEvent(self, event):
        ''' Check if asked to delete '''
        if event.key() == Qt.Key_Delete:
            self.delete()
            return  # don’t propagate
        super().keyPressEvent(event)

    def serialize(self):
        """Return a dict with info to recreate this comment."""
        data = {
            'pos': pointToDict(self.pos()),
            'text': self.text_item.toPlainText(),
            'id': id(self)  # use id as unique identifier for edges
        }
        return data

    @staticmethod
    def deserialize(data):
        """Create CommentItem from serialized dict."""
        pos = pointFromDict(data['pos'])
        text = data['text']
        comment = CommentItem(pos, text)
        comment._id = data.get('id', id(comment)) # pylint: disable=W0212, W0201
        return comment
