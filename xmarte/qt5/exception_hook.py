'''
This module overrides the typical python exception handling so
that our GUI application doesn't crash
at an unknown error but instead displays an error to the user
and prompts them to report it or not.
'''
import sys
import webbrowser
import traceback as tb
import threading

from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

DEBUGGING = False

# Custom Exception Hook
def exceptionHook(exctype, value, traceback_obj):  # pylint: disable=W0613
    '''
    New exception handler: Inform the user, allow them to report this to our gitlab/github.
    Displays main error and full traceback on demand.
    '''
    # Initialize QApplication if needed
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    QApplication.restoreOverrideCursor()
    QApplication.setOverrideCursor(Qt.ArrowCursor)

    class ErrorDialog(QDialog):
        ''' Error Dialog to display on an exception '''
        def __init__(self, exctype, value, traceback_obj):
            super().__init__()
            self.screen = app.primaryScreen()
            self.size = self.screen.size()
            self.setGeometry(
                int(self.size.width() * 0.35),
                int(self.size.height() * 0.41),
                int(self.size.width() * 0.3),
                int(self.size.height() * 0.08),
            )
            self.setWindowTitle("Application Error")
            self.setMinimumWidth(600)

            # Format the traceback
            full_trace = ''.join(tb.format_exception(exctype, value, traceback_obj))
            main_error = str(value)

            # Main error label
            self.label = QLabel(f"<b>Unexpected exception in application: {main_error}</b>")
            self.label.setWordWrap(True)

            # Details text area (initially hidden)
            self.text_area = QTextEdit()
            self.text_area.setReadOnly(True)
            self.text_area.setText(full_trace)
            self.text_area.setVisible(False)

            # Show/Hide Details button
            self.toggle_button = QPushButton("Show Details")
            self.toggle_button.setCheckable(True)
            self.toggle_button.toggled.connect(self.toggleDetails)

            # Yes / No buttons
            self.yes_button = QPushButton("Report")
            self.yes_button.clicked.connect(self.accept)
            self.no_button = QPushButton("Close")
            self.no_button.clicked.connect(self.reject)

            # Layouts
            button_layout = QHBoxLayout()
            button_layout.addWidget(self.toggle_button)
            button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
            button_layout.addWidget(self.yes_button)
            button_layout.addWidget(self.no_button)

            main_layout = QVBoxLayout()
            main_layout.addWidget(self.label)
            main_layout.addLayout(button_layout)
            main_layout.addWidget(self.text_area)

            self.setLayout(main_layout)

        def toggleDetails(self, checked):
            ''' Show or hide the details of the error and traceback '''
            self.text_area.setVisible(checked)
            self.toggle_button.setText("Hide Details" if checked else "Show Details")
            if not checked:
                self.setGeometry(
                    int(self.size.width() * 0.35),
                    int(self.size.height() * 0.41),
                    int(self.size.width() * 0.3),
                    int(self.size.height() * 0.08),
                )
            else:
                self.setGeometry(
                    int(self.size.width() * 0.35),
                    int(self.size.height() * 0.3),
                    int(self.size.width() * 0.3),
                    int(self.size.height() * 0.3),
                )

    dialog = ErrorDialog(exctype, value, traceback_obj)
    result = dialog.exec_()

    if result == QDialog.Accepted:
        reportException(value, tb)  # Replace with your reporting function


    exc_type, exc_value, exc_tb = sys.exc_info()
    # "Clear" the exception by deleting the references
    del exc_type, exc_value, exc_tb

# Replace the default excepthook with our custom handler
if not DEBUGGING:
    sys.excepthook = exceptionHook
    def wrapper(args):
        ''' Wrap around the exception for better user experience '''
        exceptionHook(args.exc_type, args.exc_value, args.traceback_obj)
    threading.excepthook = wrapper

def reportException(exception, traceback):
    ''' Report an exception to our gitlab instance '''
    title: str = "exception"
    description: str = f"""Error%3A%20%3A%20`{exception}` at {traceback}"""
    url: str = f"https://github.com/ukaea/xmarte/issues/new?title={title}&body={description}"
    webbrowser.open(url)
