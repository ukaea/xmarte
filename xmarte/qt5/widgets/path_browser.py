''' Standardising our file browser to a layout of a text of the location and button to dialog '''
from PyQt5.QtWidgets import (QLineEdit,
                             QHBoxLayout,
                             QLabel,
                             QPushButton,
                             QFileDialog,
                             QWidget,
                             QVBoxLayout)

class FileBrowser(QWidget):
    ''' Standardised file browser layout '''
    def __init__(self, parent=None, label="", key="", fileext="", filedesc=""):
        super().__init__(parent)
        top_layout = QVBoxLayout()
        self.setLayout(top_layout)
        lbl = QLabel(label)
        top_layout.addWidget(lbl)
        horiz_widg = QWidget()
        top_layout.addWidget(horiz_widg)
        layout = QHBoxLayout()
        horiz_widg.setLayout(layout)
        self.fileext = fileext
        self.filedesc = filedesc
        self.loc = QLineEdit()
        self.loc.setText(key)
        self.loc.key = key
        self.loc.textChanged.connect(self.linechange)
        browse = QPushButton("Browse")
        browse.clicked.connect(self.browse)
        layout.addWidget(self.loc)
        layout.addWidget(browse)

    def browse(self):
        ''' Browse File '''
        filename = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            f"{self.filedesc} (*.{self.fileext})",
        )
        if filename[0]:
            self.loc.key = filename[0]
            self.loc.setText(filename[0])

    def linechange(self, text):
        ''' Text of location changed directly by user '''
        self.loc.key = text

class FolderBrowser(QWidget):
    ''' The folder browser instance '''
    def __init__(self, parent=None, label="", key=""):

        super().__init__(parent)
        top_layout = QVBoxLayout()
        self.setLayout(top_layout)
        lbl = QLabel(label)
        top_layout.addWidget(lbl)
        horiz_widg = QWidget()
        top_layout.addWidget(horiz_widg)
        layout = QHBoxLayout()
        horiz_widg.setLayout(layout)
        self.loc = QLineEdit()
        self.loc.setText(key)
        self.loc.key = key
        self.loc.textChanged.connect(self.linechange)
        browse = QPushButton("Browse")
        browse.clicked.connect(self.browse)
        layout.addWidget(self.loc)
        layout.addWidget(browse)

    def browse(self):
        '''
        Browser
        '''
        folderpath = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folderpath:
            self.loc.setText(folderpath)
            self.loc.key = folderpath

    def linechange(self, text):
        ''' Location changed in LineEdit by user '''
        self.loc.key = text
