'''
The available setting panels:
- General
- Remote
- Compilation
- Defaults
'''

from xmarte.qt5.widgets.settings.defaults import DefaultPanel
from xmarte.qt5.widgets.settings.general import GeneralPanel

__all__ = [
    "GeneralPanel",
    "DefaultPanel",
]
