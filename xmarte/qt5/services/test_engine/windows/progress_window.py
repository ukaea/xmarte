''' Runs the test thread which executes the test and shows the progress to the user '''
import os
import copy

from PyQt5.QtWidgets import (QVBoxLayout,
                             QWidget,
                             QLabel,
                             QProgressBar,
                             QPlainTextEdit,
                             QHBoxLayout,
                             QPushButton,
                             QSizePolicy,
                             QMessageBox,
                             QMainWindow)
from PyQt5.QtCore import QThread

from qtpy.QtCore import Qt

from xmarte.qt5.services.data_handler.data_handler import DataException

from ..test_run_thread import RunThread

class TestProgressWindow(QMainWindow):
    '''
    The Test Execution Window
    '''

    def __init__(self, application, app, test_window, files):
        super().__init__(application)
        self.application = application
        self.app = app
        self.setSize(0.3,0.35,0.4,0.3)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("Executing Simulation...")
        self.settings = application.settings
        self.test_window = test_window
        self.graphing = application.API.getServiceByName('DataManager')
        self.files = files
        # Design QT
        holder = QWidget()
        self.setCentralWidget(holder)
        vlayout = QVBoxLayout()
        holder.setLayout(vlayout)

        self.progress_lbl = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_textbox = QPlainTextEdit()

        vlayout.addWidget(self.progress_lbl)
        vlayout.addWidget(self.progress_bar)
        vlayout.addWidget(self.progress_textbox)

        btn_holder = QWidget()
        hlayout = QHBoxLayout()
        btn_holder.setLayout(hlayout)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout.addWidget(spacer)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancelThread)
        self.cancel_btn.setEnabled(False)
        hlayout.addWidget(self.cancel_btn)

        vlayout.addWidget(btn_holder)

        # Thread and worker objects
        self.thread = None
        self.worker = RunThread(self.settings,
                                self.files,
                                self.application.API.getServiceByName('TypeDefinitionService'),
                                self.application.API.getServiceByName('Compiler'))

    def startThread(self):
        ''' Start our test thread '''
        temp_directory = os.path.join(self.settings['RemotePanel']['temp_folder'],'temp')
        log_path = os.path.abspath(os.path.join(temp_directory, "output.csv"))
        if os.path.exists(log_path):
            os.remove(log_path)
        log_path = os.path.abspath(os.path.join(temp_directory, "log_0.csv"))
        if os.path.exists(log_path):
            os.remove(log_path)
        # Connect signals from the worker to slots in the main thread
        self.worker.progress_update.connect(self.progressBarCallback)
        self.worker.finished.connect(self.threadFinished)
        self.worker.test_error.connect(self.showErrorMessage)
        self.worker.label_update.connect(self.progressLabelCallback)
        self.worker.text_update.connect(self.progressTextCallback)
        # Create a QThread and move the worker object to its thread
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.sim_app_def = copy.deepcopy(self.test_window.sim_app_def)
        # Connect thread's started signal to worker's run method
        self.thread.started.connect(self.worker.run)

        # Start the thread
        self.thread.start()

        # Enable cancel button
        self.cancel_btn.setEnabled(True)

    def setSize(self,x_pos=0.4,y_pos=0.3,width=0.3,height=0.2):
        '''
        Set the Window Size
        '''
        # Set Window Size
        self.screen = self.app.primaryScreen()
        self.size = self.screen.size()
        self.setGeometry(
            int(self.size.width() * x_pos),
            int(self.size.height() * y_pos),
            int(self.size.width() * width),
            int(self.size.height() * height),
        )
        self.setCentralWidget(QWidget(self))

    def progressBarCallback(self, value):
        ''' Update Progress Bar and expose this utility to the thread via signals.'''
        self.progress_bar.setValue(value)

    def progressLabelCallback(self, string):
        ''' Update Progress Label and expose this utility to the thread via signals.'''
        self.progress_lbl.setText(string)

    def progressTextCallback(self, string):
        ''' Update Progress Text and expose this utility to the thread via signals.'''
        self.progress_textbox.setPlainText(self.progress_textbox.toPlainText() + "\n" + string)
        # Scroll to the bottom after adding new text
        scroll_bar = self.progress_textbox.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def cancelThread(self):
        ''' Cancel our thread and close this window '''
        self.close()

    def closeEvent(self, event):
        ''' Close window event called - check thread status and prompt user '''
        if self.worker is not None and self.thread is not None and self.thread.isRunning():
            confirm = QMessageBox.question(self, "Close Window",
                                           """The test is still running.
 Do you want to close the window?""",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                if self.worker:
                    self.worker.interrupt()
                self.close()
            else:
                event.ignore()
        else:
            event.accept()
            self.close()

    def threadFinished(self, val):
        ''' Handles the thread completion signal - load CSV file into nodes '''
        self.thread.quit()
        self.thread.wait()
        self.test_window.finished.emit(val)
        self.thread = None
        self.cancel_btn.setEnabled(False)
        if val == 0:
            temp_directory = os.path.join(self.settings['RemotePanel']['temp_folder'],'temp')
            log_path = os.path.abspath(os.path.join(temp_directory, "log_0.csv"))
            cfg_path = os.path.abspath(os.path.join(temp_directory, "Simulation.cfg"))
            if os.path.exists(log_path):
                try:
                    csv_path = os.path.abspath(os.path.join(temp_directory, "log_0.csv"))
                    self.graphing.loadCSVData(csv_path)
                except DataException as e:
                    self.showErrorMessage(str(e))
            else:
                self.showErrorMessage(f"""No output log was recorded, this can happen if a
 non-runnable simulation was generated, check the config at {cfg_path} for any errors""")
        self.close()

    def showErrorMessage(self, message):
        ''' Show an error message to the user '''
        txt = self.progress_textbox.toPlainText() + "\n" + f"Error {message} has occurred"
        self.progress_textbox.setPlainText(txt)
        # Scroll to the bottom after adding new text
        scroll_bar = self.progress_textbox.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(f"Error {message} has occurred.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setDefaultButton(QMessageBox.Ok)
        msg_box.exec_()
