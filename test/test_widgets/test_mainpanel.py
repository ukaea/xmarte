
from collections import OrderedDict
import pdb
import pytest

from ..utilities import *

from martepy.marte2.reader import readApplicationText

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QWidget, QPushButton, QVBoxLayout


def test_mainpanel_listeners(mainwindow):
    def listener(node):
        pass
    mainwindow.rightpanel.addSelectedListener(listener)
    mainwindow.rightpanel.clearSelectedListeners()
    mainwindow.rightpanel.addDeselectedListener(listener)
    mainwindow.rightpanel.clearDeselectedListeners()
    class scene():
        def addModifiedListener(self, listener):
            pass
    mainwindow.rightpanel.setupListener(scene())