"""Application package for the Teledeck AI microservice."""

from .container import ServiceContainer, get_container
from .http_api import create_http_app
from .grpc_server import create_grpc_server
from .settings import Settings

__all__ = [
    "ServiceContainer",
    "get_container",
    "create_http_app",
    "create_grpc_server",
    "Settings",
]
