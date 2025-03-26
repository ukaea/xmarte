'''
The widget that provides a standardised save, close button layout
'''
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QPushButton

class QSaveClose(QWidget):
    ''' The standardised save, cancel button layout '''
    def __init__(self, parent=None, ongo_lbl = "Save", ongo=None, oncancel=None):
        super().__init__(parent)
        # Add save/close buttons here to top_layout
        btns_layout = QHBoxLayout()
        self.setLayout(btns_layout)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        btns_layout.addWidget(spacer)

        go_btn = QPushButton(ongo_lbl)
        go_btn.clicked.connect(ongo)
        btns_layout.addWidget(go_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(oncancel)
        btns_layout.addWidget(cancel_btn)
