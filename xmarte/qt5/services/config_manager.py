'''
This service handles the configuration file setup for all services dynamically
'''

import os
import yaml

from xmarte.qt5.services.service import Service
from xmarte.qt5.libraries.functions import getUserFolder
from xmarte.qt5.windows.settings_window import SettingsWindow


class ConfigurationException(Exception):
    '''
    The Exception that should be thrown when a configuration has been corrupted
    or is simply not setup
    '''

top_python_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class ConfigManager(Service):
    '''
    This class managed the configuration file that sits in the users ~/.xmarte/config.yml
    directory. In the future this should be seperated out into it's own file and segmented
    so we can package RTCC2 and other applications since they define the plugins to load in the
    config.yml so we need a way to support multiple config file defaults depending on application.

    Notes: Oddly enough we don't super() init this service as it would try and use the editToolbar
    before it exists if thats the case but loading everything needs this service.
    '''
    service_name = 'ConfigManager'
    def __init__(self, application) -> None:
        self.application = application
        super().__init__(application)
        self.user_folder = getUserFolder()
        self.plugins = self._discoverPlugins()  # find application plugins
        if not self.plugins:  # no plugins were discovered
            raise ConfigurationException("No plugins found!")
        if os.getenv("CI_PROJECT_DIR"):  # if executing in a pipeline
            for plugin_name, plugin_info in self.plugins.items():
                plugin_info['location'] = os.path.join(  # replace location with build directory
                    '/', 'builds', 'marte21', 'xmarte', 'xmarte', 'qt5', 'plugins',
                    plugin_name, f'{plugin_name}.py'
                )
        self.application.settings = self._discoverSettings()  # create application settings
        if not self.application.settings:
            raise ConfigurationException("No settings found and could not be generated!")
        self.application.settings['plugins'] = self.plugins  # update with discovered plugins

    def _discoverPlugins(self) -> dict:
        '''Find all application plugin files.'''
        plugin_yaml = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'plugins.yml'
        )
        if os.path.exists(plugin_yaml):  # yaml file exists -> check if it's valid
            if self._validatePluginYaml(plugin_files := self._readYaml(plugin_yaml)):
                return plugin_files  # valid yaml file -> return found plugins
        if self._generatePluginYaml(plugin_yaml):  # no yaml or invalid yaml -> generate yaml
            return self._readYaml(plugin_yaml)
        return {}  # no plugins found

    def _readYaml(self, filename) -> dict:
        '''Read in yaml file.'''
        try:
            with open(filename, "r", encoding='utf-8') as yamlfile:  # read plugin info from yaml
                data = yaml.load(yamlfile, Loader=yaml.FullLoader)
            yamlfile.close()
            return data
        except yaml.YAMLError:  # invalid yaml file
            return {}

    def _validatePluginYaml(self, plugin_files) -> bool:
        '''Determine whether the plugins.yml is valid.'''
        for plugin_info in plugin_files.values():
            if os.path.exists(os.path.normpath(plugin_info['location'])):  # valid file path
                return True
        return False  # no valid file paths found

    def _generatePluginYaml(self, plugin_yaml) -> dict:
        '''Try to generate the plugin file based on files in the plugin directory.'''
        plugin_dir = os.path.join(os.path.dirname(plugin_yaml), 'qt5', 'plugins')
        plugins = {}
        for element in os.listdir(plugin_dir):  # search plugin directory for subdirectories
            directory = os.path.join(plugin_dir, element)
            if os.path.isdir(directory) and all(x not in directory for x in ['__pycache__',
                                                                             'widgets']):
                # search subdirectories for top-level file
                for subelement in os.listdir(directory):
                    file = os.path.join(directory, subelement)
                    # this file should specify the GUIPlugin implementation
                    if os.path.isfile(file):

                        plugins[
                            os.path.splitext(os.path.basename(file))[0]
                        ] = {
                            'location': os.path.abspath(file),
                            'status': 'Enabled'
                        }
        with open(plugin_yaml, 'w', encoding='utf-8') as fhand:
            yaml.dump(plugins, fhand, indent=4)  # write found plugin info to yaml
        fhand.close()
        return plugins

    def _discoverSettings(self) -> dict:
        '''Find/create the application settings file.'''
        settings_yaml = os.path.join(self.user_folder, 'config.yml')
        if os.path.exists(settings_yaml):  # settings yaml found -> validate
            if self._validateSettingsYaml(settings := self._readYaml(settings_yaml)):
                return settings  # settings yaml is valid -> return settings
        if not os.path.exists(self.user_folder):
            os.mkdir(self.user_folder)  # create the user folder
        with open(settings_yaml, "w", encoding='utf-8') as outfile:  # no settings yaml
            yaml.dump(settings := self._generateSettingsYaml(), outfile)  # generate one
        outfile.close()
        if self._validateSettingsYaml(settings := self._readYaml(settings_yaml)):
            return settings
        return {}

    def _validateSettingsYaml(self, settings) -> bool:
        '''Determine whether the settings.yml is valid.'''
        try:
            directories = [
                settings["RemotePanel"]["temp_folder"],
            ]
        except (AttributeError, ValueError):  # invalid yaml file
            return False
        for directory in directories:  # validate and fix
            if not os.path.exists(directory):
                os.mkdir(directory)
        return True

    def _generateSettingsYaml(self) -> dict:
        '''Try to generate the settings.yml based on available files.'''
        dictionary = {}
        for _, panel_cls in SettingsWindow.getSettingsClasses().items():
            paneldictionary = panel_cls.generateDefaults()
            dictionary[panel_cls.__name__] = paneldictionary
        dictionary['gui'] = {"scene_height": 6400, "scene_width": 6400}
        dictionary['hidden'] = {
                "recovery_document": os.path.join(self.user_folder, "recovery.xmt")
        }
        return dictionary


    def saveSettings(self, settings) -> None:
        ''' Save the settings passed through to file '''
        settings_yaml = os.path.join(self.user_folder, 'config.yml')
        with open(settings_yaml, "w", encoding='utf-8') as yamlfile:
            yaml.dump(settings, yamlfile, indent=4,default_flow_style=False)
        yamlfile.close()
