
from collections import OrderedDict
import json
import sys

from nodeeditor.utils_no_qt import dumpException
from nodeeditor.node_scene import Scene, DEBUG_REMOVE_WARNINGS, InvalidFile
from nodeeditor.node_node import Node
from nodeeditor.node_edge import Edge

from xmarte.nodeeditor.node_edge import XMARTeEdge
from xmarte.nodeeditor.node_graphics_scene import XMARTeQDMGraphicsScene

class XMARTeScene(Scene):
    def __init__(self):
        super().__init__()
        self.deserialisers = {}
        self.serialisers = {}
        
    def initUI(self):
        """Set up Graphics Scene Instance"""
        self.grScene = XMARTeQDMGraphicsScene(self)
        self.grScene.setGrScene(self.scene_width, self.scene_height)

    @property
    def has_been_modified(self):
        """
        Has this `Scene` been modified?

        :getter: ``True`` if the `Scene` has been modified
        :setter: set new state. Triggers `Has Been Modified` event
        :type: ``bool``
        """
        return self._has_been_modified

    @has_been_modified.setter
    def has_been_modified(self, value):
        # set it now, because we will be reading it soon
        self._has_been_modified = value

        # call all registered listeners
        if value:
            for callback in self._has_been_modified_listeners: callback()

    def getEdgeClass(self):
        """Return the class representing Edge. Override me if needed"""
        return XMARTeEdge
        
    def addNode(self, node: Node):
        """Add :class:`~nodeeditor.node_node.Node` to this `Scene`

        :param node: :class:`~nodeeditor.node_node.Node` to be added to this `Scene`
        :type node: :class:`~nodeeditor.node_node.Node`
        """
        self.nodes.append(node)
        self.has_been_modified = True
        
    def addEdge(self, edge: Edge):
        """Add :class:`~nodeeditor.node_edge.Edge` to this `Scene`

        :param edge: :class:`~nodeeditor.node_edge.Edge` to be added to this `Scene`
        :return: :class:`~nodeeditor.node_edge.Edge`
        """
        self.edges.append(edge)
        self.has_been_modified = True
        
    def removeNode(self, node: Node):
        """Remove :class:`~nodeeditor.node_node.Node` from this `Scene`

        :param node: :class:`~nodeeditor.node_node.Node` to be removed from this `Scene`
        :type node: :class:`~nodeeditor.node_node.Node`
        """
        if node in self.nodes:
            self.nodes.remove(node)
            self.has_been_modified = True
        else:
            if DEBUG_REMOVE_WARNINGS: print("!W:", "Scene::removeNode", "wanna remove nodeeditor", node,
                                            "from self.nodes but it's not in the list!")
            
    def removeEdge(self, edge: Edge):
        """Remove :class:`~nodeeditor.node_edge.Edge` from this `Scene`

        :param edge: :class:`~nodeeditor.node_edge.Edge` to be remove from this `Scene`
        :return: :class:`~nodeeditor.node_edge.Edge`
        """
        if edge in self.edges:
            self.edges.remove(edge)
            self.has_been_modified = True
        else:
            if DEBUG_REMOVE_WARNINGS: print("!W:", "Scene::removeEdge", "wanna remove edge", edge,
                                            "from self.edges but it's not in the list!")

    def clear(self):
        """Remove all `Nodes` from this `Scene`. This causes also to remove all `Edges`"""
        while len(self.nodes) > 0:
            self.nodes[0].remove()

        self.has_been_modified = True
        
    def saveToFile(self, filename: str):
        """
        Save this `Scene` to the file on disk.

        :param filename: where to save this scene
        :type filename: ``str``
        """
        with open(filename, "w") as file:
            file.write( json.dumps( self.serialize(), indent=4 ) )
            print("saving to", filename, "was successfull.")

            self.has_been_modified = False
            self.filename = filename

    def loadFromFile(self, filename: str, *args, **kwargs):
        """
        Load `Scene` from a file on disk

        :param filename: from what file to load the `Scene`
        :type filename: ``str``
        :raises: :class:`~nodeeditor.node_scene.InvalidFile` if there was an error decoding JSON file
        """

        with open(filename, "r") as file:
            raw_data = file.read()
            try:
                if sys.version_info >= (3, 9):
                    data = json.loads(raw_data)
                else:
                    data = json.loads(raw_data, encoding='utf-8')
                self.filename = filename
                self.deserialize(data, *args, **kwargs)
                self.has_been_modified = False
            except json.JSONDecodeError:
                raise InvalidFile("%s is not a valid JSON file" % os.path.basename(filename))
            except Exception as e:
                dumpException(e)

    def adddeserialiser(self, name, function):
        self.deserialisers[name] = function

    def addserialiser(self, name, function):
        self.serialisers[name] = function

    def removedeserialiser(self, name):
        self.deserialisers.pop(name,None)

    def removeserialiser(self, name):
        self.serialisers.pop(name,None)
        
    def serialize(self) -> OrderedDict:
        additionals = OrderedDict()
        for k,v in self.serialisers.items():
            odict = v(self)
            additionals.update(odict)
        nodes, edges = [], []
        for node in self.nodes:
            newnode = node.serialize()
            if not any (newnode['id'] == a['id'] for a in nodes):
                nodes.append(newnode)
        for edge in self.edges:
            newedge = edge.serialize()
            if not any (newedge['id'] == a['id'] for a in edges):
                edges.append(newedge)
        arr = OrderedDict([
            ('id', self.id),
            ('scene_width', self.scene_width),
            ('scene_height', self.scene_height),
            ('nodes', nodes),
            ('edges', edges),
        ])
        arr.update(additionals)
        return arr

    def deserialize(self, data: dict, hashmap: dict={}, restore_id: bool=True, *args, **kwargs) -> bool:
        hashmap = {}

        for k,v in self.deserialisers.items():
            v(self, data, hashmap, restore_id, args, kwargs)

        if restore_id: self.id = data['id']

        # -- deserialize NODES

        ## Instead of recreating all the nodes, reuse existing ones...
        # get list of all current nodes:
        all_nodes = self.nodes.copy()

        # go through deserialized nodes:
        for node_data in data['nodes']:
            # can we find this node in the scene?
            found = False
            for node in all_nodes:
                if node.id == node_data['id']:
                    found = node
                    break

            if not found:
                try:
                    new_node = self.getNodeClassFromData(node_data)(self)
                    new_node.deserialize(node_data, hashmap, restore_id, *args, **kwargs)
                    new_node.onDeserialized(node_data)
                    # print("New node for", node_data['title'])
                except:
                    dumpException()
            else:
                try:
                    found.deserialize(node_data, hashmap, restore_id, *args, **kwargs)
                    found.onDeserialized(node_data)
                    all_nodes.remove(found)
                    # print("Reused", node_data['title'])
                except: dumpException()

        # remove nodes which are left in the scene and were NOT in the serialized data!
        # that means they were not in the graph before...
        while all_nodes != []:
            node = all_nodes.pop()
            node.remove()


        # -- deserialize EDGES


        ## Instead of recreating all the edges, reuse existing ones...
        # get list of all current edges:
        all_edges = self.edges.copy()

        # go through deserialized edges:
        for edge_data in data['edges']:
            # can we find this node in the scene?
            found = False
            for edge in all_edges:
                if edge.id == edge_data['id']:
                    found = edge
                    break

            if not found:
                new_edge = self.getEdgeClass(self).deserialize(edge_data, hashmap, restore_id, *args, **kwargs)
                # print("New edge for", edge_data)
            else:
                found.deserialize(edge_data, hashmap, restore_id, *args, **kwargs)
                all_edges.remove(found)

        # remove nodes which are left in the scene and were NOT in the serialized data!
        # that means they were not in the graph before...
        while all_edges != []:
            edge = all_edges.pop()
            edge.remove()


        return True
