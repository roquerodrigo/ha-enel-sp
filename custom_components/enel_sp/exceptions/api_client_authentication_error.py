"""Erro de autenticação levantado pelo cliente da API."""

from __future__ import annotations

from .api_client_error import EnelSpApiClientError


class EnelSpApiClientAuthenticationError(
    EnelSpApiClientError,
):
    """Exceção que indica um erro de autenticação."""
