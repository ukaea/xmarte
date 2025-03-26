''' The standardised panel for any settings '''

import base64
import webbrowser
from cryptography.fernet import Fernet

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout

from xmarte.qt5.libraries.functions import loadKey

# Load the previously generated key
key = loadKey()
cipher = Fernet(key)

def helpRedirect(link):
    ''' Redirects to documentation '''
    webbrowser.open(link)

class BasePanel(QWidget):
    ''' Basic panel implementation '''
    def defineHelp(self, layout, link):
        ''' Defines the show help button '''
        help_box_layout = QHBoxLayout()
        help_button = QPushButton("?")
        def helpWrap():
            helpRedirect(link)
        help_button.clicked.connect(helpWrap)
        help_button.setMinimumSize(40, 15)
        help_box_layout.addStretch()
        help_box_layout.addWidget(help_button)

        layout.addLayout(help_box_layout)

    def linechange(self, text, widget):
        ''' Update LineEdit '''
        self.data.settings[self.getName()][widget.key] = text

    def chkboxchange(self, state, widget):
        ''' Update Combo '''
        self.data.settings[self.getName()][widget.key] = not state == 0

    def combochange(self, text, widget):
        ''' Update Combo '''
        self.data.settings[self.getName()][widget.key] = text

    def getName(self):
        ''' Get my class/panel name '''
        return self.__class__.__name__

    def passchange(self, text, widget):
        ''' A password field has changed '''
        self.data.settings[self.getName()][widget.key] = self.encryptPassword(text)

    def encryptPassword(self, plain_text):
        ''' Encrypt the given password/text '''
        return cipher.encrypt(base64.encodebytes(bytes(plain_text, encoding="ascii")))

    def decryptPassword(self, encrypted_data):
        ''' Decrypt the given password/text '''
        return base64.decodebytes(cipher.decrypt(encrypted_data[2:-1])).decode('utf-8')
