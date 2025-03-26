'''Gives the ability to show a tooltip on buttons'''

from PyQt5.QtWidgets import QPushButton, QLabel
from PyQt5.QtCore import QPoint, Qt

class HoverButton(QPushButton):
    ''' A button which contains a tooltip on mouseover '''
    def __init__(self, text, parent=None, tooltip=""):
        ''' Create the tooltip and start tracking the mouse '''
        super().__init__(text, parent)
        self.tooltip = CustomTooltip(parent)
        self.setMouseTracking(True)
        self.tooltip_text = tooltip

    def enterEvent(self, event):
        ''' Mouse enter - show the tooltip '''
        if self.tooltip_text:
            pos = self.mapToGlobal(QPoint(self.width(), 0))
            self.tooltip.showTooltip(self.tooltip_text, pos)
        super().enterEvent(event)

    def leaveEvent(self, event):
        ''' Mouse leave - hide our tooltip '''
        self.tooltip.hide()
        super().leaveEvent(event)

class CustomTooltip(QLabel):
    ''' The tooltip label for our hover button class '''
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip)
        self.setWindowFlags(Qt.ToolTip)
        self.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;  /* Dark background */
                color: #ffffff;  /* White text color */
                border: 1px solid #3a3a3a;  /* Dark border */
                padding: 5px;  /* Padding around the text */
                border-radius: 5px;  /* Rounded corners */
                max-width: 200px;  /* Maximum width of the tooltip */
                white-space: normal;  /* Enable text wrapping */
            }
        """)
        self.setWordWrap(True)
        self.hide()

    def showTooltip(self, text, pos):
        ''' Show our tooltip '''
        self.setText(text)
        self.move(pos)
        self.adjustSize()
        self.show()
