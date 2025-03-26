# -*- coding: utf-8 -*-
"""
A module containing ``NodeEditorWidget`` class
"""
from nodeeditor.node_editor_widget import NodeEditorWidget
from nodeeditor.utils import dumpException
from nodeeditor.node_scene import InvalidFile
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox, QApplication

class XMARTeNodeEditorWidget(NodeEditorWidget):
    def fileLoad(self, filename:str, *args, **kwargs):
        """Load serialized graph from JSON file

        :param filename: file to load
        :type filename: ``str``
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.scene.loadFromFile(filename, *args, **kwargs)
            self.filename = filename
            self.scene.history.clear()
            self.scene.history.storeInitialHistoryStamp()
            return True
        except FileNotFoundError as e:
            dumpException(e)
            QMessageBox.warning(self, "Error loading %s" % os.path.basename(filename), str(e).replace('[Errno 2]',''))
            return False
        except InvalidFile as e:
            dumpException(e)
            # QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "Error loading %s" % os.path.basename(filename), str(e))
            return False
        finally:
            QApplication.restoreOverrideCursor()