'''
The General Settings Panel as a widget
'''
import os
from functools import partial

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QWidget,
    QSizePolicy
)

from xmarte.qt5.widgets.settings.panel import BasePanel

class GeneralPanel(BasePanel):
    '''
    The General settings widget panel that appears on the right hand side in the
    settings window when general is selected (or by default on load).
    '''
    def __init__(self, parent=None, settings_data={}, application=None):
        super().__init__(parent)
        self.data = settings_data
        self.application = application

        layout = QVBoxLayout()
        self.setLayout(layout)
        # Generate the General Panel
        # Split View
        _ = QLabel("Split View Display:")
        self.sview_type = QComboBox()

        link = """https://marte21.gitpages.ccfe.ac.uk/xmarte/\
options.html#general-menu"""
        self.defineHelp(layout, link)

        for file_handler in self.application.file_handlers:
            self.sview_type.addItem(file_handler.getDescription())

        split_lbl = QLabel("Default Split View:")
        layout.addWidget(split_lbl)

        self.sview_type.key = "split_view"
        saved_sview = self.sview_type.findText(self.data.settings["GeneralPanel"]["split_view"])
        if saved_sview == -1:
            self.sview_type.setCurrentIndex(0)
        else:
            self.sview_type.setCurrentIndex(saved_sview)
        self.sview_type.currentTextChanged.connect(
            partial(self.combochange, widget=self.sview_type)
        )
        layout.addWidget(self.sview_type)

        # File Extension
        file_lbl = QLabel("File Extension:")
        self.file_ext = QLineEdit()
        self.file_ext.setText(self.data.settings["GeneralPanel"]["file_extension"])
        self.file_ext.key = "file_extension"
        self.file_ext.textChanged.connect(partial(self.linechange, widget=self.file_ext))
        layout.addWidget(file_lbl)
        layout.addWidget(self.file_ext)

        filed_lbl = QLabel("File Description:")
        self.filed_ext = QLineEdit()
        self.filed_ext.setText(self.data.settings["GeneralPanel"]["file_description"])
        self.filed_ext.key = "file_description"
        self.filed_ext.textChanged.connect(partial(self.linechange, widget=self.filed_ext))
        layout.addWidget(filed_lbl)
        layout.addWidget(self.filed_ext)

        # self.filebrowse = FolderBrowser(
        #     parent,
        #     'Default File Location',
        #     os.getcwd()
        # )
        # layout.addWidget(self.filebrowse)

        # dtool_lbl = QLabel("Diff Tool:")
        # self.dtool = QComboBox()
        # options = ["meld", "WinMerge"]
        # for option in options:
        #     self.dtool.addItem(option)
        # self.dtool.key = "diff_tool"
        # self.dtool.setCurrentIndex(
        #     self.dtool.findText(self.data.settings["GeneralPanel"]["diff_tool"])
        # )
        # self.dtool.currentTextChanged.connect(partial(self.combochange, widget=self.dtool))
        # layout.addWidget(dtool_lbl)
        # layout.addWidget(self.dtool)

        # spacer
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(spacer)

    @staticmethod
    def generateDefaults():
        ''' Config yaml doesn't exist - create the basic defaults for our application '''
        return {
                "file_description": "xMARTe Design",
                "file_extension": "xmt",
                "file_location": os.getcwd(),
                "split_view": "MARTe2ConfigFormat",
                "test_handler": "marte2",
                "diff_tool": "meld",
                }
