import os
import glob
import pdb
from PyQt5.QtCore import pyqtRemoveInputHook

from qtpy.QtWidgets import QFileDialog

from test.utilities import *

def test_export_import(mainwindow, monkeypatch):
    '''
    This will be a dynamic test generation of all RT-App configs available in padova
    Importing them and then exporting to JSON, then it will import the JSON and finally
    export as cfg - the test will be if the cfg matches its original in terms of nodes.
    '''

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