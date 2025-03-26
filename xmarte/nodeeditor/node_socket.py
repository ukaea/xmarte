
from collections import OrderedDict

from nodeeditor.node_socket import Socket,LEFT_TOP

from xmarte.nodeeditor.node_graphics_socket import XMARTeQDMGraphicsLabeledSocket

class XMARTeSocket(Socket):
    def __init__(self, node: 'Node', index: int=0, position: int=LEFT_TOP, socket_type: int=1, multi_edges: bool=True,
                 count_on_this_node_side: int=1, is_input: bool=False):
        super().__init__(node, index, position, socket_type, multi_edges,
                 count_on_this_node_side, is_input)
        self.data = None
        
    def delete(self):
        """Delete this `Socket` from graphics scene for sure"""
        self.grSocket.setParentItem(None)
        self.node.scene.grScene.removeItem(self.grSocket)
        while(len(self.edges)):
            self.edges[0].remove()
        del self.grSocket
    
    def deserialize(self, data: dict, hashmap: dict={}, restore_id: bool=True) -> bool:
        if restore_id: self.id = data['id']
        self.is_multi_edges = self.determineMultiEdges(data)
        self.changeSocketType(data['socket_type'])
        hashmap[data['id']] = self
        return data

class XMARTeLabeledSocket(XMARTeSocket):

    Socket_GR_Class = XMARTeQDMGraphicsLabeledSocket

    def __init__(self, node: 'Node', index: int=0, position: int=LEFT_TOP, socket_type: int=1, multi_edges: bool=True,
                 count_on_this_node_side: int=1, is_input: bool=False, label: str=""):
        """
        :param node: reference to the :class:`~nodeeditor.node_node.Node` containing this `Socket`
        :type node: :class:`~nodeeditor.node_node.Node`
        :param index: Current index of this socket in the position
        :type index: ``int``
        :param position: Socket position. See :ref:`socket-position-constants`
        :param socket_type: Constant defining type(color) of this socket
        :param multi_edges: Can this socket have multiple `Edges` connected?
        :type multi_edges: ``bool``
        :param count_on_this_node_side: number of total sockets on this position
        :type count_on_this_node_side: ``int``
        :param is_input: Is this an input `Socket`?
        :type is_input: ``bool``
        :param label: The label of the socket that is displayed next to it
        :type label: ``str``
        """

        super().__init__(node, index, position, socket_type, multi_edges, count_on_this_node_side, is_input)
        self.label = label

    def serialize(self) -> OrderedDict:
        res = super().serialize()
        res['label'] = self.label
        if hasattr(self,"name"):
            res['name'] = self.name
        return res

    def deserialize(self, data: dict, hashmap: dict={}, restore_id: bool=True, *args, **kwargs) -> bool:
        res = super().deserialize(data, hashmap, restore_id)
        if 'name' in res:
            self.name = res['name']
        else:
            self.name = ""
        self.label = res['label']
        return res