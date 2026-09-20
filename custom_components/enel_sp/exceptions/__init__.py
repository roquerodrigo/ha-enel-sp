"""Classes de exceção do cliente da API do enel_sp."""

from __future__ import annotations

from .api_client_authentication_error import (
    EnelSpApiClientAuthenticationError,
)
from .api_client_communication_error import (
    EnelSpApiClientCommunicationError,
)
from .api_client_error import EnelSpApiClientError

__all__ = [
    "EnelSpApiClientAuthenticationError",
    "EnelSpApiClientCommunicationError",
    "EnelSpApiClientError",
]
