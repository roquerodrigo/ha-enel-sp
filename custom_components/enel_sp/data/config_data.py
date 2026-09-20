"""Formato tipado das credenciais persistidas na config entry."""

from __future__ import annotations

from typing import TypedDict


class EnelSpConfigData(TypedDict):
    """Formato das credenciais persistidas na config entry."""

    username: str
    password: str
