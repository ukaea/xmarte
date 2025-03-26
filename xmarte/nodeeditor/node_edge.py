# -*- coding: utf-8 -*-
"""
A module containing NodeEditor's class for representing Edge and Edge Type Constants.
"""
from nodeeditor.node_edge import Edge

from xmarte.nodeeditor.node_graphics_edge import XMARTeQDMGraphicsEdge

class XMARTeEdge(Edge):

    def createEdgeClassInstance(self):
        """
        Create instance of grEdge class
        :return: Instance of `grEdge` class representing the Graphics Edge in the grScene
        """
        self.grEdge = self.getGraphicsEdgeClass()(self)
        self.scene.grScene.addItem(self.grEdge)
        if self.start_socket is not None:
            self.updatePositions()
        return self.grEdge

    def getGraphicsEdgeClass(self):
        """Returns the class representing Graphics Edge"""
        return XMARTeQDMGraphicsEdge
    
    def deserialize(self, data:dict, hashmap:dict={}, restore_id:bool=True, *args, **kwargs) -> bool:
        if restore_id: self.id = data['id']
        if data['start'] is not None:
            self.start_socket = hashmap[data['start']]
            self.end_socket = hashmap[data['end']]
        self.edge_type = data['edge_type']