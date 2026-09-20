"""Formato tipado de uma linha ``ET_INST`` do usuário atual do portal."""

from __future__ import annotations

from typing import TypedDict


class EnelSpInstallationRow(TypedDict, total=False):
    """Registro de instalação do SAP como o portal o serializa."""

    ANLAGE: str
    APELIDO: str
    ENDERECO: str
    PARTNER: str
    VERTRAG: str
    VKONT: str
    NIVEL_TENSAO: str
    SERIE: str
    EINZDAT: str
    AUSZDAT: str
