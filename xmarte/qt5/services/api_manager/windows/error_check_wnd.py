'''
The state message window allows the user to create the messages to be sent
upon a state transition.
'''
from PyQt5.QtWidgets import (
    QHBoxLayout, QListWidget, QMainWindow, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)


class AppErrorWindow(QMainWindow):
    ''' The window that displays the application errors found '''
    def __init__(self, application, app, exceptions) -> None:
        super().__init__()
        self.application = application
        self.setSize(app, 0.35,0.4,0.3,0.2)
        self.setWindowTitle("Application Errors")
        vlayout = QVBoxLayout()
        layout_holder = QWidget()
        self.setCentralWidget(layout_holder)
        layout_holder.setLayout(vlayout)

        self.listbox = QListWidget()
        for exception in exceptions:
            self.listbox.addItem(str(exception))

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        button_holder = QWidget()
        button_layout = QHBoxLayout()
        button_holder.setLayout(button_layout)
        button_layout.addWidget(spacer)

        refresh_btn = QPushButton("Refresh")
        button_layout.addWidget(refresh_btn)
        refresh_btn.clicked.connect(self.refresh)

        vlayout.addWidget(self.listbox)
        vlayout.addWidget(button_holder)

    def setSize(self,app,x_pos=0.4,y_pos=0.3,width=0.3,height=0.2):
        '''
        Set the Window Size
        '''
        # Set Window Size
        screen = app.primaryScreen()
        size = screen.size()
        self.setGeometry(
            int(size.width() * x_pos),
            int(size.height() * y_pos),
            int(size.width() * width),
            int(size.height() * height),
        )

    def refresh(self):
        ''' Retry the error check and re-display '''
        exceptions = self.application.API.buildApplication().onlyErrors()

        self.listbox.clear()
        for exception in exceptions:
            self.listbox.addItem(str(exception))
        