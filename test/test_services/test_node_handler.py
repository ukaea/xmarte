
from test.utilities import *

from xmarte.qt5.nodes.node_handler import NodeHandler

def test_safe_get_nodes(mainwindow, qtbot) -> None:
    create_basic_diagram(mainwindow, qtbot)
    nodes = NodeHandler.getNodes(mainwindow.scene, safe=False)
    safe_nodes = NodeHandler.getNodes(mainwindow.scene, safe=True)

    assert len(nodes) == 2
    assert len(safe_nodes) == 2
    assert nodes[0].btype == safe_nodes[0].btype
    assert nodes[1].btype == safe_nodes[1].btype
    assert nodes == safe_nodes
    assert not nodes is safe_nodes  # not the same memory location (safe duplicates the nodes)

def test_old_execution_algorithm(mainwindow, qtbot, monkeypatch) -> None:
    create_basic_diagram(mainwindow, qtbot)
    api = mainwindow.API

    orig = NodeHandler.getExecutionGroups
    def mock(nodes, improved_algorithm=False):
        return orig(nodes, improved_algorithm)

    monkeypatch.setattr(NodeHandler, 'getExecutionGroups', mock)
    api.buildApplication()
