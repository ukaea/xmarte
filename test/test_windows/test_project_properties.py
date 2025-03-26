'''Testing the project properties panel.'''

from martepy.marte2.qt_classes import MessageConfigWindow

from ..utilities import *


def test_app_name(mainwindow, qtbot) -> None:
    '''
    Check that changes to the app name in the project properties panel
    are updated in the app definition and the split view window.
    '''
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)  # add a constant
    mainwindow.leftpanel.tab_wgt.setCurrentIndex(1)  # switch to the project properties panel
    mainwindow.leftpanel.project_panel.app_edt.setText('TestAppName')  # change the app name
    assert mainwindow.leftpanel.project_panel.app_edt.text() == 'TestAppName'  # check the line edit updated
    assert mainwindow.API.getServiceByName('ApplicationDefinition').configuration['app_name'] == 'TestAppName'  # app def updated
    assert '$TestAppName' in (text := getSplitText(mainwindow))  # split view updated
    assert '$App' not in text

    setApplicationName(mainwindow, 'TestAppName')  # further assertion

def test_timing_name(mainwindow, qtbot) -> None:
    '''
    Check that changes to the timing datasource name in the project
    properties panel are updated in the app definition and the split view.
    '''
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)  # add a constant
    mainwindow.leftpanel.tab_wgt.setCurrentIndex(1)  # switch to the project properties panel
    mainwindow.leftpanel.project_panel.t_edt.setText('TestTimingsDataSource')  # change the timing datasource name
    assert mainwindow.leftpanel.project_panel.t_edt.text() == 'TestTimingsDataSource'  # check the line edit updated
    assert mainwindow.API.getServiceByName('ApplicationDefinition').configuration['misc']['timingsource'] == 'TestTimingsDataSource'  # app def updated
    assert 'TimingDataSource = TestTimingsDataSource' in (text := getSplitText(mainwindow))  # split view updated
    assert 'TimingDataSource = TimingsDataSource' not in text

    setTimingDataSource(mainwindow, 'TestTimingsDataSource')  # further assertion

def test_gam_datasources(mainwindow, qtbot) -> None:
    '''
    Add multiple new GAM Datasources and connect them to constant block outputs
    then check that the split view is updated to reflect this.
    '''
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)  # add a constant
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)
    mainwindow.leftpanel.tab_wgt.setCurrentIndex(1)  # switch to the project properties panel
    qtbot.mouseClick(mainwindow.leftpanel.project_panel.g_edt.add_button, Qt.LeftButton)  # add a GAM datasource
    qtbot.mouseClick(mainwindow.leftpanel.project_panel.g_edt.add_button, Qt.LeftButton)
    assert mainwindow.leftpanel.project_panel.g_edt.listbox.count() == 3  # check there are 3 gam datasources
    assert len(mainwindow.scene.nodes) == 3  # check there are 3 constants

    for i in range(3):  # configure each constant to output to a different gam datasource
        mainwindow.scene.nodes[i].onDoubleClicked(None)  # open configbarbox of constant
        mainwindow.rightpanel.configbarBox.itemAt(4).widget().setText('1')  # add a signal
        mainwindow.rightpanel.configbarBox.itemAt(5).widget().clicked.emit()  # configure the signal
        mainwindow.newwindow.signal_tbl.item(0, 1).setText(f'DDB{i}')  # set the GAM datasource field
        assert mainwindow.newwindow.signal_tbl.item(0, 1).text() == f'DDB{i}'  # check the item updated
        qtbot.mouseClick(mainwindow.newwindow.save_button, Qt.LeftButton)  # save the configured signal

    text: str = getSplitText(mainwindow)  # get the split view text
    for i in range(3):  # check each gam datasource is written
        assert f'+DDB{i} = {{\n            Class = GAMDataSource\n        }}' in text

def test_gam_scheduler(mainwindow, qtbot) -> None:
    '''
    Check that changing the GAM Scheduler updates the app definition and the split view window.
    '''
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)  # add a constant
    mainwindow.leftpanel.tab_wgt.setCurrentIndex(1)  # switch to the project properties panel
    mainwindow.leftpanel.project_panel.sched_combo.setCurrentIndex(1)  # change the gam scheduler
    assert mainwindow.leftpanel.project_panel.sched_combo.currentText() == 'FastScheduler'  # check the combobox updated
    assert mainwindow.API.getServiceByName('ApplicationDefinition').configuration['misc']['scheduler'] == 'FastScheduler'  # app def udpated
    assert '+Scheduler = {\n        Class = FastScheduler\n' in (text := getSplitText(mainwindow))  # split view updated
    assert '+Scheduler = {\n        Class = GAMScheduler\n' not in text

    setScheduler(mainwindow, 'FastScheduler')  # further assertion

def test_http(mainwindow, qtbot) -> None:
    '''
    Check that enabling the http service and changing the directory are updated in the split view.
    '''
    qtbot.mouseClick(mainwindow.leftpanel.toolboxes.marte2_functions.gbox.itemAt(0).widget(), Qt.LeftButton)  # add a constant
    mainwindow.leftpanel.tab_wgt.setCurrentIndex(1)  # switch to the project properties panel
    enableHTTP(mainwindow)  # enable HTTP server and check split view is udpated
    setHTTPFolder(mainwindow, '/test/folder')  # change HTTP folder and check split view is updated
    setHTTPMessage(mainwindow)  # configure a message and check split view is updated
