''' The Node Picker widget available in the Graph Window '''
import copy
from functools import partial

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget,
                             QMenu,
                             QAction,
                             QHBoxLayout,
                             QVBoxLayout,
                             QSizePolicy,
                             QComboBox,
                             QGridLayout,
                             QPushButton)

from nodeeditor.node_edge import EDGE_TYPE_BEZIER

from xmarte.qt5.nodes.node_handler import NodeHandler
from xmarte.qt5.widgets.settings.panel import helpRedirect
from xmarte.qt5.services.data_handler.graph_window.data.data_node import DataNode
from xmarte.nodeeditor.node_edge import XMARTeEdge as Edge

class NodePicker(QWidget):
    '''The left panel node picker as one widget.'''
    def __init__(self, parent=None, app=None, editor=None, window=None):
        super().__init__(parent)
        self.app = app
        self.editor = editor
        self.output_data = None
        self.scenes = window.scenes # Pointer to our graph windows definition of scenes
        self.selectionlayout = QVBoxLayout()
        self.window = window
        link = 'https://marte21.gitpages.ccfe.ac.uk/xmarte/graphing_tool.html'
        help_box_layout = QHBoxLayout()
        help_button = QPushButton("?")
        def helpWrap():
            helpRedirect(link)
        help_button.clicked.connect(helpWrap)
        help_button.setMinimumSize(40, 15)
        help_box_layout.addStretch()
        help_box_layout.addWidget(help_button)
        self.selectionlayout.addLayout(help_box_layout)
        self.load_options = QComboBox()
        self.populateCombos(self.scenes)
        self.load_options.currentIndexChanged.connect(self.changeThread)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.selectionlayout.addWidget(self.load_options)

        self.selection = QWidget()
        self.selection.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.selection_options = QGridLayout()
        self.selection.setLayout(self.selection_options)

        self.selectionlayout.addWidget(self.selection)

        self.load_options.setCurrentIndex(1)

        self.setLayout(self.selectionlayout)

    def populateCombos(self, dictionary, indent=0) -> None:
        '''Populate the state and thread comboboxes.'''
        for key, value in dictionary.items():
            if isinstance(value, dict):
                item_text = " " * indent + key
                self.load_options.addItem(item_text)
                self.populateCombos(value, indent=indent+2)
            else:
                item_text = " " * (indent + 2) + key
                self.load_options.addItem(item_text)

    def changeThread(self, _):
        '''Change the current scene in the viewport according to the thread.'''
        self.load_options.currentIndexChanged.disconnect()

        # Now figure out what the key pairs were
        state, thread = self.resolveThread()

        self.loadSelections(state, thread)
        self.load_options.currentIndexChanged.connect(self.changeThread)

    def resolveThread(self):
        '''This function uses the combobox to figure out what thread and
        state are currently selected.'''
        selected_item_text = self.load_options.currentText()
        selected_item_idx = self.load_options.currentIndex()
        if selected_item_idx == -1:
            self.load_options.setCurrentIndex(0)
        indent = selected_item_text.count(" ")
        parent_key = None
        current_key = selected_item_text.strip()
        if indent > 0:
            # Find it's parent, traverse up the list until we find an item without an indent
            count = 1
            while True:
                parent_key = self.load_options.itemText(selected_item_idx - count)
                indent = parent_key.count(" ")
                if indent == 0:
                    break
                count = count + 1
        if not parent_key:
            self.load_options.setCurrentIndex(selected_item_idx + 1)
            parent_key, current_key = self.resolveThread()
        return parent_key, current_key

    def loadSelections(self, state, thread):
        '''Load nodes available based on user selection.'''
        i = 0
        j = 0
        # reset gridlayout
        while self.selection_options.count():
            widget = self.selection_options.takeAt(0).widget()
            self.selection_options.removeWidget(widget)
            widget.setParent(None)

        scene = self.scenes[state][thread]

        for node in NodeHandler.getNodes(scene, safe=False):
            button = QPushButton(self.selection)
            button.clicked.connect(self.addBlock)
            button.node = node
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(
                partial(self.buttonMenu, button)
            )
            button.setText(node.title)
            if i == 5:
                i = 0
                j = j + 1
            self.selection_options.addWidget(button, j, i)
            i = i + 1

    def buttonMenu(self, button, _):
        '''Shortcut menu.'''
        menu = QMenu()
        def getlatestPlotBtn():
            self.latestPlotButton(button)
        menu.addAction("Latest Plot", getlatestPlotBtn)
        sub = QMenu()
        sub.setTitle("Add to Plot")
        for i in self.rightlayout.history:
            unique = QAction("&" + str(copy.copy(i.chart().title())), self)
            unique.triggered.connect(
                partial(self.subMenuButton, button, str(copy.copy(i.chart().title())))
            )
            sub.addAction(unique)
        def submenuBtn():
            return self.subMenuButton(button, "New...")
        sub.addAction("New...", submenuBtn)
        menu.addMenu(sub)
        menu.exec_(QtGui.QCursor.pos())

    def latestPlotButton(self, button):
        ''' Show latest plot '''
        node = self.addSimBlock(button)
        # Get input to PlotNode
        self.plotnode(node, self.rightlayout.history[-1].chart().title())


    def plotnode(self, node, title):
        ''' Setup plot node'''
        plotinput = next(
            a for a in self.rightlayout.plotnode.inputs if a.label == title
        )
        for out in node.outputs:
            Edge(self.editor.scene, out, plotinput, edge_type=EDGE_TYPE_BEZIER)
            self.rightlayout.plotnode.onInputChanged(plotinput)
        # Update all graphically
        self.rightlayout.plotnode.updateSocketPositions()
        for inputs in self.rightlayout.plotnode.inputs:
            for edge in inputs.edges:
                edge.updatePositions()
        self.rightlayout.plotnode.updateHeight()

    def subMenuButton(self, button, chart_title):
        ''' Add a node '''
        if button.jpn:
            node = self.addJpnBlock(button)
        else:
            node = self.addSimBlock(button)
        if chart_title == "New...":
            self.plotnode(node, "...")
        else:
            self.plotnode(node, chart_title)

    def addBlock(self, _):
        ''' Handle new simulation block '''
        sending_button = self.sender()
        self.addSimBlock(sending_button)

    def addSimBlock(self, sending_button):
        ''' Add simulation Block '''
        node = sending_button.node
        # Sanity check our data attribute under each output
        for a in node.outputs:
            if hasattr(a, 'data'):
                if a.data is not None:
                    if isinstance(a.data, list):
                        if len(a.data) == 0:
                            a.data = None
                    else:
                        a.data = None
            else:
                a.data = None

        outputs = [(a.socket_type, a.label, a.data) for a in node.outputs]
        datanode = DataNode(
            self.editor.scene,
            node.title,
            [],
            outputs,
            node,
            "Simulation",
        )
        return datanode
