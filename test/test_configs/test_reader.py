
import os
import glob
import pdb
from PyQt5.QtCore import pyqtRemoveInputHook

from qtpy.QtWidgets import QFileDialog

from test.utilities import *

def test_configurations(mainwindow, monkeypatch):
    '''
    This will be a dynamic test generation of all RT-App configs available in padova
    '''

    class Cfg_analysis():
        def __init__(self, name):
            self.filename = name
            self.passed = False
            self.no_of_GAMS = 0
            self.no_of_datasources = 0
            self.no_of_states = 0
            self.browser = False

    configs_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../MARTe2-demos-padova', 'Configurations')

    files = glob.glob(os.path.join(configs_folder, 'RTApp-[0-9]*-[0-9]*.cfg'))
    blacklisted_files = []
    analyses = []
    # Now try to import each one
    for filepath in files:
        # Get base name
        mainwindow.fileToolBar.newAction.trigger()
        assert len(mainwindow.scene.nodes) == 0
        name = os.path.basename(filepath)
        if name not in blacklisted_files:
            # Import
            import_file = os.path.join(filepath)
            monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'cfg (*.cfg)'))
            mainwindow.fileToolBar.importAction.trigger()
            new_analysis = Cfg_analysis(name)
            if len(mainwindow.scene.nodes) == 0:
                new_analysis.passed = False
            else:
                new_analysis.passed = True
                gams = 0
                datasources = 0
                states = 0
                # TODO: Iterate through nodes in scene. Is there a HTTP browser? Work out how many states, GAMs and datasources
#               #for node in mainwindow.scene.nodes:
            analyses.append(new_analysis)
            # Test against that it has certain things
            # For each testable item, create a CSV file corresponding to it's basename
#            test_file = name + '.csv'
            # Open, check criteria.
pass

def test_split_view(mainwindow, monkeypatch):
    # Test Split view with no nodes in scene
    mainwindow.API.application.file_handlers[0].generatesplit()
    configs_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'MARTe2-demos-padova', 'Configurations')
    file = os.path.join(configs_folder, 'RTApp-1-1.cfg')
    mainwindow.fileToolBar.newAction.trigger()
    import_file = os.path.join(file)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (import_file, 'cfg (*.cfg)'))
    mainwindow.fileToolBar.importAction.trigger()
    # Test Split view with nodes in scene
    mainwindow.API.application.file_handlers[0].generatesplit()
    return

def test_create_delete(mainwindow):
    current_folder = os.path.dirname(os.path.dirname(__file__))
    test_file = os.path.join(current_folder, "delete_me.test")
    with open(test_file, "w") as f:
        f.write("Should be deleted by test/test_configs/test_reader.py")
        f.close()
    mainwindow.API.application.file_handlers[0]._delete(test_file)
    return
