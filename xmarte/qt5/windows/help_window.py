'''
The About/Help Window
'''
import os
import webbrowser

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

from xmarte.qt5.windows.base_window import BaseWindow

class HelpWindow(BaseWindow):
    '''
    The Help Window
    '''
    def __init__(self, application, app):
        self.app = app
        super().__init__(application)
        self.setWindowTitle("About")
        self.application = application

        # Set Window Size
        self.setSize()

        version_file = os.path.join(
            os.path.abspath(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ),
            "version",
        )
        version = "Undocumented"
        try:
            with open(version_file, "r", encoding='UTF-8') as infile:
                version = infile.read()
        except FileNotFoundError:
            pass

        layout = QVBoxLayout()
        help_text = QTextBrowser()
        help_text.setOpenLinks(True)
        help_text.setReadOnly(True)
        release_notes_link = (
            f'<a href="https://github.com/ukaea/xmarte/-/releases/{version}">'
            'Release Notes</a>'
        )
        help_text.setHtml(
            '<style>'
            'a:link, a:visited, a:hover, a:active {'
            '    color: #32CD32;  /* Light green color */'
            '    text-decoration: none;  /* No underline */'
            '}'
            '</style>'
            '<p>This application provides a graphical interface for defining and '
            'reading MARTe2 configurations.</p>'
            '<p>Please contact Adam Stephen (Advanced Computing) to get in touch with the '
            'support team: '
            '<a href="mailto:adam.stephen@ukaea.uk">adam.stephen@ukaea.uk</a></p>'
            f'<p>Version: Release {version}</p>'
            f'<p>Find release notes at: {release_notes_link}</p>'
        )
        layout.addWidget(help_text)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(layout)

        help_text.anchorClicked.connect(self.openLink)

    def openLink(self, url):
        """
        Opens the given URL.
        
        Args:
            url (QUrl): The URL to open.
        """
        webbrowser.open(url.url())
