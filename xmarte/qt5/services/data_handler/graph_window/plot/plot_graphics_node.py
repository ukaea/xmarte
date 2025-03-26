''' The graphics component to the plot node which is used to define plot graphs '''
from xmarte.qt5.nodes.node_graphics import BlockGraphicsNode


class PlotGraphicsNode(BlockGraphicsNode):
    '''
    The Plot Graphics setup
    '''
    def __init__(self, node, parent = None):
        self.height = 0
        super().__init__(node, parent)

    def keyReleaseEvent(self, QKeyEvent): # pylint: disable=C0103
        ''' Ignore Key Release '''

    def keyPressEvent(self, QKeyEvent): # pylint: disable=C0103
        ''' Ignore Key Press '''
