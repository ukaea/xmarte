
import pytest
import pdb
import os
import shutil

from test.utilities import *
from xmarte.qt5.services.type_db.windows.types_window import TypesDBWindow

from PyQt5.QtWidgets import QMessageBox

@pytest.fixture
def test_type_window(mainwindow, qtbot, monkeypatch):
    adv_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Advanced')
    type_action = next(a for a in adv_menu.menu().actions() if a.text() == '&Type Database')
    type_action.triggered.emit()
    assert mainwindow.newwindow.__class__ == TypesDBWindow

    # We've already preloaded some header files in the conftest
    assert mainwindow.newwindow.main_pnl.left_list.count() == 3
    text_list = {'test3': '5.7','test2': '2.2','test1': '2.2'}
    for i in range(3):
        assert mainwindow.newwindow.main_pnl.left_list.item(i).text() in list(text_list.keys())
        assert list(text_list.keys())[i] in [mainwindow.newwindow.main_pnl.left_list.item(a).text() for a in range(3)]
        
    # Test that it opens with the right type definition

    assert mainwindow.newwindow.type_edit.text() == mainwindow.newwindow.main_pnl.left_list.currentItem().text()
    version = text_list[mainwindow.newwindow.main_pnl.left_list.currentItem().text()]
    assert mainwindow.newwindow.version_lbl.text() == f"Version: {version.replace('_','.')}"
    
    # Make sure we set for aelmPkt
    aelmItem = next(mainwindow.newwindow.main_pnl.left_list.item(a) for a in range(mainwindow.newwindow.main_pnl.left_list.count()) if mainwindow.newwindow.main_pnl.left_list.item(a).text() == 'test1')
    mainwindow.newwindow.main_pnl.left_list.setCurrentItem(aelmItem)
    return mainwindow

def test_type_loaded(test_type_window, qtbot):
    mainwindow = test_type_window
    text_list = {'test3': '5.7','test2': '2.2','test1': '2.2'}
    assert mainwindow.newwindow.type_edit.text() == mainwindow.newwindow.main_pnl.left_list.currentItem().text()
    version = text_list[mainwindow.newwindow.main_pnl.left_list.currentItem().text()]
    assert mainwindow.newwindow.version_lbl.text() == f"Version: {version.replace('_','.')}"
    
    assert mainwindow.newwindow.table_wgt.rowCount() == 15
    assert mainwindow.newwindow.table_wgt.columnCount() == 3

    names = ['sequenceNo','sampleTime','available','saturated','devHz','freq','DampingRaw','DampingNorm','TimeDamping','devHz_sta','freq_sta','DampingRaw_sta','DampingNorm_sta','TimeDamping_sta','test1Pkt_488000002']
    types = ['uint32','uint32','uint32','uint32','float32','float32','float32','float32','float32','uint32','uint32','uint32','uint32','uint32','uint32']
    lengths = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    for row in range(15):
        assert mainwindow.newwindow.table_wgt.item(row, 0).text() == names[row]
        assert mainwindow.newwindow.table_wgt.cellWidget(row, 1).text() == types[row]
        assert int(mainwindow.newwindow.table_wgt.item(row, 2).text()) == lengths[row]


def test_change_type_rows(test_type_window, qtbot):
    mainwindow = test_type_window
    # Now test that if we make the length 1.5 it will be ignored
    # If however we make it 6, it will be modified in the GUI and the filedef
    # 
    mainwindow.newwindow.table_wgt.item(6, 0).setText('AEFr')
    mainwindow.newwindow.table_wgt.cellWidget(6, 1).setText('uint8')
    mainwindow.newwindow.table_wgt.cellWidget(6, 1).editingFinished.emit()
    mainwindow.newwindow.table_wgt.item(6, 2).setText('8')

    mainwindow.newwindow.reset_btn.clicked.emit()

    assert mainwindow.newwindow.table_wgt.item(6, 0).text() == 'DampingRaw'
    assert mainwindow.newwindow.table_wgt.cellWidget(6, 1).text() == 'float32'
    assert mainwindow.newwindow.table_wgt.item(6, 2).text() == '1'

    mainwindow.newwindow.table_wgt.item(6, 0).setText('AEFr')
    mainwindow.newwindow.table_wgt.cellWidget(6, 1).setText('uint8')
    mainwindow.newwindow.table_wgt.cellWidget(6, 1).editingFinished.emit()
    mainwindow.newwindow.table_wgt.item(6, 2).setText('8')

    mainwindow.newwindow.save_btn.clicked.emit()

    assert mainwindow.newwindow.table_wgt.item(6, 0).text() == 'AEFr'
    assert mainwindow.newwindow.table_wgt.cellWidget(6, 1).text() == 'uint8'
    assert mainwindow.newwindow.table_wgt.item(6, 2).text() == '8'

    mainwindow.newwindow.table_wgt.item(6, 2).setText('8.792749')
    assert mainwindow.newwindow.table_wgt.item(6, 2).text() == '8'

    mainwindow.newwindow.table_wgt.item(6, 2).setText('8,792749')
    assert mainwindow.newwindow.table_wgt.item(6, 2).text() == '8'

    mainwindow.newwindow.table_wgt.item(6, 2).setText('8hhegf')
    assert mainwindow.newwindow.table_wgt.item(6, 2).text() == '8'

    mainwindow.newwindow.table_wgt.cellWidget(6, 1).setText('8hhegf')
    assert mainwindow.newwindow.table_wgt.cellWidget(6, 1).text() == 'uint8'

@pytest.fixture
def test_add_new_type(test_type_window, qtbot):
    mainwindow = test_type_window

    mainwindow.newwindow.add_rem_btn.add_btn.clicked.emit()

    assert 'new_packet' in [mainwindow.newwindow.main_pnl.left_list.item(a).text() for a in range(mainwindow.newwindow.main_pnl.left_list.count())]
    new_packet = next(mainwindow.newwindow.main_pnl.left_list.item(a) for a in range(mainwindow.newwindow.main_pnl.left_list.count()) if mainwindow.newwindow.main_pnl.left_list.item(a).text() == 'new_packet')
    mainwindow.newwindow.main_pnl.left_list.setCurrentItem(new_packet)
    assert mainwindow.newwindow.version_lbl.text() == "Version: 1.0"
    assert mainwindow.newwindow.type_edit.text() == "new_packet"
    assert mainwindow.newwindow.table_wgt.rowCount() == 0
    assert mainwindow.newwindow.table_wgt.columnCount() == 3

    for i in range(6):
        mainwindow.newwindow.type_add_btns.add_btn.clicked.emit()

    mainwindow.newwindow.save_btn.clicked.emit()

    assert mainwindow.newwindow.table_wgt.rowCount() == 6
    
    names = ['new_field'] + [f'new_field{i+1}' for i in range(5)]

    for i in range(6):
        assert mainwindow.newwindow.table_wgt.item(i, 0).text() == names[i]
        assert mainwindow.newwindow.table_wgt.cellWidget(i, 1).text() == 'uint32'
        assert mainwindow.newwindow.table_wgt.item(i, 2).text() == '1'
        
    mainwindow.newwindow.table_wgt.selectRow(3)
    mainwindow.newwindow.type_add_btns.remove_btn.clicked.emit()
    mainwindow.newwindow.table_wgt.selectRow(3)
    mainwindow.newwindow.type_add_btns.remove_btn.clicked.emit()
    
    mainwindow.newwindow.reset_btn.clicked.emit()

    for i in range(6):
        assert mainwindow.newwindow.table_wgt.item(i, 0).text() == names[i]
        assert mainwindow.newwindow.table_wgt.cellWidget(i, 1).text() == 'uint32'
        assert mainwindow.newwindow.table_wgt.item(i, 2).text() == '1'

    mainwindow.newwindow.table_wgt.selectRow(3)
    names.pop(3)
    mainwindow.newwindow.type_add_btns.remove_btn.clicked.emit()
    mainwindow.newwindow.table_wgt.selectRow(3)
    names.pop(3)
    mainwindow.newwindow.type_add_btns.remove_btn.clicked.emit()

    for i in range(4):
        assert mainwindow.newwindow.table_wgt.item(i, 0).text() == names[i]
        assert mainwindow.newwindow.table_wgt.cellWidget(i, 1).text() == 'uint32'
        assert mainwindow.newwindow.table_wgt.item(i, 2).text() == '1'

    mainwindow.newwindow.save_btn.clicked.emit()

    return mainwindow

def test_add_rm_type(test_add_new_type, qtbot, monkeypatch):
    mainwindow = test_add_new_type
    new_packet = next(mainwindow.newwindow.main_pnl.left_list.item(a) for a in range(mainwindow.newwindow.main_pnl.left_list.count()) if mainwindow.newwindow.main_pnl.left_list.item(a).text() == 'new_packet')
    mainwindow.newwindow.main_pnl.left_list.setCurrentItem(new_packet)
    
    
    monkeypatch.setattr(
        QMessageBox, 'question', lambda *args: QMessageBox.Ok
    )
    mainwindow.newwindow.add_rem_btn.remove_btn.clicked.emit()
    assert 'new_packet' not in [mainwindow.newwindow.main_pnl.left_list.item(a).text() for a in range(mainwindow.newwindow.main_pnl.left_list.count())]
    
def test_close_cancel(test_add_new_type, qtbot, monkeypatch):
    mainwindow = test_add_new_type
    type_wnd = mainwindow.newwindow
    def mock_question(*args, **kwargs):
        return QMessageBox.Cancel
    monkeypatch.setattr(QMessageBox, 'question', mock_question)
    mainwindow.newwindow.add_rem_btn.add_btn.clicked.emit()
    type_wnd.close()
    
def test_close_save(test_add_new_type, qtbot, monkeypatch):
    mainwindow = test_add_new_type
    type_wnd = mainwindow.newwindow
    def mock_question(*args, **kwargs):
        return QMessageBox.Save
    monkeypatch.setattr(QMessageBox, 'question', mock_question)
    mainwindow.newwindow.add_rem_btn.add_btn.clicked.emit()
    type_wnd.close()

def test_import_export(test_add_new_type, qtbot, monkeypatch):
    mainwindow = test_add_new_type
    type_wnd = mainwindow.newwindow
    folder_path = os.path.join(TEST_FILES_DIR, 'test_type_dir')
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.mkdir(folder_path)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args, **kwargs: folder_path)
    type_wnd.menuBar().actions()[0].menu().actions()[1].trigger()
    assert sorted(os.listdir(folder_path)) == ['new_packet_1_1.h', 'std_import.h', 'test1_2_2.h', 'test2_2_2.h', 'test3_5_7.h']
    type_wnd.menuBar().actions()[0].menu().actions()[0].trigger()
    
def test_save_all(test_add_new_type, qtbot, monkeypatch):
    mainwindow = test_add_new_type
    type_wnd = mainwindow.newwindow
    type_wnd.updateDb()
    
