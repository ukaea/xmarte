''' The thread which executes a test '''
import os
import shutil
from urllib.error import HTTPError, URLError
from urllib import request
import uuid
import subprocess
import ftplib
from io import BytesIO

from PyQt5.QtCore import QObject, pyqtSignal

from xmarte.qt5.libraries.functions import decryptPassword

from .exceptions import AbortException


class RunThread(QObject):
    ''' Thread which executes a test of a MARTe2 Cfg '''
    progress_update = pyqtSignal(int)
    finished = pyqtSignal(int) # 0 for success, 1 for failure
    label_update = pyqtSignal(str)
    text_update = pyqtSignal(str)
    test_error = pyqtSignal(str)

    def __init__(self, settings, files, type_service, compile_service):
        super().__init__()
        # The scene should be read-from only - never changed
        self.files = files
        # deepcopy to preserve the original as we modify the sim_app_def
        self.remote_settings = settings['RemotePanel']
        self.compile_settings = settings['CompilationPanel']
        self.type_service = type_service
        self.compile_service = compile_service
        self._is_interrupted = False
        self.packet_libraries = []

        self.session = hash(
            uuid.uuid1()
        )  # creates unique ID from hostID, current time...
        self.session_id = 0
        self.marte2_text: str = ""

    def interrupt(self):
        ''' Interrupt the thread '''
        self._is_interrupted = True

    def run(self) -> None:
        '''
        Execute the Test - Called by the Test Window which kicks off this thread
        that then runs through the stages and updates the Qt Window with siganls
        at each stage.
        If an error occurs it opens a window to Gitlab to report the issue.
        '''
        self._is_interrupted = False
        #https://medium.com/@armin.samii/avoiding-random-crashes-when-multithreading-qt-f740dc16059
        try:
            if self._is_interrupted:
                return
            self.updateProgress("Generating type libraries...", 25)
            self.generateLibraries()
            if self._is_interrupted:
                return
            self.updateProgress("Defining Configuration...", 35)
            self.generateConfig()
            if self._is_interrupted:
                return
            self.updateProgress("Preparing Execution...", 50)
            self.executeConfig()
            if self._is_interrupted:
                return
            self.updateProgress("Testing Complete", 80)
            self.updateProgress("Generating Output files to your home directory", 80)
            if self._is_interrupted:
                return
            self.generateOutputFormats()
            if self._is_interrupted:
                return
            self.updateProgress("Completed Simulation", 100)
            self.finished.emit(0)
        except AbortException as abort:  # noqa: F405
            # Get the traceback object
            tb = abort.__traceback__

            # Iterate through the traceback to find the line number
            while tb.tb_next:
                tb = tb.tb_next
            line_number = tb.tb_lineno
            self.progress_update.emit(0)
            self.text_update.emit(
                f"Test Errored and was unable to complete due to: {str(abort.args[0])}"
            )
            self.test_error.emit(
                f"""Test Errored and was unable to complete due to: {str(abort.args[0])},
 error occurred at line: {line_number}"""
            )
            self.finished.emit(1)

    def generateLibraries(self):
        ''' Generate the type definition libraries '''
        paths = self.type_service.gen()
        paths = [a.strip() for a in paths.split('.x\\\n') if a != '']

        self.packet_libraries = []
        # Decide whether to compile
        if os.path.exists(self.compile_settings['temp_folder']):
            shutil.rmtree(self.compile_settings['temp_folder'])
        shutil.copytree(self.type_service.output_path, self.compile_settings['temp_folder'])
        for types in self.sim_app_def.types_used:
            if types not in paths:
                msg = "Unknown type detected, please add this type to the type database first."
                raise AbortException(msg)
        if len(self.sim_app_def.types_used) > 0:
            if self.compile_settings["use_remote"]:
                # Send to server to be compiled
                try:
                    self.compile_service._is_interrupted = self._is_interrupted # pylint: disable=W0212
                    self.compile_service.compileOnServer()
                except URLError as e:
                    msg = """Could not connect to compilation server,
check your settings, connection and the runner on the server."""
                    raise AbortException(msg) from e
            else:
                # compile locally
                self.compile_service.compileLocally(self.compile_settings['temp_folder'])
            for lib_name in paths:
                lib_path = os.path.join(self.compile_settings['temp_folder'], 'Build',
                                        'x86-linux', 'Packets', lib_name, f'{lib_name}.so')
                self.packet_libraries.append(lib_path)
                shutil.copy(lib_path, os.path.join(self.remote_settings['temp_folder'],
                                                   "temp", f'{lib_name}.so'))

    def updateProgress(self, text, progress_int):
        ''' Signal to update the progress window '''
        self.label_update.emit(text)
        self.progress_update.emit(progress_int)

    def generateConfig(self):
        """
        The first section of this function is to setup the test_inputs.csv file for building the
        simulation and then to feed this configuration in the GUI into IDunnConfigGenerator
        """
        try:
            self.text_update.emit("Creating marte2 application instance...")
            # We should re-write this such that it reads-only the configuration
            # defined by the user in the test_window and works out how to rebuild
            # this into the sim_app_def


            # Assume done, now write to file
            # Okay open modal window and communicate with it to show stuff.
            config = self.sim_app_def.writeToConfig()
            temp_directory = os.path.join(self.remote_settings['temp_folder'], "temp")
            if not os.path.exists(temp_directory):
                os.mkdir(temp_directory)
            with open(
                os.path.join(temp_directory,'Simulation.cfg'),
                'w',
                encoding='utf-8'
            ) as outfile:
                outfile.write(config)
        except AttributeError as e:
            msg = f"Could not generate configuration file because of error {str(e)}"
            raise AbortException(msg) from e

    def executeConfig(self):
        '''
        Execute the generated configuration
        '''
        try:
            if self._is_interrupted:
                return
            self.text_update.emit("Preparing files...")
            self.progress_update.emit(50)

            temp_directory = os.path.join(self.remote_settings['temp_folder'], "temp")
            if self.remote_settings["use_remote"]:
                if self._is_interrupted:
                    return
                self.text_update.emit("Configured to send test to remote server")
                self.sendToServer(
                    self.remote_settings["remote_server"],
                    int(self.remote_settings["remote_http_port"]),
                    int(self.remote_settings["remote_ftp_port"]),
                    self.remote_settings["ftp_username"],
                    self.remote_settings["ftp_password"],
                    temp_directory,
                )
            else:
                # Replace filename in simulated inputs of file to /root/tests/test_inputs.csv
                if self._is_interrupted:
                    return
                self.progress_update.emit(55)
                self.text_update.emit("Executing Simulation.cfg...")

                directory = str(os.path.abspath(temp_directory))
                prepend = ""
                if os.name == "nt":
                    prepend = "wsl "
                    replacements = [('\\\\','/'),('\\','/'),(':','')]
                    directory = directory.lower()
                    for replacement_1, replacement_2 in replacements:
                        directory = directory.replace(replacement_1, replacement_2)
                    directory = "/mnt/" + directory
                volume = f"{directory}:/root/tests"
                parameters = "-f Simulation.cfg -m StateMachine:START -l RealTimeLoader"
                image = "sudilav1/xmarte:main"
                script = "/root/Projects/marte.sh"
                cmd = "docker run"
                cmd = f"{prepend}{cmd} -v {volume} -w /root/tests {image} {script} {parameters}"
                p = subprocess.Popen(cmd.split()) # pylint:disable=R1732
                p.wait()
                if os.path.exists(os.path.join(os.path.abspath(temp_directory), 'output.csv')):
                    shutil.copy(os.path.join(os.path.abspath(temp_directory), 'output.csv'),
                                os.path.join(os.path.abspath(temp_directory),'log_0.csv'))
                if self._is_interrupted:
                    return
                self.text_update.emit("Test Execution completed")
                self.progress_update.emit(70)
            if self._is_interrupted:
                return
            self.text_update.emit("Loading Data from test...")
            self.progress_update.emit(75)
        except (AttributeError, HTTPError) as e:
            raise AbortException(e) from e

    def sendToServer(self, hostname, http_port, ftp_port, username, password, temp_directory):
        '''
        Send the whole setup to the remote session
        '''
        try:
            if self._is_interrupted:
                return
            self.text_update.emit("Requesting Session from remote server...")
            username = decryptPassword(username)
            password = decryptPassword(password)
            self.startSession(hostname, http_port, ftp_port, username, password, temp_directory)
            self.progress_update.emit(60)
            if self._is_interrupted:
                return
            self.text_update.emit("Triggering Server Execution...")

            self.runSession(hostname, http_port)
            if self._is_interrupted:
                return
            self.text_update.emit("Server has finished session")
            self.progress_update.emit(70)
            if self._is_interrupted:
                return
            self.text_update.emit("Collecting Results...")

            self.collectResults(hostname, ftp_port,  username, password, temp_directory)
        except (AttributeError, HTTPError) as e:
            raise AbortException(e) from e

    def startSession(self, hostname, http_port, ftp_port, username, password,temp_directory): # pylint:disable=R0914
        '''
        Open a new remote session with the server which sets up remote files
        '''
        try:
            # Get a session ID
            url = "http://" + str(hostname) + ":" + str(http_port) + "/start_session"
            self.session_id = request.urlopen(url, timeout=10).read().decode("ASCII") # pylint:disable=R1732
            if self._is_interrupted:
                return
            self.text_update.emit("Open FTP session with server...")
            self.progress_update.emit(52)

            # Push files to FTP of session
            simulation_file = os.path.join(temp_directory, "Simulation.cfg")
            session = ftplib.FTP()
            session.connect(hostname, ftp_port)
            # Output: '220 Server ready for new user.'
            session.login(username, password)
            if self._is_interrupted:
                return
            self.progress_update.emit(54)
            self.text_update.emit("Sending files to server...")
            self.text_update.emit("Sending config file to server...")

            with open(simulation_file, "rb") as file_in: # file to send
                command = f"STOR {self.session_id}/Simulation.cfg"
                session.storbinary(command, file_in)  # send the file
                file_in.close()  # close file

            self.text_update.emit("Sending type libraries to server...")
            lib_names = self.type_service.getLibNames()
            for lib in lib_names:
                lib_path = os.path.join(temp_directory, f"{lib}.so")
                if os.path.exists(lib_path):
                    # file to send
                    with open(os.path.join(temp_directory, f"{lib}.so"), "rb") as file_in:
                        command = f"STOR {self.session_id}/{lib}.so"
                        session.storbinary(command, file_in)  # send the file
                        file_in.close()  # close file

            for filepath in self.files:
                with open(filepath, "rb") as file_in: # file to send
                    command = f"STOR {self.session_id}/{os.path.basename(filepath)}"
                    content = file_in.read()
                    content = content.replace(b'\r\n', b'\n')
                    file_obj = BytesIO(content)
                    session.storbinary(command, file_obj)  # send the file
                    file_in.close()  # close file

            self.progress_update.emit(59)
            session.quit()
        except (AttributeError,HTTPError) as e:
            raise AbortException(e) from e

    def runSession(self, hostname, http_port):
        '''
        Call for the remote to execute the setup directory and return when done
        '''
        try:
            url = (
                "http://"
                + str(hostname)
                + ":"
                + str(http_port)
                + f"/run_session?session_id={self.session_id}"
            )
            request.urlopen(url).read() #pylint:disable=R1732
        except (AttributeError,HTTPError) as e:
            raise AbortException(e) from e

    def collectResults(self, hostname, ftp_port, username, password, temp_directory):
        ''' Pull the file and put it to temp_directory/log_0.csv '''
        try:
            if self._is_interrupted:
                return
            self.text_update.emit("Reopening FTP Session...")
            # Instead we want to collect all files as we might not know what
            # they will be at this stage.
            #file_to = os.path.abspath(os.path.join(temp_directory, "log_0.csv"))
            session = ftplib.FTP()
            file_to = os.path.join(temp_directory, 'log_0.csv')
            session.connect(hostname, ftp_port)
            self.progress_update.emit(72)
            # Output: '220 Server ready for new user.'
            session.login(username, password)
            if self._is_interrupted:
                return
            self.text_update.emit("Getting results file...")
            self.progress_update.emit(75)

            with open(file_to, "wb") as file_out:
                command = f"RETR {self.session_id}/log_0.csv"
                session.retrbinary(command, file_out.write)
                file_out.close()  # close file and FTP
                if self._is_interrupted:
                    return
                self.text_update.emit("File Retrieved")
                self.progress_update.emit(79)

            session.quit()
        except (AttributeError,HTTPError) as e:
            raise AbortException(e) from e

    def generateOutputFormats(self):
        '''Pass'''
