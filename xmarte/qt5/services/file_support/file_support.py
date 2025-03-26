''' This service is primarily so that when changes occur in fixes to the .xmt
file format we can backwards support old versions by automatically upgrading them '''
import tarfile
import json
import copy
import os
import tempfile

from PyQt5.QtWidgets import QMessageBox

from martepy.marte2.objects.message import MARTe2Message
from martepy.marte2.objects.real_time_state import MARTe2RealTimeState
from martepy.marte2.objects.statemachine import MARTe2StateMachine
from xmarte.qt5.services.service import Service
from xmarte.qt5.widgets.scene import EditorScene

class FileSupportService(Service):
    ''' Upconverting file service which handles .xmt files before they are loaded '''
    def __init__(self, application):
        super().__init__(application)

        self.upconversion_map = {
            'never': [self.upconversionFunction1, self.upconversionFunction2,
                      self.upconversionFunction3],
            '50236cc66845a50aa5bfd591fe4e4b76bbf1bba8':[self.upconversionFunction2,
                                                        self.upconversionFunction3],
            'a9fe940257a910ba8b4f45d7ed9d3c62d12b9174': [self.upconversionFunction3],
        # Add more mappings as needed
        }

    def upconversionFunction3(self, tar_file, _):
        ''' Conversion Function 3: Fixes changes to replacement of threads with Ref Container
        to conform inline to cfg's '''
        with tarfile.open(tar_file, 'r') as tar:
            file_info = tar.getmember("states.json")
            file_content = tar.extractfile(file_info).read()
            content = copy.deepcopy(json.loads(file_content.decode('utf-8')))

        for state in content:
            state['threads'] = {"configuration_name": "Threads",
                                "class_name": "ReferenceContainer",
                                "objects": state['threads']}
        self.modifyFileInTar(tar_file, tar_file, 'states.json', json.dumps(content, indent=4))

    def upconversionFunction1(self, tar_file, _): # pylint:disable=R0914
        '''
        Upconversion to fix changes into message and parameter saving where parameters now conform
        to the more cfg based case of using the Configuration Database to store these
        '''
        with tarfile.open(tar_file, 'r') as tar:
            file_info = tar.getmember("state_def.json")
            file_content = tar.extractfile(file_info).read()
            content = copy.deepcopy(json.loads(file_content.decode('utf-8')))

            for state_obj in content.get('states', []): # pylint: disable=R1702
                for obj in state_obj.get('objects',[]):
                    key = None
                    if 'messages' in list(obj.keys()):
                        key = 'messages'
                    elif 'objects' in list(obj.keys()):
                        key = 'objects'
                    if key:
                        for msg in obj.get(key, []):
                            # Get the parameters field and modify it for our new format
                            # It used to not match the serialization to class format and
                            # only support one parameter in this way
                            if msg['parameters']:
                                config_name = msg['parameters'][0]['configuration_name']
                                class_name = 'ConfigurationDatabase'
                                objects = {}
                                for param in msg['parameters']:
                                    for param1 in param['parameters']:
                                        objects[param1['name']] = param1['value']
                                new_value = {'configuration_name': config_name,
                                             'class_name': class_name, 'objects': objects}
                            else:
                                new_value = {'configuration_name': '+Parameters',
                                             'class_name': 'ConfigurationDatabase', 'objects': {}}

                            msg['parameters'] = new_value

        self.modifyFileInTar(tar_file, tar_file, 'state_def.json', json.dumps(content, indent=4))

    def upconversionFunction2(self, tar_file, _):
        ''' Upconversion to fix the change of specific parameter namings for EPICSSubscriber '''
        with tarfile.open(tar_file, 'r') as tar:
            for member in tar.getmembers(): # pylint: disable=R1702
                if member.isdir():
                    # Is a state definition
                    state_name = member.name
                    subdir_and_files = [tarinfo for tarinfo in tar.getmembers() if
                                        tarinfo.name.startswith(f"{state_name}/")]
                    already_handled = []
                    for thread in subdir_and_files:
                        thread_name = thread.name.split('/')[-1].split('.')[0]
                        if thread_name in already_handled:
                            continue
                        already_handled.append(thread_name)
                        file_content = tar.extractfile(thread).read()
                        content = copy.deepcopy(json.loads(file_content.decode('utf-8')))
                        for node in content.get('nodes', []):
                            if node['class_name'] == 'EPICSSubscriber':
                                if 'StackSize' in list(node['parameters'].keys()):
                                    stacksize = node['parameters']['StackSize']
                                    node['parameters']['stacksize'] = stacksize
                                    del node['parameters']['StackSize']
                                if 'CPUs' in list(node['parameters'].keys()):
                                    node['parameters']['cpus'] = node['parameters']['CPUs']
                                    del node['parameters']['CPUs']
                        self.modifyFileInTar(tar_file, tar_file,
                                             f'{state_name}/{thread_name}.xms',
                                             json.dumps(content, indent=4))

    def getUpconversionFunctions(self, git_commit):
        """Return the list of upconversion functions for the given commit."""
        return self.upconversion_map.get(git_commit, [])


    def upconvert(self, file_path, version, mfactory): # pylint: disable=R0914
        ''' Try upconverting our .xmt file after checking it's version '''
        try:
            app_def = self.application.API.getServiceByName("ApplicationDefinition")
            state_service = self.application.API.getServiceByName("StateDefinitionService")
            # Upconvert if needed
            upconversion_functions = self.getUpconversionFunctions(version)
            for func in upconversion_functions:
                func(file_path, mfactory)

            current_version = "db9c44e14fec01a0fe78b1cd9d9c991502a1cb75"
            self.modifyFileInTar(file_path, file_path, 'version', current_version)


            # Open the tar file for reading
            with tarfile.open(file_path, 'r') as tar:
                for member in tar.getmembers():
                    if member.isdir():
                        # Is a state definition
                        state_name = member.name
                        self.application.state_scenes[state_name] = {}
                        subdir_and_files = [tarinfo for tarinfo in tar.getmembers() if
                                            tarinfo.name.startswith(f"{state_name}/")]
                        for thread in subdir_and_files:
                            thread_name = thread.name.split('/')[-1].split('.')[0]
                            file_content = tar.extractfile(thread).read()
                            scene_name = f'{state_name}-{thread_name}'
                            new_scene = EditorScene(self.application, True, scene_name)
                            new_scene.large_import = True
                            state_service.resetScene(new_scene)
                            self.application.state_scenes[state_name][thread_name] = new_scene
                            new_scene.deserialize(json.loads(file_content.decode('utf-8')))
                            new_scene.large_import = False

                # Load app definition
                file_info = tar.getmember("project_desc.json")
                file_content = tar.extractfile(file_info).read()
                app_def.loadConfig(json.loads(file_content.decode('utf-8')))

                # Load test config
                if any(member.name == 'test_def.json' for member in tar.getmembers()):
                    file_info = tar.getmember("test_def.json")
                    file_content = tar.extractfile(file_info).read()
                    self.application.test_definition = json.loads(file_content.decode('utf-8'))
                else:
                    self.application.test_definition = {}
                # Load HTTP messages
                file_info = tar.getmember("http_messages.json")
                file_content = tar.extractfile(file_info).read()
                file_dict = json.loads(file_content.decode('utf-8'))
                app_def.http_messages = [MARTe2Message().deserialize(item) for item in file_dict]
                # Load state machine into app def
                file_info = tar.getmember("state_def.json")
                file_content = tar.extractfile(file_info).read()
                file_dict = json.loads(file_content.decode('utf-8'))
                app_def.statemachine = MARTe2StateMachine().deserialize(file_dict,
                                                                        factory=mfactory)

                file_info = tar.getmember("state_scene.json")
                file_content = tar.extractfile(file_info).read()
                app_def.statemachine_serialized = json.loads(file_content.decode('utf-8'))

                # states.json
                file_info = tar.getmember("states.json")
                file_content = tar.extractfile(file_info).read()
                file_dict = json.loads(file_content.decode('utf-8'))
                def toState(item):
                    ''' Given a definition, return the MARTe2RealTimeState '''
                    return MARTe2RealTimeState().deserialize(item,factory=mfactory)
                self.application.states = [toState(item) for item in file_dict]
                # Now set our scene view to the scene selected in the QComboBox
        except PermissionError:
            QMessageBox.critical(None, "Insufficient Permissions",
                                 """Insufficient permissions to open file
 for writing, is it open elsewhere?""",
                                 QMessageBox.Ok)

    def modifyFileInTar(self, input_tar_path, output_tar_path, target_file, target_contents): # pylint:disable=R0914
        """
        Modify the contents of a specific file in a tar archive
        without changing any other contents.
    
        :param input_tar_path: Path to the input tar file.
        :param output_tar_path: Path to the output tar file.
        :param target_file: The relative path of the file to be modified
        within the tar archive.
        :param modify_function: A function that modifies the contents
        of the target file.
        """
        # Create a temporary directory to work with
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the contents of the tar file
            with tarfile.open(input_tar_path, 'r') as tar:
                tar.extractall(path=temp_dir)

            # Modify the target file
            with open(os.path.join(temp_dir, target_file), 'w', encoding='utf-8') as modify_file:
                modify_file.write(target_contents)

            # Create a new tar file with the modified contents
            with tarfile.open(output_tar_path, 'w') as tar:
                for root, dirs, files in os.walk(temp_dir):
                    for directory in dirs:
                        dir_path = os.path.join(root, directory)
                        arcname = os.path.relpath(dir_path, temp_dir)
                        tar.add(dir_path, arcname=arcname)  # Add directory explicitly
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        tar.add(file_path, arcname=arcname)

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
