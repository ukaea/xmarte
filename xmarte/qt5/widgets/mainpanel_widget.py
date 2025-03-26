'''
The main panel widget which comprises of our split view and node editor
'''
from PyQt5.QtWidgets import QWidget, QSplitter
from PyQt5.QtCore import Qt, QEvent

# Using nodeeditor from https://gitlab.com/pavel.krupala/pyqt-node-editor
from nodeeditor.node_edge_validators import (
    edge_cannot_connect_input_and_output_of_different_type,
    edge_cannot_connect_two_outputs_or_two_inputs
)

from qtpy.QtWidgets import QVBoxLayout

from xmarte.nodeeditor.node_edge_validators import edge_start_socket_must_exist
from xmarte.nodeeditor.node_edge import XMARTeEdge

XMARTeEdge.registerEdgeValidator(edge_cannot_connect_input_and_output_of_different_type)
XMARTeEdge.registerEdgeValidator(edge_cannot_connect_two_outputs_or_two_inputs)
XMARTeEdge.registerEdgeValidator(edge_start_socket_must_exist)

class MainPanelWidget(QWidget):
    '''
    The widget
    '''

    def __init__(self, parent=None, nodeeditor=None):
        super().__init__(parent)
        self._selected_listeners = []
        self._deselected_listeners = []
        self.parent = parent
        self.vlayout = QVBoxLayout()
        # Widget two is a container box for our parameters - need to decide on best layout for this
        self.setLayout(self.vlayout)
        self.nodeeditor = nodeeditor

        view = self.nodeeditor.view
        view.centerOn(
            float(self.nodeeditor.scene.scene_width / 2),
            float(self.nodeeditor.scene.scene_height / 2),
        )
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.nodeeditor)
        self.vlayout.addWidget(self.splitter)
        self.parent.scene.addItemsDeselectedListener(self.deselected)
        self.parent.scene.addModifiedListener(self.splitlistener)
        self.parameterbar = None
        self.split_size = [150, 150]
        self.split = None
        self.changingSubNode = False
        self.recovery_document = parent.settings["hidden"]["recovery_document"]

    def addSelectedListener(self, func):
        ''' Detect when a node is selected '''
        self._selected_listeners.append(func)

    def clearSelectedListeners(self):
        ''' clear the selected listeners '''
        self._selected_listeners = []

    def addDeselectedListener(self, func):
        ''' Add a deselected listener for when nodes are unselected '''
        self._deselected_listeners.append(func)

    def clearDeselectedListeners(self):
        ''' clear the deselect listeners '''
        self._deselected_listeners = []

    def eventFilter(self, source, event):
        ''' Capture resize events for the split view '''
        if event.type() == QEvent.Resize and source == self.scrollArea:
            newsize = (
                self.splitter.sizes()[1] - self.scrollArea.verticalScrollBar().width()
            )
            if newsize > 0:
                # self.split.setFixedHeight(sizes-15)
                self.split.setFixedWidth(self.splitter.sizes()[1] - 10)
        return super().eventFilter(source, event)

    def splitlistener(self, _):
        ''' Toggle split view and parameter bar '''
        if self.split is not None:
            # Send split signal to trigger
            self.split.updateSplit()
            if "Inittext" in str(self.split):
                self.split.setFixedHeight(
                    self.split.calcHeight()
                )
            self.split.update()
        if hasattr(self, "parameterbar"):
            if self.parameterbar is not None:
                if self.parameterbar.node not in self.parent.scene.nodes:
                    # Node has been deleted
                    self.deselected()

    def deselected(self):
        '''
        On deselected
        Remove the parameter bar if it exists
        '''
        if hasattr(self, "parameterbar"):
            if self.parameterbar is not None:
                oldheight = self.height()
                self.parameterbar.deleteLater()
                self.parameterbar = None
                self.parent.scene.has_been_modified = True
                self.nodeeditor.setMaximumHeight(oldheight)
                if self.parent.rightpanel.split:
                    self.scrollArea.setMaximumHeight(oldheight)
        self.update()

    def setupListener(self, scene):
        ''' Setup the listener for a given scene'''
        scene.addModifiedListener(self.splitlistener)
