'''
The Node Factory
'''
import importlib
import json
import os


class Factory:
    '''
    Factory implementation that provides capability to dynamically define and load node types
    '''
    def __init__(self):
        '''
        Initialise our local definitions
        '''
        self.classes = {}

    def importModule(self, name: str):
        ''' import a library/module '''
        return importlib.import_module(name)  # type: ignore

    def unloadAll(self):
        ''' Unload our definitions of classes we can produce '''
        self.classes = {}

    def loadOnlyClass(self, class_name):
        ''' Load only a specific class '''
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nodes.json")
        with open(path, encoding='UTF-8') as json_file:
            plugins = json.load(json_file)
        self.loadPlugins([plugins[class_name]], self.classes)

    def loadRemote(self, path=None):
        ''' Load a remotely provided file, if none then load locally defined file '''
        if path is None:
            path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "nodes.json"
            )
            with open(path, encoding='UTF-8') as json_file:
                plugins = json.load(json_file).values()
            self.loadPlugins(plugins, self.classes)
        else:
            with open(path, encoding='UTF-8') as json_file:
                plugins = json.load(json_file).values()
            self.loadPlugins(plugins, self.classes)

    def loadPlugins(self, plugins, plugin_datastore) -> None:
        """Load the plugins defined in the plugins list."""
        for plugin_name in plugins:
            plugin = self.importModule(plugin_name)
            plugin.initialize(self, plugin_datastore)

    def registerBlock(self, class_name: str, block_class: object, plugin_datastore):
        ''' function for registering a block into our local definitions '''
        plugin_datastore[class_name] = block_class

    def unregisterBlock(self, class_name: str):
        ''' unregister a block '''
        if class_name in self.classes:
            self.classes.pop(class_name)

    def create(self, node_type="and"):
        """Create a block of a specific type, given an initblock."""
        if node_type in self.classes:
            return self.classes[node_type]
        return False

    def getAll(self):
        ''' return a list of all the object definitions available to us '''
        return list(self.getNodes())

    def getNodes(self):
        ''' return all the possible nodes '''
        return self.classes.values()
