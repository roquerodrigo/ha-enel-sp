"""A conta de cliente por trás do login do portal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .installation import EnelSpInstallation
    from .tariff_flag import EnelSpTariffFlag


@dataclass(frozen=True)
class EnelSpAccount:
    """Identidade do cliente, bandeira tarifária e as instalações que o portal lista."""

    enel_id: str
    name: str
    tariff_flag: EnelSpTariffFlag
    installations: tuple[EnelSpInstallation, ...]

    @property
    def active_installations(self) -> tuple[EnelSpInstallation, ...]:
        """Retorna as instalações que o cliente ainda mantém."""
        return tuple(
            installation for installation in self.installations if installation.active
        )
