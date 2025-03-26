'''
The left panel which contains all the blocks available to the test engine
'''

from functools import partial
from PyQt5.QtWidgets import (
    QGridLayout,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QGroupBox,
    QTabWidget,
    QLabel,
    QComboBox,
    QLineEdit,
)

from martepy.marte2.gams.constant_gam import ConstantGAM
from martepy.marte2.datasources import FileReader
from martepy.marte2.gams.iogam import IOGAM

class TestPanelWidget(QWidget):
    '''
    The widget itself for the blocks available to the test engine
    '''
    def __init__(self, parent=None, scene=None, application=None):
        self.subbuttons = []
        super().__init__(parent)
        self.parent = parent
        self.scene = scene
        self.application = application
        # Lets adjust and have a main widget which holds our tab control and
        self.tab_wgt = QTabWidget(self)
        self.setObjectName("TestPanelWidget")
        self.toolbox_wgt = QWidget()
        self.toolboxes = QVBoxLayout()
        self.toolbox_wgt.setLayout(self.toolboxes)
        self.tab_wgt.addTab(self.toolbox_wgt, "Functions")
        self.test_panel = QWidget()
        self.test_panel.setObjectName("TestPanel")
        self.populateTestPanel(self.test_panel)
        self.tab_wgt.addTab(self.test_panel, "Test Properties")

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.toolboxes.addWidget(spacer)
        self.layout_i = QVBoxLayout()
        self.layout_i.addWidget(self.tab_wgt)
        self.setLayout(self.layout_i)

        self.loadNodes()

    def populateTestPanel(self, widget):
        '''Create QtWidgets and populate them for the config settings panel.'''
        panel_layout = QVBoxLayout()
        widget.setLayout(panel_layout)
        config_grp = QGroupBox("Test Configuration Settings")

        v_layout = QVBoxLayout()
        solver_lbl = QLabel("Solver:")
        self.solver_edt = QComboBox()
        self.solver_edt.addItems(['MARTe2'])
        self.solver_edt.setCurrentText(self.application.settings['TestPanel']['solver'])

        v_layout.addWidget(solver_lbl)
        v_layout.addWidget(self.solver_edt)

        mcycles_lbl = QLabel("Max Cycles:")
        self.mcycles_edt = QLineEdit(self.application.settings['TestPanel']['Max Cycles'])

        v_layout.addWidget(mcycles_lbl)
        v_layout.addWidget(self.mcycles_edt)

        rate_lbl = QLabel("Execution Rate (Hz):")
        self.rate_edt = QLineEdit(self.application.settings['TestPanel']['Execution Rate (Hz)'])

        v_layout.addWidget(rate_lbl)
        v_layout.addWidget(self.rate_edt)

        config_grp.setLayout(v_layout)
        panel_layout.addWidget(config_grp)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        panel_layout.addWidget(spacer)

    def loadNodes(self):
        '''
        Load our toolbox of blocks we provide in the test engine
        '''
        row = 0
        column = 0
        posbl_inputs = QGroupBox("Available inputs")
        self.toolboxes.insertWidget(0,posbl_inputs)
        posbl_inputs.gbox = QGridLayout()
        posbl_inputs.setLayout(posbl_inputs.gbox)

        blocks = [ConstantGAM, FileReader, IOGAM]
        for block in list(blocks):
            block_action = QPushButton(block.__name__)
            block_action.clicked.connect(partial(self.addBlock, block))
            posbl_inputs.gbox.addWidget(block_action, row, column)
            block_action.show()
            if column == 2:
                row = row + 1
                column = 0
            else:
                column = column + 1
        # fill out grid
        if column != 2:
            for i in range((2 - column)):
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
                posbl_inputs.gbox.addWidget(spacer, row, column + i)

    def addBlock(self, block_cls):
        '''
        Add a requested block and override it's input changed listener
        '''
        block = block_cls()
        node = self.application.API.toNode(block, self.parent.scene)
        node.application = self.parent
