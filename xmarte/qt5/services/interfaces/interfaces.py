'''
This service stores and provides UI to configure interfaces in the application.
'''
import copy
from functools import partial

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QDialog, QListWidgetItem, QMessageBox
)
from xmarte.qt5.services.app_def.widgets.project_properties import ProjectPropertiesWidget

from xmarte.qt5.services.service import Service

class Interfaces(Service):
    ''' The service itself, provides a UI to define and configure interfaces in the application '''
    service_name = 'Interfaces'
    def __init__(self, application) -> None:
        """Initialise the service and create the recovery directory and file"""
        super().__init__(application=application)
        self.application = application
        self.interfaces = []
        self.available_interfaces = []
        for key, value in self.application.factories['marte2_interfaces'].classes.items():
            if value not in self.available_interfaces:
                self.available_interfaces.append(value)
        self.interfaces_panel = InterfacePanel(application, self.interfaces, self.available_interfaces)
        self.application.leftpanel.tab_wgt.addTab(self.interfaces_panel, "Interfaces")

    def reloadPanel(self):
        self.interfaces_panel.refresh_list(self.interfaces)

class InterfacePanel(QWidget):
    def __init__(self, application, interfaces, available_interfaces):
        super().__init__()
        self.interfaces = interfaces
        self.application = application
        self.available_interfaces = available_interfaces

        self.setWindowTitle("Interface Manager")

        # --- Main layout ---
        main_layout = QVBoxLayout(self)

        # Listbox
        self.listbox = QListWidget()
        main_layout.addWidget(self.listbox)

        # Button row
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_delete = QPushButton("Delete")
        self.btn_configure = QPushButton("Configure")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_configure)
        main_layout.addLayout(btn_layout)

        # Spacer to push everything up
        main_layout.addStretch()

        # Connections
        self.btn_add.clicked.connect(self.add_interface)
        self.btn_delete.clicked.connect(self.delete_interface)
        self.btn_configure.clicked.connect(self.configure_interface)

        # Populate existing interfaces
        self.refresh_list()

    def refresh_list(self, interfaces = []):
        self.listbox.clear()
        if interfaces:
            self.interfaces = interfaces
        for iface in self.interfaces:
            QListWidgetItem(iface.configuration_name, self.listbox)

    def add_interface(self):
        dlg = AvailableInterfacesDialog(self.available_interfaces, self)
        if dlg.exec_():
            iface = copy.deepcopy(dlg.selected_interface)()

            # Make unique configuration_name
            base_name = iface.configuration_name
            existing_names = {i.configuration_name for i in self.interfaces}
            counter = 1
            new_name = base_name
            while new_name in existing_names:
                new_name = f"{base_name}{counter}"
                counter += 1
            iface.configuration_name = new_name

            self.interfaces.append(iface)
            self.refresh_list()

    def delete_interface(self):
        selected = self.listbox.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No selection", "Select an item to delete.")
            return
        del self.interfaces[selected]
        self.refresh_list()

    def configure_interface(self):
        selected = self.listbox.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No selection", "Select an item to configure.")
            return
        iface = self.interfaces[selected]
        
        iface.configure()


class AvailableInterfacesDialog(QDialog):
    """Dialog for selecting from available interfaces"""
    def __init__(self, available_interfaces, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Available Interfaces")
        self.available_interfaces = available_interfaces
        self.selected_interface = None

        self.listbox = QListWidget()
        for iface in available_interfaces:
            QListWidgetItem(iface().serialize()['label'], self.listbox)

        btn_add = QPushButton("Add Selected")
        btn_add.clicked.connect(self.accept_selection)

        layout = QVBoxLayout()
        layout.addWidget(self.listbox)
        layout.addWidget(btn_add)
        self.setLayout(layout)

    def accept_selection(self):
        selected = self.listbox.currentItem()
        if not selected:
            QMessageBox.warning(self, "No selection", "Please select an interface to add.")
            return
        idx = self.listbox.currentRow()
        self.selected_interface = self.available_interfaces[idx]
        self.accept()