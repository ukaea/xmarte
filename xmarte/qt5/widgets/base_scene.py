'''
The base definition of the scene for several standard overrides like node classifier
'''
import uuid
import json
from collections import OrderedDict

from nodeeditor.node_edge import EDGE_TYPE_DEFAULT

from xmarte.nodeeditor.node_scene import XMARTeScene
from xmarte.nodeeditor.node_edge import XMARTeEdge
from xmarte.qt5.libraries.functions import PluginException

class BaseScene(XMARTeScene):
    '''
    Base Scene Definition
    '''
    def __init__(self, application, real=False):
        self._clearListeners = []
        self._nodeRemoveListeners = []
        self._modifiedListeners = []
        self.application = application
        self.version_uuid = str(uuid.uuid4())
        self.playback = False
        self.real = real
        self.count = 0
        self.large_import = False
        super().__init__()
        self.scene_width = 6400
        self.scene_height = 6400
        self.initUI()
        self.setNodeClassSelector(self.nodeClassSelectorFunction)

    def updateCounter(self, val):
        ''' Update the scene counter for playback'''
        self.count = val

    def onDeserialize(self, node):
        ''' Event Callback for deserialization '''

    def nodeRemovedListeners(self, node):
        ''' Activate the node removal listeners '''
        for listener in self._nodeRemoveListeners:
            listener(node)

    def addNodeRemoveListener(self, func):
        ''' add listener for nodes calling remove '''
        self._nodeRemoveListeners += [func]

    def clearNodeRemoveListener(self):
        ''' clear listeners for nodes calling remove '''
        self._nodeRemoveListeners = []

    def resetClearCallbacks(self):
        ''' Reset Clear Callbacks '''
        self._clearListeners = []

    def addClearListener(self, func):
        ''' Add clear button listener '''
        self._clearListeners.append(func)

    def addModifiedListener(self, func):
        ''' Add a modified listener to the list of listeners '''
        self._modifiedListeners += [func]

    def clearModifiedListener(self):
        ''' Clear the list of modified listeners '''
        self._modifiedListeners = []

    def modifiedListeners(self):
        ''' Trigger modifier listeners and act on '''
        if not self.large_import:
            for i in self._modifiedListeners:
                i(self)

    def saveToFile(self, filename: str, printoutput=True, updateModified=True):
        """
        Save this `Scene` to the file on disk.

        :param filename: where to save this scene
        :type filename: ``str``
        
        Override to include a unique UUID for each save action
        """
        if self._has_been_modified:
            # We're new, update our uuid hash
            self.version_uuid = str(uuid.uuid4())
        with open(filename, "w", encoding='utf-8') as file:
            file.write( json.dumps( self.serialize(), indent=4 ) )
            if printoutput:
                print("saving to", filename, "was successful.")
            if updateModified:
                self.has_been_modified = False
            self.filename = filename

    def addEdge(self, edge: XMARTeEdge):
        """Add :class:`~nodeeditor.node_edge.Edge` to this `Scene`

        :param edge: :class:`~nodeeditor.node_edge.Edge` to be added to this `Scene`
        :return: :class:`~nodeeditor.node_edge.Edge`
        """
        self.edges.append(edge)
        if edge.start_socket is not None and edge.end_socket is not None:
            self.has_been_modified = True

    def serialize(self) -> OrderedDict:
        ''' Include UUID in Serialisation '''
        additionals = OrderedDict(
            [
                ("version_uuid", self.version_uuid),
            ]
        )
        ser = super().serialize()
        ser.update(additionals)
        return ser

    def nodeClassSelectorFunction(self, data):
        ''' Use application's factory as node classifier '''
        return self.application.factories.create(data["type"])

    def deserialize( # pylint:disable=W1113, R0914, R0912
        self, data: dict, hashmap: dict = {}, restore_id: bool = True, *args, **kwargs
    ) -> bool:
        ''' Deserialise and override to include UUID '''
        prev = self.large_import
        self.large_import = True
        hashmap = {}

        if restore_id:
            self.id = data["id"]

        self.version_uuid = data["version_uuid"]
        # -- deserialize NODES

        ## Instead of recreating all the nodes, reuse existing ones...
        # get list of all current nodes:
        all_nodes = self.nodes.copy()

        # go through deserialized nodes:
        for node_data in data["nodes"]:
            # can we find this node in the scene?
            found = False
            for node in all_nodes:
                if node.id == node_data["id"]:
                    found = node
                    break

            if not found:
                try:
                    new_node_class = self.getNodeClassFromData(node_data)
                    new_node = new_node_class(self)
                    new_node.deserialize(
                        node_data, hashmap, restore_id, *args, **kwargs
                    )
                    new_node.onDeserialized(node_data)
                    self.onDeserialize(new_node)
                    # print("New node for", node_data['title'])
                except (KeyError, ValueError, AssertionError) as exc:
                    raise PluginException() from exc
            else:
                try:
                    found.deserialize(node_data, hashmap, restore_id, *args, **kwargs)
                    found.onDeserialized(node_data)
                    self.onDeserialize(found)
                    all_nodes.remove(found)
                    # print("Reused", node_data['title'])
                except (KeyError, ValueError, AssertionError) as exc:
                    raise PluginException() from exc

        # remove nodes which are left in the scene and were NOT in the serialized data!
        # that means they were not in the graph before...
        while all_nodes:
            node = all_nodes.pop()
            node.remove()

        # -- deserialize EDGES

        ## Instead of recreating all the edges, reuse existing ones...
        # get list of all current edges:
        all_edges = self.edges.copy()

        # go through deserialized edges:
        for edge_data in data["edges"]:
            # can we find this node in the scene?
            found = False
            for edge in all_edges:
                if edge.id == edge_data["id"]:
                    found = edge
                    break

            if not found:
                XMARTeEdge(self,edge_type=EDGE_TYPE_DEFAULT).deserialize(
                    edge_data, hashmap, restore_id, *args, **kwargs
                )
                # print("New edge for", edge_data)
            else:
                found.deserialize(edge_data, hashmap, restore_id, *args, **kwargs)
                all_edges.remove(found)

        # remove nodes which are left in the scene and were NOT in the serialized data!
        # that means they were not in the graph before...
        while all_edges:
            edge = all_edges.pop()
            edge.remove()

        # We should move the deserialisers to the end so that our hashmap is pre-defined
        for v in self.deserialisers.values():
            v(self, data, hashmap, restore_id, args, kwargs)

        self.large_import = prev
        return True

    # Search function using list comprehension
    def findInputById(self, objects, object_id):
        '''Find node input by id.'''
        return next(
            (
                input_obj for obj in objects
                for input_obj in obj.inputs
                if input_obj.id == object_id
            ),
            None
        )
