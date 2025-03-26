
import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox
from unittest.mock import patch
from xmarte.qt5.exception_hook import reportException, exceptionHook
from .utilities import qapp

def test_exception_report():
    with patch('webbrowser.open') as mock_open:
        reportException(ValueError())
        mock_open.assert_called_once_with("https://git.ccfe.ac.uk/marte21/xmarte/-/issues/new?issue[title]=exception&issue[description]=Error%3A%20%3A%20``")
        
def test_exception_prompt(qapp, mocker):
    # Mock QMessageBox to simulate a user response
    mock_msg_box = mocker.patch.object(QMessageBox, 'exec_', return_value=QMessageBox.Yes)
    
    # Mock reportException to track if it gets called
    mock_report = mocker.patch("xmarte.qt5.exception_hook.reportException")

    # Call the exception hook with a sample exception
    sample_exception = ValueError("Sample exception")
    exceptionHook(ValueError, sample_exception, None)

    # Assertions
    mock_msg_box.assert_called_once()  # Check if QMessageBox was shown
    mock_report.assert_called_once_with(sample_exception)  # Check if reportException was called with the exception