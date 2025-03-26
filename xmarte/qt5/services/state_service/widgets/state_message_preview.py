'''
This class shows a preview of the state message configuration when a user
hovers over and edge in the state transitions diagram. It is not editable.
'''
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel


class StateMessagePreview(QDialog):
    '''State machine transition preview.'''
    def __init__(self, edge) -> None:
        super().__init__()
        self.edge = edge
        self.initUi()

    def initUi(self) -> None:
        '''Initialise the UI features.'''
        self.setWindowTitle('Event Preview')
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.raise_()
        data = self.edge.state_message

        name_layout = QHBoxLayout()
        name_label = QLabel(f'Name: {data.configuration_name.replace("+", "") if data else ""}')
        name_layout.addWidget(name_label)
        layout.addLayout(name_layout)

        next_state_layout = QHBoxLayout()
        next_state_label = QLabel(f'Next State: {data.nextstate if data else ""}')
        next_state_layout.addWidget(next_state_label)
        layout.addLayout(next_state_layout)

        next_error_layout = QHBoxLayout()
        next_error_label = QLabel(f'Next Error State: {data.nextstateerror if data else ""}')
        next_error_layout.addWidget(next_error_label)
        layout.addLayout(next_error_layout)

        timeout_layout = QHBoxLayout()
        timeout_label = QLabel(f'Timeout: {data.timeout if data else ""}')
        timeout_layout.addWidget(timeout_label)
        layout.addLayout(timeout_layout)

    def setPos(self) -> None:
        '''Set the position of the window.'''
        cursor_pos = QCursor.pos()
        offset = QPoint(40, 40)
        self.move(cursor_pos + offset)
