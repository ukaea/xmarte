'''
The base class definition for a plugin of the application
'''

import os
import webbrowser

from PyQt5 import QtCore
from PyQt5.QtWidgets import QPlainTextEdit, QSizePolicy, QAction


class PluginException(Exception):
    ''' Exception class to be used by default for plugins '''

class GUIPlugin(QtCore.QObject):
    '''
    The basics of the plugin object itself.
    '''
    plugin_name = "Notaplugin"
    plugin_description = "The plugin has not had it's name and description overridden."
    default_file_handler = "The plugin has not specified it's default file handler."

    def __init__(self, application):
        super().__init__()
        self.application = application
        plugin_dir = self.getPluginDirectory()
        if not os.path.exists(plugin_dir):
            os.mkdir(plugin_dir)

        plugin_temp_dir = os.path.join(plugin_dir, "temp")
        if not os.path.exists(plugin_temp_dir):
            os.mkdir(plugin_temp_dir)

    def getPluginDirectory(self):
        '''
        Get the plugins temporary acting directory
        '''
        virtual_folder = self.application.settings["RemotePanel"]["temp_folder"]
        virtual_folder = os.path.abspath(
            os.path.join(
                os.path.join(virtual_folder, "plugins"),
                self.pluginDescription()["plugin_name"],
            )
        )
        if not os.path.exists(virtual_folder):
            os.mkdir(virtual_folder)
        return virtual_folder

    @staticmethod
    def getPluginPath(name: str):
        ''' Return the assumed plugin python file for entrypoint '''
        return f"{name}/{name}.py"

    def getServiceByClassName(self, name: str):
        '''
        Allows us to get a service if we need it by name
        '''
        for i in self.getServices():
            if i.__class__.__name__ == name:
                return i

        # If we got here then we couldn't find it
        raise PluginException("""Could not find requested service \
within this plugins list of services""")

    def registerService(self, service, append=True, index=0):
        '''
        This function adds to the application a service. If you select append as True
        the the index is ignored, if you select False then the service will be added
        to the list of services at the index requested (we're mostly assuming default
        to append and not a too useful application).
        If the service already exists, an error will be raised.
        '''
        if any(a for a in self.application.services if a.__class__ == service.__class__):
            raise PluginException("""Attempted to add a service to the\
application which already exists""")

        # Okay it is unique, add to the list
        if append:
            self.application.services += [service]
        else:
            self.application.services.insert(index,service)

    def registerFileHandler(self, file_handler):
        '''
        This function registers a file_handler class with the application for use to read/write
        file types.
        '''
        self.application.file_handlers += [file_handler]
        # Add the file handlers to the menu and set default
        # Check if in developer mode and setup for this if so
        if hasattr(self.application.editToolBar , 'split_files'):
            self.application.editToolBar.split_files.addItem(
                file_handler.getName()
            )

            if self.application.settings["general"]["split_view"].replace(
                " ", "_") == file_handler.getName():
                self.application.editToolBar.split_files.setCurrentIndex(
                        self.application.editToolBar.split_files.findText(
                            self.application.settings["general"]["split_view"].replace(" ", "_")
                        )
                    )

    def registerDocumentation(self, title, link):
        '''
        This functions registers an additional documentation link from a plugin to the application
        such that it appears under the help menu
        '''
        self.application.doc_links[title] = link
        help_menu = next(a for a in self.application.menuBar.actions() if a.text() == "&Help")
        doc_menu = help_menu.menu().actions()[0].menu()
        plugin_help_action = QAction("&"+title, doc_menu)
        def openURL():
            webbrowser.open(link)
        plugin_help_action.triggered.connect(openURL)
        doc_menu.addAction(plugin_help_action)

    @staticmethod
    def getServices():
        '''
        This function returns a plugins services and should be overridden in the plugin
        '''
        raise NotImplementedError("This plugin does not have a defined getServices function")

    @staticmethod
    def getFileHandlers() -> list:
        '''Returns all file handlers registered by the plugin - should be overriden.'''
        raise NotImplementedError('This plugin does not have a defined getFileHandlers function!')

    def registerSettingsWidget(self, panel_name, panel_widget):
        '''
        Similar to registering a service, you cannot have a panel name duplicated.
        The panel name is how it appears in the list on the settings panel and the widget
        is the layout displayed on click of said list item in the right hand section
        of the window.
        '''
        if panel_name in self.application.settings_widgets:
            raise PluginException("""Attempted to add a settings panel with the same \
name as one which already exists""")

        # Okay it is unique, add to the list
        self.application.settings_widgets[panel_name] = panel_widget

    def pluginDescription(self):
        '''
        Gives the application a pointer to our self, our title and description.
        '''
        return {
            "plugin_name": self.plugin_name,
            "plugin": self,
            "plugin_description": self.plugin_description,
        }

    def addToolbarOptions(self, layout):
        """
        This function is called at startup and allows you to add functions to the toolbar
        """

class SplitText(QPlainTextEdit):
    '''
    Generic Split Text Edit with updateSplit function
    '''
    def __init__(self, parent=None, handler=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setReadOnly(True)
        self.handler = handler
        self.setMinimumHeight(
            self.handler.application.rightpanel.splitter.height() - 20
        )

    def updateSplit(self):
        ''' Update the split view contents '''
        split_service = [
            service for service in self.handler.application.services
            if service.__class__.__name__ == 'SplitView'
        ]
        if split_service:
            split_service[0].updateSplit(self.handler)

class FileHandlerPlugin:
    '''
    Plugin handler for file IO representing the defined networks as files
    '''
    def __init__(self, application):
        self.application = application

    def getName(self):
        ''' Return the name of our filehandler '''
        return self.__class__.__name__.replace(" ", "_")

    def loadFile(self, _):
        ''' Load the file given '''
        self.application.API.getServiceByName('DataManager').clearData()
        raise PluginException(
            "Error, plugin does not have the load file function implemented for selected file type"
        )

    def createFileContents(self):
        ''' Create file contents '''

    def generatesplit(self):
        '''
        Generate a return the contents for the split view.
        '''
        split = SplitText(handler=self)
        num_nodes = 0
        for _, state in self.application.state_scenes.items():
            for _, thread_scene in state.items():
                num_nodes += len(thread_scene.nodes)
        if num_nodes > 0:
            split.setPlainText(self.createFileContents())
        else:
            split.setPlainText("No node blocks exist in the editor")
        return split

    @staticmethod
    def getDescription():
        ''' Return the file handler description '''
        return ""

    @staticmethod
    def getFileExtension():
        ''' Return the file handler extension '''
        return ""
