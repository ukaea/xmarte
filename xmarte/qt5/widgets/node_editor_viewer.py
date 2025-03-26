'''
Our application specific definitions for the ViewPort Editor instance and Scene instances.
'''

from nodeeditor.node_scene_history import SceneHistory
from nodeeditor.node_scene_clipboard import SceneClipboard
from qtpy.QtWidgets import QGraphicsView
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from xmarte.qt5.nodes.marte2_base import UniversalNodeFeatures
from xmarte.nodeeditor.node_graphics_node import XMARTeQDMGraphicsNode
from xmarte.nodeeditor.node_scene import XMARTeScene
from xmarte.nodeeditor.node_editor_widget import XMARTeNodeEditorWidget
from xmarte.nodeeditor.node_graphics_view import XMARTeQDMGraphicsView

class NodeEditorWidgetViewer(XMARTeNodeEditorWidget):
    '''
    The Viewer Editor Instance
    '''
    def __init__(self, parent: QWidget = None):
        self.application = parent
        super().__init__()

    def initUI(self):
        """Set up this ``NodeEditorWidget`` with its layout, 
        :class:`~nodeeditor.node_scene.Scene` and
        :class:`~nodeeditor.node_graphics_view.QDMGraphicsView`"""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # crate graphics scene
        self.scene = ViewerScene(self.application)

        # create graphics view
        self.view = ViewerView(self.scene.grScene, self)
        self.layout.addWidget(self.view)


class ViewerScene(XMARTeScene):
    '''
    The initial abstract Scene instance used by the application.
    '''
    def __init__(self, application):
        """
        :Instance Attributes:

            - **nodes** - list of `Nodes` in this `Scene`
            - **edges** - list of `Edges` in this `Scene`
            - **history** - Instance of :class:`~nodeeditor.node_scene_history.SceneHistory`
            - **clipboard** - Instance of :class:`~nodeeditor.node_scene_clipboard.SceneClipboard`
            - **scene_width** - width of this `Scene` in pixels
            - **scene_height** - height of this `Scene` in pixels
        """
        self.scene_name = ''
        super().__init__()
        self.real = True
        self.application = application
        self.nodes = []
        self.edges = []
        self.large_import = False
        # current filename assigned to this scene
        self.filename = None

        self.scene_width = 400
        self.scene_height = 400

        # custom flag used to suppress triggering onItemSelected which does a bunch of stuff
        self._silent_selection_events = False

        self._has_been_modified = False
        self._last_selected_items = None

        # initialize all listeners
        self._has_been_modified_listeners = []
        self._item_selected_listeners = []
        self._items_deselected_listeners = []

        # here we can store callback for retrieving the class for Nodes
        self.node_class_selector = None

        self.initUI()
        self.history = SceneHistory(self)
        self.clipboard = SceneClipboard(self)

        self.grScene.itemSelected.connect(self.onItemSelected)
        self.grScene.itemsDeselected.connect(self.onItemsDeselected)

        self.deserialisers = {}
        self.serialisers = {}


class ViewerView(XMARTeQDMGraphicsView):
    '''
    The Viewer Instance
    '''
    def initUI(self):
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)


class SimpleBlockView(XMARTeQDMGraphicsNode):
    '''
    The overall graphical representation of the node
    '''

    def contextMenuEvent(self, event):
        ''' Context Menu Display '''

    def avoidOffscene(self, scene_x, scene_y):
        ''' Pass through '''
        return scene_x, scene_y

class ViewNode(UniversalNodeFeatures):
    ''' Basic Node Definition '''
    GraphicsNode_class = SimpleBlockView

    def __init__(self, scene, inputs, outputs, title):
        self._title = title
        super().__init__(scene, inputs, outputs)

    def onDoubleClicked(self, event):
        ''' Do Nothing just yet - overridable class '''

    @property
    def title(self):
        ''' Ensure our title conforms to the expected value '''
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
