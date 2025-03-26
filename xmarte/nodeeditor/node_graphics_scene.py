
from nodeeditor.node_graphics_scene import QDMGraphicsScene

class XMARTeQDMGraphicsScene(QDMGraphicsScene):
        def setGrScene(self, width: int, height: int):
            """Set `width` and `height` of the `Graphics Scene`"""
            self.setSceneRect(0, 0, width, height)