''' Defines the error button that exists on the toolbar, sets how many errors have been found in
the application and opens the error message window. '''

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QLabel

from xmarte.qt5.services.api_manager.windows.error_check_wnd import AppErrorWindow

class ErrorWidgetButton(QWidget):
    ''' Definition of the error widget button '''
    def __init__(self, parent=None, application=None):
        super().__init__(parent)
        self.application = application
        self.hlayout = QHBoxLayout()
        self.setLayout(self.hlayout)
        self.error_lbl = QLabel("Errors: 0")
        self.hlayout.addWidget(self.error_lbl)

        self.open_wnd = QPushButton("Check Errors")
        self.open_wnd.clicked.connect(self.checkerrorwnd)
        self.hlayout.addWidget(self.open_wnd)

    def handleSceneChange(self, _, unused_arg):
        ''' When the user changes something, recheck for errors '''
        self.reseterrors()

    def reseterrors(self, application=None):
        ''' Check the application definition for errors '''
        if application:
            exceptions = application.onlyErrors()
        else:
            exceptions = self.application.API.buildApplication().onlyErrors()
        # update our label
        self.error_lbl.setText(f"Errors: {len(exceptions)}")
        return exceptions

    def checkerrorwnd(self, application=None):
        ''' Open the error window and pass it the found exceptions '''
        # perform the error check again
        exceptions = self.reseterrors(application)
        # open the window with this information
        self.application.newwindow = AppErrorWindow(self.application,
                                                    self.application.app,
                                                    exceptions)
        self.application.newwindow.show()
