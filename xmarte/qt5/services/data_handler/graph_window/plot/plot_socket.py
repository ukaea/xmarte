''' The socket used by the plot node - mostly basic socket but has unique class name
and modifies defaults '''
from nodeeditor.node_socket import LEFT_TOP

from xmarte.nodeeditor.node_socket import XMARTeLabeledSocket

class PlotSocket(XMARTeLabeledSocket):
    '''
    Socket for the plot node so we can handle input changes
    '''
    def __init__(
        self,
        node,
        index: int = 0,
        position: int = LEFT_TOP,
        socket_type: int = 1,
        multi_edges: bool = True,
        count_on_this_node_side: int = 1,
        is_input: bool = False,
        label: str = "",
    ):
        super().__init__(
            node=node,
            index=index,
            position=position,
            socket_type=socket_type,
            multi_edges=True,
            count_on_this_node_side=count_on_this_node_side,
            is_input=is_input,
            label=label,
        )
