'''
The definition of components of the node in it's graphical representation
'''

from nodeeditor.node_content_widget import QDMNodeContentWidget

from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMenu,
)
from qtpy.QtGui import QColor, QPen, QPainterPath
from qtpy.QtCore import Qt, QRect, QRectF

from PyQt5 import QtGui

from xmarte.nodeeditor.node_graphics_node import XMARTeQDMGraphicsNode

class NodeContent(QDMNodeContentWidget):
    '''
    The main content box which is the area of a node not including the title.
    '''
    def initUI(self):
        """Sets up layouts and widgets to be rendered in 
        :py:class:`~nodeeditor.node_graphics_node.QDMGraphicsNode` class."""
        self.layout = QVBoxLayout()
        # self.chart = QChart()
        # self.chart_view = QChartView(self.chart)
        #self.layout.addWidget(GraphDrawer(self.node))
        self.setLayout(self.layout)

    def updateDim(self):
        '''
        Update our dimensions so everything fits correctly
        '''
        # Get Current Height
        if self.node.grNode:
            height = self.node.grNode.height
            self.setFixedHeight(int(self.node.grNode.height - self.node.grNode.title_height))
            # Check the Inputs
            nSockets = self.node.inputs
            input_height = sum(a.grSocket.boundingRect().height() for a in nSockets)
            if (input_height * 1.4) > height:
                height = input_height * 1.4
                self.setFixedHeight(int(height + self.node.grNode.title_height))
                self.node.grNode.height = height + (self.node.grNode.title_height * 2)

            # Check the Outputs
            nSockets = self.node.outputs
            output_height = sum(a.grSocket.boundingRect().height() for a in nSockets)
            if (output_height * 1.4) > height:
                height = output_height * 1.4
                self.setFixedHeight(int(height + self.node.grNode.title_height))
                self.node.grNode.height = height + (self.node.grNode.title_height * 2)

        self.node.updateSocketPositions()

class BlockGraphicsNode(XMARTeQDMGraphicsNode):
    '''
    The overall graphical representation of the node
    '''
    def __init__(self, node, parent: QWidget = None):
        '''
        Setup our node
        '''
        self.grContent = None
        self.edge_padding = 0
        self.width = 200
        self.title_height = 40
        super().__init__(node, parent)
        self.adjustTitleSize()

        self.downstream = False
        self.upstream = False
        self._pen_upstream = QColor("#C87EDE")
        self._pen_downstream = QColor("#27b338")

        self.actionsMenu = QMenu()
        deleteAct = self.actionsMenu.addAction("Delete")

        def deletenode(self):
            self.node.remove()
            self.node.scene.nodes = [
                a for a in self.node.scene.nodes if a is not self.node
            ]
            if hasattr(self.node.application, "configbar"):
                if self.node.application.configbar is not None:
                    if self.node.application.configbar.node == self.node:
                        self.node.application.rightpanel.vlayout.removeWidget(
                            self.node.application.configbar
                        )
                        self.node.application.configbar = None

        deleteAct.act = deletenode
        self.actions = [deleteAct]
        try:
            viewportRect = QRect(
                0,
                0,
                self.node.scene.getView().width(),
                self.node.scene.getView().height(),
            )
            visibleSceneRect = QRectF(
                self.node.scene.getView().mapToScene(
                    viewportRect
                ).boundingRect()
            )
            right = visibleSceneRect.right()
            left = visibleSceneRect.left()
            top = visibleSceneRect.top()
            bottom = visibleSceneRect.bottom()
            x = (((right - left) / 2) + visibleSceneRect.left()) - self.width / 2
            y = ((top - bottom) / 2) + visibleSceneRect.bottom() - self.height / 2
            super().setPos(x, y)
        except (IndexError,AttributeError):  # noqa: E722
            pass

    def mouseMoveEvent(self, event):
        """Overridden event to detect that we moved with this `Node`"""
        super().mouseMoveEvent(event)

        # optimize me! just update the selected nodes
        for node in self.scene().scene.nodes:
            if node.grNode is not None:
                if node.grNode.isSelected():
                    node.updateConnectedEdges()
        self._was_moved = True

    def initSizes(self):
        '''
        Initialise the node sizes
        '''
        super().initSizes()
        self.width = 200
        self.height = 150
        self.graph_height = 100
        self.edge_roundness = 6
        self.edge_padding = 0
        self.title_horizontal_padding = 8
        self.title_vertical_padding = 10
        self.title_height = 40

    def contextMenuEvent(self, event):
        '''
        Activate right click menu
        '''
        action = self.actionsMenu.exec_(event.screenPos())
        for actor in self.actions:
            if actor == action:
                actor.act(self)

    def setPos(self, scene_x: float, scene_y: float):
        ''' set position of node in reference to the scene '''
        # x, y = self.avoidOffscene(x, y)
        super().setPos(scene_x, scene_y)
        self.node.updateConnectedEdges()
        self.update()

    def avoidOffscene(self, scene_x, scene_y):
        '''
        Avoid displaying items such as labels when we are outside of the viewport in the scene
        '''
        scene = self.scene()
        scene_height = scene.sceneRect().height()
        scene_width = scene.sceneRect().width()
        scene_y = max(scene_y, 0)
        if scene_y > scene_height:
            scene_y = (scene_height) - self.height
        scene_x = max(scene_x, 0)
        if scene_x > scene_width:
            scene_x = (scene_width) - self.width
        return scene_x, scene_y

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

    def initContent(self):
        """ Set up the `grContent` - ``QGraphicsProxyWidget``
         to have a container for `Graphics Content` """
        if self.content is not None:
            self.updateContent()

        # get the QGraphicsProxyWidget when inserted into the grScene
        if self.node.scene.real:
            self.grContent = self.node.scene.grScene.addWidget(self.content)
            self.grContent.node = self.node
            self.grContent.setParentItem(self)

    def adjustTitleSize(self):
        ''' Titles changed somehow or something has, update title changes '''
        metrics = QtGui.QFontMetrics(self.title_item.font())
        self.width = (
            (metrics.width(self.node.title) + 50)
            if (metrics.width(self.node.title) + 50) > 200
            else 200
        )
        self.setContentDim()
        self.title_item.setTextWidth(self.width - 2 * self.title_horizontal_padding)
        self.content.updateDim()

    def setContentDim(self):
        ''' Set the dimensions of the node content '''
        self.title_height = int(self.title_height)
        self.edge_padding = int(self.edge_padding)
        if self.content is not None:
            self.content.setGeometry(
                int(self.edge_padding),
                int(self.title_height + self.edge_padding),
                int(self.width - 2 * self.edge_padding),
                int(self.height - 2 * self.edge_padding - self.title_height),
            )

    def initAssets(self):
        ''' Initialise the drawing graphical assets '''
        super().initAssets()
        self._graph_color = QColor("#FFFFFF")

        self._pen_graph = QPen(self._graph_color)
        self._pen_graph.setWidthF(2.0)

    def adjustLabelSizes(self):
        """Adjust for long socket names"""
        longestinput = 0
        longestoutput = 0
        for node_input in self.node.inputs:
            longestinput = (
                node_input.grSocket.label_width
                if node_input.grSocket.label_width > longestinput
                else longestinput
            )

        for node_output in self.node.outputs:
            longestoutput = (
                node_output.grSocket.label_width
                if node_output.grSocket.label_width > longestoutput
                else longestoutput
            )

        bufferpix = 60
        if (longestoutput + longestinput + bufferpix) > self.width:
            self.width = longestoutput + longestinput + bufferpix
            self.setContentDim()
            self.title_item.setTextWidth(self.width - 2 * self.title_horizontal_padding)
            self.node.updateSocketPositions()

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        """Painting the rounded rectanglar `Node`"""
        self.adjustLabelSizes()
        # title
        path_title = QPainterPath()
        path_title.setFillRule(Qt.WindingFill)
        path_title.addRoundedRect(
            0,
            0,
            self.width,
            self.title_height,
            self.edge_roundness,
            self.edge_roundness,
        )
        path_title.addRect(
            0,
            self.title_height - self.edge_roundness,
            self.edge_roundness,
            self.edge_roundness,
        )
        path_title.addRect(
            self.width - self.edge_roundness,
            self.title_height - self.edge_roundness,
            self.edge_roundness,
            self.edge_roundness,
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # content
        path_content = QPainterPath()
        path_content.setFillRule(Qt.WindingFill)
        path_content.addRoundedRect(
            0,
            self.title_height,
            self.width,
            self.height - self.title_height,
            self.edge_roundness,
            self.edge_roundness,
        )
        path_content.addRect(
            0, self.title_height, self.edge_roundness, self.edge_roundness
        )
        path_content.addRect(
            self.width - self.edge_roundness,
            self.title_height,
            self.edge_roundness,
            self.edge_roundness,
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # outline
        path_outline = QPainterPath()
        path_outline.addRoundedRect(
            -1,
            -1,
            self.width + 2,
            self.height + 2,
            self.edge_roundness,
            self.edge_roundness,
        )
        painter.setBrush(Qt.NoBrush)
        if self.hovered:
            painter.setPen(self._pen_hovered)
            painter.drawPath(path_outline.simplified())
            painter.setPen(self._pen_default)
            painter.drawPath(path_outline.simplified())
        elif self.upstream:
            painter.setPen(self._pen_upstream)
            painter.drawPath(path_outline.simplified())
        elif self.downstream:
            painter.setPen(self._pen_downstream)
            painter.drawPath(path_outline.simplified())
        else:
            painter.setPen(
                self._pen_default if not self.isSelected() else self._pen_selected
            )
            painter.drawPath(path_outline.simplified())
