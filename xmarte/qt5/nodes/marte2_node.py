'''
The base definition of the main node of the GUI application which is what
is displayed in the scene.
'''

import copy
import re

from PyQt5.QtWidgets import QVBoxLayout

from qtpy.QtWidgets import (
    QMainWindow,
    QGridLayout,
    QLineEdit,
    QSizePolicy,
    QMessageBox,
    QWidget,
    QLabel,
)

from nodeeditor.node_socket import (
    LEFT_BOTTOM,
    LEFT_CENTER,
    LEFT_TOP,
    RIGHT_BOTTOM,
    RIGHT_CENTER,
    RIGHT_TOP,
)
from nodeeditor.node_scene import Scene

from martepy.functions.gam_functions import getAlias
from martepy.marte2.datasource import MARTe2DataSource

from xmarte.qt5.libraries.functions import fixSocketOrdering
from xmarte.qt5.nodes.node_graphics import BlockGraphicsNode, NodeContent
from xmarte.qt5.nodes.marte2_base import UniversalNodeFeatures

class MARTe2Node(UniversalNodeFeatures):
    '''
    The base definition of the main node of the GUI application which is what
    is displayed in the scene.
    '''
    GraphicsNode_class = BlockGraphicsNode
    NodeContent_class = NodeContent

    def __init__(
        self,
        scene: Scene = None,
        application: QMainWindow = None,
        plugin="marte2",
        btype="ConstantGAM",
        configuration_name="ConstantGAM",
        comment="",
        parameters=[],
        inputs=[],
        outputs=[],
        inputsb=[],
        outputsb=[],
        rank=False,
    ):
        """Each block should have:
        plugin - plugin that originally loaded this block
        type - equivalent to init_block.blocktype, the class of the block
        configuration_name - equivalent to init_block.label
        order_number - equivalent to row_number
        comment - comment, peripheral but rather unused at the moment
        parameters - we want to maintain the init_blocks way of defining an input type, but instead
        we make it more MARTe2 general parameters is still a dictionary of key_name, type, value, 
        options (If is selector type). The types available are:
            - Selector (ComboBox loaded with options)
            - Text
            - Float
        """

        self._modified_callbackListeners = []
        self.scene = scene
        prev = scene.large_import
        scene.large_import = True
        self.graph_adata = None
        self.graph_ddata = None
        self.graph = False
        self.plugin = plugin
        self.comment = comment
        self.parameters = parameters
        self.inputsb = inputsb
        self.outputsb = outputsb
        self.application = application
        self.rank = rank
        self.changed = False
        self.number_name = "order"
        self._before = {}
        super().__init__(scene, inputs, outputs)
        self.btype = btype
        self.configuration_name = configuration_name
        # it's really important to mark all nodes Dirty by default
        self.markDirty()
        GraphicsNode_class = BlockGraphicsNode(self)
        GraphicsNode_class.title = self.title
        GraphicsNode_class.adjustLabelSizes()
        self.content.updateDim()
        scene.large_import = prev

    def deleteAllListener(self):
        '''
        Action to delete all listeners
        '''
        self._modified_callbackListeners = []

    def addModifiedListener(self, func):
        '''
        Action to add a listener for modifications
        '''
        self._modified_callbackListeners.append(func)

    def delete(self):
        '''
        Delete this node and make sure we close any open config bars
        '''
        self.remove()
        if self.application.rightpanel.parameterbar.node == self:
            self.resetParameterbar()

    def remove(self):
        ''' We want to allow services to override this function to action something
        when a node is about to be removed
        '''
        if hasattr(self.scene, 'nodeRemovedListeners'):
            self.scene.nodeRemovedListeners(self)

        super().remove()

    def initSettings(self):
        '''
        Setup socket positions
        '''
        super().initSettings()
        self.input_socket_position = LEFT_CENTER
        self.output_socket_position = RIGHT_CENTER

    def eval(self, index=0):
        '''
        Eval - required function definition of nodeeditor
        '''
        self.markDirty(False)
        self.markInvalid(False)
        # Later we may come up with a criterion we want to verify heres
        return 1

    def initSockets(self, inputs: list, outputs: list, reset: bool=True):
        super().initSockets(inputs, outputs, reset)
        if self.grNode:
            self.content.updateDim()

    def getSocketPosition(
        self, index: int, position: int, num_out_of: int = 1
    ):
        """
        Get the relative `x, y` position of a :class:`~nodeeditor.node_socket.Socket`. This is used
        for placing the `Graphics Sockets` on `Graphics Node`.

        :param index: Order number of the Socket. (0, 1, 2, ...)
        :type index: ``int``
        :param position: `Socket Position Constant` describing where the Socket is located.
        See :ref:`socket-position-constants`
        :type position: ``int``
        :param num_out_of: Total number of Sockets on this `Socket Position`
        :type num_out_of: ``int``
        :return: Position of described Socket on the `Node`
        :rtype: ``x, y``
        """
        x = (
            self.socket_offsets[position]
            if (position in (LEFT_TOP, LEFT_CENTER, LEFT_BOTTOM))
            else self.grNode.width + self.socket_offsets[position]
        )

        if position in (LEFT_BOTTOM, RIGHT_BOTTOM):
            # start from bottom
            y = (
                self.grNode.height
                - self.grNode.edge_roundness
                - self.grNode.title_vertical_padding
                - index * self.socket_spacing
            )
        elif position in (LEFT_CENTER, RIGHT_CENTER):
            num_sockets = num_out_of
            node_height = self.grNode.height
            top_offset = (
                self.grNode.title_height
                + 2 * self.grNode.title_vertical_padding
                + self.grNode.edge_padding
            )
            available_height = node_height - top_offset

            # y = top_offset + index * self.socket_spacing + new_top / 2
            y = (
                top_offset
                + available_height / 2.0
                + (index - 0.5) * self.socket_spacing
            )
            if num_sockets > 1:
                y -= self.socket_spacing * (num_sockets - 1) / 2

        elif position in (LEFT_TOP, RIGHT_TOP):
            # start from top
            y = (
                self.grNode.title_height
                + self.grNode.title_vertical_padding
                + self.grNode.edge_roundness
                + index * self.socket_spacing
            )
        else:
            # this should never happen
            y = 0

        return [x, y]

    def onInputChanged(self, socket=None):
        '''
        Update the socket labels to match.
        '''
        try:
            our_socket_index = next(index for index, a in enumerate(self.inputs) if a == socket)
            if not socket.edges:
                return
            node_from = socket.edges[-1].start_socket.node
            start_socket_idx = next(index for index, a in enumerate(node_from.outputs) if
                                      a == socket.edges[-1].start_socket)

            if isinstance(self.application.API.toGAM(self), MARTe2DataSource):
                # If my signal is already connected to another datasource - do not allow and
                # end edge writing put in error message about this - cannot connect signal
                # to two different datasources!
                numedges = len(node_from.outputs[start_socket_idx].edges)
                if numedges > 1 and not node_from.outputsb[start_socket_idx][1][
                    'MARTeConfig']['DataSource'] == self.configuration_name.strip('+'):
                    socket.edges[0].remove()
            # update last connected edge label
            fixSocketOrdering(node_from)
            # index = socket.edges[-1].start_socket.index # Dont trust indexes
            new_cfg = copy.deepcopy(node_from.outputsb[start_socket_idx][1]['MARTeConfig'])
            # Set Alias as input name
            # If actual signal name already taken - generate unique name
            if 'Default' in list(new_cfg.keys()):
                del new_cfg['Default']
            new_cfg['Alias'] = getAlias(node_from.outputsb[start_socket_idx])

            new_tuple = (self.inputsb[our_socket_index][0], {'MARTeConfig': new_cfg})
            self.inputsb[our_socket_index] = new_tuple

            # Am I a datasource?
            if isinstance(self.application.API.toGAM(self), MARTe2DataSource):
                # Change the input signal DDB to my datasource name
                node_from.outputsb[start_socket_idx][1][
                    'MARTeConfig']['DataSource'] = self.configuration_name.strip('+')
            # Is my input a datasource?
            # Set the inputs DDB to the datasource name
            if isinstance(self.application.API.toGAM(node_from), MARTe2DataSource):
                self.inputsb[our_socket_index][1][
                    'MARTeConfig']['DataSource'] = node_from.configuration_name.strip('+')
                attr = list(node_from.outputsb[start_socket_idx][1]['MARTeConfig'].keys())
                if 'Frequency' in attr:
                    self.inputsb[our_socket_index][1][
                        'MARTeConfig']['Frequency'] = node_from.outputsb[start_socket_idx][1][
                            'MARTeConfig']['Frequency']

        except (AttributeError, ValueError):
            pass

    def modifiedListenerFunction(self):
        '''
        We've been modified - trigger the callback listeners
        '''
        for function in self._modified_callbackListeners:
            function(self)  # Function must take argument of our actual node itself.

    def resetParameterbar(self):
        '''
        Remove the parameter bar if it exists
        '''
        mainpanel = self.application.rightpanel
        if hasattr(mainpanel, "parameterbar"):
            if mainpanel.parameterbar is not None:
                mainpanel.vlayout.removeWidget(mainpanel.parameterbar)
                mainpanel.parameterbar = None
                if self.changed:
                    self.scene.has_been_modified = True
                self.changed = False
        return mainpanel

    def onDoubleClicked(self, event):
        '''
        onDoubleClicked - show config bar
        '''
        mainpanel = self.resetParameterbar()

        mainpanel.parameterbar = QWidget(self.application)
        mainpanel.parameterbar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        mainpanel.parameterbar.node = self
        mainpanel.outer_con = QWidget(mainpanel.parameterbar)

        mainpanel.outer_layout = QVBoxLayout()
        mainpanel.parameterbar.setLayout(mainpanel.outer_layout)

        mainpanel.configHolder = QWidget(mainpanel.outer_con)
        mainpanel.configbarBox = QGridLayout()
        mainpanel.configHolder.setLayout(mainpanel.configbarBox)

        mainpanel.outer_layout.addWidget(mainpanel.configHolder)
        # self.display.configbarBox = QToolBar(self.display)
        label = QLabel("Label:")
        mainpanel.parameterbar.labelinput = QLineEdit(mainpanel)
        mainpanel.parameterbar.labelinput.setText(self.configuration_name)
        mainpanel.parameterbar.labelinput.resize(280, 80)
        mainpanel.parameterbar.labelinput.editingFinished.connect(self.labelchange)
        mainpanel.configbarBox.addWidget(label, 0, 0)
        mainpanel.configbarBox.addWidget(mainpanel.parameterbar.labelinput, 0, 1)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        mainpanel.configbarBox.addWidget(spacer, 0, 2)

        self._before["label"] = self.configuration_name

        self.setupParameters()

        mainpanel.vlayout.addWidget(mainpanel.parameterbar)

    def setupParameters(self):
        '''
        Assume the parameter bar exists, populate this based on our nodes
        variables.
        '''
        # parameter example [{'name':'JETEnabled','type':'selector',
        #                     'value':'No','options':['Yes','No']}]

        # New method, find the node's class and call it's loadParameters function
        mainpanel = self.application.rightpanel

        self.application.factories[self.plugin].create(self.btype).loadParameters(mainpanel,self)

    def labelchange(self):
        '''
        Action the user changing the label of a node (configuration_name)
        '''
        node = self.application.rightpanel.parameterbar.node
        if re.match(
            "^[A-Za-z0-9_-]+$",
            node.application.rightpanel.parameterbar.labelinput.text(),
        ):
            node.configuration_name = (
                node.application.rightpanel.parameterbar.labelinput.text()
            )
            node.title = (
                (node.application.rightpanel.parameterbar.labelinput.text())
                + " ("
                + node.btype
                + ")"
            )
            node.grNode.title = node.title
            node.grNode.update()
            node.grNode.adjustTitleSize()
            node.updateSocketPositions()
        else:
            node.application.rightpanel.parameterbar.labelinput.setText(
                node.configuration_name
            )
            _ = QMessageBox.warning(
                None,
                'Illegal label name',
                'Label names may only contain lower and upper case characters, '
                'numbers, underscores, and dashes.',
            )
        if isinstance(self.application.API.toGAM(node), MARTe2DataSource):
            # Change my outputs definitions
            for output in node.outputsb:
                output[1]['MARTeConfig']['DataSource'] = node.configuration_name

    def onDeserialized(self, data: dict):
        """Event manually called when this node was deserialized. Currently called when node is 
        deserialized from scene passing `data` containing the data which have been deserialized"""
        self.updateSocketPositions()

    def __eq__(self, other):
        '''
        Override whether instances are the same (avoid id being the specifying criteria)
        '''
        if isinstance(other, self.__class__):
            res1 = other.serialize()
            res2 = self.serialize()
            return (
                res1["title"] == res2["title"]
                and res1["parameters"] == res2["parameters"]
                and res1["configuration_name"] == res2["configuration_name"]
                and res1["type"] == res2["type"]
                and res1["inputsb"] == res2["inputsb"]
                and res1["outputsb"] == res2["outputsb"]
            )
        return False

    def serialize(self):
        '''
        Serialise our node
        '''
        self.scene.large_import = True
        self.id = id(self)
        self.scene.large_import = False
        res = super().serialize()
        res["plugin"] = self.plugin
        res["class_name"] = self.btype
        res["configuration_name"] = self.configuration_name
        res["comment"] = self.comment
        res["parameters"] = self.parameters
        res["inputsb"] = self.inputsb
        res["outputsb"] = self.outputsb
        res['outputs_identities'] = {
            a.socket_type: [str(b.end_socket.node.configuration_name)
                for b in a.edges
                if b.end_socket is not None
            ] for a in self.outputs
        }
        res['input_identities'] = {
            a.index: [str(b.start_socket.node.configuration_name)
                for b in a.edges
                if b.end_socket is not None
            ] for a in self.inputs
        }
        res["type"] = "MARTe2Node"
        res['scene_name'] = self.scene.scene_name
        if hasattr(self, "lookup_table"):
            res["lookup_table"] = self.lookup_table
        return res

    def deserialize(self, data, hashmap={}, restore_id=True, *args, **kwargs): # pylint: disable=W1113
        '''
        Deserialise our node
        '''
        self.application = self.scene.application
        res = super().deserialize(data, hashmap, restore_id)
        self.plugin = data["plugin"]
        # Attempting to remove below as causing dependency and coupling with the service.
        #try:
        #    service = next(
        #        a for a in self.application.services if a.service_name == self.plugin
        #    )
        #    service.prepareNode(self)
        #except (StopIteration, AttributeError):
        #    if not self.application.plugin_not_loaded:
        #        msg_box = QMessageBox()
        #        msg_box.setText(
        #            """ The plugin for this node is not loaded, unexpected behaviour will occur """
        #        )
        #        msg_box.exec()
        #        self.application.plugin_not_loaded = True
        self.btype = data["class_name"]
        self.configuration_name = data["configuration_name"]
        self.comment = data["comment"]
        self.parameters = data["parameters"]
        self.inputsb = data["inputsb"]
        self.outputsb = data["outputsb"]
        title = self.configuration_name + " (" + self.btype + ")"
        if self.grNode is not None:
            self.grNode.title = title
            self.grNode.update()
            self.grNode.adjustTitleSize()
            self.updateSocketPositions()
            self.content.updateDim()
        return res


def initialize(factory, plugin_datastore) -> None:
    '''
    Register our node in our factory
    '''
    factory.registerBlock("MARTe2Node", MARTe2Node, plugin_datastore)
