''' Override of the socket definition in the Graph Window to include data and make it
serializable and deserializable for simplifying saving and loading '''
from collections import OrderedDict

from nodeeditor.node_socket import LEFT_TOP

from xmarte.nodeeditor.node_socket import XMARTeLabeledSocket

class DataSocket(XMARTeLabeledSocket):
    ''' The new data socket format which includes defined data '''
    def __init__(self, node, index: int=0, position: int=LEFT_TOP,
                 socket_type: int=1, multi_edges: bool=True,
                 count_on_this_node_side: int=1, is_input: bool=False,
                 label: str="", data=None):
        self.data = data
        super().__init__(node, index, position, socket_type, multi_edges,
                         count_on_this_node_side, is_input, label)

    def serialize(self) -> OrderedDict:
        ''' Serialize our socket along with the data '''
        res = super().serialize()
        res['data'] = self.data
        return res

    def deserialize(self, data: dict, hashmap: dict={}, # pylint:disable=W1113
                    restore_id: bool=True, *args, **kwargs) -> bool:
        ''' Deserialize and get our data back into the socket '''
        res = super().deserialize(data, hashmap, restore_id)
        if 'data' in res:
            self.data = res['data']
        else:
            self.data = None
        return res
