

from collections import OrderedDict

from nodeeditor.node_node import Node
from nodeeditor.node_serializable import Serializable
from nodeeditor.utils_no_qt import dumpException

from xmarte.nodeeditor.node_socket import XMARTeLabeledSocket

class XMARTeNode(Node):
    def updateSocketPositions(self):
        '''
        Redraw our sockets
        '''
        if hasattr(self, 'inputs'):
            for in_socket in self.inputs:
                in_socket.setSocketPosition()
        if hasattr(self, 'outputs'):
            for out_socket in self.outputs:
                out_socket.setSocketPosition()
                
    def serialize(self) -> OrderedDict:
        inputs, outputs = [], []
        for socket in self.inputs: inputs.append(socket.serialize())
        for socket in self.outputs: outputs.append(socket.serialize())
        ser_content = self.content.serialize() if isinstance(self.content, Serializable) else {}
        pos_x, pos_y = 0, 0
        
        if hasattr(self.grNode, 'scenePos'):
            pos_x = self.grNode.scenePos().x()
            pos_y = self.grNode.scenePos().y()
            
        return OrderedDict([
            ('id', self.id),
            ('title', self.title),
            ('pos_x', pos_x),
            ('pos_y', pos_y),
            ('inputs', inputs),
            ('outputs', outputs),
            ('content', ser_content),
        ])

class XMARTeLabeledSocketNode(XMARTeNode):

    Socket_class = XMARTeLabeledSocket

    def initSockets(self, inputs: list, outputs: list, reset: bool = True):
        """
        Create sockets for inputs and outputs

        :param inputs: list of tuples with socket types and labels (int, str)
        :type inputs: ``list``
        :param outputs: list of tuples with socket types and labels (int, str)
        :type outputs: ``list``
        :param reset: if ``True`` destroys and removes old `Sockets`
        :type reset: ``bool``
        """
        if reset:
            # clear old sockets
            if hasattr(self, 'inputs') and hasattr(self, 'outputs'):
                # remove grSockets from scene
                for socket in (self.inputs + self.outputs):
                    self.scene.grScene.removeItem(socket.grSocket)
                self.inputs = []
                self.outputs = []

        # create new sockets
        counter = 0
        for item in inputs:
            socket = self.__class__.Socket_class(
                node=self, index=counter, position=self.input_socket_position,
                socket_type=item[0], multi_edges=self.input_multi_edged,
                count_on_this_node_side=len(inputs), is_input=True, label=item[1]
            )
            counter += 1
            self.inputs.append(socket)

        counter = 0
        for item in outputs:
            socket = self.__class__.Socket_class(
                node=self, index=counter, position=self.output_socket_position,
                socket_type=item[0], multi_edges=self.output_multi_edged,
                count_on_this_node_side=len(outputs), is_input=False, label=item[1]
            )
            counter += 1
            self.outputs.append(socket)

    def updateSocket(self, outputs):
        '''Update the labels of sockets'''
        for socket, (_, label) in zip(self.outputs, outputs):
            socket.label = label
            socket.grSocket.update()
