"""Erro de comunicação levantado pelo cliente da API."""

from __future__ import annotations

from .api_client_error import EnelSpApiClientError


class EnelSpApiClientCommunicationError(
    EnelSpApiClientError,
):
    """Exceção que indica um erro de comunicação."""
