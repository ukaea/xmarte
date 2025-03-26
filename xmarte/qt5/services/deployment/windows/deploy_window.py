''' Both the deployment and statue window (To be completed) '''

from functools import partial
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout,
                             QHeaderView,
                             QLabel,
                             QMessageBox,
                             QPushButton,
                             QSizePolicy,
                             QTableWidget,
                             QTableWidgetItem,
                             QVBoxLayout,
                             QWidget)
from qtpy.QtWidgets import QPlainTextEdit, QProgressBar
from martepy.marte2.qt_functions import deleteChildren
from xmarte.qt5.windows.base_window import ModalOptionsWindow


class DeployWindow(ModalOptionsWindow):
    ''' The deploy window instance - as a modal window) '''
    cancel_signal = pyqtSignal(bool)
    def __init__(self, application, app, status=False):
        super().__init__(application, app, 0.32,0.37,0.35,0.25)

        self.setWindowTitle("Deployment")

        self.main_wgt = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_wgt.setLayout(self.main_layout)

        self.setCentralWidget(self.main_wgt)
        self.cancelled_search = False
        self.status = status
        self.deploy_thread = None
        self.udp_thread = None
        self.progress_bar = None
        self.udp_worker = None
        self.text_edit = None
        self.deploy_worker = None
        self.dev_tbl = None
        if status:
            self.drawStatus()
        else:
            self.application.devices = []
            self.drawSearch()

        self.show()

    def closeEvent(self, event):
        ''' If close event cause, check our threads are not still running and prompt
        user for action '''
        deploy_thread = self.deploy_thread is not None and self.deploy_thread.is_alive()
        udp_thread = self.udp_thread is not None and self.udp_thread.is_alive()
        if udp_thread or deploy_thread:
            reply = QMessageBox.question(self, 'Exit Confirmation',
                                         'Are you sure you want to exit now?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cancel_signal.emit(False)
                event.accept()
            else:
                event.ignore()

    def drawSearch(self):
        ''' Draw that we are searching for devices '''
        deleteChildren(self.main_layout)

        # Redraw

        lbl = QLabel("Searching for devices...")
        self.progress_bar = QProgressBar()
        self.text_edit = QPlainTextEdit()
        # Slot to update QPlainTextEdit
        def updateTextEdit(self, message):
            self.text_edit.appendPlainText(message)

        # Slot to update QProgressBar
        def updateProgressBar(self, value):
            self.progress_bar.setValue(value)

        def cancel(self):
            reply = QMessageBox.question(self, 'Cancel Confirmation',
                                         'Are you sure you want to cancel at this stage?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cancel_signal.emit(False)

        def processUDPCompleted(self, data_list):
            self.application.devices = data_list
            # Now go to draw next page
            self.drawDevices()

        button_holder = QWidget()
        button_layout = QHBoxLayout()
        button_holder.setLayout(button_layout)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(partial(cancel, self))
        button_layout.addWidget(spacer)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addWidget(lbl)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.text_edit)
        self.main_layout.addWidget(button_holder)

        # Create UDP worker and connect its signals to GUI slots
        self.udp_worker = UDPWorker(self.cancel_signal)
        self.udp_worker.update_signal.connect(partial(updateTextEdit, self))
        self.udp_worker.progress_signal.connect(partial(updateProgressBar, self))
        self.udp_worker.finished_signal.connect(partial(processUDPCompleted, self))
        # Start UDP messaging task in a separate thread
        self.udp_thread = threading.Thread(target=self.udp_worker.run)
        self.udp_thread.start()

    def drawDevices(self):
        ''' Draw the devices we found '''
        deleteChildren(self.main_layout)
        # Create table widget
        self.dev_tbl = QTableWidget()
        self.dev_tbl.setColumnCount(5)
        self.dev_tbl.setHorizontalHeaderLabels(["Device name", "IP Address",
                                                "MAC Address", "Status", "Version"])
        self.dev_tbl.setEditTriggers(QTableWidget.NoEditTriggers)  # Make cells read-only
        self.dev_tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.dev_tbl.setRowCount(len(self.application.devices))
        for row, item in enumerate(self.application.devices):
            for col, value in enumerate(item):
                self.dev_tbl.setItem(row, col, QTableWidgetItem(value))

        # Set table size to fit contents
        header = self.dev_tbl.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        btn_wdg = QWidget()
        btn_layout = QHBoxLayout()
        btn_wdg.setLayout(btn_layout)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_deploy = QPushButton("Deploy")
        btn_deploy.clicked.connect(self.deploy)
        btn_layout.addWidget(spacer)
        btn_layout.addWidget(btn_deploy)

        self.main_layout.addWidget(self.dev_tbl)
        self.main_layout.addWidget(btn_wdg)

    def deploy(self):
        ''' Activate the deploying simulation '''
        # Activate drawDeploying
        # Get selected row information and send it to drawDeploying
        selected_rows = []
        for index in self.dev_tbl.selectionModel().selectedRows():
            row = index.row()
            row_data = []
            for col in range(self.dev_tbl.columnCount()):
                item = self.dev_tbl.item(row, col)
                row_data.append(item.text())
            selected_rows.append(tuple(row_data))
        self.drawDeploying(selected_rows)

    def drawStatus(self):
        ''' Draw the status of devices '''
        deleteChildren(self.main_layout)
        # Draw out our devices only
        # Create table widget
        self.dev_tbl = QTableWidget()
        self.dev_tbl.setColumnCount(5)
        self.dev_tbl.setHorizontalHeaderLabels(["Device name", "IP Address",
                                                "MAC Address", "Status", "Version"])
        self.dev_tbl.setEditTriggers(QTableWidget.NoEditTriggers)  # Make cells read-only
        self.dev_tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.dev_tbl.setRowCount(len(self.application.devices))
        for row, item in enumerate(self.application.devices):
            for col, value in enumerate(item):
                self.dev_tbl.setItem(row, col, QTableWidgetItem(value))

        # Set table size to fit contents
        header = self.dev_tbl.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        btn_wdg = QWidget()
        btn_layout = QHBoxLayout()
        btn_wdg.setLayout(btn_layout)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(spacer)
        btn_layout.addWidget(btn_cancel)

        self.main_layout.addWidget(self.dev_tbl)
        self.main_layout.addWidget(btn_wdg)

    def drawDeploying(self, devices_to_deploy):
        ''' Draw the deploying progress '''
        deleteChildren(self.main_layout)
        self.udp_worker = UDPWorker(self.cancel_signal)
        # Start up a deployment thread and do this while giving
        # the user the detailed info on the status of it
        lbl = QLabel("Deploying to selected devices...")
        self.progress_bar = QProgressBar()
        self.text_edit = QPlainTextEdit()
        # Slot to update QPlainTextEdit
        def updateTextEdit(self, message):
            self.text_edit.appendPlainText(message)

        # Slot to update QProgressBar
        def updateProgressBar(self, value):
            self.progress_bar.setValue(value)

        def cancel(self):
            reply = QMessageBox.question(self, 'Cancel Confirmation', '''Are you sure you want to
cancel at this stage? Only some devices have been deployed too and this could end up in a
corrupted state.''',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cancel_signal.emit(False)

        def processUDPCompleted(self, data_list):
            self.application.devices = data_list
            self.drawStatus()

        def processDeploymentCompleted(self):
            # Now go to draw next page
            # Run UDP thread again to get status
            # Create UDP worker and connect its signals to GUI slots
            self.udp_worker.update_signal.connect(partial(updateTextEdit, self))
            self.udp_worker.progress_signal.connect(partial(updateProgressBar, self))
            self.udp_worker.finished_signal.connect(partial(processUDPCompleted, self))
            # Start UDP messaging task in a separate thread
            self.udp_thread = threading.Thread(target=self.udp_worker.run)
            self.udp_thread.start()

        button_holder = QWidget()
        button_layout = QHBoxLayout()
        button_holder.setLayout(button_layout)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(partial(cancel, self))
        button_layout.addWidget(spacer)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addWidget(lbl)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.text_edit)
        self.main_layout.addWidget(button_holder)

        # Create UDP worker and connect its signals to GUI slots
        self.deploy_worker = DeployWorker(self.cancel_signal, devices_to_deploy)
        self.deploy_worker.update_signal.connect(partial(updateTextEdit, self))
        self.deploy_worker.progress_signal.connect(partial(updateProgressBar, self))
        self.deploy_worker.finished_signal.connect(partial(processDeploymentCompleted, self))
        # Start UDP messaging task in a separate thread
        self.deploy_thread = threading.Thread(target=self.deploy_worker.run)
        self.deploy_thread.start()

# Worker class to perform UDP messaging
class UDPWorker(QObject):
    ''' UDP Thread for finding devices '''
    update_signal = pyqtSignal(str)  # Signal to send messages to GUI
    progress_signal = pyqtSignal(int)  # Signal to update progress bar
    finished_signal = pyqtSignal(list)  # Signal to notify completion

    def __init__(self, cancel_signal):
        super().__init__()
        self.running = True
        cancel_signal.connect(self.cancel)

    def run(self):
        ''' Run the find process '''
        for i in range(1, 101):
            if self.running: # This is a way for the user to cancel at any stage
                time.sleep(0.1)  # Simulate UDP messaging task
                self.update_signal.emit(f"Message {i} received.")  # Send message to GUI
                self.progress_signal.emit(i)  # Update progress bar
            else:
                break

        data_list = [
            ("Device 1", "192.168.1.1", "AA:BB:CC:DD:EE:FF", "Undeployed", "1.0"),
            ("Device 2", "192.168.1.2", "11:22:33:44:55:66", "Running", "2.0"),
            ("Device 3", "192.168.1.3", "AA:BB:CC:DD:EE:FF", "Undeployed", "1.0"),
            ("Device 4", "192.168.1.4", "11:22:33:44:55:66", "Running", "2.0"),
            ("Device 5", "192.168.1.5", "AA:BB:CC:DD:EE:FF", "Undeployed", "1.0")
        ]

        self.finished_signal.emit(data_list)

    def cancel(self):
        ''' Cancel the thread '''
        self.running = False

# Worker class to perform UDP messaging
class DeployWorker(QObject):
    ''' Deploy thread '''
    update_signal = pyqtSignal(str)  # Signal to send messages to GUI
    progress_signal = pyqtSignal(int)  # Signal to update progress bar
    finished_signal = pyqtSignal()  # Signal to notify completion

    def __init__(self, cancel_signal, devices_to_deploy):
        super().__init__()
        self.running = True
        cancel_signal.connect(self.cancel)
        self.devices_to_deploy = devices_to_deploy

    def run(self):
        ''' Run the thread '''
        for i in range(1, 101):
            if self.running: # This is a way for the user to cancel at any stage
                time.sleep(0.1)  # Simulate UDP messaging task
                self.update_signal.emit(f"Deploying {i}...")  # Send message to GUI
                self.progress_signal.emit(i)  # Update progress bar
            else:
                break

        self.finished_signal.emit()

    def cancel(self):
        ''' Cancel the thread '''
        self.running = False
