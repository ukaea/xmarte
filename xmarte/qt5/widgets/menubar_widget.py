'''
The Menu Bar of the application
'''
from functools import partial
import webbrowser

from PyQt5.QtWidgets import QMenuBar, QMenu, QAction

from ..windows.settings_window import SettingsWindow
from ..windows.help_window import HelpWindow
from ..widgets.base_menu import BaseFileMenu

class MARTeMenuBar(BaseFileMenu, QMenuBar):
    '''
    Application Menu Bar
    '''
    def __init__(self, parent=None):
        BaseFileMenu.__init__(self, parent=parent)
        QMenuBar.__init__(self, parent=parent)

        fileMenu = QMenu("&File", self)
        self.createFilemenu(fileMenu)

        self.addMenu(fileMenu)

        for service in parent.services:
            service.loadMenu(self)

        self.advancedMenu = QMenu("&Advanced", self)

        self.options = QAction("&Options...", self)
        self.options.triggered.connect(partial(self.openwindow, SettingsWindow))
        self.advancedMenu.addAction(self.options)
        self.addMenu(self.advancedMenu)

        helpMenu = QMenu("&Help", self)
        submenu = helpMenu.addMenu("&Documentation")

        for key,value in parent.doc_links.items():
            current = QAction("&" + key, self)
            current.triggered.connect(
                partial(self.openweb, link=value)
            )
            submenu.addAction(current)

        helpMenu.addSeparator()
        about = QAction("&About", self)
        about.triggered.connect(partial(self.openwindow, HelpWindow))
        helpMenu.addAction(about)
        self.addMenu(helpMenu)

    def openweb(self, link):
        ''' Open Documentation Link '''
        webbrowser.open(link)

    def openwindow(self, wnd_class, _):
        ''' Open a window based on it's class as expected '''
        self.parent.newwindow = wnd_class(self.parent, self.parent.app) # pylint:disable=W0201
        self.parent.newwindow.show()
