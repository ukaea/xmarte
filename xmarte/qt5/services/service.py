'''
The basic definition of a service
'''
import os

class Service:
    '''
    The class object for representing services of a plugin
    '''
    service_name = ""

    def __init__(self, application):
        self.application = application
        self.plugin_name = ""

    def loadMenu(self, menu_bar):
        ''' Method in which services can add to the menubar '''

    def addToolbarOptions(self, layout):
        """
        This function is called at startup and allows you to add functions to the toolbar
        """

    def addToolBar(self):
        '''
        Optional to add whole new toolbars
        '''

    @staticmethod
    def getDefaultSettings():
        '''
        Static method for the config manager to establish defaults when a config file
        needs rebuilding
        '''
        return {}

    def exit(self):
        '''
        This allows us to safely exit a service if they need to do something on close
        '''

    def loadBlocks(self):
        '''Load blocks.'''

    def getPluginDirectory(self):
        '''
        Get the plugins temporary acting directory
        '''
        virtual_folder = self.application.settings["RemotePanel"]["temp_folder"]
        virtual_folder = os.path.abspath(virtual_folder)
        if not os.path.exists(virtual_folder):
            os.mkdir(virtual_folder)
        return virtual_folder
