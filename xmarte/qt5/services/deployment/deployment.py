''' The Deployment service - not yet complete, will allow us to deploy to hardware '''

from PyQt5.QtWidgets import QAction

from qtpy.QtWidgets import QMenu

from xmarte.qt5.services.service import Service
from .windows.deploy_window import DeployWindow

class DeploymentService(Service):
    ''' The service instance for deploying to hardware '''
    service_name = 'DeploymentService'
    def __init__(self, application):
        super().__init__(application)
        self.deploy_action = None
        self.status_action = None

    def loadMenu(self, menu_bar):
        ''' Load our menu items '''
        deployMenu = QMenu("&Deployment", menu_bar)
        self.deploy_action = QAction("&Deploy")
        self.deploy_action.triggered.connect(self.deployWnd)
        self.status_action = QAction("&Status")
        self.status_action.triggered.connect(self.statusWnd)
        deployMenu.addAction(self.deploy_action)
        deployMenu.addAction(self.status_action)
        menu_bar.addMenu(deployMenu)

    def deployWnd(self):
        ''' Open the deployment window '''
        self.application.newwindow = DeployWindow(self.application, self.application.app)

    def statusWnd(self):
        ''' Open the Status Window of devices '''
        self.application.newwindow = DeployWindow(self.application,
                                                  self.application.app,
                                                  status=True)

    @staticmethod
    def getDefaultSettings():
        '''
        Static method for the config manager to establish defaults when a config file
        needs rebuilding
        '''
        return {
                "deployment_udp_port": 8004,
                "deployment_ftp_port": 8005,
                }
