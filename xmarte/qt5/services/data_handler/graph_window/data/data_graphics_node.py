''' The graphics component of the data node used in plotting in the Graph Window '''
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import QRect, QRectF

from xmarte.qt5.nodes.node_graphics import BlockGraphicsNode


class DataGraphicsNode(BlockGraphicsNode):
    '''The Graphics representation for the Data Node.'''
    def __init__(self, node, parent = None):
        super().__init__(node, parent)
        self.adjustTitleSize()

        self.downstream = False
        self.upstream = False
        self._pen_upstream = QColor("#FCBA03")
        self._pen_downstream = QColor("#27b338")

        self.actionsMenu = QMenu()
        deleteAct = self.actionsMenu.addAction("Delete")

        def deletenode(self):
            ''' Delete a node '''
            self.node.remove()
            self.node.scene.nodes = [
                a for a in self.node.scene.nodes if a is not self.node
            ]

        deleteAct.act = deletenode
        self.actions = [deleteAct]
        viewportRect = QRect(
            0,
            0,
            self.node.scene.grScene.views()[0].viewport().width(),
            self.node.scene.grScene.views()[0].viewport().height(),
        )
        visibleSceneRect = QRectF(
            self.node.scene.grScene.views()[0].mapToScene(viewportRect).boundingRect()
        )
        right = visibleSceneRect.right()
        left = visibleSceneRect.left()
        top = visibleSceneRect.top()
        bottom = visibleSceneRect.bottom()
        x = (((right - left) / 2) + visibleSceneRect.left()) - self.width / 2
        y = ((top - bottom) / 2) + visibleSceneRect.bottom() - self.height / 2
        super().setPos(x, y)

    def scene(self):
        '''Return the graphics scene.'''
        return self.node.scene.grScene
