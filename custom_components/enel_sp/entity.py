"""Classe base EnelSpEntity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import EnelSpDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .data import (
        EnelSpBill,
        EnelSpInstallation,
        EnelSpInstallationData,
        EnelSpPayload,
    )


class EnelSpEntity(CoordinatorEntity[EnelSpDataUpdateCoordinator]):
    """Entidade base vinculada a uma instalação da conta do cliente."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EnelSpDataUpdateCoordinator,
        installation: EnelSpInstallation,
    ) -> None:
        """Vincula a entidade à instalação que ela reporta."""
        super().__init__(coordinator)
        self._installation = installation

    @property
    def payload(self) -> EnelSpPayload | None:
        """Retorna o último payload obtido, se houver."""
        return self.coordinator.data

    @property
    def installation_data(self) -> EnelSpInstallationData | None:
        """Retorna a instalação obtida por último, ou None se o portal a removeu."""
        payload = self.payload
        if payload is None:
            return None
        return payload.installations.get(self._installation.number)

    @property
    def latest_bill(self) -> EnelSpBill | None:
        """Retorna a conta mais recente da instalação, se houver."""
        data = self.installation_data
        return None if data is None else data.latest_bill

    @property
    def available(self) -> bool:
        """Fica indisponível quando o portal deixa de listar a instalação."""
        return super().available and self.installation_data is not None

    @property
    def device_info(self) -> DeviceInfo:
        """
        Retorna um dispositivo por instalação, com o nome dado pelo cliente.

        O apelido do portal também vai em ``model``, para que o cartão do dispositivo
        continue a mostrá-lo quando o usuário renomeia o dispositivo no Home Assistant.
        """
        installation = self._installation
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{self.coordinator.config_entry.entry_id}_{installation.number}",
                ),
            },
            name=installation.name,
            manufacturer="Enel",
            model=installation.name,
            serial_number=installation.number,
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, str | int | float]:
        """Expõe a instalação e o mês de faturamento a que o estado se refere."""
        attributes: dict[str, str | int | float] = {
            "installation_number": self._installation.number,
            "meter_serial": self._installation.meter_serial,
        }
        bill = self.latest_bill
        if bill is not None:
            attributes["bill_year"] = bill.year
            attributes["bill_month"] = bill.month
        return attributes
