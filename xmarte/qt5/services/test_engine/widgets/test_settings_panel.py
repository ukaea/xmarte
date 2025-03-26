'''
The Testing Settings Panel as a widget
'''

from functools import partial
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QComboBox,
)

from xmarte.qt5.widgets.settings.panel import BasePanel

class TestPanel(BasePanel):
    '''
    The General settings widget panel that appears on the right hand side in the
    settings window when general is selected (or by default on load).
    '''
    def __init__(self, parent=None, settings_data={}, application=None):
        super().__init__(parent)
        self.data = settings_data
        _ = application

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Generate the Advanced Panel
        ahlay = QHBoxLayout()
        panel = QWidget(self)
        panel.setLayout(ahlay)
        layout.addWidget(panel)

        link = """https://marte21.gitpages.ccfe.ac.uk/xmarte/\
options.html#general-menu"""
        self.defineHelp(layout, link)

        defaults = ['Max Cycles','Execution Rate (Hz)']

        sched_lbl = QLabel("Default Solver:")
        layout.addWidget(sched_lbl)
        self.sched_combo = QComboBox()
        self.sched_combo.addItems(['MARTe2'])
        self.sched_combo.setCurrentText(self.data.settings['TestPanel']['solver'])
        self.sched_combo.key = 'solver'
        self.sched_combo.currentTextChanged.connect(partial(self.combochange,
                                                            widget=self.sched_combo))
        layout.addWidget(self.sched_combo)

        self.defineDefaultNames(layout, defaults)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(spacer)

    def defineDefaultNames(self, layout, defaults):
        '''Create widgets to allow the user to define defaults for the application.'''
        for default in defaults:
            default_lbl = QLabel(default)
            default_edit = QLineEdit()
            default_edit.setText(self.data.settings["TestPanel"][default])
            default_edit.key = default
            default_edit.textChanged.connect(partial(self.linechange, widget=default_edit))
            layout.addWidget(default_lbl)
            layout.addWidget(default_edit)
            setattr(self,
                    default.lower().replace(' ','_').replace('(','').replace(')',''),
                    default_edit)

    @staticmethod
    def generateDefaults():
        ''' Generate default values in the abscence of a config yaml '''
        return {'solver':'MARTe2','Max Cycles':'500','Execution Rate (Hz)':'500'}
