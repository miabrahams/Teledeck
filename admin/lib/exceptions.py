# exceptions.py
class TelegramClientError(Exception):
    """Base exception for telegram client errors"""
    pass

class ChannelError(TelegramClientError):
    """Raised when there are issues with channel operations"""
    pass

class MediaProcessingError(TelegramClientError):
    """Raised when there are issues processing media"""
    pass