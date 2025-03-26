"""Saving of the recovery file in case of a crash."""

import os
import threading

from PyQt5.QtWidgets import QMessageBox

from xmarte.qt5.services.service import Service

class RecoveryService(Service):
    """Save recovery file service class"""
    service_name = 'RecoveryService'
    def __init__(self, application) -> None:
        """Initialise the service and create the recovery directory and file"""
        super().__init__(application)
        self.recovery_doc: str = self.application.settings['hidden']['recovery_document']
        self._lock = threading.Lock()
        self.application.scene.addModifiedListener(self.saveRecovery)

    def _save(self) -> None:
        with self._lock:
            try:
                self.application.API.saveToFile(self.recovery_doc, cursor=False)
            except (AttributeError, ValueError):
                pass # Don't care, this is to help users but sometimes we save during bad states

    def saveRecovery(self, _) -> None:
        """Save recovery file"""
        threading.Thread(target=self._save, args=()).start()

    def loadRecovery(self) -> None:
        """Check if a recovery file exists and load it"""
        if os.path.exists(self.recovery_doc) and not os.path.isdir(self.recovery_doc):
            # Aply there are some so lets ask the user
            msg = QMessageBox.question(
                self.application,
                "Recovery Document",
                "A recovery document has been found, do you want to restore it?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if msg == QMessageBox.Yes:
                self.application.API.loadFile(self.recovery_doc)
            else:
                # Delete the recovery directory
                os.remove(self.recovery_doc)
