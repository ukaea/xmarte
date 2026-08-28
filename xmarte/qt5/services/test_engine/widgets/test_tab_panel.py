'''
The left panel which contains all the blocks available to the test engine
'''
import os
from functools import partial
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QGroupBox,
    QTabWidget,
    QLabel,
    QComboBox,
    QLineEdit,
    QFileDialog,
)

from martepy.marte2.gams.simulink_gam import SimulinkGAM
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
        self.lib_table = None
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
        self.library_panel = QWidget()
        self.library_panel.setLayout(self.createKeyValueTable())
        self.tab_wgt.addTab(self.library_panel, "Libraries")

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.toolboxes.addWidget(spacer)
        self.layout_i = QVBoxLayout()
        self.layout_i.addWidget(self.tab_wgt)
        self.setLayout(self.layout_i)

        self.loadNodes()

    def chooseFileForCell(self, row, column):
        """
        Open a file dialogue when the user double-cliks a cell in the
        'actual location' column.
        """
        if column != 1:
            return  # only open dialogue for column 2

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*)",
        )

        if file_path:
            self.lib_table.item(row, column).setText(file_path)

    def populateKeys(self, keys):
        """
        Populate the table with keys in the left-hand column.
        The key cells are read-only.
        """

        self.lib_table.setRowCount(len(keys))

        for row, key in enumerate(keys):
            key_item = QTableWidgetItem(os.path.basename(key))

            # Make the left-hand column read-only
            key_item.setFlags(
                key_item.flags() & ~Qt.ItemIsEditable
            )

            self.lib_table.setItem(row, 0, key_item)

            # Create an empty editable value cell
            value_item = QTableWidgetItem("")
            self.lib_table.setItem(row, 1, value_item)

    def createKeyValueTable(self):
        """
        Creates a 2-column table on the supplied tab.

        Column 0: read-only key
        Column 1: editable value

        Returns the QTableWidget.
        """

        layout = QVBoxLayout()

        self.lib_table = QTableWidget()
        self.lib_table.setColumnCount(2)
        self.lib_table.setHorizontalHeaderLabels(["Library", "Actual Location"])
        self.lib_table.horizontalHeader().setStretchLastSection(True)
        self.lib_table.cellClicked.connect(self.chooseFileForCell)

        layout.addWidget(self.lib_table)

        return layout

    def tableToDict(self):
        """
        Convert the table contents into:

            {
                left_column: right_column,
                ...
            }
        """

        result = {}

        for row in range(self.lib_table.rowCount()):

            key_item = self.lib_table.item(row, 0)
            value_item = self.lib_table.item(row, 1)

            if key_item is None:
                continue

            key = key_item.text()

            value = (
                value_item.text()
                if value_item is not None
                else ""
            )

            result[key] = value

        return result

    def applyDictToTable(self, key_map):
        """
        Apply a saved dictionary to the table.

        Existing rows are updated where their left-column key
        exists in key_map.

        Example:
            {
                "libA": "/path/to/libA.so",
                "libB": "/path/to/libB.so",
            }
        """

        for row in range(self.lib_table.rowCount()):

            key_item = self.lib_table.item(row, 0)

            if key_item is None:
                continue

            key = key_item.text()

            if key in key_map:
                value = key_map[key]

                value_item = self.lib_table.item(row, 1)

                if value_item is None:
                    value_item = QTableWidgetItem()
                    self.lib_table.setItem(row, 1, value_item)

                value_item.setText(str(value))

    def addMissingLibraries(self, library_names):
        """
        Append library names which are not already present
        in the first column of the table.

        New rows get an empty editable value in column 2.
        """

        existing_keys = set()

        for row in range(self.lib_table.rowCount()):
            item = self.lib_table.item(row, 0)

            if item is not None:
                existing_keys.add(item.text())

        for library_name in library_names:

            if library_name in existing_keys:
                continue

            row = self.lib_table.rowCount()
            self.lib_table.insertRow(row)

            key_item = QTableWidgetItem(library_name)
            value_item = QTableWidgetItem("")

            # Left column cannot be edited
            key_item.setFlags(
                key_item.flags() & ~Qt.ItemIsEditable
            )

            self.lib_table.setItem(row, 0, key_item)
            self.lib_table.setItem(row, 1, value_item)

            existing_keys.add(library_name)

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

        blocks = [ConstantGAM, FileReader, IOGAM, SimulinkGAM]
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
