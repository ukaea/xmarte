''' This service provides the ability to compile C++ code from the UI itself '''
import os
import subprocess
import shutil
import ftplib
from urllib import request
from urllib.error import HTTPError

from xmarte.qt5.libraries.functions import decryptPassword

from xmarte.qt5.services.service import Service


class Compiler(Service):
    ''' The service that provides the interface and wraps around the compilation functionality '''
    service_name = 'Compiler'

    def __init__(self, application):
        super().__init__(application)
        self._is_interrupted = False
        self.session_id = ''
        self.compile_settings = {}

    def compileLocally(self, directory, pipe=None):
        ''' Configured for local compilation - activate through Popen '''
        self.compile_settings = self.application.settings['CompilationPanel']
        # Define the command to be run
        command = ["make", "-f", "Makefile.x86-linux", "clean"]
        directory = str(os.path.abspath(directory))
        # Ensure the directory exists
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"The directory {directory} does not exist.")

        # Prepare the subprocess arguments
        subprocess_args = {
            'cwd': directory,  # Set the working directory
            'stdout': pipe,    # Redirect stdout to the provided pipe if any
            'stderr': subprocess.STDOUT  # Redirect stderr to stdout
        }

        try:
            if os.name == "nt":
                replacements = [('\\\\','/'),('\\','/'),(':','')]
                directory = directory.lower()
                for replacement_1, replacement_2 in replacements:
                    directory = directory.replace(replacement_1, replacement_2)
                directory = "/mnt/" + directory
                volume = f"{directory}:/root/tests"
                image = "sudilav1/xmarte:main"
                newcommand = f"wsl docker run -v {volume} -w /root/tests {image}".split()
                command = newcommand + command
            # Run the command and wait for it to complete
            with subprocess.Popen(command, **subprocess_args) as process:
                process.communicate()  # Wait for the subprocess to complete
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command)

            command = ["make", "-f", "Makefile.x86-linux"]

            if os.name == "nt":
                newcommand = f"wsl docker run -v {volume} -w /root/tests {image}".split()
                command = newcommand + command

            # Run the command and wait for it to complete
            with subprocess.Popen(command, **subprocess_args) as process:
                process.communicate()  # Wait for the subprocess to complete
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command)

        except subprocess.CalledProcessError as e:
            print(f"Command {e.cmd} failed with return code {e.returncode}")
            raise

    def log(self, text):
        ''' Log to the cmd terminal '''
        print(text)

    def uploadFile(self, ftp, local_file_path, remote_file_path):
        ''' Upload a file to the compile server '''
        with open(local_file_path, 'rb') as file:
            ftp.storbinary(f'STOR {remote_file_path}', file)

    def uploadDirectory(self, ftp, local_dir, remote_dir):
        ''' Upload an entire directory to the compile server '''
        # Change to the remote directory
        if remote_dir not in ftp.nlst():
            ftp.mkd(remote_dir)
        ftp.cwd(remote_dir)

        # Iterate over all items in the local directory
        for item in os.listdir(local_dir):
            local_path = os.path.join(local_dir, item)
            if os.path.isfile(local_path):
                self.uploadFile(ftp, local_path, item)
            elif os.path.isdir(local_path):
                # Create the remote directory and upload its contents
                if item not in ftp.nlst():
                    ftp.mkd(item)
                self.uploadDirectory(ftp, local_path, item)

        # Go back to the parent directory
        ftp.cwd('..')

    def downloadFile(self, ftp, remote_file_path, local_file_path):
        ''' Download a file from the compile server '''
        with open(local_file_path, 'wb') as file:
            ftp.retrbinary(f'RETR {remote_file_path}', file.write)

    def downloadDirectory(self, ftp, remote_dir, local_dir):
        ''' Download a directory from the compile server '''
        # Ensure the local directory exists
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        # Change to the remote directory
        ftp.cwd(remote_dir)

        # List items in the remote directory
        items = ftp.nlst()

        for item in items:
            # Skip special directories
            if item in ['.', '..']:
                continue

            remote_path = f"{remote_dir}/{item}"
            local_path = os.path.join(local_dir, item)

            # Check if item is a directory or a file
            try:
                ftp.cwd(item)
                # If we can change directory, it's a directory
                if not os.path.exists(local_path):
                    os.mkdir(local_path)
                self.downloadDirectory(ftp, remote_path, local_path)
            except HTTPError:
                # If we can't change directory, it's a file
                self.downloadFile(ftp, remote_path, local_path)

        # Go back to the parent directory
        ftp.cwd('..')

    def compileOnServer(self):
        ''' Compile on a server - establish a session with the runner on the server and
        execute '''
        self._is_interrupted = False
        self.compile_settings = self.application.settings['CompilationPanel']
        hostname = self.compile_settings['remote_server']
        http_port = self.compile_settings['remote_http_port']
        ftp_port = self.compile_settings['remote_ftp_port']
        username = self.compile_settings['ftp_username']
        password = self.compile_settings['ftp_password']
        self.log("Requesting Session from compile server...")
        # Get a session ID
        url = "http://" + str(hostname) + ":" + str(http_port) + "/start_session"
        self.session_id = request.urlopen(url, timeout=10).read().decode("ASCII") # pylint: disable=R1732
        self.log("Open FTP session with server...")

        # Push files to FTP of session
        session = ftplib.FTP()
        session.connect(hostname, int(ftp_port))
        # Output: '220 Server ready for new user.'
        session.login(decryptPassword(username), decryptPassword(password))
        if self._is_interrupted:
            return
        self.log("Sending files to server...")

        self.uploadDirectory(session, self.compile_settings['temp_folder'], self.session_id)

        session.quit()
        if self._is_interrupted:
            return
        self.log("Triggering Server Execution...")

        url = (
            "http://"
            + str(hostname)
            + ":"
            + str(http_port)
            + f"/run_session?session_id={self.session_id}"
        )
        request.urlopen(url).read() # pylint: disable=R1732
        if self._is_interrupted:
            return
        self.log("Server has finished session")
        if self._is_interrupted:
            return
        self.log("Collecting Results...")
        # Push files to FTP of session
        session = ftplib.FTP()
        session.connect(hostname, int(ftp_port))
        # Output: '220 Server ready for new user.'
        session.login(decryptPassword(username), decryptPassword(password))
        build_dir = os.path.join(self.compile_settings['temp_folder'],
                                    "Build", "x86-linux","Packets")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        os.makedirs(build_dir, exist_ok=True)
        session.cwd(os.path.join(self.session_id,"Build", "x86-linux","Packets"))
        items = session.nlst()
        for item in items:
            os.makedirs(os.path.join(build_dir, item), exist_ok=True)
            static = os.path.join(item, item+".a")
            shared = os.path.join(item, item+".so")

            self.downloadFile(session, shared, os.path.join(build_dir, item, item+".so"))
            self.downloadFile(session, static, os.path.join(build_dir, item, item+".a"))

        session.quit()

    def getDirectoryContentsWithRelativePaths(self, root_dir):
        """
        Get the contents of a directory recursively with their relative paths.

        :param root_dir: The root directory to start the recursion from.
        :return: A list of file and directory paths relative to the root directory.
        """
        relative_paths = []

        for root, dirs, files in os.walk(root_dir):
            for name in dirs:
                dir_path = os.path.relpath(os.path.join(root, name), root_dir)
                relative_paths.append(dir_path)
            for name in files:
                file_path = os.path.relpath(os.path.join(root, name), root_dir)
                relative_paths.append(file_path)

        return relative_paths

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
