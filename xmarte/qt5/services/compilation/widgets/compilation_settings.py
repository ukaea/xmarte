'''
The General Settings Panel as a widget
'''
from functools import partial
import os
import base64
from cryptography.fernet import Fernet

from PyQt5.QtWidgets import (
    QCheckBox,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
    QSizePolicy
)

from xmarte.qt5.libraries.functions import getUserFolder
from xmarte.qt5.widgets.settings.panel import BasePanel
from xmarte.qt5.widgets.path_browser import FolderBrowser

class CompilationPanel(BasePanel):
    '''
    The General settings widget panel that appears on the right hand side in the
    settings window when general is selected (or by default on load).
    '''
    def __init__(self, parent=None, settings_data={}, application=None): # pylint: disable=R0915, R0914
        super().__init__(parent)
        self.data = settings_data
        self.application = application

        layout = QVBoxLayout()
        self.setLayout(layout)
        # Generate the Remote Execution Panel

        link = """https://marte21.gitpages.ccfe.ac.uk/xmarte/\
options.html#general-menu"""
        self.defineHelp(layout, link)

        server_chk_lbl = QLabel("Use remote server for compilation:")
        self.server_chk = QCheckBox()
        self.server_chk.setChecked(self.data.settings["CompilationPanel"]["use_remote"])
        self.server_chk.key = "use_remote"
        self.server_chk.stateChanged.connect(partial(self.chkboxchange, widget=self.server_chk))
        layout.addWidget(server_chk_lbl)
        layout.addWidget(self.server_chk)

        server_lbl = QLabel("Remote Server:")
        self.server_edt = QLineEdit()
        self.server_edt.setText(self.data.settings["CompilationPanel"]["remote_server"])
        self.server_edt.key = "remote_server"
        self.server_edt.textChanged.connect(partial(self.linechange, widget=self.server_edt))
        layout.addWidget(server_lbl)
        layout.addWidget(self.server_edt)

        port_lbl = QLabel("Remote HTTP Port:")
        self.port_edt = QLineEdit()
        self.port_edt.setText(str(self.data.settings["CompilationPanel"]["remote_http_port"]))
        self.port_edt.key = "remote_http_port"
        self.port_edt.textChanged.connect(partial(self.linechange, widget=self.port_edt))
        layout.addWidget(port_lbl)
        layout.addWidget(self.port_edt)

        ftp_port_lbl = QLabel("Remote FTP Port:")
        self.ftp_port_edt = QLineEdit()
        self.ftp_port_edt.setText(str(self.data.settings["CompilationPanel"]["remote_ftp_port"]))
        self.ftp_port_edt.key = "remote_ftp_port"
        self.ftp_port_edt.textChanged.connect(partial(self.linechange, widget=self.ftp_port_edt))
        layout.addWidget(ftp_port_lbl)
        layout.addWidget(self.ftp_port_edt)

        ftp_user_lbl = QLabel("Remote Username:")
        self.ftp_user_edt = QLineEdit()
        encrypted_user = str(self.data.settings["CompilationPanel"]["ftp_username"])
        self.ftp_user_edt.setText(self.decryptPassword(encrypted_user))
        self.ftp_user_edt.key = "ftp_username"
        self.ftp_user_edt.textChanged.connect(partial(self.passchange, widget=self.ftp_user_edt))
        layout.addWidget(ftp_user_lbl)
        layout.addWidget(self.ftp_user_edt)

        ftp_pass_lbl = QLabel("Remote Password:")
        self.ftp_pass_edt = QLineEdit()
        encrypted_pass = str(self.data.settings["CompilationPanel"]["ftp_password"])
        self.ftp_pass_edt.setText(self.decryptPassword(encrypted_pass))
        self.ftp_pass_edt.key = "ftp_password"
        self.ftp_pass_edt.textChanged.connect(partial(self.passchange, widget=self.ftp_pass_edt))
        layout.addWidget(ftp_pass_lbl)
        layout.addWidget(self.ftp_pass_edt)

        tmpfile = FolderBrowser(self, "Temporary Folder:",
                                self.data.settings["CompilationPanel"]["temp_folder"])
        layout.addWidget(tmpfile)

        server_chk_lbl = QLabel("Compile for static executable:")
        self.server_static_chk = QCheckBox()
        self.server_static_chk.setChecked(self.data.settings["CompilationPanel"]["static"])
        self.server_static_chk.key = "static"
        self.server_static_chk.stateChanged.connect(partial(self.chkboxchange,
                                                            widget=self.server_static_chk))
        layout.addWidget(server_chk_lbl)
        layout.addWidget(self.server_static_chk)

        # spacer
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(spacer)

    @staticmethod
    def generateDefaults():
        ''' Generate the default settings when a yaml is not found '''
        # Function to load the key
        def loadKey():
            return open(os.path.join(getUserFolder(),'secret.key'), 'rb').read()

        # Load the previously generated key
        key = loadKey()
        cipher = Fernet(key)
        def encryptPassword(plain_text):
            return cipher.encrypt(base64.encodebytes(bytes(plain_text, encoding="ascii")))
        return {
                "temp_folder": os.path.join(getUserFolder(), 'compile'),
                "use_remote": False,
                "remote_server": "127.0.0.1",
                "remote_http_port": "8012",
                "remote_ftp_port": "8235",
                "ftp_username": encryptPassword('admin'),
                "ftp_password": encryptPassword('admin'),
                "static": True
                }
