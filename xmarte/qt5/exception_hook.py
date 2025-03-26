'''
This module overrides the typical python exception handling so
that our GUI application doesn't crash
at an unknown error but instead displays an error to the user
and prompts them to report it or not.
'''
import sys
import webbrowser

from PyQt5.QtWidgets import QApplication, QMessageBox

DEBUGGING = False

# Custom exception hook
def exceptionHook(exctype, value, traceback): # pylint: disable=W0613
    '''
    New exception handler: Inform the user, allow them to report this to our gitlab/github
    '''
    # Initialize a QApplication instance if not already running
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Create and configure the message box
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Application Error")
    msg_box.setText("An unexpected error occurred, would you like to report it?")
    msg_box.setInformativeText(str(value))
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.Yes)
    response = msg_box.exec_()
    if response == QMessageBox.Yes:
        # Report error functionality goes here
        reportException(value)

# Replace the default excepthook with our custom handler
if not DEBUGGING:
    sys.excepthook = exceptionHook

def reportException(exception):
    ''' Report an exception to our gitlab instance '''
    title: str = "issue[title]=exception"
    description: str = f"""issue[description]=Error%3A%20%3A%20`{exception}`"""
    url: str = f"https://git.ccfe.ac.uk/marte21/xmarte/-/issues/new?{title}&{description}"
    webbrowser.open(url)
