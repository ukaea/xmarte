''' A listbox widget for the user to modify GAM Datasources, specifically it extends
the listbox to include editting items inline '''
import copy
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QAbstractItemView,
                             QLineEdit,
                             QListWidgetItem,
                             QWidget,
                             QVBoxLayout,
                             QHBoxLayout,
                             QListWidget,
                             QPushButton,
                             QMessageBox)

from martepy.marte2.qt_functions import generateUniqueGamName


class GAMDataSourcesWgt(QWidget):
    ''' The overall widget layout which is the listbox, and an add and remove button '''
    def __init__(self):
        super().__init__()
        self.initUI()

    # App Def should connect to these and that's how we ensure that the app definition
    # is updated as needed during user interactions.
    gam_added = pyqtSignal(str)
    gam_removed = pyqtSignal(str)
    gam_modified = pyqtSignal(str, str) # oldvalue, newvalue

    def initUI(self):
        ''' Create our custom layout where we include the widgets '''
        layout = QVBoxLayout()

        # List box
        self.listbox = CustomListWidget()
        self.listbox.itemChanged.connect(self.modifiedItem)
        self.listbox.setSelectionMode(QAbstractItemView.SingleSelection)
        triggers = QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked
        self.listbox.setEditTriggers(triggers)
        self.listbox.setEnabled(True)
        layout.addWidget(self.listbox)

        # Add and remove buttons
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.addItem)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.removeItem)
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def modifiedItem(self, item):
        ''' Track if an item was modified and emit a signal to have it updated in app_def '''
        if hasattr(item, 'oldname'):
            self.gam_modified.emit(copy.copy(item.oldname), item.text())

        item.oldname = item.text()

    def addItem(self):
        ''' Add a new GAM based on user clicking add button '''
        existing = [self.listbox.item(i).text() for i in range(self.listbox.count())]
        name = generateUniqueGamName(existing)
        item = QListWidgetItem(name)
        item.oldname = name
        self.listbox.addItem(item)
        self.gam_added.emit(name)
        for index in range(self.listbox.count()):
            item = self.listbox.item(index)
            flags = item.flags() | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
            item.setFlags(flags)

    def removeItem(self):
        ''' remove the current selected GAM based on user clicking remove button '''
        selected_items = self.listbox.selectedItems()
        if selected_items:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Confirmation")
            msg_box.setText("Are you sure you want to delete the selected item(s)?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            if msg_box.exec() == QMessageBox.Yes:
                for item in selected_items:
                    self.listbox.takeItem(self.listbox.row(item))
                    self.gam_removed.emit(item.text())


class CustomListWidget(QListWidget):
    ''' The listbox widget which extends to inline editting by the user for items '''
    def __init__(self, parent=None):
        super().__init__(parent)

    def edit(self, index, trigger, event):
        ''' Capture the edit event and allow the user to modify as a QLineEdit that item '''
        # Call the base class edit method
        super().edit(index, trigger, event)
        if trigger == 0:
            return super().edit(index, trigger, event)


        # Get the line edit widget
        editor = self.findChild(QLineEdit)

        # Adjust the size of the line edit widget based on the text
        if editor and trigger == QAbstractItemView.DoubleClicked:
            margins = self.parent().contentsMargins()

            # Extract the width of the left and right margins
            left_margin_width = margins.left()
            right_margin_width = margins.right()

            # Total width of the content margins
            total_margin_width = left_margin_width + right_margin_width
            # Add extra width for padding
            editor.setMinimumWidth(self.parent().width()-total_margin_width)
            editor.setMinimumHeight(editor.sizeHint().height() + 2)
        return True
