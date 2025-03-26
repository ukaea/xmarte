import pdb
from unittest.mock import patch

from test.utilities import *
from xmarte.qt5.windows.help_window import HelpWindow

def test_about_menuitem(mainwindow, qtbot, monkeypatch) -> None:
    help_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Help')
    about_action = next(a for a in help_menu.menu().actions() if a.text() == '&About')
    about_action.triggered.emit()
    assert mainwindow.newwindow.__class__ == HelpWindow
    
def test_docs_menuitems(mainwindow, qtbot, monkeypatch) -> None:
    help_menu = next(a for a in mainwindow.menuBar.actions() if a.text() == '&Help')
    docs_action = next(a for a in help_menu.menu().actions() if a.text() == '&Documentation')
    xmarte_action = next(a for a in docs_action.menu().actions() if a.text() == '&xmarte')
    with patch('webbrowser.open') as mock_open:
        xmarte_action.triggered.emit()
        mock_open.assert_called_once_with("https://github.com/ukaea/xmarte/")
        
    marte_python_action = next(a for a in docs_action.menu().actions() if a.text() == '&marte2_python')
    with patch('webbrowser.open') as mock_open:
        marte_python_action.triggered.emit()
        mock_open.assert_called_once_with("https://ukaea.github.io/MARTe2-python/")