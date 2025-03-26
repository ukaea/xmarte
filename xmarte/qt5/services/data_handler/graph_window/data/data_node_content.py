''' The content aspect of our data nodes - shows the parameters of the node configuration '''
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton

from xmarte.qt5.nodes.node_graphics import NodeContent


class DataNodeContent(NodeContent):
    '''
    The Data Nodes content (allows us to display the parameters for this node configuration)
    '''
    def __init__(self, node, parent = None):
        self.layout = QVBoxLayout()
        self.origin = None
        self.para = None
        self.expand = None
        super().__init__(node=node, parent=parent)
        self.setLayout(self.layout)
        self.display_para = True

    def initUI(self):
        ''' Setup UI '''
        for child in self.children():
            if not isinstance(child, QVBoxLayout):
                child.setParent(None)
                child.deleteLater()
        # Okay start writing data about this node, parameters, configs etc... - later we'll
        # update the size of our node based on content in order to occupy all this and possibly
        # change text font size and font to clean things up
        self.origin = QLabel("Origin: " + self.node.origin)
        self.layout.addWidget(self.origin)
        self.showParameters()

    def showParameters(self):
        ''' Show our nodes parameter configuration '''
        self.para = QLabel("Parameters:")
        self.layout.addWidget(self.para)
        for name, value in self.node.node.parameters.items():
            if name != 'Class name':
                new_para = QLabel(
                    "    " + str(name) + ": " + str(value)
                )
                self.layout.addWidget(new_para)
        self.expand = QPushButton("...")
        self.expand.clicked.connect(self.toggleExpand)
        self.layout.addWidget(self.expand)

    def toggleExpand(self, _):
        ''' Expand our parameters in contents '''
        self.display_para = not self.display_para
        for child in self.children():
            if not isinstance(child, QVBoxLayout):
                child.setParent(None)
                child.deleteLater()
        if self.display_para:
            self.origin = QLabel("Origin: " + self.node.origin)
            self.layout.addWidget(self.origin)
            if len(self.node.node.parameters) > 0:
                self.showParameters()
        else:
            self.origin = QLabel("Origin: " + self.node.origin)
            self.layout.addWidget(self.origin)
            if len(self.node.node.parameters) > 0:
                self.expand = QPushButton("...")
                self.expand.clicked.connect(self.toggleExpand)
                self.layout.addWidget(self.expand)
        self.updateDim()
