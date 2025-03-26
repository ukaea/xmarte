'''
The basic definitions of abstract-ish classes for nodes within the application.
'''

from xmarte.nodeeditor.node_edge import XMARTeEdge
from xmarte.nodeeditor.node_scene import XMARTeScene
from xmarte.nodeeditor.node_node import XMARTeLabeledSocketNode


class UniversalNodeFeatures(XMARTeLabeledSocketNode):
    '''
    Some concepts we maintain across all nodes:
    - upstream
    - downstream
    - setattr triggers scene has been modified
    '''
    def __init__(self, scene: XMARTeScene = None, inputs=[], outputs=[]):
        self.configuration_name = ''
        self.btype = ''
        super().__init__(scene, self.title, inputs, outputs)

    @property
    def title(self):
        ''' Ensure our title conforms to the expected value '''
        return self.configuration_name + " (" + self.btype + ")"

    @title.setter
    def title(self, value):
        pass

    def doSelect(self, new_state: bool = True):
        ''' on selected, trigger downstream and upstream'''
        for node in self.scene.nodes:
            node.grNode.upstream = False
            node.grNode.downstream = False
        super().doSelect(new_state)
        # Get Upstream blocks
        upstream_nodes = []
        self.getupstream(self, upstream_nodes)
        # Get Downstream blocks
        downstream_nodes = []
        self.getdownstream(self, downstream_nodes)
        for node in upstream_nodes:
            node.grNode.upstream = True

        for node in downstream_nodes:
            node.grNode.downstream = True

    def getdownstream(self, node, nodes):
        ''' Return recursively the nodes that are fed from this node '''
        for output in node.outputs:
            for edge in output.edges:
                if hasattr(edge, "end_socket") and edge.end_socket is not None:
                    if edge.end_socket.node in nodes:
                        _ = nodes.index(edge.end_socket.node)
                        # Loop Detected - use hare and tortoise to solve this
                        # nodes = nodes[:-(len(nodes)-place)]
                    else:
                        nodes += [edge.end_socket.node]
                        self.getdownstream(edge.end_socket.node, nodes)

    def __setattr__(self, name, value):
        ''' If an attribute is changed in anyway on our node we want to trigger the scene 
        has been modified. '''
        if not name == 'large_import' and not name == 'changed':
            try:
                if not hasattr(self, name):
                    if hasattr(self, "scene"):
                        self.scene.has_been_modified = True
                else:
                    if getattr(self, name) is not value:
                        # New change
                        if hasattr(self, "scene"):
                            self.scene.has_been_modified = True
            except (ValueError, AttributeError):
                pass
        super().__setattr__(name, value)

    def getupstream(self, node, nodes):
        ''' Return recursively the nodes that feed this node '''
        for node_input in node.inputs:
            for edge in node_input.edges:
                if isinstance(edge, XMARTeEdge):
                    if edge.start_socket.node in nodes:
                        _ = nodes.index(edge.start_socket.node)
                        # nodes = nodes[:-(len(nodes)-place)]
                    else:
                        nodes += [edge.start_socket.node]
                        self.getupstream(edge.start_socket.node, nodes)
