"""Formato tipado do objeto ``currentUser`` que o portal retorna após o login."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .installation_row import EnelSpInstallationRow


class EnelSpCurrentUser(TypedDict, total=False):
    """Subconjunto do cadastro do usuário atual do qual a integração depende."""

    enel_id: str
    access_token: str
    E_NOME: str
    E_SOBRENOME: str
    E_BANDEIRA: str
    ET_INST: list[EnelSpInstallationRow]


class EnelSpCurrentUserResponse(TypedDict, total=False):
    """Envelope de ``/bin/enel-br/<site>/currentuser``."""

    status: str
    message: str
    currentUser: EnelSpCurrentUser | None
