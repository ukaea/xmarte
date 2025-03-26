'''
This provides basic functions which should exist between our toolbar groups
'''
import os
import re

from typing import Union

from PyQt5.QtWidgets import QMenu, QAction, QToolBar, QFileDialog, QMessageBox
from PyQt5.QtCore import QSize

from xmarte.qt5.libraries.functions import updateDefaultDialogDir
from xmarte.qt5.plugins.base_plugin import PluginException

extension_finder = re.compile("\((.*?)\)") # pylint:disable=W1401

class BaseFileMenu:
    ''' Shared menu functions '''
    def __init__(self, parent=None, *args, **kwargs): # pylint:disable=W1113, W0613
        self.parent = parent
        super().__init__()
        self.newAction = QAction("&New", self)
        self.newAction.setShortcut("Ctrl+N")
        self.openAction = QAction("&Open...", self)
        self.openAction.setShortcut("Ctrl+O")
        self.saveAction = QAction("&Save", self)
        self.saveAction.setShortcut("Ctrl+S")
        self.exportAction = QAction("&Export", self)
        self.exportAction.setShortcut("Ctrl+E")
        self.importAction = QAction("&Import", self)
        self.importAction.setShortcut("Ctrl+I")
        self.exitAction = QAction("&Exit", self)
        self.exitAction.setShortcut("Alt+F4")

    def newFile(self):
        ''' Clear the current Scene and reset Split View '''
        # Reset App Def
        app_def = self.parent.API.getServiceByName('ApplicationDefinition')
        app_def.resetDefaults()
        app_def.loadConfig(app_def.configuration)
        app_def.initGAMList()
        class EmptyState:
            ''' Simulate Empty State Machine to avoid errors at startup '''
            def write(self, config_writer):
                ''' Fake Write if state machine not yet established
                - allows to still write to cfg on the grander application scope '''
        app_def.statemachine = EmptyState()
        app_def.statemachine_serialized = None
        # Reset Test Def
        self.parent.test_definition = {}
        # Reset States and scenes
        state_service = self.parent.API.getServiceByName('StateDefinitionService')
        state_service.setupDefaultStates()
        self.parent.state_scenes = {}

        state_service.setupStateScenes()

        state_service.thread_wdgt.currentIndexChanged.disconnect()
        state_service.thread_wdgt.clear()
        state_service.populateCombos(self.parent.state_scenes)
        state_service.thread_wdgt.currentIndexChanged.connect(state_service.changeThread)
        state, thread = state_service.resolveThread()

        state_service.updateScene(state, thread)
        # Reset message definition
        app_def.http_messages = []
        self.parent.API.getServiceByName('DataManager').clearData()

    def createFilemenu(self, file_menu: Union[QMenu, QToolBar]):
        ''' Setup the generic file menu items '''
        self.newAction = QAction("&New", self)
        self.openAction = QAction("&Open...", self)
        self.saveAction = QAction("&Save", self)
        self.exportAction = QAction("&Export", self)
        self.importAction = QAction("&Import", self)
        self.exitAction = QAction("&Exit", self)
        self.newAction.triggered.connect(self.newFile)
        self.exportAction.triggered.connect(self.exportfile)
        self.importAction.triggered.connect(self.importfile)
        self.openAction.triggered.connect(self.openFile)
        self.saveAction.triggered.connect(self.saveFile)
        self.exitAction.triggered.connect(self.parent.exit)
        if isinstance(file_menu, QToolBar):
            file_menu.setIconSize(QSize(50, 50))
        file_menu.addAction(self.newAction)
        file_menu.addAction(self.importAction)
        file_menu.addAction(self.openAction)
        file_menu.addAction(self.saveAction)
        file_menu.addAction(self.exportAction)
        file_menu.addAction(self.exitAction)

    def saveFile(self):
        ''' Save network to file '''
        default_dir = ""
        if "file_location" in self.parent.settings["GeneralPanel"].keys():
            default_dir = self.parent.settings["GeneralPanel"]["file_location"]

        file_extension = self.parent.settings["GeneralPanel"]["file_extension"]
        file_description = self.parent.settings["GeneralPanel"]["file_description"]

        file_filter = file_description + " (*." + file_extension + ");;All Files (*)"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Project", default_dir, file_filter
        )
        if filename:
            # Check whether file extension = .xmt
            ext = self.parent.settings["GeneralPanel"]["file_extension"]
            if filename.rsplit('.', maxsplit=1)[-1] != ext:
                # Open a dialogue box to check whether this is deliberate
                msgBox = QMessageBox()
                msgBox.setText(f"Not saved as a .{ext} file")
                msgBox.setInformativeText(
                    f"Would you like to change the extension to .{ext}?"
                )
                msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msgBox.setDefaultButton(QMessageBox.Yes)
                ret = msgBox.exec()
                # return code 16384 = "Yes"
                if ret == QMessageBox.Yes:
                    filename = filename.split('.', maxsplit=1)[0] + f".{ext}"

            # Now save to file in our new format
            self.parent.API.saveToFile(filename)

            # Now update that nothing has been modified since last save
            self.parent.scene.has_been_modified = False

            self.parent.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename)
            # Save new default directory
            updateDefaultDialogDir(os.path.dirname(filename))

    def importfile(self):
        """Making this more so it's a plugin based system"""
        default_dir = ""
        if "file_location" in self.parent.settings["GeneralPanel"].keys():
            default_dir = self.parent.settings["GeneralPanel"]["file_location"]

        sfilter = ""
        for file_handler in self.parent.file_handlers:
            sfilter += (
                file_handler.getDescription().replace(" ", "_")
                + " (*"
                + file_handler.getFileExtension()
                + ");;"
            )
        sfilter = sfilter[:-2]
        filename, _ = QFileDialog.getOpenFileName(self, "Open file", default_dir, sfilter)

        if filename:
            split_tup = os.path.splitext(filename)
            file_extension = split_tup[1]
            self.parent.scene.large_import = True
            def getExt(a):
                return a.getFileExtension().strip('*')
            file_handler = next(
                (a for a in self.parent.file_handlers if getExt(a) == file_extension),
                None)

            if file_handler is None:
                raise PluginException(
                    "No plugin found to load selected file type, an error has occurred"
                )
            self.parent.scene.clear()
            try:
                file_handler.loadFile(filename)

                self.parent.scene.large_import = False
                self.parent.scene.has_been_modified = True

                self.parent.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename)
                config_manager = next(
                    a for a in self.parent.services if a.__class__.__name__ == "ConfigManager")
                config_manager.saveSettings(self.parent.settings)
            except RuntimeError as e:
                QMessageBox.critical(
                    self.parent, 'Error during import of .cfg', str(e), QMessageBox.Ok
                )

    def exportfile(self):
        ''' Export to file '''
        default_dir = ""
        if "file_location" in self.parent.settings["GeneralPanel"].keys():
            default_dir = self.parent.settings["GeneralPanel"]["file_location"]

        sfilter = ""
        for file_handler in self.parent.file_handlers:
            sfilter += (
                file_handler.getDescription().replace(" ", "_")
                + " ("
                + file_handler.getFileExtension()
                + ");;"
            )
        filename = QFileDialog.getSaveFileName(
            self, "Export file", default_dir, sfilter
        )
        if filename[0]:
            split_tup = list(os.path.splitext(filename[0]))
            file_extension = split_tup[1]
            res = extension_finder.search(filename[1])
            filter_extension = res.group(1).strip('*')
            # Re-written so the the file extension is automatically appended. The only possible
            # extensions are those that there are plugins for. I'm deleting the check for whether
            # a plugin exists for the filetype, because only filetypes that there are plugins
            # for can be selected from.
            if file_extension == "":
                file_extension = filter_extension
            if file_extension != filter_extension.strip('*'):
                # Open a dialogue box to point out weird extension
                msgBox = QMessageBox()
                msgBox.setText(f"No plugin to save as {file_extension}")
                msgBox.setInformativeText(
                    f"Would you like to change the extension to {filter_extension}?"
                )
                msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msgBox.setDefaultButton(QMessageBox.Yes)
                ret = msgBox.exec()
                # return code 16384 = "Yes"
                if ret == 16384:
                    file_extension = filter_extension.strip('*')
            split_tup[1] = file_extension
            filename = tuple(split_tup)
            def getExt(a):
                return a.getFileExtension().strip('*')
            file_handler = next(
                (a for a in self.parent.file_handlers if getExt(a) == file_extension),
                None)

            if file_handler is None:
                msgBox = QMessageBox.warning(self,"Error",f"No plugin to save as {file_extension}")
            else:
                text = file_handler.createFileContents()
                with open("".join(filename), "w", encoding='UTF-8') as newfile:
                    newfile.write(text)

            self.parent.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename[0])
            config_manager = next(
                a for a in self.parent.services if a.__class__.__name__ == "ConfigManager")
            config_manager.saveSettings(self.parent.settings)

    def openFile(self):
        ''' Open a file '''
        default_dir = ""
        if "file_location" in self.parent.settings["GeneralPanel"].keys():
            default_dir = self.parent.settings["GeneralPanel"]["file_location"]

        file_extension = self.parent.settings["GeneralPanel"]["file_extension"]
        file_description = self.parent.settings["GeneralPanel"]["file_description"]

        file_filter = file_description + " (*." + file_extension + ")"

        filename, _ = QFileDialog.getOpenFileName(
            self, "Open file", default_dir, file_filter + ";;All files (*)"
        )  # Options separated by ;;
        if filename:
            prev = self.parent.scene.large_import
            self.parent.scene.large_import = True

            self.parent.API.loadFile(filename)

            self.parent.scene.large_import = prev
            self.parent.scene.has_been_modified = False

            self.parent.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename)
            updateDefaultDialogDir(os.path.dirname(filename))
