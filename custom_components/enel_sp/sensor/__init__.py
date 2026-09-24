"""Plataforma de sensores do enel_sp."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import callback

from .bill_amount import EnelSpBillAmountSensor
from .bill_consumption import EnelSpBillConsumptionSensor
from .bill_due_date import EnelSpBillDueDateSensor
from .bill_status import EnelSpBillStatusSensor
from .energy_price import EnelSpEnergyPriceSensor
from .meter_reading import EnelSpMeterReadingSensor
from .open_bills_amount import EnelSpOpenBillsAmountSensor
from .open_bills_count import EnelSpOpenBillsCountSensor
from .tariff_flag import EnelSpTariffFlagSensor

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from ..coordinator import EnelSpDataUpdateCoordinator
    from ..data import EnelSpConfigEntry, EnelSpInstallation, EnelSpPayload
    from ..entity import EnelSpEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: EnelSpConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura a plataforma de sensores, adicionando instalações conforme o portal."""
    coordinator = entry.runtime_data.coordinator
    known_numbers: set[str] = set()

    @callback
    def _async_add_new_installations() -> None:
        payload: EnelSpPayload | None = coordinator.data
        if payload is None:
            return
        new_installations = [
            data.installation
            for number, data in payload.installations.items()
            if number not in known_numbers
        ]
        if not new_installations:
            return
        known_numbers.update(installation.number for installation in new_installations)
        async_add_entities(
            [
                entity
                for installation in new_installations
                for entity in _entities_for_installation(coordinator, installation)
            ],
        )

    _async_add_new_installations()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_installations))


def _entities_for_installation(
    coordinator: EnelSpDataUpdateCoordinator,
    installation: EnelSpInstallation,
) -> tuple[EnelSpEntity, ...]:
    """Retorna os sensores que toda instalação expõe."""
    return (
        EnelSpBillAmountSensor(coordinator, installation),
        EnelSpBillConsumptionSensor(coordinator, installation),
        EnelSpBillDueDateSensor(coordinator, installation),
        EnelSpBillStatusSensor(coordinator, installation),
        EnelSpEnergyPriceSensor(coordinator, installation),
        EnelSpMeterReadingSensor(coordinator, installation),
        EnelSpOpenBillsAmountSensor(coordinator, installation),
        EnelSpOpenBillsCountSensor(coordinator, installation),
        EnelSpTariffFlagSensor(coordinator, installation),
    )
