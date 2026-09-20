"""Payload do coordinator: a conta do cliente e as suas instalações ativas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .account import EnelSpAccount
    from .installation_data import EnelSpInstallationData


@dataclass(frozen=True)
class EnelSpPayload:
    """Dados da conta do cliente e de cada instalação, indexados pelo número."""

    account: EnelSpAccount
    installations: Mapping[str, EnelSpInstallationData]
