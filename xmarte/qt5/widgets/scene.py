'''
The Application Scene Component
'''

from martepy.marte2.generic_application import MARTe2Application

from xmarte.qt5.nodes.node_factory import Factory
from xmarte.qt5.widgets.base_scene import BaseScene

factory = Factory()
factory.loadRemote()


class EditorScene(BaseScene):
    '''
    The Application Scene Component
    '''

    def __init__(self, application, real=True, scene_name="marte2"):
        """
        :Instance Attributes:

            - **nodes** - list of `Nodes` in this `Scene`
            - **edges** - list of `Edges` in this `Scene`
            - **history** - Instance of :class:`~nodeeditor.node_scene_history.SceneHistory`
            - **clipboard** - Instance of :class:`~nodeeditor.node_scene_clipboard.SceneClipboard`
            - **scene_width** - width of this `Scene` in pixels
            - **scene_height** - height of this `Scene` in pixels
        """

        self.changingSubNode = False
        self.large_import = False
        self.application = MARTe2Application()

        super().__init__(application)
        self.scene_name = scene_name
        self.real = real
        self.setNodeClassSelector(self.nodeClassSelectorFunction)

        self.addItemsDeselectedListener(self.deselected)
        self.addItemSelectedListener(self.selected)
        if hasattr(self.application, "settings"):
            self.grScene.setGrScene(
                int(self.application.settings["gui"]["scene_width"]),
                int(self.application.settings["gui"]["scene_height"]),
            )
            self.scene_width = int(self.application.settings["gui"]["scene_width"])
            self.scene_height = int(self.application.settings["gui"]["scene_height"])

        self.grScene.setGrScene(self.scene_width, self.scene_height)

    def saveRecovery(self):
        ''' Save Recovery action '''
        # self.application.editor.fileSave(self.application.recovery_document)

    def nodeClassSelectorFunction(self, data):
        ''' Node Classifier using factory '''
        return factory.create(data["type"])

    def selected(self):
        ''' When selected '''
        selected_items = self.getSelectedItems()
        for item in selected_items:
            if hasattr(item, "node"):
                item.node.doSelect()

    def deselected(self):
        '''
        On deselected
        '''
        for node in self.nodes:
            node.grNode.upstream = False
            node.grNode.downstream = False

    def clear(self):
        """Override to allow plugins to put a callback in"""
        prev = self.large_import
        self.large_import = True
        for callback in self._clearListeners:
            callback(self)
        super().clear()
        self.large_import = prev
        self.has_been_modified = True

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
        ''' Has been modified setter '''
        # set it now, because we will be reading it soon
        self._has_been_modified = value
        if not self.large_import:
            if not self.changingSubNode and value:
                # call all registered listeners
                self.modifiedListeners()

        # self._has_been_modified = False
