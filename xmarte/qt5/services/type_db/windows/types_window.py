'''
This Window displays pre-defined types and allows the user to create/edit/delete types
'''
import os
import copy
import shutil
from functools import partial

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLineEdit, QAction

from PyQt5.QtWidgets import (QFileDialog,
                             QGroupBox,
                             QLabel,
                             QHeaderView,
                             QListWidgetItem,
                             QMessageBox,
                             QPushButton,
                             QSizePolicy,
                             QTableWidget,
                             QTableWidgetItem,
                             QWidget)

from martepy.marte2.type_database import TypeDBv2, Type, Field
from martepy.marte2.qt_classes import PanelledListConfig, AddRemoveHBtn
from martepy.marte2.qt_classes import AutoCompleteLineEdit
from martepy.marte2.qt_functions import deleteChildren, generateUniqueName
from martepy.functions.extra_functions import isint

from xmarte.qt5.libraries.functions import getUserFolder
from xmarte.qt5.widgets.close_save import QSaveClose
from xmarte.qt5.windows.base_window import ModalOptionsWindow

class TypesDBWindow(ModalOptionsWindow):
    '''
    The Types Database Window
    '''

    def __init__(self, application, app):
        super().__init__(application, app, 0.2,0.15,0.6,0.7)
        self.db = TypeDBv2()
        self.setWindowTitle("Type Database")
        self.type_edit = None
        self.version_lbl = None
        self.type_grp = None
        self.type_grp_layout = None
        self.table_wgt = None
        self.type_add_btns = None
        self.reset_btn = None
        self.save_btn = None

        self.type_db = os.path.join(getUserFolder(),"typedb")
        if not os.path.exists(self.type_db):
            os.mkdir(self.type_db)

        self.db.loadDb(self.type_db)
        self.main_pnl = PanelledListConfig(self)
        top_layout = self.main_pnl.v_layout
        self.setCentralWidget(self.main_pnl)

        # Connect auto populator for types
        self.main_pnl.left_list.currentItemChanged.connect(self.populateTypedef)
        self.add_rem_btn = AddRemoveHBtn()
        self.main_pnl.left_panel_vlayout.addWidget(self.add_rem_btn)
        self.add_rem_btn.add_btn.clicked.connect(self.addType)
        self.add_rem_btn.remove_btn.clicked.connect(self.remType)
        # Add save/close buttons here to top_layout
        btns_wgt = QSaveClose(self,"Save",self.updateDb,self.close)

        top_layout.addWidget(btns_wgt)

        # Now load our type definitions
        self.loadTypes()
        self.createContextMenu()

    def updateDb(self):
        ''' Update the DB and then refresh the GUI '''
        # Go through each type and save it
        self.db.updateDb(self.type_db)
        self.populateTypedef()

    def createContextMenu(self):
        ''' create the window menu '''
        context_menu = self.menuBar()

        file_menu = context_menu.addMenu("File")

        import_action = QAction("Import", self)
        export_action = QAction("Export", self)
        exit_action = QAction("Exit", self)

        import_action.triggered.connect(self.importTypes)
        export_action.triggered.connect(self.exportTypes)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(import_action)
        file_menu.addAction(export_action)
        file_menu.addAction(exit_action)

    def loadTypes(self):
        ''' Load our types into the left list '''
        try:
            self.main_pnl.left_list.currentItemChanged.disconnect()
        except TypeError:
            pass
        # First we need our type locations
        self.main_pnl.left_list.clear()

        for our_type in list(self.db.types.keys()):
            self.main_pnl.left_list.addItem(QListWidgetItem(our_type))

        self.main_pnl.left_list.setCurrentRow(0)
        first_item_key, _ = next((iter(self.db.types.items())), (None, None))
        if first_item_key:
            self.populateTypedef()
        self.main_pnl.left_list.currentItemChanged.connect(self.populateTypedef)

    def populateTypedef(self): # pylint:disable=R0915
        ''' Populate the type def area '''
        try:
            ref_type = self.main_pnl.left_list.currentItem().text()
        except AttributeError:
            ref_type = list(self.db.types.keys())[0]
            self.main_pnl.left_list.setCurrentRow(0)
        type_def = self.db.types[ref_type]
        deleteChildren(self.main_pnl.right_panel_vlayout)

        # Setup version label
        version_line = QWidget()
        version_layout = QHBoxLayout()
        version_line.setLayout(version_layout)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        type_lbl = QLabel("Type Name:")
        self.type_edit = QLineEdit()
        self.type_edit.setText(ref_type)
        version_layout.addWidget(type_lbl)
        version_layout.addWidget(self.type_edit)
        version_layout.addWidget(spacer)
        self.version_lbl = QLabel(f"Version: {type_def.version.replace('_','.')}")
        version_layout.addWidget(self.version_lbl)

        self.main_pnl.right_panel_vlayout.addWidget(version_line)

        # GroupBox

        self.type_grp = QGroupBox("Type Definition:")
        self.type_grp_layout = QVBoxLayout()
        self.type_grp.setLayout(self.type_grp_layout)
        self.main_pnl.right_panel_vlayout.addWidget(self.type_grp)

        self.table_wgt = QTableWidget()
        self.table_wgt.setRowCount(len(type_def.fields))
        self.table_wgt.setColumnCount(3)
        self.table_wgt.itemChanged.connect(self.onItemChanged)
        self.table_wgt.setHorizontalHeaderLabels(["Type Name", "Type", "Length"])
        self.table_wgt.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_wgt.setEditTriggers(QTableWidget.DoubleClicked)
        header = self.table_wgt.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        # Populate our types
        # Fundamental types
        type_options = ["uint8", "uint16", "uint32", "uint64",
                        "int8", "int16", "int32", "int64",
                        "float32", "float64"]
        # Now add our known types
        type_options += [a for a in list(self.db.types.keys()) if not ref_type]

        for row, field in enumerate(type_def.fields):
            self.table_wgt.setItem(row, 0, QTableWidgetItem(field.name))
            combo_box = AutoCompleteLineEdit(self, type_options, self.app)
            combo_box.editingFinished.connect(partial(self.typeChanged, row, combo_box))
            self.table_wgt.setCellWidget(row, 1, combo_box)
            combo_box.setText(field.type)

            self.table_wgt.setItem(row, 2, QTableWidgetItem(str(field.noelements)))

        # Now add a selector
        self.type_grp_layout.addWidget(self.table_wgt)

        # Now add a Add/Delete Button
        add_rem_btn = AddRemoveHBtn()
        self.type_add_btns = add_rem_btn
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.resetType)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.saveType)

        add_rem_btn.add_btn.clicked.connect(self.addField)
        add_rem_btn.remove_btn.clicked.connect(self.remField)

        add_rem_btn.hlayout.insertWidget(1, self.reset_btn)
        add_rem_btn.hlayout.insertWidget(2, self.save_btn)
        self.type_grp_layout.addWidget(add_rem_btn)

    def resetType(self):
        ''' Reset the type definition to what it is on file '''
        try:
            self.main_pnl.left_list.currentItemChanged.disconnect()
        except TypeError:
            pass
        # Reload
        # Get the types file from type
        try:
            ref_type = self.main_pnl.left_list.currentItem().text()
        except AttributeError:
            ref_type = list(self.db.types.keys())[0]
            self.main_pnl.left_list.setCurrentRow(0)
        type_def = self.db.types[ref_type]
        self.db.loadFile(type_def.file)
        self.populateTypedef()
        self.main_pnl.left_list.currentItemChanged.connect(self.populateTypedef)

    def typeChanged(self, row, item):
        ''' Update the types name in the left list '''
        try:
            ref_type = self.main_pnl.left_list.currentItem().text()
        except AttributeError:
            ref_type = list(self.db.types.keys())[0]
            self.main_pnl.left_list.setCurrentRow(0)
        type_def = self.db.types[ref_type]
        matching_field = type_def.fields[row]
        matching_field.type = item.text()

    def onItemChanged(self, item):
        ''' When the selected type in the left list changes, update the shown type '''
        row = item.row()
        column = item.column()
        # Now we know the column and row...
        try:
            ref_type = self.main_pnl.left_list.currentItem().text()
        except AttributeError:
            ref_type = list(self.db.types.keys())[0]
            self.main_pnl.left_list.setCurrentRow(0)
        type_def = self.db.types[ref_type]
        self.table_wgt.item(row, 0).text()
        matching_field = type_def.fields[row]
        if matching_field:
            if column == 0:
                matching_field.name = item.text()
            else:
                if not isint(item.text()):
                    item.setText(str(matching_field.noelements))
                    QMessageBox.information(self,
                                            'Length only supports integers',
                                            'You can only input integers as length',
                                            QMessageBox.Ok)
                matching_field.noelements = int(item.text())

    def closeEvent(self, event) -> None:
        ''' Check that our user has unsaved changes and prompt if okay? '''
        old_db = copy.deepcopy(self.db)
        self.db.loadDb(self.type_db)
        if old_db != self.db:
            reply = QMessageBox.question(
                self, 'Save Changes', "Do you want to save changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if reply == QMessageBox.Save:
                self.updateDb()
            elif reply == QMessageBox.Cancel:
                event.ignore()

    def importTypes(self):
        ''' Open a folder dialog for the user to select the import folder '''
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Import .h Files")

        if folder_path:
            # Get all .h files in the selected folder (non-recursively)
            for file_name in os.listdir(folder_path):
                if file_name.endswith('.h'):
                    src_file = os.path.join(folder_path, file_name)
                    dest_file = os.path.join(self.type_db, file_name)
                    shutil.copy2(src_file, dest_file)

    def exportTypes(self):
        ''' Open a folder dialog for the user to select the export folder '''
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Export .h Files")

        if folder_path:
            # Get all .h files in the type_db folder (non-recursively)
            for file_name in os.listdir(self.type_db):
                if file_name.endswith('.h'):
                    src_file = os.path.join(self.type_db, file_name)
                    dest_file = os.path.join(folder_path, file_name)
                    shutil.copy2(src_file, dest_file)

    def saveType(self):
        ''' Now we save the type '''
        try:
            ref_type = self.main_pnl.left_list.currentItem().text()
        except AttributeError:
            ref_type = list(self.db.types.keys())[0]
            self.main_pnl.left_list.setCurrentRow(0)

        self.db.saveTypeDef(self.type_db, ref_type, self.db.types[ref_type])

        self.populateTypedef()

    def addField(self):
        ''' Add a new field to our current type '''
        try:
            self.main_pnl.left_list.currentItemChanged.disconnect()
        except TypeError:
            pass
        try:
            ref_type = self.main_pnl.left_list.currentItem().text()
        except AttributeError:
            ref_type = list(self.db.types.keys())[0]
            self.main_pnl.left_list.setCurrentRow(0)
        row_position = self.table_wgt.rowCount()
        column_items = [self.table_wgt.item(a, 0).text() for a in range(self.table_wgt.rowCount())]
        new_name = generateUniqueName(column_items, 'new_field')
        new_field = Field(new_name, "uint32", "1")
        self.db.types[ref_type].fields += [new_field]
        self.table_wgt.insertRow(row_position)
        type_options = ["uint8", "uint16", "uint32", "uint64",
                        "int8", "int16", "int32", "int64",
                        "float32", "float64"]
        # Now add our known types
        type_options += [a for a in list(self.db.types.keys()) if not ref_type]
        combo_box = AutoCompleteLineEdit(self, type_options, self.app)
        # Adding sample data to the new row
        combo_box.setText('uint32')
        self.table_wgt.setItem(row_position, 0, QTableWidgetItem(new_name))
        self.table_wgt.setCellWidget(row_position, 1, combo_box)
        self.table_wgt.setItem(row_position, 2, QTableWidgetItem("1"))

        self.main_pnl.left_list.currentItemChanged.connect(self.populateTypedef)

    def addType(self):
        ''' Add a new type to the DB '''
        try:
            self.main_pnl.left_list.currentItemChanged.disconnect()
        except TypeError:
            pass
        name = generateUniqueName(list(self.db.types.keys()), 'new_packet')
        new_type = Type(name, file=os.path.join(self.type_db, f'{name}_1_0.h'))
        self.db.types[name] = new_type
        # Really we want to keep a version in
        # our code versus having to save immediately
        self.loadTypes()
        self.main_pnl.left_list.currentItemChanged.connect(self.populateTypedef)

    def remField(self):
        ''' Remove the selected field from the type '''
        try:
            self.main_pnl.left_list.currentItemChanged.disconnect()
        except TypeError:
            pass

        try:
            ref_type = self.main_pnl.left_list.currentItem().text()
        except AttributeError:
            ref_type = list(self.db.types.keys())[0]
            self.main_pnl.left_list.setCurrentRow(0)

        selected_rows = sorted(set(index.row() for index in self.table_wgt.selectedIndexes()),
                               reverse=True)
        for row in selected_rows:
            self.table_wgt.removeRow(row)
            self.db.types[ref_type].fields.pop(row)

        self.main_pnl.left_list.currentItemChanged.connect(self.populateTypedef)

    def remType(self):
        ''' Remove the current type from the DB '''
        try:
            self.main_pnl.left_list.currentItemChanged.disconnect()
        except TypeError:
            pass
        try:
            ref_type = self.main_pnl.left_list.currentItem().text()
        except AttributeError:
            ref_type = list(self.db.types.keys())[0]
            self.main_pnl.left_list.setCurrentRow(0)

        reply = QMessageBox.question(
                self, 'Delete', "Are you sure, this will delete the header file?",
                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Ok:

            if os.path.exists(self.db.types[ref_type].file):
                file_path = self.db.types[ref_type].file
                # Create the archive folder path
                archive_folder = os.path.join(os.path.dirname(file_path), "archive")

                # Ensure the archive folder exists
                os.makedirs(archive_folder, exist_ok=True)

                # Create the archived file path
                archived_file_path = os.path.join(archive_folder, os.path.basename(file_path))

                # Move the old version file to the archive folder
                shutil.move(file_path, archived_file_path)
            # Get the selected items
            selected_items = self.main_pnl.left_list.selectedItems()

            if not selected_items:
                return

            # Remove selected items
            for item in selected_items:
                self.main_pnl.left_list.takeItem(self.main_pnl.left_list.row(item))
            self.db.types.pop(ref_type, None)
        elif reply == QMessageBox.Cancel:
            return
        self.main_pnl.left_list.currentItemChanged.connect(self.populateTypedef)
