'''
Basic window implementation and functions
'''
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QSizePolicy,
    QHBoxLayout,
    QPushButton,
)
from qtpy.QtCore import Qt

class BaseWindow(QMainWindow):
    '''
    Not really used much - a predecessor to pytests, probably needs an overhaul
    '''
    def __init__(self, application):
        self.save_button = None
        self.application = application
        self.cancel_button = None
        if hasattr(application, "test"):
            if application.test:
                super().__init__()
                application.newwindow = self
            else:
                super().__init__(application)
        else:
            super().__init__(application)

    def defineSaveCancelButtons(self, layout):
        '''
        Add the generic save and cancel buttons to a given window layout and use self
        for referencing the given expected function names to connect to the button signals.
        '''
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(spacer)

        # Now save and cancel buttons
        buttons = QWidget(self)
        hbox = QHBoxLayout()
        button_spacer = QWidget(self)
        button_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        hbox.addWidget(button_spacer)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save)
        hbox.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        hbox.addWidget(self.cancel_button)

        buttons.setLayout(hbox)
        layout.addWidget(buttons)

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

class ModalOptionsWindow(BaseWindow):
    '''
    Setup a modal window type
    '''
    def __init__(self, application, app,x_pos=0.4,y_pos=0.3,width=0.3,height=0.2):
        super().__init__(application)
        self.app = app
        self.setWindowModality(Qt.ApplicationModal)

        # Set Window Size
        self.setSize(x_pos,y_pos,width,height)
