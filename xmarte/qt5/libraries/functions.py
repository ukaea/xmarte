'''
Becoming more and more general purpose stuff but originally for shared menu items between toolbars
'''

import os
import sys
import copy
import importlib
import base64
from pathlib import Path

import yaml

from cryptography.fernet import Fernet

class PluginException(Exception):
    ''' Our generic application exception for plugins '''

class GenericData:
    ''' Generic data instance '''
    def __init__(self):
        self.settings = {}

def fixSocketOrdering(node):
    '''
    This function ensures the ordering of the MARTeConfig signal definitions match
    that of the socket and socket labels in the node
    '''
    prev = node.scene.large_import
    node.scene.large_import = True
    inputsb = copy.deepcopy(node.inputsb)
    new_inputsb = [() for a in inputsb]
    outputsb = copy.deepcopy(node.outputsb)
    new_outputsb = [() for a in outputsb]
    for index, input_socket in enumerate(node.inputs):
        name = input_socket.label
        signal = [a for a in inputsb if a[0] == name][0]
        new_inputsb[index] = signal
    node.inputsb = new_inputsb
    for index, output_socket in enumerate(node.outputs):
        name = output_socket.label
        signal = [a for a in outputsb if a[0] == name][0]
        new_outputsb[index] = signal
    node.outputsb = new_outputsb
    node.scene.large_import = prev

def loadPlugin(filename, application=None, register=True):
    ''' Generic function for loading a module file '''
    spec = importlib.util.spec_from_file_location("module.name", filename)
    module_from_spec = importlib.util.module_from_spec(spec)
    sys.modules["module.name"] = module_from_spec
    spec.loader.exec_module(module_from_spec)
    if register:
        newplugin = module_from_spec.registerPlugin(application)
        return newplugin["plugin"]
    return module_from_spec.getPluginClass()

def getUserFolder():
    ''' Get the user folder with our hidden directory '''
    return os.path.join(
            os.path.abspath(str(Path.home())), r".xmarte/"
        )

def deepcopyWithoutAttribute(obj, attribute):
    """
    Deep copy an object while excluding a specified attribute.
    """
    if isinstance(obj, list):
        # If the object is a list, deep copy its elements recursively
        return [deepcopyWithoutAttribute(item, attribute) for item in obj]
    if hasattr(obj, '__dict__'):
        # If the object has a dictionary of attributes, create a new
        # instance and copy its attributes recursively
        new_obj = obj.__class__()  # Create a new instance of the object's class
        for item_key, value in obj.__dict__.items():
            if item_key != attribute:  # Exclude the specified attribute
                setattr(new_obj, item_key, deepcopyWithoutAttribute(value, attribute))
        return new_obj
    # If the object is neither a list nor an instance with a dictionary of attributes,
    # it's immutable, so return it as is
    return obj

def updateDefaultDialogDir(file_dir):
    """
    Open a YAML file, change a specified attribute, and save the modified YAML file.

    Args:
        file_path (str): Path to the YAML file.
        attribute_name (str): Name of the attribute to change.
        new_value: New value for the attribute.
    """
    # Open the YAML file
    yml_file = os.path.join(getUserFolder(), 'config.yml')
    with open(yml_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # Change the specified attribute
    data["GeneralPanel"]["file_location"] = file_dir

    # Save the modified YAML file
    with open(yml_file, 'w', encoding='utf-8') as file:
        yaml.dump(data, file)

def getTopPythonDir(filepath):
    '''Get the path of the top directory in the project from a given file.'''
    if os.path.split(filepath)[1] == 'xmarte':
        return os.path.dirname(filepath)
    return getTopPythonDir(os.path.dirname(filepath))

def loadKey():
    ''' Function to load the cipher key for encyrption/decryption '''
    if not os.path.exists(getUserFolder()):
        os.mkdir(getUserFolder(), 0o777)
    if not os.path.exists(os.path.join(getUserFolder(),'secret.key')):
        # Generate a key
        cipher_key = Fernet.generate_key()

        # Save the key to a file
        with open(os.path.join(getUserFolder(),'secret.key'), 'wb') as key_file:
            key_file.write(cipher_key)
    return open(os.path.join(getUserFolder(),'secret.key'), 'rb').read()

# Load the previously generated key
key = loadKey()
cipher = Fernet(key)

def decryptPassword(encrypted_data):
    ''' Decrypt the given password '''
    return base64.decodebytes(cipher.decrypt(str(encrypted_data)[2:-1])).decode('utf-8')
