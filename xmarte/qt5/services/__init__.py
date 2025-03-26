'''
Default service definitions
'''

from xmarte.qt5.services.recovery import RecoveryService
from xmarte.qt5.services.test_engine.test_engine import TestExecutor
from xmarte.qt5.services.api_manager.api_manager import APIManager
from xmarte.qt5.services.split_view import SplitView
from xmarte.qt5.services.app_def.app_def import ApplicationDefinition
from xmarte.qt5.services.data_handler.data_handler import DataManager
from xmarte.qt5.services.deployment.deployment import DeploymentService
from xmarte.qt5.services.state_service.states import StateDefinitionService
from xmarte.qt5.services.type_db.type_db import TypeDefinitionService
from xmarte.qt5.services.file_support.file_support import FileSupportService
from xmarte.qt5.services.compilation.compile import Compiler

__all__ = [
    "RecoveryService",
    "TestExecutor",
    "APIManager",
    "SplitView",
    "ApplicationDefinition",
    "DataManager",
    "DeploymentService",
    "StateDefinitionService",
    "TypeDefinitionService",
    "FileSupportService",
    "Compiler"
]
