''' Exception definitions for the test service '''

class HandledException(Exception):
    """
    Exception that is handled elsewhere
    """

class AbortException(Exception):
    """
    Exception that is not handled and needs aborting...
    """
