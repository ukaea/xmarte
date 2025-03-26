
from test.utilities import *

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtChart import QLineSeries
from PyQt5.QtWidgets import QToolBar, QAction

from xmarte.qt5.services.data_handler.graph_window.data.data_node import DataNode
from xmarte.qt5.services.data_handler.graph_window.plot.plot_node import PlotNode
from xmarte.qt5.services.data_handler.graph_window.graph_window import GraphWindow
from xmarte.qt5.services.data_handler.widgets.playback_widget import PlayToolbarWidget
from xmarte.nodeeditor.node_edge import XMARTeEdge

@pytest.fixture
def graph_window(mainwindow, monkeypatch) -> GraphWindow:
    '''Place blocks, import data, and open the graph window.'''
    import_data(mainwindow, monkeypatch)
    playbackToolBar = next(a for a in mainwindow.findChildren(QToolBar) if a.__class__ == PlayToolbarWidget)
    open_graph_action = next(a for a in playbackToolBar.actions() if a.text() == '&Graph Window')
    open_graph_action.triggered.emit()
    return mainwindow.newwindow

@pytest.fixture
def plot_graph(graph_window, qtbot) -> GraphWindow:
    '''Plot a single line series'''
    graph_window.selectionpanel.load_options.setCurrentIndex(2)
    qtbot.mouseClick(
        graph_window.selectionpanel.selection_options.itemAt(0).widget(),
        Qt.LeftButton
    )
    data_node = next(node for node in graph_window.editor.scene.nodes if isinstance(node, DataNode))
    plot_node = next(node for node in graph_window.editor.scene.nodes if isinstance(node, PlotNode))
    Edge = graph_window.editor.scene.getEdgeClass()
    Edge(graph_window.editor.scene, start_socket=data_node.outputs[0], end_socket=plot_node.inputs[1], edge_type=2)
    plot_node.onInputChanged(plot_node.inputs[1])
    return graph_window

def get_action(window, label: str='&Exit') -> QAction:
    return next(act for act in window.menuBar().actions()[0].menu().actions() if act.text() == label)

def test_plot_graph(plot_graph) -> None:
    '''Test plotting a single line series.'''
    assert len(charts := plot_graph.rightlayout.plotnode.chart_list) == 1  # assert there is just one plot
    assert len(charts[0].series()) == 1  # assert there is one series within the plot
    assert isinstance(line := charts[0].series()[0], QLineSeries)  # assert the series is a line series
    exitAction = get_action(plot_graph)
    exitAction.trigger()

def test_remove_plot(plot_graph) -> None:
    '''Test deleting an edge to remove the plot.'''
    plot_graph.editor.scene.edges[0].remove()
    plot_node = next(node for node in plot_graph.editor.scene.nodes if isinstance(node, PlotNode))
    plot_node.onInputChanged(plot_node.inputs[1])

def test_plot_node_sockets(plot_graph) -> None:
    '''Test adding and remove plot node sockets.'''
    plot_node = next(node for node in plot_graph.editor.scene.nodes if isinstance(node, PlotNode))
    data_node = next(node for node in plot_graph.editor.scene.nodes if isinstance(node, DataNode))
    Edge = plot_graph.editor.scene.getEdgeClass()
    XMARTeEdge(plot_graph.editor.scene, start_socket=data_node.outputs[0], end_socket=plot_node.inputs[1], edge_type=2)
    plot_node.onInputChanged(plot_node.inputs[1])
    XMARTeEdge(plot_graph.editor.scene, start_socket=data_node.outputs[1], end_socket=plot_node.inputs[0], edge_type=2)
    plot_node.onInputChanged(plot_node.inputs[0])
    XMARTeEdge(plot_graph.editor.scene, start_socket=data_node.outputs[0], end_socket=plot_node.inputs[2], edge_type=2)
    plot_node.onInputChanged(plot_node.inputs[2])

    plot_graph.editor.scene.edges[2].remove()
    plot_node.onInputChanged(plot_node.inputs[2])

def test_right_click_menu(plot_graph) -> None:
    '''Test loading the right click menu options.'''
    plot_graph.selectionpanel.buttonMenu(plot_graph.selectionpanel.selection_options.itemAt(0).widget(), None)

def test_latest_plot(plot_graph) -> None:
    '''Test showing the latest plot.'''
    plot_graph.selectionpanel.latestPlotButton(plot_graph.selectionpanel.selection_options.itemAt(0).widget())

def test_plot_interaction(plot_graph) -> None:
    '''Test zooming on the plot.'''
    event = QMouseEvent(
        QMouseEvent.MouseButtonPress,
        QPoint(50, 50),
        Qt.RightButton,
        Qt.RightButton,
        Qt.NoModifier
    )
    plot_graph.rightlayout.history[0].mouseReleaseEvent(event)

def test_expand_parameters(plot_graph, qtbot) -> None:
    '''Test expanding a data node parameter section.'''
    data_node = next(node for node in plot_graph.editor.scene.nodes if isinstance(node, DataNode))
    qtbot.mouseClick(data_node.grNode.content.expand, Qt.LeftButton)  # collapse
    qtbot.mouseClick(data_node.grNode.content.expand, Qt.LeftButton)  # expand

def test_export_graph(plot_graph, monkeypatch, qtbot) -> None:
    '''Test exporting a graph to a pdf.'''
    exportAction = get_action(plot_graph, label='&Export as PDF')
    path = os.path.join(TEST_FILES_DIR, 'graph_export.pdf')
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
        lambda *args, **kwargs: (path, 'pdf (*.pdf)'),
    )
    exportAction.trigger()
    def pdf_exists() -> None:
        assert os.path.exists(path)
    def pdf_removed() -> None:
        assert not os.path.exists(path)
    qtbot.waitUntil(pdf_exists)
    os.remove(path)
    qtbot.waitUntil(pdf_removed)

def test_save_load(plot_graph, monkeypatch, qtbot) -> None:
    '''Test saving and loading a plot setup.'''
    saveAction = get_action(plot_graph, label='&Save')
    path = os.path.join(TEST_FILES_DIR, 'graph_save.xgraph')
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
        lambda *args, **kwargs: (path, 'graph report (*.xgraph)'),
    )
    saveAction.trigger()
    def save_exists() -> None:
        assert os.path.exists(path)
    qtbot.waitUntil(save_exists)

    loadAction = get_action(plot_graph, label='&Load')
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
        lambda *args, **kwargs: (path, 'graph report (*.xgraph)'),
    )
    loadAction.trigger()
