'''
Toolbar Widget for the application
'''

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QToolBar,
    QWidget,
    QSizePolicy,
    QMessageBox,
    QAction,
)
from PyQt5 import QtCore, QtWidgets
from qtpy.QtCore import QRect, QRectF

from xmarte.qt5.widgets.base_menu import BaseFileMenu
from xmarte.qt5.nodes.node_graphics import BlockGraphicsNode
from xmarte.qt5.nodes.node_handler import NodeHandler
from xmarte.qt5.nodes.node_factory import Factory

factory = Factory()
factory.loadRemote()


class FileToolbarWidget(QToolBar, BaseFileMenu):
    '''
    File Toolbar Widget for the application
    '''

    def __init__(self, title=None, parent=None):
        QToolBar.__init__(self, title, parent)
        BaseFileMenu.__init__(self, parent)
        self.createFilemenu(self)

    def onEditToolbarResized(self, size):
        '''Slot to handle the resize signal from the EditToolbarWidget'''
        # Update the height of the FileToolbarWidget to match the size of the EditToolbarWidget
        self.setFixedHeight(size.height())


class EditToolbarWidget(QToolBar):
    '''
    Edit Toolbar Widget for the application
    '''

    resized = QtCore.pyqtSignal(QtCore.QSize)

    def __init__(self, title=None, parent=None):
        super().__init__(title, parent)
        self.parent = parent
        self.application = parent
        self.clearAction = QAction("&Clear", self)
        self.cleanAction = QAction("&Clean diagram", self)
        # self.subAction = QAction("&Make SubNode", self)
        self.cleanAction.triggered.connect(self.cleanDiagram)
        self.clearAction.triggered.connect(self.clear)
        # self.subAction.triggered.connect(self.makeSubNode)
        self.addAction(self.clearAction)
        self.addAction(self.cleanAction)
        self.current_file_handler = None
        # self.addAction(self.subAction)
        self.split = None
        QtCore.QTimer.singleShot(0, self.onTimeout)


        self.parent = parent
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer.setObjectName("MenuBarSpacer")

        self.addWidget(spacer)

        # Provide our services with their method of adding buttons
        self.service_buttons = QWidget()
        self.service_layout = QHBoxLayout()
        self.service_buttons.setLayout(self.service_layout)
        self.service_buttons.setObjectName('service_buttons')
        self.service_buttons.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.service_layout.setContentsMargins(0,0,0,0)
        self.addWidget(self.service_buttons)

    @QtCore.pyqtSlot()
    def onTimeout(self):
        '''Set the expand button to be invisible'''
        button = self.findChild(QtWidgets.QToolButton, "qt_toolbar_ext_button")
        if button is not None:
            button.setFixedSize(0, 0)

    def event(self, _):
        '''Override the event when mouse leaves the toolbar'''
        if _.type() == QtCore.QEvent.Leave:
            return True
        return super().event(_)

    def resizeEvent(self, event):
        '''rewrite the resize event to emit a signal with the current size'''
        self.resized.emit(event.size())
        return super().resizeEvent(event)

    def cleanDiagram(self): # pylint:disable=R0914
        """
        This function "cleans" the block diagram. That is to say that it arranges
        our nodes in a sensible fashion based on their linkage which subsequently
        demands their execution order.
        """
        self.parent.API.cleanDiagram(self.parent.scene, self.parent.editor.view)

    def clear(self):
        '''CLear the current design'''
        if len(self.parent.scene.nodes) > 0:
            ret = QMessageBox.question(
                self,
                "",
                "Are you sure you want to lose the current design?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if ret == QMessageBox.No:
                return
            self.parent.scene.clear()
            self.parent.scene.has_been_modified = False
            self.parent.editor.view.setScene(self.parent.scene.grScene)
