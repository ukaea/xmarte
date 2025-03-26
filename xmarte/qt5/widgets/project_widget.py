'''
The left panel which contains all the blocks available to the application
'''

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QTabWidget,
)

class ProjectWidget(QWidget):
    '''
    The widget itself for the blocks available to the application
    '''
    def __init__(self, parent=None):
        self.subbuttons = []
        super().__init__(parent)
        self.parent = parent
        # Lets adjust and have a main widget which holds our tab control and
        self.tab_wgt = QTabWidget(self)
        self.setObjectName("ProjectWidget")
        self.toolbox_wgt = QWidget()
        self.toolboxes = QVBoxLayout()
        self.toolbox_wgt.setLayout(self.toolboxes)
        self.tab_wgt.addTab(self.toolbox_wgt, "Functions")

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.toolboxes.addWidget(spacer)
        self.layout_i = QVBoxLayout()
        self.layout_i.addWidget(self.tab_wgt)
        self.setLayout(self.layout_i)
