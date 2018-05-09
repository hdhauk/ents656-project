"""reasons for connection error"""
LOW_SIGNAL = 0
NO_FREE_CHANNELS = 1


class ConnectionError(Exception):
    """Exception thrown when a user fail to connect to a 
    tower, reason should be either LOW_SIGNAL or NO_FREE CHANNELS"""

    def __init__(self, reason):
        self.reason = reason


class InitializationError(Exception):
    """Failure due to faulty or missing initalization."""
    pass
