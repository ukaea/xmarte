''' The Type definition service which manages complex types in MARTe2 allowing
the user toe define them and can auto generate these to C++ code '''
import os
from functools import partial

from PyQt5.QtWidgets import QAction, QPushButton
from martepy.marte2.type_database import TypeDBv2
from xmarte.qt5.services.service import Service
from xmarte.qt5.libraries.functions import getUserFolder
from .windows.types_window import TypesDBWindow

class TypeDefinitionService(Service):
    '''Handles complex types.'''

    service_name = 'TypeDefinitionService'

    def __init__(self, application) -> None:
        super().__init__(application)
        self.addToolbarOptions(self.application.editToolBar.service_layout)
        self.template_path = os.path.join(os.path.dirname(__file__), 'templates')
        if not os.path.exists(path := os.path.join(os.path.dirname(__file__), 'types')):
            os.mkdir(path)
        self.output_path = path
        self.loadMenu(None)

    def loadMenu(self, menu_bar):
        ''' Load the menu for this service '''
        self.advancedMenu = self.application.menuBar.advancedMenu
        self.type_db_wndact = QAction("&Type Database", self.application.menuBar)
        self.type_db_wndact.triggered.connect(partial(self.application.menuBar.openwindow,
                                                      TypesDBWindow))
        self.advancedMenu.insertAction(self.advancedMenu.actions()[0], self.type_db_wndact)

    def addToolbarOptions(self, layout) -> None:
        '''Add type generation button to toolbar.'''
        self.gen_types = QPushButton("Generate types")
        self.gen_types.clicked.connect(self.gen)
        #layout.addWidget(self.gen_types)  # uncomment to add gen types button to tool bar

    def gen(self) -> None:
        '''Generate .cpp and .h files from the type database.'''
        type_db = TypeDBv2()
        type_db.loadDb(os.path.join(getUserFolder(),"typedb"))
        return type_db.toLibrary(self.output_path)

    def getLibNames(self):
        ''' Return a list of type names '''
        type_db = TypeDBv2()
        type_db.loadDb(os.path.join(getUserFolder(),"typedb"))
        return list(type_db.types.keys())
