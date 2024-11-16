from typing import Optional
from dataclasses import dataclass
from datetime import datetime

# TODO: Fully implement

@dataclass
class ErrorContext:
    """Context information for errors to aid debugging"""
    timestamp: datetime
    operation: str = "unknown"
    channel_id: Optional[int] = None
    channel_title: Optional[str] = None
    message_id: Optional[int] = None
    file_id: Optional[int] = None
    additional_info: Optional[dict] = None

    @classmethod
    def new(cls, **kwargs):
        return cls(timestamp=datetime.now(), **kwargs)

class TeledeckError(Exception):
    """
    Base exception for all Teledeck errors.
    Includes context information to aid debugging.
    """
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.context = context or ErrorContext.new()

    def __str__(self):
        base_msg = super().__str__()
        if self.context:
            return f"{base_msg}\nContext: {self.context}"
        return base_msg

class ConfigurationError(TeledeckError):
    """Raised when there are issues with configuration values"""
    pass

class TelegramError(TeledeckError):
    """Base class for Telegram-related errors"""
    pass

class NetworkError(TelegramError):
    """Raised for network-related issues (timeouts, connection failures)"""
    pass

class RateLimitError(TelegramError):
    """Raised when hitting Telegram API rate limits"""
    def __init__(self, message: str, retry_after: int, context: Optional[ErrorContext] = None):
        super().__init__(message, context)
        self.retry_after = retry_after

class AuthenticationError(TelegramError):
    """Raised for authentication/authorization issues"""
    pass

class MediaError(TeledeckError):
    """Base class for media processing errors"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, context)
    pass

class DownloadError(MediaError):
    """Raised when media download fails"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None,
                 can_retry: bool = True):
        super().__init__(message, context)
        self.can_retry = can_retry

class ProcessingError(MediaError):
    """Raised when processing downloaded media fails"""
    pass

class StorageError(MediaError):
    """Raised when there are issues storing media files"""
    pass

class DatabaseError(TeledeckError):
    """Base class for database-related errors"""
    pass

class IntegrityError(DatabaseError):
    """Raised when database constraints are violated"""
    pass

class QueueError(TeledeckError):
    """Base class for queue-related errors"""
    pass

class QueueFullError(QueueError):
    """Raised when the queue is full and cannot accept more items"""
    pass
