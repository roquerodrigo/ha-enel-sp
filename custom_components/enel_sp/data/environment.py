"""Formato tipado da configuração do site que o portal publica."""

from __future__ import annotations

from typing import TypedDict


class EnelSpEnvironment(TypedDict, total=False):
    """Subconjunto de ``/bin/enel-br/<site>/environment`` que a integração usa."""

    portalSPUri: str
