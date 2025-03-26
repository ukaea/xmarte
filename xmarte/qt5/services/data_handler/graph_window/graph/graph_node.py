''' The generic node implementation for our graph window - primarily handles socket position '''
from xmarte.nodeeditor.node_node import XMARTeLabeledSocketNode

class GraphNode(XMARTeLabeledSocketNode):
    '''
    The base graph node implementation
    '''

    def updateSocketPositions(self):
        '''
        Update sockets based on changes
        '''
        if hasattr(self, 'inputs') and hasattr(self, 'outputs'):
            for in_socket in self.inputs:
                in_socket.setSocketPosition()
            for out_socket in self.outputs:
                out_socket.setSocketPosition()

    def serialize(self):
        '''
        Serialise
        '''
        res = super().serialize()
        return res

    def deserialize(self, data, hashmap={}, restore_id=True, *args, **kwargs): # pylint:disable=W1113
        '''
        Deserialise
        '''
        res = super().deserialize(data, hashmap, restore_id)
        return res
