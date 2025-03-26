
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QInputDialog

from martepy.functions.extra_functions import getname

from test.utilities import *
from xmarte.qt5.services.state_service.states import StateDefinitionService
from xmarte.qt5.services.state_service.widgets.state_message_preview import StateMessagePreview
from xmarte.qt5.services.state_service.widgets.state_edge import (
    NextErrorStateEdge, NextStateEdge, StateGraphicsEdge, StateEdge, GraphicsEdgePathArc
)

def test_state_initialisation(mainwindow) -> None:
    '''Check the default state and thread initialisation.'''
    assert len(mainwindow.state_scenes) == 2  # initialises with two states - State1 and Error
    for default_threads in mainwindow.state_scenes.values():
        assert len(default_threads) == 1  # each state initialises with one default thread

    state_def = mainwindow.API.getServiceByName('ApplicationDefinition').statemachine
    assert len(state_def.states) == 3  # INITIAL, STATE1, ERROR
    for state in state_def.states:
        if getname(state) == 'INITIAL':
            assert len(state.objects) == 1
            assert getname(state.objects[0]) == 'START'
        elif getname(state) == 'STATE1':
            assert len(state.objects) == 1
            assert getname(state.objects[0]) == 'ERROR'
        elif getname(state) == 'ERROR':
            assert len(state.objects) == 2
            assert getname(state.objects[0]) == 'ENTER'
            assert getname(state.objects[1]) == 'RESET'

@pytest.fixture
def state_machine(mainwindow, qtbot) -> None:
    '''Open the state machine window.'''
    qtbot.mouseClick(mainwindow.API.getServiceByName('StateDefinitionService').state_machine, Qt.LeftButton)
    return mainwindow.newwindow

def test_add_remove_state(state_machine, qtbot, monkeypatch) -> None:
    '''Test adding and removing a state in the state machine window.'''
    assert len(state_machine.application_states) == 2
    qtbot.mouseClick(state_machine.add_btn, Qt.LeftButton)  # add state
    assert len(state_machine.application_states) == 3

    qtbot.mouseClick(state_machine.rem_btn, Qt.LeftButton)  # try to remove before selecting
    assert len(state_machine.application_states) == 3

    item = state_machine.statetree.model.findItems('STATE')
    state_machine.removeState(item[0])  # remove state
    assert len(state_machine.application_states) == 2

    monkeypatch.setattr(QMessageBox, 'information', lambda *args: QMessageBox.Ok)
    item = state_machine.statetree.model.findItems('INITIAL')
    state_machine.removeState(item[0])  # try to remove initial state
    assert len(state_machine.application_states) == 2

    monkeypatch.setattr(QMessageBox, 'information', lambda *args: QMessageBox.Ok)
    item = state_machine.statetree.model.findItems('ERROR')
    state_machine.removeState(item[0])  # try to remove error state
    assert len(state_machine.application_states) == 2

def test_save_state(state_machine, qtbot) -> None:
    '''Test saving a state machine configuration.'''
    qtbot.mouseClick(state_machine.add_btn, Qt.LeftButton)
    state_machine.menuBar().children()[1].actions()[0].trigger()

def test_state_name_change(state_machine) -> None:
    '''Test changing the name of a state.'''
    item = state_machine.statetree.model.findItems('STATE1')
    state_machine.stateClicked(item[0])
    state_machine.configBox.name_edt.setText('STATE1_test')
    assert state_machine.configBox.name_edt.text() == 'STATE1_test'

def test_add_remove_message(state_machine, qtbot) -> None:
    '''Test configuring messages for an event.'''
    item = state_machine.statetree.model.findItems('STATE1')
    event = item[0].child(0)
    state_machine.eventClicked(event)
    qtbot.mouseClick(state_machine.configBox.config_msg_btn, Qt.LeftButton)
    msg_window = state_machine.configBox.msg_window
    qtbot.mouseClick(msg_window.add_remmsg.add_btn, Qt.LeftButton)
    qtbot.mouseClick(msg_window.add_remmsg.remove_btn, Qt.LeftButton)

def test_add_remove_event(state_machine, monkeypatch) -> None:
    '''Test adding and removing events from a state.'''
    state = state_machine.statetree.model.findItems('STATE1')
    assert state[0].rowCount() == 1  # 1 event
    monkeypatch.setattr(QInputDialog, 'getText', lambda *args, **kwargs: ('TEST', True))
    monkeypatch.setattr(QInputDialog, 'getItem', lambda *args, **kwargs: ('STATE1', True))
    state_machine.statetree.addEvent(state[0])
    assert state[0].rowCount() == 2  # 2 events
    event = state[0].child(1)
    state_machine.statetree.deleteEvent(event)
    assert state[0].rowCount() == 1  # 1 event
    event = state[0].child(0)
    state_machine.statetree.deleteEvent(event)
    assert state[0].rowCount() == 1  # still 1 event

def test_change_next_state(state_machine) -> None:
    '''Test changing the next state and error state.'''
    state_machine.statetree.clearSelect()
    item = state_machine.statetree.model.findItems('STATE1')
    event = item[0].child(0)
    state_machine.eventClicked(event)
    state_machine.configBox.next_state_edt.setCurrentIndex(0)
    assert state_machine.configBox.next_state_edt.currentText() == 'STATE1'
    state_machine.configBox.next_state_err_edt.setCurrentIndex(0)
    assert state_machine.configBox.next_state_err_edt.currentText() == 'STATE1'
    state_machine.deselect()
    state_machine.getStatesToUpdate('BadState', 'BadState')

def test_change_thread_error(state_machine, monkeypatch) -> None:
    '''Test changing the CPU mask to an erroneous value.'''
    item = state_machine.statetree.model.findItems('STATE1')
    state_machine.stateClicked(item[0])
    value = state_machine.configBox.thread_tbl.item(0, 1)
    monkeypatch.setattr('xmarte.qt5.services.state_service.windows.state_machine_window.showErrorDialog', lambda *args: print())
    value.setText('t')

def test_add_remove_thread(state_machine, qtbot) -> None:
    '''Test adding and removing a thread from a state.'''
    item = state_machine.statetree.model.findItems('STATE1')
    state_machine.stateClicked(item[0])
    assert state_machine.configBox.thread_tbl.rowCount() == 1  # 1 thread
    qtbot.mouseClick(state_machine.configBox.add_thread_btn, Qt.LeftButton)
    assert state_machine.configBox.thread_tbl.rowCount() == 2  # 2 threads
    state_machine.configBox.thread_tbl.selectRow(0)
    qtbot.mouseClick(state_machine.configBox.rem_thread_btn, Qt.LeftButton)
    assert state_machine.configBox.thread_tbl.rowCount() == 1  # 1 thread

def test_state_edge_arrow() -> None:
    '''Test the code to draw the state edge arrow.'''
    p1 = QPointF(3200.0, 3160.0)
    p2 = QPointF(3204.9, 3159.5)
    grEdge = StateGraphicsEdge(None, None)
    grEdge.arrowCalc(p1, p2)

    p1 = QPointF(0, 0)
    p2 = QPointF(0, 0)
    grEdge = StateGraphicsEdge(None, None)
    grEdge.arrowCalc(p1, p2)

def test_state_message_preview(state_machine) -> None:
    '''Test displaying the state message preview.'''
    edge = state_machine.main_view.scene().scene.edges[0]
    msg = StateMessagePreview(edge)
    msg.setPos()

def test_state_thread_functions(mainwindow, qtbot) -> None:
    '''Test retreiving all gams in a given state and thread.'''
    create_basic_diagram(mainwindow, qtbot)
    gams = StateDefinitionService.getStateThreadFunctions(mainwindow, 'State1', 'Thread1')
    assert len(gams) == 2

def test_save_open_state_machine(mainwindow, qtbot) -> None:
    '''Test saving and opening the state machine window.'''
    qtbot.mouseClick(mainwindow.API.getServiceByName('StateDefinitionService').state_machine, Qt.LeftButton)
    state_machine = mainwindow.newwindow
    qtbot.mouseClick(state_machine.add_btn, Qt.LeftButton)
    state_machine.menuBar().children()[1].actions()[0].trigger()
    qtbot.mouseClick(mainwindow.API.getServiceByName('StateDefinitionService').state_machine, Qt.LeftButton)
    state_machine = mainwindow.newwindow
    state = state_machine.statetree.model.findItems('STATE')
    assert len(state) == 1
    assert state_machine.scene.getEdgeClass() == StateEdge

def test_state_edge_dragging_class(state_machine) -> None:
    '''Test the getStateEdgeClass method in the StateEdgeDragging class.'''
    assert state_machine.main_view.dragging.getStateEdgeClass(socket_type=0) == NextStateEdge
    assert state_machine.main_view.dragging.getStateEdgeClass(socket_type=1) == NextErrorStateEdge

    state_machine.main_view.dragging.edgeDragStart(item=state_machine.scene.nodes[0].outputs[0].grSocket)
    state_machine.main_view.dragging.edgeDragEnd(item=state_machine.scene.nodes[1].inputs[0].grSocket)  # valid socket
    state_machine.main_view.dragging.edgeDragStart(item=state_machine.scene.nodes[0].outputs[0].grSocket)
    state_machine.main_view.dragging.edgeDragEnd(item=state_machine.scene.nodes[1].inputs[1].grSocket)  # invalid socket
    state_machine.main_view.dragging.edgeDragStart(item=state_machine.scene.nodes[0].outputs[0].grSocket)
    state_machine.main_view.dragging.edgeDragEnd(item=None)  # no socket

def test_state_editor_view(state_machine, qtbot) -> None:
    '''Test interacting with the StateEditorGRView.'''
    qtbot.mouseClick(state_machine.main_view, Qt.LeftButton)
    qtbot.keyPress(state_machine.main_view, Qt.Key_Delete)
    qtbot.keyPress(state_machine.main_view, Qt.Key_Escape)

def test_state_edges(state_machine) -> None:
    '''Test state edge messages and paths.'''
    assert state_machine.scene.edges[0].loadStateMessages() is not None
    state_machine.scene.edges[0].saveStateMessages(None)
    assert state_machine.scene.edges[0].loadStateMessages() is None

    path = GraphicsEdgePathArc(state_machine.scene.edges[0].grEdge)
    path.resetPath()
    path.setControlPoint(0, 0, 0)
    
def test_open(mainwindow, monkeypatch, qtbot) -> None:
    '''Test saving and opening the state machine window.'''
    filepath = os.path.join(TEST_FILES_DIR, "saved_state.xmt")
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (
            filepath,
            "xmt (*.xmt)",
        ),
    )
    mainwindow.fileToolBar.openAction.trigger()  # load network
    qtbot.mouseClick(mainwindow.API.getServiceByName('StateDefinitionService').state_machine, Qt.LeftButton)
    state_machine = mainwindow.newwindow
