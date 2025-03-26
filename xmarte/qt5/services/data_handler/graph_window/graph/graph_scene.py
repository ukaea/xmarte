''' The scene element of the graph window - allows multiple edges to an input and provides
two node classes '''
from nodeeditor.node_editor_widget import NodeEditorWidget
from nodeeditor.node_edge_validators import (
    edge_cannot_connect_two_outputs_or_two_inputs,
    edge_cannot_connect_input_and_output_of_same_node,
)

from xmarte.qt5.services.data_handler.graph_window.plot.plot_node import PlotNode
from xmarte.qt5.services.data_handler.graph_window.data.data_node import DataNode
from xmarte.nodeeditor.node_edge import XMARTeEdge
from xmarte.nodeeditor.node_scene import XMARTeScene

class DataEdge(XMARTeEdge):
    '''Override the Data Edge so we can allow edge connections of different types.'''
    edge_validators = []

DataEdge.registerEdgeValidator(edge_cannot_connect_input_and_output_of_same_node)
DataEdge.registerEdgeValidator(edge_cannot_connect_two_outputs_or_two_inputs)


class GraphScene(XMARTeScene):
    '''A specific scene for the graph window to override things like class specifier.'''
    def __init__(self):
        super().__init__()
        self.real = True

        class History:
            '''Override our history definition, do not support undo/redo,
            no history - causes issues.'''
            def storeHistory(self, s, setModified=False): # pylint: disable=C0103
                '''Overridden store history function.'''

        self.history = History()
        self.owner = None
        self.playback = False # Never used but required to exist

    def getEdgeClass(self):
        '''Return the class representing Edge.'''
        return DataEdge

    def getNodeClassFromData(self, data):
        '''Return the node class type.'''
        if data['type'] == 'PlotNode':
            return PlotNode
        return DataNode

    def removeNode(self, node, admin=False):
        """Remove :class:`~nodeeditor.node_node.Node` from this `Scene`

        :param node: :class:`~nodeeditor.node_node.Node` 
        to be removed from this `Scene`
        :type node: :class:`~nodeeditor.node_node.Node`
        """
        if node in self.nodes:
            if (isinstance(node, PlotNode) and admin) or not isinstance(node, PlotNode):
                self.nodes.remove(node)
                self.has_been_modified = True


class GraphEditorWidget(NodeEditorWidget):
    '''Node widget for the graph.'''
    Scene_class = GraphScene
