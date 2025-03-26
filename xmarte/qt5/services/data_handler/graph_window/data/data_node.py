''' The data node used in plotting in the Graph Window '''

from xmarte.nodeeditor.node_node import XMARTeLabeledSocketNode
from xmarte.qt5.services.data_handler.graph_window.graph.graph_node import GraphNode
from xmarte.qt5.services.data_handler.graph_window.data.data_socket import DataSocket
from xmarte.qt5.services.data_handler.graph_window.data.data_node_content import DataNodeContent
from xmarte.qt5.services.data_handler.graph_window.data.data_graphics_node import DataGraphicsNode


class DataNode(GraphNode):
    '''The Data Node itself.'''
    Socket_class = DataSocket
    GraphicsNode_class = DataGraphicsNode
    NodeContent_class = DataNodeContent
    graph = False

    def __init__(
        self,
        scene: "Scene",
        title: str = "Undefined Node",
        inputs: list = [],
        outputs: list = [], # list of tuple - socket_type, socket_label, socket_data
        origin_node: XMARTeLabeledSocketNode = None,
        origin: str = "",
    ):
        self.inputs = []
        self.outputs = []
        data = [a[2] for a in outputs]
        outputs = [(a[0], a[1]) for a in outputs]
        self.node = origin_node
        self.origin = origin
        self.type = "DataNode"
        self.application = scene.application
        super().__init__(scene=scene, title=title, inputs=inputs, outputs=outputs)
        self.grNode.content.updateDim()
        self.grNode.adjustTitleSize()
        for data_row, output in zip(data, self.outputs):
            output.data = data_row

    def serialize(self):
        ''' Serialise '''
        res = super().serialize()
        res["node"] = self.node.serialize()
        res["origin"] = self.origin
        res["type"] = "DataNode"
        return res

    def deserialize(self, data, hashmap={}, restore_id=True, *args, **kwargs): # pylint: disable=W1113
        ''' Deserialise '''
        res = super().deserialize(data, hashmap, restore_id)
        self.grNode.adjustTitleSize()
        return res

def initialize(factory, plugin_datastore) -> None:
    '''
    Register our node in our factory
    '''
    factory.registerBlock("DataNode", DataNode, plugin_datastore)
